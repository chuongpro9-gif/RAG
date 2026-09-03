import os
import sys
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "chunks_normalized.csv")
    df = pd.read_csv(data_path)
    
    print("Khởi tạo BM25 Retriever...")
    bm25 = BM25Retriever(df)
    
    print("Khởi tạo Dense Retriever...")
    dense = DenseRetriever(df)
    
    print("Khởi tạo Hybrid Retriever...")
    hybrid = HybridRetriever(bm25, dense)
    
    print("Khởi tạo Reranker...")
    reranker = Reranker()
    
    query = "Quyết định phê duyệt tín dụng"
    print(f"\n--- TRUY VẤN: '{query}' ---")
    
    print("\n[1] Kết quả BM25:")
    res_bm25 = bm25.retrieve(query, top_k=2)
    for r in res_bm25:
        print(f" - ID: {r['id']}, Score: {r['score']:.4f}, Text: {r['text'][:50]}...")
        
    print("\n[2] Kết quả Dense:")
    res_dense = dense.retrieve(query, top_k=2)
    for r in res_dense:
        print(f" - ID: {r['id']}, Score: {r['score']:.4f}, Text: {r['text'][:50]}...")
        
    print("\n[3] Kết quả Hybrid:")
    res_hybrid = hybrid.retrieve(query, top_k=5) # Get top 5 for reranking
    for r in res_hybrid:
        print(f" - ID: {r['id']}, Score: {r['score']:.4f}, Text: {r['text'][:50]}...")
        
    print("\n[4] Kết quả sau khi Rerank (từ top 5 Hybrid):")
    res_reranked = reranker.rerank(query, res_hybrid, top_k=2)
    for r in res_reranked:
        print(f" - ID: {r['id']}, Rerank Score: {r['rerank_score']:.4f}, Text: {r['text'][:50]}...")

if __name__ == "__main__":
    main()
