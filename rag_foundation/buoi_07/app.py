import streamlit as st
import rag

st.set_page_config(page_title="RAG Buổi 07", page_icon="🤖", layout="wide")

st.title("Hệ thống RAG Chuyên sâu - Buổi 07")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Cấu hình & Trạng thái")
    
    st.write(f"**API Key:** {'✅ Có' if rag.GEMINI_API_KEY else '❌ Thiếu'}")
    st.write(f"**Embedding Model:** {rag.GEMINI_EMBEDDING_MODEL}")
    st.write(f"**Dimension:** {rag.GEMINI_EMBEDDING_DIM}")
    st.write(f"**Generation Model:** {rag.GEMINI_GENERATION_MODEL}")
    st.write(f"**Distance Threshold:** {rag.RAG_MAX_DISTANCE}")
    
    strategy = st.selectbox("Chọn Strategy", ["hierarchical", "semantic", "fixed-size"])
    top_k = st.slider("Số lượng Chunk (Top K)", 1, 10, rag.DEFAULT_TOP_K)
    
    # Read status
    col_name = rag.get_collection_name(strategy)
    client = rag.get_chroma_client()
    try:
        col = client.get_collection(name=col_name, embedding_function=None)
        count = col.count()
        exists = True
    except Exception:
        count = 0
        exists = False
        
    st.write(f"**Collection:** `{col_name}`")
    st.write(f"**Tồn tại:** {'✅' if exists else '❌'}")
    st.write(f"**Số Chunk đã Index:** {count}")

# --- INDEX AREA ---
st.header("1. Quản lý Dữ Liệu (Index)")
col1, col2 = st.columns([1, 4])
with col1:
    reset_db = st.checkbox("Reset Collection trước khi index?")
with col2:
    if st.button("Index Dữ Liệu", type="primary"):
        if not rag.GEMINI_API_KEY:
            st.error("Vui lòng điền GEMINI_API_KEY vào file .env")
        else:
            with st.spinner(f"Đang tiến hành Index với strategy '{strategy}'..."):
                try:
                    stats = rag.index_data(strategy, reset=reset_db)
                    st.success(f"Đã Index thành công {stats.get('valid_chunks', 0)} chunks!")
                    if stats.get('empty_text_skipped', 0) > 0:
                        st.info(f"Đã bỏ qua {stats['empty_text_skipped']} chunks rỗng.")
                    if stats.get('errors'):
                        with st.expander("Các lỗi phát sinh khi kiểm duyệt dữ liệu"):
                            for e in stats['errors']:
                                st.write(f"- {e}")
                except Exception as e:
                    st.error(f"Lỗi khi Index: {e}")

st.divider()

# --- QUESTION AREA ---
st.header("2. Hỏi & Đáp (Query)")
question = st.text_area("Nhập câu hỏi của bạn:", placeholder="Ví dụ: Cơ cấu lại thời hạn trả nợ được quy định như thế nào?")

if st.button("Gửi Câu Hỏi", type="primary"):
    if not question.strip():
        st.warning("Vui lòng nhập câu hỏi.")
    elif not rag.GEMINI_API_KEY:
        st.error("Thiếu API Key để chạy mô hình AI.")
    elif not exists or count == 0:
        st.error("Collection chưa tồn tại hoặc rỗng. Vui lòng Index dữ liệu trước.")
    else:
        with st.spinner("Đang tìm kiếm thông tin và tổng hợp câu trả lời..."):
            try:
                res = rag.query_rag(question, strategy=strategy, top_k=top_k)
                st.session_state["last_result"] = res
            except Exception as e:
                st.error(f"Lỗi: {e}")

# --- Hiển thị Kết quả ---
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    status = res["status"]
    
    st.subheader("🤖 Trả lời:")
    if status == "insufficient_evidence":
        st.warning("⚠️ " + res["answer"])
    elif status == "retrieval_only":
        st.info("ℹ️ " + res["answer"])
        if res["warnings"]:
            for w in res["warnings"]:
                st.error(f"Cảnh báo: {w}")
    else:
        st.write(res["answer"])
        if res["warnings"]:
            for w in res["warnings"]:
                st.warning(f"Cảnh báo từ hệ thống: {w}")
        
    st.subheader("📚 Nguồn Tham Khảo (Evidence)")
    if not res["evidence"]:
        st.write("Chưa có evidence nào.")
    else:
        for ev in res["evidence"]:
            p_str = f"tr. {ev['page_start']}" if ev['page_start'] == ev['page_end'] else f"tr. {ev['page_start']}-{ev['page_end']}"
            gate = "✅ Đạt" if ev["accepted"] else "❌ Loại (Khoảng cách cao)"
            
            with st.expander(f"[{ev['evidence_id']}] {ev['source']} – {p_str} – {ev['chunk_id']} | {gate}"):
                st.write(f"**Distance:** {ev['distance']:.4f}")
                st.text_area("Nội dung Chunk:", ev['text'], height=150, disabled=True)
