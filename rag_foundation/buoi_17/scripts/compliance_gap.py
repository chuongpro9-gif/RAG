import os
import google.generativeai as genai
from .secure_retrieval_adapter import SecureRetrievalAdapter
from .audit_logger import log_audit_event
import uuid

class ComplianceGapChecker:
    def __init__(self):
        self.retriever = SecureRetrievalAdapter()
        
    def check_gap(self, user_id, user_roles, requirement_text, top_k=5):
        request_id = str(uuid.uuid4())
        
        res = self.retriever.retrieve(requirement_text, user_roles=user_roles, method="hybrid_rerank", top_k=top_k)
        results = res["results"]
        denied_count = res["denied_count"]
        
        if not results:
            log_audit_event(user_id, str(user_roles), "GAP_CHECK", requirement_text, "hybrid_rerank", [], [], [], denied_count, "DENIED")
            return {
                "request_id": request_id,
                "classification": "CHUA_DU_BANG_CHUNG",
                "reason": "Không tìm thấy quy định nội bộ nào liên quan trong quyền hạn của bạn.",
                "confidence": 0,
                "review_status": "NEEDS_HUMAN_REVIEW",
                "internal_citations": []
            }
            
        context_str = ""
        internal_citations = []
        doc_ids = []
        chunk_ids = []
        for r in results:
            doc_ids.append(r["document_id"])
            chunk_ids.append(r["chunk_id"])
            if r["citation"]:
                internal_citations.append(r["citation"])
            context_str += f"- {r['citation']}: {r['text']}\n"
            
        prompt = f"""Bạn là Kiểm toán viên Tuân thủ. Hãy so sánh Yêu cầu của Cơ quan nhà nước (NHNN) với Quy định nội bộ hiện có của ngân hàng.
        Chỉ kết luận dựa trên các quy định nội bộ được cung cấp dưới đây.
        Phân loại vào 1 trong 4 nhóm: DAP_UNG, THIEU, CHENH_LECH, CHUA_DU_BANG_CHUNG.
        
        YÊU CẦU TỪ NHNN:
        {requirement_text}
        
        QUY ĐỊNH NỘI BỘ TÌM THẤY:
        {context_str}
        
        Hãy trả lời chính xác theo định dạng JSON sau, KHÔNG dùng markdown block ```json:
        {{
            "classification": "...",
            "reason": "Giải thích ngắn gọn tại sao...",
            "confidence": 85
        }}"""
        
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            text_response = response.text
                
            txt = text_response.replace("```json", "").replace("```", "").strip()
            import json
            out = json.loads(txt)
        except Exception as e:
            out = {
                "classification": "ERROR",
                "reason": f"LLM Error: {str(e)}\n\nRaw Text: {response.text if 'response' in locals() else ''}",
                "confidence": 0
            }
            
        log_audit_event(user_id, str(user_roles), "GAP_CHECK", requirement_text, "hybrid_rerank", doc_ids, chunk_ids, internal_citations, denied_count, "SUCCESS")
        
        out["review_status"] = "NEEDS_HUMAN_REVIEW"
        out["internal_citations"] = list(set(internal_citations))
        out["request_id"] = request_id
        
        return out
