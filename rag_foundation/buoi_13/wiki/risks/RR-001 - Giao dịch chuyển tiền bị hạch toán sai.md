---
id: RR-001
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---

# Giao dịch chuyển tiền bị hạch toán sai

**Mô tả:** Đối soát giao dịch cuối ngày không đầy đủ

- **Category:** Rui ro van hanh
- **Cause:** Thiếu đối chiếu giữa hệ thống thanh toán và sổ cái
- **Event:** Giao dịch được ghi nhận sai trạng thái
- **Impact:** Tổn thất tài chính và khiếu nại khách hàng
- **Inherent Level:** Cao
- **Residual Level:** Trung binh
- **Owner Unit ID:** DV-OPS

## Kiểm soát liên quan
- [[KS-001 - Đối soát tự động giao dịch và sổ cái]] (Quan hệ: MITIGATES, Trạng thái: VERIFIED, Bằng chứng: Dữ liệu mô phỏng: đối soát tự động giảm nguy cơ hạch toán sai)

## Sự kiện liên quan
- [[SK-001]] (Quan hệ: OBSERVED_AS, Trạng thái: VERIFIED, Bằng chứng: Dữ liệu mô phỏng: sự kiện đối soát giao dịch)
