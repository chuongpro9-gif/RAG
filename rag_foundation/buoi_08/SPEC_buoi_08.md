# SPECIFICATIONS BUỔI 08 - ADVANCED RAG

## 1. Workspace và security
- Chỉ thao tác trong thư mục `rag_foundation/buoi_08`.
- Không in hoặc hardcode API Key.
- Không commit file `.env` hay cache HuggingFace, ChromaDB.

## 2. Quan hệ với Buổi 05 và Buổi 07
- Sử dụng raw data chunks từ Buổi 05.
- Kế thừa baseline semantic RAG (loader, index, gemini embedding) từ Buổi 07 nhưng sửa cấu hình theo `.env` Buổi 08.

## 3. Data contract
- Chunk giữ đúng chuẩn `chunk_id`, `text`, `source`, `page_start`, `page_end`.
- Metadata bổ sung khi index gồm `strategy`, `embedding_model`, `embedding_dim`.

## 4. BM25 tokenizer/retrieval contract
- Tokenizer: Unicode NFC, casefold, tách từ giữ nguyên chữ Việt Nam và số. Không loại stopword.
- BM25 chạy in-memory bằng `rank-bm25`.

## 5. Semantic candidate contract
- Lấy `candidate_k` chunks bằng ChromaDB theo Gemini Embedding.

## 6. RRF fusion contract
- Sử dụng Reciprocal Rank Fusion: `score = bm25_weight/(k+bm25_rank) + semantic_weight/(k+semantic_rank)`.

## 7. Cross-encoder reranker contract
- Lazy-load model `BAAI/bge-reranker-v2-m3` từ HuggingFace.
- Rerank tối đa `RERANK_CANDIDATES` chunks theo batch.

## 8. Final evidence và citation contract
- Chỉ context đạt `RERANK_MIN_SCORE` (hoặc ngưỡng `RAG_MAX_DISTANCE` nếu mode semantic) mới được đưa vào Prompt Generation.
- Map đúng [E1], [E2] với metadata thực tế.

## 9. Pipeline trace contract
- Trả về chi tiết `bm25_candidates`, `semantic_candidates`, `overlap`, `accepted`.
- Trả về latency theo milisecond cho từng bước.

## 10. Evaluation metrics contract
- Tính Recall@K, MRR@K, nDCG@K bằng binary relevance (1 nếu chunk_id nằm trong `relevant_chunk_ids`).

## 11. Offline testing contract
- 100% tests chạy offline không cần API/Model thật.

## 12. UI comparison contract
- Giao diện Streamlit có 4 tab: Hỏi đáp, So sánh, Trace và Đánh giá, trực quan hóa quá trình dịch chuyển rank.
