import os
import sys
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker
from src.secure_retriever import SecureRetriever

@st.cache_resource
def load_secure_retrievers():
    data_path = os.path.join(os.path.dirname(__file__), "data", "processed", "chunks_secure.csv")
    df = pd.read_csv(data_path)
    bm25 = BM25Retriever(df)
    dense = DenseRetriever(df)
    hybrid = HybridRetriever(bm25, dense)
    reranker = Reranker()
    
    # Wrap in secure retriever
    secure_bm25 = SecureRetriever(bm25)
    secure_dense = SecureRetriever(dense)
    secure_hybrid = SecureRetriever(hybrid)
    
    return secure_bm25, secure_dense, secure_hybrid, reranker, df

st.set_page_config(page_title="Hệ thống RAG - Phân quyền RBAC", layout="wide")

st.title("🛡️ Secure RAG System: Role-Based Access Control")

secure_bm25, secure_dense, secure_hybrid, reranker, df = load_secure_retrievers()

# Giao diện chọn Role
st.sidebar.header("🔑 Chọn Vai Trò (Impersonate Role)")
available_roles = ["Admin", "HR", "Risk_Manager", "Staff", "Guest"]
selected_roles = st.sidebar.multiselect("Vai trò của bạn hiện tại:", available_roles, default=["Guest"])

query = st.text_input("Nhập câu hỏi của bạn:", "Quy định về rủi ro tín dụng là gì?")
method = st.selectbox("Phương pháp Retrieval", ["BM25", "Dense", "Hybrid", "Hybrid + Reranker"])

if st.button("Tìm kiếm an toàn"):
    if not query:
        st.warning("Vui lòng nhập câu hỏi!")
    elif not selected_roles:
        st.error("Vui lòng chọn ít nhất 1 vai trò để truy cập!")
    else:
        with st.spinner(f"Đang tìm kiếm dưới quyền {selected_roles}..."):
            if method == "BM25":
                results = secure_bm25.retrieve(query, selected_roles, top_k=5)
            elif method == "Dense":
                results = secure_dense.retrieve(query, selected_roles, top_k=5)
            elif method == "Hybrid":
                results = secure_hybrid.retrieve(query, selected_roles, top_k=5)
            elif method == "Hybrid + Reranker":
                # Need to retrieve more context securely, then rerank
                res_hybrid = secure_hybrid.retrieve(query, selected_roles, top_k=10)
                results = reranker.rerank(query, res_hybrid, top_k=5)
                
            st.success(f"Tìm thấy {len(results)} kết quả (đã lọc quyền truy cập)!")
            
            import streamlit.components.v1 as components
            for i, res in enumerate(results):
                with st.expander(f"Top {i+1}: Độ liên quan {res.get('rerank_score', res['score']):.4f}"):
                    st.write("**ID:**", res["id"])
                    st.write("**Quyền yêu cầu:**", res["metadata"].get("allowed_roles"))
                    html_content = f"<style>body {{ background-color: white; color: black; padding: 10px; border-radius: 5px; }}</style>{res['text']}"
                    components.html(html_content, height=300, scrolling=True)
