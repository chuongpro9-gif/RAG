import os
import sys
import pandas as pd
import json

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

# Use Gemini instead of HF/OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import Reranker
from src.secure_retriever import SecureRetriever

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure API Key
if not os.getenv("GEMINI_API_KEY"):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", "buoi_11", ".env")) # Fallback

def get_rag_answer(llm, query, contexts):
    context_str = "\n\n".join(contexts)
    prompt = f"Dựa vào thông tin sau:\n{context_str}\n\nHãy trả lời câu hỏi: {query}"
    res = llm.invoke(prompt)
    return res.content

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    out_dir = os.path.join(base_dir, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Init Retrievers
    df = pd.read_csv(os.path.join(base_dir, "data", "processed", "chunks_secure.csv"))
    bm25 = BM25Retriever(df)
    dense = DenseRetriever(df)
    hybrid = HybridRetriever(bm25, dense)
    reranker = Reranker()
    secure_hybrid = SecureRetriever(hybrid)
    
    # 2. Init LLM
    print("Khởi tạo Gemini LLM thay cho HF...")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # 3. Create Sample QA (Golden Dataset)
    # Rút gọn số lượng câu hỏi để test nhanh
    print("Tạo mẫu câu hỏi (Golden Dataset)...")
    sample_qa = [
        {
            "question": "Ai là người có thẩm quyền phê duyệt tín dụng?",
            "ground_truth": "Người có thẩm quyền phê duyệt tín dụng được quy định theo phân cấp thẩm quyền của ngân hàng."
        },
        {
            "question": "Quy trình đối soát tự động giao dịch diễn ra như thế nào?",
            "ground_truth": "Hệ thống sẽ tự động đối chiếu các giao dịch phát sinh với sổ cái kế toán để phát hiện sai lệch."
        },
        {
            "question": "Mục đích của việc rà soát phân quyền truy cập định kỳ là gì?",
            "ground_truth": "Để đảm bảo các tài khoản chỉ có quyền truy cập phù hợp với phạm vi công việc, tránh rò rỉ dữ liệu."
        }
    ]
    
    user_roles = ["Admin", "HR", "Risk_Manager", "Staff"]
    
    data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }
    
    print("Bắt đầu sinh câu trả lời RAG...")
    for qa in sample_qa:
        q = qa["question"]
        # Retrieve context
        res_hybrid = secure_hybrid.retrieve(q, user_roles, top_k=5)
        res_reranked = reranker.rerank(q, res_hybrid, top_k=3)
        
        contexts = [r["text"] for r in res_reranked]
        
        # Generate answer
        answer = get_rag_answer(llm, q, contexts)
        
        data["question"].append(q)
        data["contexts"].append(contexts)
        data["answer"].append(answer)
        data["ground_truth"].append(qa["ground_truth"])
        
    dataset = Dataset.from_dict(data)
    
    print("Bắt đầu đánh giá bằng Ragas...")
    # Wrap in langchain LLM for Ragas
    
    result = evaluate(
        dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ],
        llm=llm,
        embeddings=embeddings
    )
    
    df_res = result.to_pandas()
    res_csv = os.path.join(base_dir, "data", "eval", "evaluation_results.csv")
    os.makedirs(os.path.dirname(res_csv), exist_ok=True)
    df_res.to_csv(res_csv, index=False)
    
    report_path = os.path.join(out_dir, "ragas_evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Báo Cáo Đánh Giá RAG Bằng Ragas\n\n")
        f.write("## 1. Kết quả Trung Bình\n")
        f.write(f"- Context Precision: {result.get('context_precision', 0):.4f}\n")
        f.write(f"- Context Recall: {result.get('context_recall', 0):.4f}\n")
        f.write(f"- Faithfulness: {result.get('faithfulness', 0):.4f}\n")
        f.write(f"- Answer Relevancy: {result.get('answer_relevancy', 0):.4f}\n\n")
        f.write("## 2. Đề Xuất Tối Ưu\n")
        f.write("- **Faithfulness thấp**: Yêu cầu Prompt khắt khe hơn, cấm tự suy diễn.\n")
        f.write("- **Context Recall thấp**: Tăng Top K hoặc mở rộng câu hỏi (Query Expansion).\n")
        
    print(f"\n--- ĐÃ XUẤT BÁO CÁO: {report_path} ---")

if __name__ == "__main__":
    main()
