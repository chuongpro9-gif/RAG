# ĐẶC TẢ KỸ THUẬT - RAG VỚI AI AGENT (BUỔI 6)

## Workspace
Chỉ được phép thao tác trong:
- `RAG/rag_foundation/buoi_06/`
- `RAG/rag_foundation/buoi_05/.venv/` (hoặc môi trường hiện tại)
- `RAG/rag_foundation/buoi_05/output/chunks/` (để đọc dữ liệu input JSON)

Không đọc source code của các buổi trước.

## Python & Packages
Sử dụng đúng Python interpreter.
Chỉ cài đặt: `streamlit`, `google-genai`, `chromadb`, `psycopg`, `python-dotenv`.
Không cài framework phức tạp khác.

## Coding Style
Ưu tiên: ít file, ít class, ít function, code dễ đọc.
Không tạo: repository pattern, service layer, dependency injection, factory, plugin.
Mục tiêu dòng code: 300-500 dòng.

## Xử lý Lỗi & Log
Chỉ try/except tối thiểu. Không retry, batch, logging.

## Bảo mật
Không in API Key, password, secret ra terminal hay log.

## Cơ sở Dữ Liệu
1. **ChromaDB**: Lưu trữ vector embedding. Ưu tiên Embedded Persistent Client tại `storage/chroma/`. Không yêu cầu cài đặt Chroma Server.
2. **PostgreSQL**: Lưu trữ text và metadata. Nếu kết nối thất bại (không có PostgreSQL), lưu ra disk local bằng file `.db` (SQLite fallback).
