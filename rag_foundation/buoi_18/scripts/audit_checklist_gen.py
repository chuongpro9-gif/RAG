import os
import sys
import pandas as pd
from pathlib import Path

base_dir = Path(r"D:/du_an_cua_ban/RAG/rag_advanced/buoi_18")
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from scripts.audit_logger import log_audit_event

CHECKLIST_TEMPLATE = [
    {
        "item_id": "CHK_KHO_01",
        "domain": "An toàn kho quỹ & Vận chuyển tiền",
        "unit_scope": "Chi nhánh loại 1 / Phòng Giao dịch",
        "audit_question": "Chi nhánh có bố trí xe bọc thép chuyên dùng và tối thiểu 2 vệ sĩ có vũ trang trong các đợt áp tải tiền không?",
        "risk_description": "Rủi ro thất thoát tiền mặt, không bảo đảm an toàn tính mạng cán bộ áp tải trên đường vận chuyển.",
        "risk_level": "HIGH",
        "source_citation": "Điều 5 Thông tư 01/2014/TT-NHNN & Điều 8 QĐ 100/QĐ-NHNO-AT",
        "recommendation": "Kiểm tra nhật ký hành trình xe bọc thép và danh sách phân công vệ sĩ áp tải của từng chuyến.",
        "review_status": "NEEDS_HUMAN_REVIEW"
    },
    {
        "item_id": "CHK_CNTT_01",
        "domain": "Bảo mật CNTT & AI",
        "unit_scope": "Khối CNTT / Trung tâm Dữ liệu",
        "audit_question": "Hệ thống RAG AI và cơ sở dữ liệu có thực hiện mã hóa At-Rest chuẩn AES-128/Fernet và phân quyền RBAC trước khi đưa vào context không?",
        "risk_description": "Rò rỉ dữ liệu khách hàng mật, vi phạm quy định bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.",
        "risk_level": "HIGH",
        "source_citation": "Điều 9 & Điều 16 Quy chế 600/QĐ-NHNO-CNTT",
        "recommendation": "Trích xuất cấu hình mã hóa vector DB và kiểm tra ma trận RBAC pre-retrieval trên mã nguồn thực tế.",
        "review_status": "NEEDS_HUMAN_REVIEW"
    },
    {
        "item_id": "CHK_TD_01",
        "domain": "Phân quyền phê duyệt tín dụng",
        "unit_scope": "Phòng Khách hàng Doanh nghiệp",
        "audit_question": "Các khoản vay trên 15 tỷ đồng có được đưa ra Hội đồng Tín dụng Chi nhánh họp và lập biên bản biểu quyết đúng thẩm quyền?",
        "risk_description": "Vượt thẩm quyền cá nhân phê duyệt tín dụng, rủi ro nợ xấu và sai phạm trách nhiệm hình sự.",
        "risk_level": "HIGH",
        "source_citation": "Điều 2 Nghị quyết 18/NQ-HĐTV & Điều 4 QĐ 350/QĐ-NHNO-TD",
        "recommendation": "Rà soát 100% hồ sơ giải ngân trên 15 tỷ đồng, đối chiếu chữ ký trong Biên bản họp Hội đồng Tín dụng.",
        "review_status": "NEEDS_HUMAN_REVIEW"
    }
]

def generate_audit_checklist(domain: str, unit: str, user_role: str = "KiemToanVien", user_id: str = "auditor_01"):
    if user_role == "Guest":
        return pd.DataFrame()
        
    items = [c for c in CHECKLIST_TEMPLATE if (domain == "Tất cả" or c["domain"] == domain)]
    if not items:
        items = CHECKLIST_TEMPLATE
        
    results = []
    for item in items:
        req_id = log_audit_event(
            user_id_demo=user_id,
            user_role=user_role,
            action="GENERATE_AUDIT_CHECKLIST",
            query=f"Generate checklist for {domain} at {unit}",
            citation_ids=[item["source_citation"]],
            status="SUCCESS",
            details={"item_id": item["item_id"], "risk_level": item["risk_level"]}
        )
        row = dict(item)
        row["unit_scope"] = unit
        row["request_id"] = req_id
        results.append(row)
        
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(base_dir / "outputs" / "audit_checklist_results.csv", index=False, encoding="utf-8")
    return df
