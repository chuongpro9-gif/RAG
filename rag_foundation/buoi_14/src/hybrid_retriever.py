class HybridRetriever:
    def __init__(self, bm25_retriever, dense_retriever):
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever

    def retrieve(self, query, top_k=5, k_rrf=60):
        bm25_results = self.bm25_retriever.retrieve(query, top_k=10)
        dense_results = self.dense_retriever.retrieve(query, top_k=10)
        
        # RRF Fusion
        scores = {}
        items = {}
        
        for rank, res in enumerate(bm25_results):
            doc_id = res["id"]
            if doc_id not in scores:
                scores[doc_id] = 0
                items[doc_id] = res
            scores[doc_id] += 1.0 / (k_rrf + rank + 1)
            
        for rank, res in enumerate(dense_results):
            doc_id = res["id"]
            if doc_id not in scores:
                scores[doc_id] = 0
                items[doc_id] = res
            scores[doc_id] += 1.0 / (k_rrf + rank + 1)
            
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for doc_id, rrf_score in sorted_results[:top_k]:
            res = items[doc_id]
            res["score"] = rrf_score  # Replace with RRF score
            final_results.append(res)
            
        return final_results
