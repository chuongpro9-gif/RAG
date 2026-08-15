# Buổi 09: Multi-query Retrieval & Parent-Child Retrieval

## Giới thiệu
Đây là dự án RAG Nâng cao (Tiếp nối Buổi 08), sử dụng kỹ thuật sinh nhiều truy vấn (Multi-query) từ một câu hỏi gốc, kết hợp với việc tìm kiếm và truy xuất toàn bộ ngữ cảnh cha (Parent) thay vì các đoạn văn nhỏ lẻ (Child chunks).

## Tính năng chính
1. **Multi-query Generator**: Dùng Gemini sinh thêm các phiên bản câu hỏi khác nhau từ câu hỏi gốc.
2. **Cross-query RRF**: Hợp nhất kết quả tìm kiếm của các câu hỏi phụ.
3. **Hierarchy Registry**: Xây dựng cấu trúc Cha-Con từ dữ liệu chunk.
4. **Parent Aggregation**: Tập hợp các chunk con thành ngữ cảnh cha nguyên vẹn.
5. **Parent Reranking**: Chấm điểm lại ngữ cảnh cha bằng bge-reranker-v2-m3.

## Cài đặt
1. Copy file `.env.example` thành `.env` và điền `GEMINI_API_KEY`.
2. Đảm bảo môi trường Python có đầy đủ thư viện trong `requirements.txt`.
3. Chạy ứng dụng bằng `python -m streamlit run app.py`.
