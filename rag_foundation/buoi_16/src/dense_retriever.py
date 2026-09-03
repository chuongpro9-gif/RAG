import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class DenseRetriever:
    def __init__(self, df, text_column="content_html", model_name="keepitreal/vietnamese-sbert"):
        self.df = df
        self.text_column = text_column
        self.model = SentenceTransformer(model_name)
        
        texts = [str(text) for text in df[text_column]]
        self.embeddings = self.model.encode(texts, show_progress_bar=True)

    def retrieve(self, query, top_k=5):
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            row = self.df.iloc[idx]
            results.append({
                "id": row.get("id", idx),
                "text": row[self.text_column],
                "score": float(similarities[idx]),
                "metadata": row.to_dict()
            })
        return results
