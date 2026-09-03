import os
import google.generativeai as genai
from .secure_retrieval_adapter import SecureRetrievalAdapter
from .audit_logger import log_audit_event
import uuid

class InternalLookup:
    def __init__(self):
        self.retriever = SecureRetrievalAdapter()
        # Gemini tự động lấy GOOGLE_API_KEY / GEMINI_API_KEY từ biến môi trường
        
    def lookup(self, user_id, user_roles, query, top_k=2):
        request_id = str(uuid.uuid4())
        
        # 1. Secure Retrieval
        res = self.retriever.retrieve(query, user_roles=user_roles, method="hybrid_rerank", top_k=top_k)
        results = res["results"]
        denied_count = res["denied_count"]
        
        if not results:
            log_audit_event(user_id, str(user_roles), "INTERNAL_LOOKUP", query, "hybrid_rerank", [], [], [], denied_count, "DENIED")
            return {
                "request_id": request_id,
                "answer": "Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập.",
                "citations": [],
                "access_decision": f"DENIED (Bị chặn {denied_count} tài liệu do thiếu quyền)",
                "raw_results": []
            }
            
        # 2. Extract context
        context_str = ""
        citations = []
        doc_ids = []
        chunk_ids = []
        citation_ids = []
        
        for r in results:
            doc_ids.append(r["document_id"])
            chunk_ids.append(r["chunk_id"])
            if r["citation"]:
                citations.append(f"[{r['citation']}]")
                citation_ids.append(r['citation'])
            context_str += f"--- NGUỒN: {r['title']} ---\n{r['text']}\n\n"
            
        # 3. LLM Generate Answer
        prompt = f"""Bạn là trợ lý AI nội bộ của ngân hàng. Hãy trả lời câu hỏi dưới đây DỰA TRỰC TIẾP vào ngữ cảnh được cung cấp.
        Không tự bịa đặt thông tin ngoài ngữ cảnh.
        
        NGỮ CẢNH:
        {context_str}
        
        CÂU HỎI: {query}
        
        TRẢ LỜI NGẮN GỌN VÀ CHÍNH XÁC:"""
        
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Lỗi sinh câu trả lời: {str(e)}"
            
        # 4. Log Audit
        log_audit_event(user_id, str(user_roles), "INTERNAL_LOOKUP", query, "hybrid_rerank", doc_ids, chunk_ids, citation_ids, denied_count, "SUCCESS")
        
        return {
            "request_id": request_id,
            "answer": answer,
            "citations": list(set(citations)),
            "access_decision": f"ALLOWED (Bị chặn {denied_count} tài liệu)",
            "raw_results": results
        }
