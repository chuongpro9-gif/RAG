import os
import sys
import streamlit as st
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    
load_dotenv(os.path.join(BASE_DIR, ".env"))

from scripts.internal_lookup import InternalLookup
from scripts.compliance_gap import ComplianceGapChecker

st.set_page_config(page_title="Hệ thống RAG - Buổi 19", layout="wide")
st.markdown("<style>body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }</style>", unsafe_allow_html=True)

st.title("🛡️ SECURE RAG & COMPLIANCE - BUỔI 19 (Ollama/Gemini)")
st.info("Demo đào tạo — kết quả AI cần kiểm toán viên xác minh.")

st.sidebar.header("Thông tin User (Demo)")
user_id = st.sidebar.text_input("User ID", "NV001")
role_selected = st.sidebar.selectbox("Role", ["Admin", "HR", "Risk_Manager", "Staff", "Guest"])
user_roles = [role_selected]

tab1, tab2, tab3 = st.tabs(["Tra cứu Nội bộ", "Compliance Gap Checker", "Audit Log"])

@st.cache_resource
def get_engines():
    return InternalLookup(), ComplianceGapChecker()

lookup_engine, gap_engine = get_engines()

with tab1:
    st.subheader("Tra cứu Quy định nội bộ (RBAC)")
    query = st.text_input("Nhập câu hỏi nghiệp vụ:", "Chính sách bảo mật thông tin khách hàng như thế nào?")
    if st.button("Tra cứu"):
        with st.spinner("Đang tìm kiếm..."):
            res = lookup_engine.lookup(user_id, user_roles, query)
            st.write(f"**Request ID:** {res['request_id']}")
            st.write(f"**Access Decision:** {res['access_decision']}")
            st.success(res['answer'])
            if res['citations']:
                st.write("**Nguồn trích dẫn:**", ", ".join(res['citations']))
            
            with st.expander("Xem chi tiết văn bản thô (Đã được phép)"):
                import streamlit.components.v1 as components
                for r in res['raw_results']:
                    st.write(f"**ID:** {r['document_id']} | **Score:** {r['score']:.4f}")
                    html_content = f"<style>body {{ background-color: white; color: black; padding: 10px; border-radius: 5px; }}</style>{r['text']}"
                    components.html(html_content, height=200, scrolling=True)

with tab2:
    st.subheader("AI Compliance Gap Checker")
    st.write("Kiểm tra quy định nội bộ có đáp ứng yêu cầu của NHNN không.")
    req = st.text_area("Nhập Điều khoản/Yêu cầu từ NHNN:", "Ngân hàng phải có trách nhiệm bảo vệ bí mật thông tin khách hàng không được cung cấp cho bên thứ 3.")
    if st.button("Kiểm tra Gap"):
        with st.spinner("Đang đối chiếu..."):
            res = gap_engine.check_gap(user_id, user_roles, req)
            st.write(f"**Request ID:** {res['request_id']}")
            
            cls = res.get('classification', '')
            color = "green" if cls == "DAP_UNG" else "red" if cls == "THIEU" else "orange" if cls == "CHENH_LECH" else "gray"
            st.markdown(f"### Kết luận: <span style='color:{color}'>{cls}</span>", unsafe_allow_html=True)
            
            st.write(f"**Lý do:** {res.get('reason')}")
            st.write(f"**Độ tin cậy (Confidence):** {res.get('confidence')}%")
            st.warning(f"Trạng thái: {res.get('review_status')}")
            
            if res.get('internal_citations'):
                st.write("**Bằng chứng đối chiếu:**", ", ".join(res['internal_citations']))

with tab3:
    st.subheader("Audit Log (Nhật ký truy vết)")
    audit_path = os.path.join(BASE_DIR, "outputs", "audit_log.jsonl")
    if st.button("Tải lại Log"):
        if os.path.exists(audit_path):
            with open(audit_path, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f.readlines()]
            # Lọc theo role để minh hoạ
            filtered_logs = [log for log in logs if role_selected in log.get('role', '') or role_selected == "Admin"]
            
            st.write(f"Tìm thấy {len(filtered_logs)} sự kiện cho role {role_selected}:")
            for log in reversed(filtered_logs):
                color = "green" if log['status'] == "SUCCESS" else "red"
                st.markdown(f"- **{log['timestamp']}** | Tác vụ: {log['action']} | Trạng thái: <span style='color:{color}'>{log['status']}</span> | Từ chối: {log['denied_count']} tài liệu", unsafe_allow_html=True)
                with st.expander("Chi tiết"):
                    st.json(log)
        else:
            st.write("Chưa có log nào được ghi.")
