from rank_bm25 import BM25Okapi
import numpy as np

class BM25Retriever:
    def __init__(self, df, text_column="content_html"):
        self.df = df
        self.text_column = text_column
        # Tokenize very simply for BM25 (split by space)
        self.corpus = [str(text).lower().split() for text in df[text_column]]
        self.bm25 = BM25Okapi(self.corpus)

    def retrieve(self, query, top_k=5):
        tokenized_query = query.lower().split()
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(doc_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            row = self.df.iloc[idx]
            results.append({
                "id": row.get("id", idx),
                "text": row[self.text_column],
                "score": float(doc_scores[idx]),
                "metadata": row.to_dict()
            })
        return results
