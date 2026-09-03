import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Lấy đường dẫn động
base_dir = Path(__file__).parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from scripts.llm_uc3_uc4 import RealAIEngine
from dotenv import load_dotenv
load_dotenv(base_dir.parent / "buoi_17" / ".env")

st.set_page_config(page_title="AI Compliance & Audit Checklist — Buổi 18 (Real AI)", page_icon="🏦", layout="wide")

st.warning("⚠️ **Demo Đào tạo Kiểm toán AI (Phiên bản Thực tế)** — Hệ thống đang dùng Gemini AI đọc trực tiếp dữ liệu Agribank để đối soát và sinh báo cáo.")
st.title("🏦 AI Compliance Checker & Audit Checklist Generator — Buổi 18")

st.sidebar.header("👤 Định danh & Phân quyền (RBAC)")
user_id = st.sidebar.text_input("User ID Demo:", value="kiemtoan_01")
role = st.sidebar.selectbox("User Role:", ["KiemToanVien", "Admin", "Risk_Manager", "HR", "Staff", "Guest"])
st.sidebar.info(f"**Vai trò:** `{role}`\nCơ chế RBAC kiểm soát phạm vi văn bản trước khi xử lý.")

@st.cache_resource
def get_ai_engine():
    return RealAIEngine()

engine = get_ai_engine()

tab1, tab2 = st.tabs(["⚖️ 1. UC3 - XUNG ĐỘT QUY ĐỊNH", "📋 2. UC4 - AUDIT CHECKLIST GEN"])

with tab1:
    st.subheader("UC3: So sánh Chéo & Phát hiện Xung đột Quy định")
    domain_sel = st.selectbox("Chọn Miền nghiệp vụ cần đối soát:", [
        "Quản lý CAR & Tỷ lệ an toàn vốn",
        "Phân quyền phê duyệt tín dụng",
        "An toàn kho quỹ & Vận chuyển tiền"
    ])
    
    if st.button("🚀 AI Quét Xung đột", use_container_width=True):
        with st.spinner("Gemini đang đọc chéo các quy định... (sẽ mất khoảng 10 giây)"):
            results = engine.check_conflicts(domain_sel, user_role=role, user_id=user_id)
            if not results:
                st.success("✅ AI đã rà soát và KHÔNG tìm thấy bất kỳ xung đột nào giữa các quy định, hoặc bạn không có quyền truy cập.")
            elif "error" in results[0]:
                st.error(f"⛔ Lỗi Gemini: {results[0]['error']}")
            else:
                df_res = pd.DataFrame(results)
                st.error(f"⛔ Phát hiện {len(df_res)} điểm có nguy cơ xung đột!")
                for _, row in df_res.iterrows():
                    sev = row.get("severity", "MEDIUM")
                    sev_color = "🔴" if sev == "HIGH" else ("🟡" if sev == "MEDIUM" else "🟢")
                    conflict_id = row.get('conflict_id', 'CFL')
                    with st.expander(f"{sev_color} {conflict_id} | {row.get('domain')} — {row.get('conflict_type')} [Mức độ: {sev}]"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**📜 Văn bản A:**")
                            st.write(row.get("doc_a_text"))
                            st.caption(f"Trích dẫn: `{row.get('doc_a_citation')}`")
                        with c2:
                            st.markdown(f"**🏢 Văn bản B:**")
                            st.write(row.get("doc_b_text"))
                            st.caption(f"Trích dẫn: `{row.get('doc_b_citation')}`")
                        st.info(f"**Phân tích của Gemini:** {row.get('description')}\n\n**Trạng thái:** `{row.get('review_status')}`")

with tab2:
    st.subheader("UC4: Tự động Sinh Danh mục Checklist Kiểm toán")
    c_dom, c_unit = st.columns(2)
    with c_dom:
        chk_domain = st.selectbox("Miền kiểm toán:", [
            "An toàn kho quỹ & Vận chuyển tiền",
            "Bảo mật CNTT & AI",
            "Phân quyền phê duyệt tín dụng"
        ])
    with c_unit:
        chk_unit = st.selectbox("Đơn vị được kiểm toán:", [
            "Chi nhánh loại 1",
            "Phòng Giao dịch",
            "Phòng Khách hàng Doanh nghiệp"
        ])
        
    if st.button("📝 Gemini Sinh Checklist Kiểm toán", use_container_width=True):
        with st.spinner("Gemini đang nghiên cứu quy định và xây dựng Checklist... (sẽ mất khoảng 10 giây)"):
            results = engine.generate_checklist(chk_domain, chk_unit, user_role=role, user_id=user_id)
            if not results:
                st.error("⛔ Bạn không có quyền truy cập quy định này hoặc hệ thống không tìm thấy.")
            elif "error" in results[0]:
                st.error(f"⛔ Lỗi Gemini: {results[0]['error']}")
            else:
                df_res = pd.DataFrame(results)
                st.success(f"✅ AI đã lập thành công {len(df_res)} mục kiểm tra thực tế!")
                for _, r in df_res.iterrows():
                    with st.expander(f"📌 {r.get('item_id', 'CHK')}: {r.get('audit_question')}"):
                        st.markdown(f"**Rủi ro tiềm ẩn:** {r.get('risk_description')}")
                        st.markdown(f"**Mức rủi ro:** `{r.get('risk_level')}` | **Căn cứ pháp lý:** `{r.get('source_citation')}`")
                        st.markdown(f"**Khuyến nghị thực hiện (Thủ tục KT):** {r.get('recommendation')}")
