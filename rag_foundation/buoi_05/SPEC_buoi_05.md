# ĐẶC TẢ KỸ THUẬT - RAG FOUNDATION BUỔI 5

## 1. Đầu vào
- Các file tài liệu (đặc biệt là PDF quét) lưu tại thư mục: `RAG/rag_foundation/buoi_05/datademo/`. 
- Cụ thể: `Luat TCTD 2024.pdf`.

## 2. Đầu ra
- Text OCR chuẩn hóa Unicode NFC.
- Dữ liệu Chunk với cấu trúc metadata đầy đủ bao gồm: `chunk_id`, `strategy`, `source`, `page_start`, `page_end`, `text` (và có thể có các metadata khác phụ thuộc strategy).
- Các chunk được lưu dưới dạng file vào `RAG/rag_foundation/buoi_05/output/` để dễ dàng xem và trực quan hóa.

## 3. Các chiến lược Chunking (Cắt đoạn văn bản)
Cần thiết kế và so sánh 3 chiến lược:
1. **Fixed-size**: 
   - Chia văn bản theo số ký tự tĩnh. 
   - Có overlap (chồng chéo) để tránh mất ngữ cảnh khi một câu bị cắt ngang.
2. **Semantic**: 
   - Ưu tiên cắt dựa vào ranh giới đoạn văn (hết đoạn, kết đoạn, ngắt dòng). 
   - Phù hợp với văn bản chung để không phá vỡ logic của một đoạn văn.
3. **Hierarchical**: 
   - Phân cấp theo cấu trúc tự nhiên của văn bản.
   - Ví dụ: Chương → Mục → Điều/Khoản → Điểm. 
   - **Lưu ý**: Đây là chiến lược tốt nhất đối với Thông tư, Quy định nội bộ và Văn bản luật vì nó giữ được đơn vị pháp lý tự nhiên.

## 4. Các Ràng buộc
- **Không in secret:** Bất kỳ Secret/API Key nào được sử dụng đều phải thông qua biến môi trường (.env) và không được in ra file log hay terminal.
- **Không chỉnh sửa file gốc:** Tuyệt đối không thay đổi, ghi đè file PDF đầu vào.
- **Không tạo Embedding / Vector DB:** Mục tiêu của Bài tập 5 chỉ giới hạn ở Ingest: Đọc (Parse) -> Cắt đoạn (Chunk). Do đó, chưa tạo Vector Database, chưa tạo Embeddings, và chưa gọi LLM.
- **Xử lý lỗi OCR:** 
    - Text layer có sẵn trong PDF nên được ưu tiên để tối ưu chi phí OCR.
    - OCR (Llama Parse) chỉ nên được dùng như phương án dự phòng khi PyMuPDF không trích xuất được hoặc bị lỗi (font, encoding, rỗng, ký tự lạ).
    - Lỗi đọc ở 1 trang không được làm hỏng tiến trình toàn bộ tài liệu.
