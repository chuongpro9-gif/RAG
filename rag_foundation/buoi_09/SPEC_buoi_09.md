# Đặc tả kỹ thuật (Specification) - Buổi 09
## Multi-query Retrieval và Parent–Child Retrieval

### 1. Mục tiêu và khác biệt Buổi 08/09
- **Mục tiêu**: Xử lý các câu hỏi phức tạp bằng cách sinh nhiều cách diễn đạt/truy vấn phụ (Multi-query) và mở rộng ngữ cảnh câu trả lời bằng cách lấy toàn bộ Điều/Khoản gốc (Parent) thay vì chỉ đoạn nhỏ (Child chunk).
- **Khác biệt**: 
  - Buổi 08: 1 câu hỏi -> 1 luồng truy xuất -> RRF -> Rerank chunk.
  - Buổi 09: 1 câu hỏi gốc (Q0) + N câu hỏi phụ (Q1..Qn) -> Truy xuất độc lập -> Hợp nhất RRF chéo (Cross-query) -> Truy ngược từ Child lên Parent -> Rerank Parent -> Trả lời.

### 2. Sơ đồ Pipeline
```
Q0 (Gốc) + Variants (Q1..Qn)
       |
  Per-query Hybrid Retrieval
       |
  Cross-query RRF (Hợp nhất theo Child)
       |
  Child-to-Parent Mapping
       |
  Parent Aggregation
       |
  Parent Reranking (bằng Q0)
       |
  Generation
```

### 3. Bốn Mode Hỗ Trợ
- `single_flat`: Chỉ dùng Q0, trả về child chunk, rerank child (Giống Buổi 08).
- `multi_flat`: Q0 + variants, hợp nhất child, rerank child.
- `single_parent`: Chỉ dùng Q0, mở rộng child lên parent, rerank parent.
- `multi_parent`: Q0 + variants, hợp nhất child, mở rộng lên parent, rerank parent.

### 4. QueryVariant Schema
```json
{
  "original_question": "...",
  "queries": [
    {"query_id": "Q0", "text": "...", "origin": "original", "focus": "original_intent"},
    {"query_id": "Q1", "text": "...", "origin": "generated", "focus": "paraphrase"}
  ],
  "model": "...",
  "status": "ready"
}
```

### 5. Hierarchy Registry Schema
```json
{
  "child_id": "chunk_1",
  "parent_id": "parent_1",
  "source": "doc.pdf",
  "structural_path": {"chapter": null, "article": "Điều 1", "clause": null, "point": null},
  "resolution_method": "metadata",
  "ambiguous": false,
  "warnings": []
}
```

### 6. ParentDocument Schema
```json
{
  "parent_id": "parent_1",
  "source": "doc.pdf",
  "article_key": "Điều 1",
  "child_ids": ["chunk_1", "chunk_2"],
  "text": "Nội dung đầy đủ của Điều 1...",
  "char_count": 1000
}
```

### 7. Hợp nhất Child và Parent Candidate
- **MultiQueryChildHit**: Gồm `child_id`, `multi_query_rrf_score`, `support_query_count`.
- **ParentCandidate**: Gồm `parent_id`, `aggregated_score`, danh sách `anchor_children`.

### 8. Quy tắc Hierarchy Resolution
- Ưu tiên: (1) Metadata -> (2) Heading trong text -> (3) Carry forward từ chunk trước -> (4) Document fallback.
- Nếu không chắc chắn, gán `ambiguous=true` và tạo warning, không tự đoán sai.

### 9. Công thức RRF và Aggregation
- **Cross-query RRF**: Tổng của `weight(q) / (K + rank_q(d))` với mọi query q tìm thấy chunk d.
- **Parent Aggregation**: Score của Parent bằng tổng `multi_query_rrf_score` của tối đa `PARENT_SCORE_CHILD_LIMIT` child chunks thuộc parent đó.

### 10. Context Budget & Citations
- Cắt bỏ các parent có rank thấp nếu tổng độ dài vượt quá `TOTAL_CONTEXT_MAX_CHARS`.
- LLM sinh câu trả lời kèm citation (trích dẫn) dựa trên Parent ID.

### 11. Status & Failure
- Nếu API sinh câu hỏi phụ lỗi, trả về `partial` status hoặc `query_generation_unavailable`, dùng tạm Q0.
- Nếu Q0 lỗi retrieval -> Fail toàn bộ pipeline.

### 12. Testability / Dependency Injection
- Các hàm sinh query và gọi LLM phải có tham số cho phép inject hàm giả (mock/fake) để unit test không cần gọi mạng.

### 13. Metrics & Acceptance
- Đo lường recall, MRR, nDCG ở cấp độ Parent.
- Output phải có parent đúng trong top K.

### 14. Xác nhận
- Toàn bộ source code chỉ được tạo và ghi bên trong thư mục `buoi_09`. Không làm ảnh hưởng đến storage hay file của Buổi 08.
