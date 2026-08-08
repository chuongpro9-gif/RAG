"""
Evaluation Engine for Advanced RAG.
Metrics: Recall@K, MRR@K, nDCG@K.
"""
import os
import argparse
import sys
import json
import math
from pathlib import Path
from advanced_rag import query_advanced

def calculate_recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    retrieved_k = retrieved_ids[:k]
    hits = sum(1 for rid in retrieved_k if rid in relevant_ids)
    return hits / len(relevant_ids)

def calculate_mrr_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    retrieved_k = retrieved_ids[:k]
    for i, rid in enumerate(retrieved_k):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0

def calculate_ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    
    retrieved_k = retrieved_ids[:k]
    dcg = 0.0
    for i, rid in enumerate(retrieved_k):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)
            
    # idcg
    idcg = 0.0
    for i in range(min(k, len(relevant_ids))):
        idcg += 1.0 / math.log2(i + 2)
        
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

def evaluate_system(questions_file: str, strategy: str, k: int = 5):
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    eval_qs = [q for q in data if q.get("scope") != "out_of_scope" and q.get("relevant_chunk_ids")]
    print(f"Tổng số câu hỏi hợp lệ: {len(eval_qs)}")
    
    modes = ["bm25", "semantic", "hybrid", "hybrid_rerank"]
    results = {m: {"recall": [], "mrr": [], "ndcg": []} for m in modes}
    
    for q in eval_qs:
        question = q["question"]
        relevant_ids = q["relevant_chunk_ids"]
        print(f" Đang đánh giá: {question}")
        
        for m in modes:
            _, chunks, _ = query_advanced(question, strategy, m, skip_generation=True)
            retrieved_ids = [c["chunk_id"] for c in chunks]
            
            rec = calculate_recall_at_k(retrieved_ids, relevant_ids, k)
            mrr = calculate_mrr_at_k(retrieved_ids, relevant_ids, k)
            ndcg = calculate_ndcg_at_k(retrieved_ids, relevant_ids, k)
            
            results[m]["recall"].append(rec)
            results[m]["mrr"].append(mrr)
            results[m]["ndcg"].append(ndcg)
            
    # Calculate means
    summary = {}
    print(f"\n=== EVALUATION RESULTS (K={k}) ===")
    print(f"{'Mode':<15} | {'Recall':<10} | {'MRR':<10} | {'nDCG':<10}")
    print("-" * 55)
    
    for m in modes:
        avg_rec = sum(results[m]["recall"]) / len(eval_qs) if eval_qs else 0.0
        avg_mrr = sum(results[m]["mrr"]) / len(eval_qs) if eval_qs else 0.0
        avg_ndcg = sum(results[m]["ndcg"]) / len(eval_qs) if eval_qs else 0.0
        
        summary[m] = {
            "recall": avg_rec,
            "mrr": avg_mrr,
            "ndcg": avg_ndcg
        }
        print(f"{m:<15} | {avg_rec:<10.4f} | {avg_mrr:<10.4f} | {avg_ndcg:<10.4f}")
        
    out_file = Path(questions_file).parent.parent / "reports" / f"eval_report_{strategy}.json"
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved report to {out_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="eval/questions.json")
    parser.add_argument("--strategy", default="hierarchical")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    
    evaluate_system(args.questions, args.strategy, args.k)
