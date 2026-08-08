## Workspace
- Vùng được đọc: `buoi_05/output/chunks/`
- Vùng được ghi: `buoi_07/`
- Không sửa Buổi 05 và Buổi 06.

## Python & Packages
- Dùng môi trường Python hiện hành.
- Chỉ dùng package: `streamlit`, `google-genai`, `chromadb`, `python-dotenv`.

## Input
- Nguồn dữ liệu: JSON trong `buoi_05/output/chunks/`.
- Không OCR, không chunk lại.

## Pipeline
- validate -> embedding -> Chroma persistent -> retrieval -> confidence gate -> generation -> citation -> Streamlit -> unittest offline

## Data Contract
- Các field bắt buộc: `chunk_id`, `strategy`, `source`, `page_start`, `page_end`, `text`.

## Index Contract
- Một strategy trong một collection riêng.
- Model và dimension của index/query phải khớp.
- Chặn NaN, Infinity, boolean và zero vector.
- Chroma cosine, `embedding_function=None`.
- Idempotent (không trùng lặp khi chạy lại).
- Status read-only.
- Validate toàn bộ embedding xong trước khi reset/upsert.

## Retrieval & Confidence Gate Contract
- Trả evidence thật kèm distance.
- Chỉ evidence đạt threshold (`<= RAG_MAX_DISTANCE`) mới được đưa vào generation prompt.
- Evidence yếu thì KHÔNG gọi generation (tránh hallucination).

## Citation Contract
- Trích dẫn (citation) được code map từ metadata thật, không tin tưởng LLM tự tạo nguồn.
- Result trả về `citations` và `warnings`.

## Security
- Không lộ secret, API key.

## Testing
- Unittest offline với mock API và temporary storage.

## Coding Style
- Ít file, code đơn giản, không áp dụng kiến trúc phức tạp.
