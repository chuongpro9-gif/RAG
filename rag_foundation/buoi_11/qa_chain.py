import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Tải biến môi trường (GEMINI_API_KEY)
load_dotenv()

def answer_question(query, context):
    """
    Sử dụng Gemini API để trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
    """
    client = genai.Client()
    
    system_prompt = """Bạn là một chuyên gia pháp lý (Luật sư) tại Việt Nam.
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng một cách chính xác nhất dựa trên Ngữ cảnh (Context) được cung cấp.
Ngữ cảnh này được trích xuất từ một hệ thống Đồ thị tri thức (Knowledge Graph) các văn bản pháp luật, 
bao gồm cả nội dung trực tiếp của văn bản và các mối liên kết đa bước (Multi-hop) như "Thay thế", "Căn cứ", "Hợp nhất" giữa các văn bản.

QUY TẮC NGHIÊM NGẶT:
1. Chỉ trả lời dựa trên thông tin có trong Ngữ cảnh.
2. Nếu Ngữ cảnh có nhắc đến mối quan hệ giữa các tài liệu (ví dụ: A thay thế B), hãy phân tích chuỗi quan hệ đó để trả lời đầy đủ.
3. Nếu thông tin không có trong Ngữ cảnh, hãy trả lời rõ: "Dựa trên dữ liệu hiện tại, tôi không có đủ thông tin để trả lời câu hỏi này." TUYỆT ĐỐI KHÔNG tự bịa ra thông tin.
4. Câu trả lời cần rõ ràng, mạch lạc và trực tiếp vào vấn đề.
"""
    
    prompt = f"Ngữ cảnh (Context):\n{context}\n\nCâu hỏi: {query}"
    
    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.5-flash-lite"),
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"

if __name__ == "__main__":
    ctx = "[Bổ sung đa bước] (Quan hệ đồ thị): Văn bản 'Nghị định 46/2023/NĐ-CP' có quan hệ THAY_THE với văn bản 'Nghị định 73/2016/NĐ-CP'"
    print(answer_question("Nghị định 46 thay thế cho nghị định nào?", ctx))
