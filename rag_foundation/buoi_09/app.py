import streamlit as st
import json
import time
from hierarchical_rag import run_multi_query_pipeline, expand_query, build_hierarchy
from rag import load_chunks
import os

st.set_page_config(page_title="Multi-query RAG Dashboard", layout="wide")

st.title("Advanced RAG - Buổi 09")

st.sidebar.header("Công cụ quản trị")
if st.sidebar.button("Xây dựng Hierarchy (Build)"):
    with st.spinner("Đang xây dựng..."):
        try:
            build_hierarchy()
            st.sidebar.success("Xây dựng Hierarchy thành công!")
        except Exception as e:
            st.sidebar.error(f"Lỗi: {e}")

tabs = st.tabs(["Hỏi đáp (Retrieval)", "Multi-query Explorer"])

with tabs[0]:
    mode = st.selectbox("Chế độ truy vấn (Mode)", 
                        ["multi_parent", "single_parent", "multi_flat", "single_flat"], 
                        index=0)
    
    question = st.text_input("Nhập câu hỏi pháp lý:")
    
    if st.button("Hỏi", type="primary") and question:
        with st.spinner(f"Đang xử lý bằng mode {mode}..."):
            try:
                ans, docs, trace = run_multi_query_pipeline(question, mode)
                
                st.subheader("Câu trả lời")
                st.write(ans)
                
                with st.expander("Nguồn tham khảo (Evidence)"):
                    for d in docs:
                        st.markdown(f"**Nguồn:** {d['source']} (Trang {d['page_start']})")
                        st.text(d['text'])
                        st.markdown("---")
            except Exception as e:
                st.error(f"Lỗi: {e}")

with tabs[1]:
    st.write("Khám phá Multi-query Expansion")
    mq_question = st.text_input("Nhập câu hỏi để xem Query Variants:")
    if st.button("Expand Query") and mq_question:
        with st.spinner("Đang sinh truy vấn phụ..."):
            expanded = expand_query(mq_question)
            st.json(expanded)

if __name__ == "__main__":
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if not get_script_run_ctx():
        import sys
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
