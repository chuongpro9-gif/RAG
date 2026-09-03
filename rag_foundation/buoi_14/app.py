import os
import sys
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker

# Khởi tạo mô hình & dữ liệu (Cache)
@st.cache_resource
def load_retrievers():
    data_path = os.path.join(os.path.dirname(__file__), "data", "processed", "chunks_normalized.csv")
    df = pd.read_csv(data_path)
    bm25 = BM25Retriever(df)
    dense = DenseRetriever(df)
    hybrid = HybridRetriever(bm25, dense)
    reranker = Reranker()
    return bm25, dense, hybrid, reranker, df

st.set_page_config(page_title="Hệ thống RAG - Buổi 14", layout="wide")

st.title("🔍 RAG System: Hybrid Search & Reranking")

bm25, dense, hybrid, reranker, df = load_retrievers()

query = st.text_input("Nhập câu hỏi của bạn:", "Ai là người phê duyệt khoản vay?")
method = st.selectbox("Phương pháp Retrieval", ["BM25", "Dense (Vector)", "Hybrid (BM25 + Dense)", "Hybrid + Reranker (Cross-Encoder)"])

if st.button("Tìm kiếm"):
    if not query:
        st.warning("Vui lòng nhập câu hỏi!")
    else:
        with st.spinner("Đang tìm kiếm..."):
            if method == "BM25":
                results = bm25.retrieve(query, top_k=5)
            elif method == "Dense (Vector)":
                results = dense.retrieve(query, top_k=5)
            elif method == "Hybrid (BM25 + Dense)":
                results = hybrid.retrieve(query, top_k=5)
            elif method == "Hybrid + Reranker (Cross-Encoder)":
                res_hybrid = hybrid.retrieve(query, top_k=10)
                results = reranker.rerank(query, res_hybrid, top_k=5)
                
            st.success(f"Tìm thấy {len(results)} kết quả!")
            
            import streamlit.components.v1 as components
            for i, res in enumerate(results):
                with st.expander(f"Top {i+1}: Độ liên quan {res.get('rerank_score', res['score']):.4f}"):
                    st.write("**ID:**", res["id"])
                    html_content = f"<style>body {{ background-color: white; color: black; padding: 10px; border-radius: 5px; }}</style>{res['text']}"
                    components.html(html_content, height=300, scrolling=True)
