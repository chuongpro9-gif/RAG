from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        # You can use a multi-lingual model like "amberoad/bert-multilingual-passage-reranking-msmarco"
        self.model = CrossEncoder(model_name)

    def rerank(self, query, results, top_k=5):
        if not results:
            return []
            
        pairs = [[query, res["text"]] for res in results]
        scores = self.model.predict(pairs)
        
        for i, res in enumerate(results):
            res["rerank_score"] = float(scores[i])
            
        # Sort by rerank score
        sorted_results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        return sorted_results[:top_k]
