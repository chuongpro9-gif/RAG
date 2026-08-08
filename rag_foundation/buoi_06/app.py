import streamlit as st
import os
from dotenv import load_dotenv
import rag

load_dotenv()

st.set_page_config(page_title="RAG Agent - Buổi 06", layout="wide")

# SIDEBAR: Trạng thái hệ thống
with st.sidebar:
    st.header("⚙️ Trạng thái Hệ thống")
    
    # Kiểm tra API Key
    has_key = bool(os.getenv("GEMINI_API_KEY"))
    st.markdown(f"**Gemini API Key:** {'✅ Có' if has_key else '❌ Thiếu'}")
    
    # Lấy status từ RAG
    stat = rag.status()
    db_type = stat.get("text_db_type", "Unknown")
    
    if db_type == "postgres":
        st.markdown("**PostgreSQL:** ✅ Đang kết nối")
    elif db_type == "sqlite":
        st.markdown("**PostgreSQL:** ❌ Fallback (SQLite Local)")
    else:
        st.markdown("**PostgreSQL:** ❌ Mất kết nối")
        
    st.markdown(f"**ChromaDB:** ✅ Local Embedded")
    
    st.divider()
    st.metric("Tài liệu trong Text DB", stat.get("text_chunks", 0))
    st.metric("Vectors trong ChromaDB", stat.get("vector_chunks", 0))

# MAIN AREA
st.title("🤖 RAG Foundation - Khỏi tạo với AI Agent")
st.markdown("Luồng xử lý: `Question` ➔ `Top-k` ➔ `Gemini` ➔ `Answer`")

col1, col2 = st.columns([1, 4])

with col1:
    if st.button("🚀 Nút Index Dữ Liệu", use_container_width=True):
        if not has_key:
            st.error("Cần GEMINI_API_KEY để tạo embedding!")
        else:
            with st.spinner("Đang Index dữ liệu từ output Buổi 5..."):
                res = rag.index()
                if res.get("status") == "success":
                    st.success(f"Đã index {res.get('indexed')} chunks mới!")
                    st.experimental_rerun()
                else:
                    st.error(res.get("message"))

with col2:
    st.subheader("Hỏi Đáp (Q&A)")
    
    top_k = st.slider("Số lượng tài liệu truy xuất (Top-k)", min_value=1, max_value=10, value=3)
    question = st.text_input("Nhập câu hỏi của bạn:", placeholder="Ví dụ: Rủi ro tín dụng là gì?")
    
    if st.button("Hỏi", type="primary"):
        if not question:
            st.warning("Vui lòng nhập câu hỏi.")
        else:
            with st.spinner("Đang tìm kiếm và tạo câu trả lời..."):
                result = rag.ask(question, top_k=top_k)
                
                st.markdown("### Câu trả lời (Answer)")
                st.info(result.get("answer", ""))
                
                st.markdown("### Bằng chứng (Kết quả Top-k)")
                sources = result.get("sources", [])
                if sources:
                    for i, src in enumerate(sources):
                        with st.expander(f"Nguồn {i+1}"):
                            st.write(src)
                else:
                    st.write("Không tìm thấy ngữ cảnh phù hợp.")
