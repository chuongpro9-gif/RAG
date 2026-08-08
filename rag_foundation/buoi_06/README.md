# RAG Foundation - Buổi 06

Ứng dụng demo Retrieval-Augmented Generation (RAG) sử dụng:
- **Vector Database**: ChromaDB (Embedded)
- **Text Database**: PostgreSQL (hoặc fallback sang SQLite `.db`)
- **LLM**: Gemini (mô hình `gemini-embedding-2` và `gemini-flash-lite-latest`)
- **Giao diện**: Streamlit

## Hướng dẫn cài đặt
1. Cài đặt thư viện: `pip install -r requirements.txt`
2. Tạo file `.env` dựa trên `.env.example` và điền `GEMINI_API_KEY`.
3. Chạy ứng dụng: `streamlit run app.py`
