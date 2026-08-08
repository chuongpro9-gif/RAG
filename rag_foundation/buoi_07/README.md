# Hoàn thiện RAG Pipeline với AI Agent (Buổi 07)

## 1. Mục tiêu
Dự án này là bước hoàn thiện RAG từ các bài trước, với các tiêu chuẩn khắt khe về kỹ thuật phần mềm:
- Pipeline RAG có Validation, Embedding lưu Persistent trên ChromaDB.
- Retrieval với Confidence Gate: Lọc các kết quả không sát nghĩa (Distance cao).
- Trích dẫn (Citation) chính xác từ Metadata gốc, không để LLM "bịa" nguồn.
- Streamlit Giao diện.

## 2. Kiến trúc và Pipeline
`JSON -> Loader & Validator -> Gemini Embedding -> ChromaDB -> Semantic Search -> Confidence Gate -> Gemini Generation -> Citation Mapping -> Streamlit`

## 3. Cài đặt Môi trường
```bash
pip install -r requirements.txt
```

Sao chép `.env.example` thành `.env` và điền `GEMINI_API_KEY`.
Các biến cấu hình khác:
- `GEMINI_EMBEDDING_MODEL` (Mặc định: gemini-embedding-2)
- `GEMINI_GENERATION_MODEL` (Mặc định: gemini-3.5-flash-lite)
- `RAG_MAX_DISTANCE` (Ngưỡng lọc, mặc định 0.45. Text có distance cao hơn sẽ bị loại bỏ để chống ảo giác).

## 4. Lệnh chạy (CLI)

Kiểm duyệt dữ liệu:
```bash
python rag.py validate --strategy hierarchical
```

Xem trạng thái DB:
```bash
python rag.py status --strategy hierarchical
```

Index dữ liệu:
```bash
python rag.py index --strategy hierarchical
```

Index lại từ đầu (xóa collection cũ):
```bash
python rag.py index --strategy hierarchical --reset
```

Hỏi đáp từ CLI:
```bash
python rag.py query --strategy hierarchical --top-k 5 --question "Cơ cấu lại thời hạn trả nợ được quy định như thế nào?"
```

Chạy Test Tự Động (Offline):
```bash
python -m unittest discover -s tests -v
```

Khởi động Web UI:
```bash
python -m streamlit run app.py
```

## 5. Giới hạn & Chú ý
- Hệ thống này là **Bản thực hành (Demo)**, không được dùng trực tiếp như hệ thống tư vấn pháp lý chính thức.
- Kết quả từ Retrieval có thể thiếu sót nếu từ khóa không phù hợp.
- Dữ liệu text sẽ được gửi lên Google Gemini API. Hãy chú ý về quyền riêng tư.
