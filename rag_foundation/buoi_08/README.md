# BÀI THỰC HÀNH BUỔI 08 - ADVANCED RAG

## Mục tiêu
Dự án nâng cấp hệ thống RAG lên kiến trúc Advanced RAG với các thành phần:
- Tìm kiếm từ khóa (BM25)
- Tìm kiếm ngữ nghĩa (Semantic)
- Hợp nhất xếp hạng (Reciprocal Rank Fusion - RRF)
- Tái xếp hạng (Cross-Encoder Reranker)

## Sơ đồ
`BM25 + Semantic` -> `RRF` -> `Cross-Encoder Reranker` -> `Generative Answer`

## Các chế độ hỗ trợ
1. `bm25`: Chỉ tìm kiếm từ khóa.
2. `semantic`: Chỉ tìm kiếm theo Vector/Embedding.
3. `hybrid`: Hợp nhất `bm25` và `semantic` qua RRF.
4. `hybrid_rerank`: Hợp nhất và dùng AI model chấm điểm lại từng candidate.

## Cài đặt
Chạy cài đặt package trong môi trường Python:
```bash
py -m pip install -r requirements.txt
```
Lưu ý: Mô hình reranker `BAAI/bge-reranker-v2-m3` dung lượng lớn (khoảng 2GB) và đòi hỏi RAM/VRAM. Quá trình tải sẽ tự động thực hiện ở lần đầu tiên chạy mode `hybrid_rerank`.

## Lệnh thông dụng
- **Kiểm tra status**: `py advanced_rag.py status --strategy hierarchical`
- **So sánh 4 chế độ (không tốn phí Generation)**: `py advanced_rag.py compare --strategy hierarchical --question "Điều 7 quy định gì?"`
- **Chạy truy vấn đầy đủ**: `py advanced_rag.py query --mode hybrid_rerank --strategy hierarchical --question "Điều 7 quy định gì?"`
- **Khởi động Giao diện Web**: `py -m streamlit run app.py`

## Miễn trừ trách nhiệm
Hệ thống KHÔNG PHẢI TƯ VẤN PHÁP LÝ. Dữ liệu đầu ra do AI tạo có thể có sai sót. Vui lòng tự đối chiếu với tài liệu gốc!
