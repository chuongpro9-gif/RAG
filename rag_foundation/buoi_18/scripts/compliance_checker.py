import os
import sys
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

base_dir = Path(r"D:/du_an_cua_ban/RAG/rag_advanced/buoi_18")
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from scripts.audit_logger import log_audit_event

CONFLICT_DATABASE = [
    {
        "conflict_id": "CFL_01",
        "domain": "An toàn kho quỹ & Vận chuyển tiền",
        "doc_a_id": "100/QĐ-NHNO-AT",
        "doc_a_citation": "Điều 8 Quyết định 100/QĐ-NHNO-AT",
        "doc_a_text": "Cho phép vận chuyển tiền mặt bằng xe chuyên dụng hoặc xe bán tải có thùng kín kèm 1 bảo vệ.",
        "doc_b_id": "Thông tư 01/2014/TT-NHNN",
        "doc_b_citation": "Điều 5 Thông tư 01/2014/TT-NHNN",
        "doc_b_text": "Bắt buộc sử dụng xe ô tô bọc thép chuyên dùng, trang bị hệ thống định vị và tối thiểu 2 vệ sĩ có vũ trang khi vận chuyển tiền liên tỉnh.",
        "conflict_type": "Quy trình thực hiện & Phương tiện",
        "severity": "HIGH",
        "description": "Quy định nội bộ cho phép sử dụng xe bán tải thường mâu thuẫn với quy chuẩn xe bọc thép chuyên dùng bắt buộc của NHNN.",
        "review_status": "NEEDS_HUMAN_REVIEW"
    },
    {
        "conflict_id": "CFL_02",
        "domain": "Quản lý CAR & Tỷ lệ an toàn",
        "doc_a_id": "215/QĐ-NHNO-RR",
        "doc_a_citation": "Điều 12 Quyết định 215/QĐ-NHNO-RR",
        "doc_a_text": "Tỷ lệ an toàn vốn tối thiểu (CAR) mục tiêu nội bộ duy trì ở mức không thấp hơn 9.0%.",
        "doc_b_id": "Thông tư 41/2016/TT-NHNN",
        "doc_b_citation": "Điều 9 Thông tư 41/2016/TT-NHNN",
        "doc_b_text": "Tổ chức tín dụng phải duy trì tỷ lệ an toàn vốn tối thiểu (CAR) 8.0%.",
        "conflict_type": "Hạn mức/Ngưỡng an toàn",
        "severity": "LOW",
        "description": "Quy định nội bộ đặt ngưỡng an toàn 9.0% chặt chẽ hơn mức tối thiểu 8.0% của NHNN (chênh lệch an toàn, không vi phạm pháp luật).",
        "review_status": "NEEDS_HUMAN_REVIEW"
    },
    {
        "conflict_id": "CFL_03",
        "domain": "Phân quyền phê duyệt tín dụng",
        "doc_a_id": "350/QĐ-NHNO-TD",
        "doc_a_citation": "Điều 4 Quyết định 350/QĐ-NHNO-TD",
        "doc_a_text": "Giám đốc Chi nhánh loại 1 được ủy quyền cho Phó Giám đốc phê duyệt khoản vay doanh nghiệp lên đến 20 tỷ đồng.",
        "doc_b_id": "Nghị quyết 18/NQ-HĐTV",
        "doc_b_citation": "Điều 2 Nghị quyết 18/NQ-HĐTV",
        "doc_b_text": "Mọi khoản vay vượt 15 tỷ đồng tại Chi nhánh bắt buộc phải thông qua Hội đồng Tín dụng Chi nhánh biểu quyết, không ủy quyền cá nhân.",
        "conflict_type": "Thẩm quyền phê duyệt",
        "severity": "HIGH",
        "description": "Xung đột trực tiếp về thẩm quyền phê duyệt cá nhân (20 tỷ) so với yêu cầu biểu quyết tập thể qua Hội đồng (trên 15 tỷ).",
        "review_status": "NEEDS_HUMAN_REVIEW"
    }
]

def run_compliance_checker(domain_filter: str = "Tất cả", user_role: str = "KiemToanVien", user_id: str = "auditor_01"):
    if user_role == "Guest":
        return pd.DataFrame()
        
    filtered = CONFLICT_DATABASE if domain_filter == "Tất cả" else [c for c in CONFLICT_DATABASE if c["domain"] == domain_filter]
    
    results = []
    for c in filtered:
        req_id = log_audit_event(
            user_id_demo=user_id,
            user_role=user_role,
            action="COMPLIANCE_CROSS_CHECK",
            query=f"Cross check domain {c['domain']}",
            retrieved_doc_ids=[c["doc_a_id"], c["doc_b_id"]],
            citation_ids=[c["doc_a_citation"], c["doc_b_citation"]],
            status="SUCCESS",
            details={"conflict_id": c["conflict_id"], "severity": c["severity"]}
        )
        row = dict(c)
        row["request_id"] = req_id
        row["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        results.append(row)
        
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(base_dir / "outputs" / "compliance_conflicts.csv", index=False, encoding="utf-8")
    return df