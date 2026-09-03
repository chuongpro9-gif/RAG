import os
import sys
from pathlib import Path
import google.generativeai as genai
import uuid
from datetime import datetime, timezone

# Link to buoi_17 to reuse SecureRetrievalAdapter and audit_logger
b17_path = Path(__file__).parent.parent.parent / "buoi_17"
if str(b17_path) not in sys.path:
    sys.path.insert(0, str(b17_path))

from scripts.secure_retrieval_adapter import SecureRetrievalAdapter
from scripts.audit_logger import log_audit_event

class RealAIEngine:
    def __init__(self):
        self.retriever = SecureRetrievalAdapter()
        # Ensure API key is loaded
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        # Đổi sang gemini-3.7-flash để dùng một "rổ" hạn mức (quota) hoàn toàn mới 
        self.model = genai.GenerativeModel('gemini-3.7-flash')

    def check_conflicts(self, domain, user_role, user_id):
        # 1. Retrieve documents related to domain
        query = f"Quy định ngân hàng về {domain}"
        res = self.retriever.retrieve(query, user_roles=[user_role], method="hybrid_rerank", top_k=3)
        results = res["results"]
        if not results:
            return []

        context_str = ""
        doc_ids = []
        for r in results:
            doc_ids.append(r["document_id"])
            chunk_text = r['text'][:1500] + "...(lược bớt)" if len(r['text']) > 1500 else r['text']
            context_str += f"--- NGUỒN: {r['title']} ---\n{chunk_text}\n\n"

        prompt = f"""Bạn là Chuyên gia Kiểm toán Ngân hàng.
Hãy đọc các văn bản quy định dưới đây và tìm xem có bất kỳ sự CHÊNH LỆCH hoặc XUNG ĐỘT nào giữa chúng không.
Ví dụ: Văn bản A bảo 8%, văn bản B bảo 9%. Hoặc Văn bản A cho phép, Văn bản B cấm.
        
NGỮ CẢNH:
{context_str}

Hãy liệt kê các điểm mâu thuẫn (nếu có). Trả lời ngắn gọn dưới dạng JSON array:
[
  {{
    "conflict_id": "CFL_01",
    "domain": "{domain}",
    "doc_a_citation": "Tên văn bản 1",
    "doc_a_text": "Trích dẫn 1",
    "doc_b_citation": "Tên văn bản 2",
    "doc_b_text": "Trích dẫn 2",
    "conflict_type": "Loại xung đột",
    "severity": "HIGH/MEDIUM/LOW",
    "description": "Giải thích chi tiết bằng tiếng Việt",
    "review_status": "NEEDS_HUMAN_REVIEW"
  }}
]
Chỉ trả về JSON array, không kèm markdown. Nếu không có xung đột, trả về mảng rỗng []"""
        
        try:
            # Tăng output token lên 2048 để tránh việc sinh JSON bị cắt ngang giữa chừng
            config = genai.types.GenerationConfig(max_output_tokens=2048)
            response = self.model.generate_content(prompt, generation_config=config)
            txt = response.text.replace("```json", "").replace("```", "").strip()
            import json
            out = json.loads(txt)
            for item in out:
                item["request_id"] = str(uuid.uuid4())
                
            log_audit_event(user_id, str([user_role]), "COMPLIANCE_CROSS_CHECK", query, "hybrid_rerank", doc_ids, [], [], 0, "SUCCESS")
            return out
        except Exception as e:
            print("LLM Error:", e)
            return [{"error": f"LLM Error: {str(e)}"}]

    def generate_checklist(self, domain, unit, user_role, user_id):
        query = f"Quy định về {domain} áp dụng cho {unit}"
        res = self.retriever.retrieve(query, user_roles=[user_role], method="hybrid_rerank", top_k=2)
        results = res["results"]
        if not results:
            return []

        context_str = ""
        doc_ids = []
        for r in results:
            doc_ids.append(r["document_id"])
            chunk_text = r['text'][:1500] + "...(lược bớt)" if len(r['text']) > 1500 else r['text']
            context_str += f"--- NGUỒN: {r['title']} ---\n{chunk_text}\n\n"

        prompt = f"""Bạn là Trưởng đoàn Kiểm toán Nội bộ.
Dựa vào các quy định dưới đây, hãy lập một danh sách Checklist (các câu hỏi kiểm tra) dành cho đợt kiểm toán tại {unit} về mảng {domain}.

NGỮ CẢNH:
{context_str}

Trả về định dạng JSON array:
[
  {{
    "item_id": "CHK_01",
    "domain": "{domain}",
    "unit_scope": "{unit}",
    "audit_question": "Câu hỏi kiểm toán?",
    "risk_description": "Rủi ro nếu vi phạm",
    "risk_level": "HIGH/MEDIUM/LOW",
    "source_citation": "Nguồn văn bản căn cứ",
    "recommendation": "Khuyến nghị kiểm tra hồ sơ gì",
    "review_status": "NEEDS_HUMAN_REVIEW"
  }}
]
Chỉ trả về JSON array, không kèm markdown."""
        
        try:
            config = genai.types.GenerationConfig(max_output_tokens=2048)
            response = self.model.generate_content(prompt, generation_config=config)
            txt = response.text.replace("```json", "").replace("```", "").strip()
            import json
            out = json.loads(txt)
            for item in out:
                item["request_id"] = str(uuid.uuid4())
                
            log_audit_event(user_id, str([user_role]), "GENERATE_AUDIT_CHECKLIST", query, "hybrid_rerank", doc_ids, [], [], 0, "SUCCESS")
            return out
        except Exception as e:
            print("LLM Error:", e)
            return [{"error": f"LLM Error: {str(e)}"}]
