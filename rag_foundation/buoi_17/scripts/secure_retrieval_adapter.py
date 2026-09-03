import os
import sys
import pandas as pd

# Thêm đường dẫn tới buoi_16 để tái sử dụng SecureRetriever
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUOI16_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "buoi_16"))
if BUOI16_DIR not in sys.path:
    sys.path.insert(0, BUOI16_DIR)

from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker
from src.secure_retriever import SecureRetriever

class SecureRetrievalAdapter:
    """Adapter tái sử dụng SecureRetriever từ Buổi 16"""
    def __init__(self):
        # Đổi sang sử dụng data chunk thật (Agribank Internal Policies) của bạn
        base_buoi17 = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(base_buoi17, "data", "chunks_combined_secure.csv")
        data_path = os.path.abspath(data_path)
        df = pd.read_csv(data_path)
        
        # Đổi tên cột cho tương thích với code cũ
        if 'text' in df.columns and 'content_html' not in df.columns:
            df.rename(columns={'text': 'content_html'}, inplace=True)
        if 'chunk_id' in df.columns and 'id' not in df.columns:
            df.rename(columns={'chunk_id': 'id'}, inplace=True)
            
        bm25 = BM25Retriever(df)
        dense = DenseRetriever(df)
        self.hybrid = HybridRetriever(bm25, dense)
        self.reranker = Reranker()
        self.retriever = SecureRetriever(self.hybrid)
        
    def retrieve(self, query, user_roles, method="hybrid_rerank", top_k=5):
        results = self.retriever.retrieve(query, user_roles=user_roles, top_k=top_k*2 if method=="hybrid_rerank" else top_k)
        
        if method == "hybrid_rerank" and results:
            results = self.reranker.rerank(query, results, top_k=top_k)
            
        denied_count = 0 # Dummy count since we don't have exact blocked count easily
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "chunk_id": r.get("id"),
                "document_id": r.get("metadata", {}).get("document_id", ""),
                "title": r.get("metadata", {}).get("title", ""),
                "article": r.get("metadata", {}).get("article", ""),
                "citation": r.get("metadata", {}).get("citation", ""),
                "allowed_roles": r.get("metadata", {}).get("allowed_roles", []),
                "text": r.get("text"),
                "score": r.get("rerank_score", r.get("score"))
            })
            
        return {
            "results": formatted_results,
            "denied_count": denied_count
        }
