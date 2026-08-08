"""
Streamlit App for Advanced RAG comparison and trace visualization.
"""
import streamlit as st
import json
import time
from advanced_rag import query_advanced

st.set_page_config(page_title="Advanced RAG Dashboard", layout="wide")
st.title("Advanced RAG Dashboard")

if "last_trace" not in st.session_state:
    st.session_state.last_trace = None

tab_qa, tab_compare, tab_trace, tab_eval = st.tabs(["Hỏi đáp", "So sánh", "Trace", "Đánh giá"])

with tab_qa:
    st.header("Truy vấn RAG")
    col1, col2 = st.columns(2)
    with col1:
        strategy = st.selectbox("Strategy", ["hierarchical", "flat", "window"], index=0)
    with col2:
        mode = st.selectbox("Mode", ["bm25", "semantic", "hybrid", "hybrid_rerank"], index=3)
        
    question = st.text_area("Câu hỏi", height=100)
    
    if st.button("Hỏi", type="primary"):
        if not question.strip():
            st.warning("Vui lòng nhập câu hỏi.")
        else:
            with st.spinner(f"Đang xử lý bằng mode {mode}..."):
                try:
                    ans, chunks, trace = query_advanced(question, strategy, mode)
                    st.session_state.last_trace = trace
                    
                    st.markdown("### Answer")
                    st.info(ans)
                    
                    st.markdown("### Citations")
                    for i, c in enumerate(chunks, start=1):
                        with st.expander(f"[E{i}] ID: {c['chunk_id']} | Nguồn: {c['source']} trang {c['page_start']}"):
                            score_info = []
                            if "bm25_score" in c and c["bm25_score"] is not None: score_info.append(f"BM25: {c['bm25_score']:.2f}")
                            if "semantic_distance" in c and c["semantic_distance"] is not None: score_info.append(f"Sem Dist: {c['semantic_distance']:.2f}")
                            if "rrf_score" in c: score_info.append(f"RRF: {c['rrf_score']:.4f}")
                            if "rerank_score" in c: score_info.append(f"Rerank: {c['rerank_score']:.4f}")
                            
                            st.caption(" | ".join(score_info))
                            st.write(c["text"])
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab_compare:
    st.header("So sánh Ranking")
    cmp_strategy = st.selectbox("Strategy (Compare)", ["hierarchical", "flat", "window"], index=0, key="cmp_strat")
    cmp_question = st.text_input("Câu hỏi so sánh")
    
    if st.button("So sánh"):
        if cmp_question.strip():
            with st.spinner("Đang chạy cả 4 chế độ (không tốn phí API Generation)..."):
                try:
                    modes = ["bm25", "semantic", "hybrid", "hybrid_rerank"]
                    results = {}
                    for m in modes:
                        _, chunks, _ = query_advanced(cmp_question, cmp_strategy, m, skip_generation=True)
                        results[m] = chunks
                        
                    cols = st.columns(4)
                    for idx, m in enumerate(modes):
                        with cols[idx]:
                            st.subheader(m.upper())
                            if not results[m]:
                                st.write("Không tìm thấy")
                            for i, c in enumerate(results[m], start=1):
                                st.markdown(f"**{i}. {c['chunk_id']}**")
                                st.caption(f"_{c['text'][:80]}..._")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab_trace:
    st.header("Trace Detail")
    if st.session_state.last_trace:
        st.json(st.session_state.last_trace)
    else:
        st.write("Chưa có truy vấn nào được thực hiện.")

with tab_eval:
    st.header("Đánh giá hệ thống")
    st.info("Tính năng đang phát triển. Sẽ được triển khai ở module `evaluate.py`.")

