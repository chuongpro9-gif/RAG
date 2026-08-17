import os
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "10062002")

# Tải model 1 lần (dùng Singleton pattern để khỏi tải đi tải lại)
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5", device="cpu")
    return _model

def get_context(query, k=5, hops=0):
    """
    Tìm kiếm vector trên Neo4j, sau đó mở rộng N bước (hops) để lấy thêm ngữ cảnh.
    """
    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    context_chunks = []
    
    with driver.session() as session:
        # Bước 1: Tìm k chunks gần nhất bằng Cosine Similarity
        # Sử dụng hàm vector.similarity.cosine có sẵn của Neo4j 5.x
        res = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            WITH c, vector.similarity.cosine(c.embedding, $query_embedding) AS score
            ORDER BY score DESC
            LIMIT $k
            MATCH (c)-[:PART_OF]->(d:Document)
            RETURN c.id AS chunk_id, c.text AS text, d.id AS doc_id, score
        """, query_embedding=query_embedding, k=k)
        
        direct_matches = []
        doc_ids = set()
        for record in res:
            direct_matches.append(record["text"])
            doc_ids.add(record["doc_id"])
            context_chunks.append(f"[Trực tiếp] (Tài liệu: {record['doc_id']}): {record['text']}")
            
        # Bước 2: Multi-hop (nếu hops > 0)
        if hops > 0 and doc_ids:
            doc_list = list(doc_ids)
            # Truy vấn các tài liệu liên quan trong N bước
            hop_query = f"""
                MATCH (d:Document)-[r:CAN_CU|THAY_THE|HOP_NHAT*1..{hops}]-(related:Document)
                WHERE d.id IN $doc_list
                RETURN d.id AS source, type(r[-1]) AS rel_type, related.id AS target
                LIMIT 20
            """
            rel_res = session.run(hop_query, doc_list=doc_list)
            
            for record in rel_res:
                rel_info = f"[Bổ sung đa bước] (Quan hệ đồ thị): Văn bản '{record['source']}' có quan hệ {record['rel_type']} với văn bản '{record['target']}'"
                context_chunks.append(rel_info)
                
    driver.close()
    return "\n\n".join(context_chunks)

if __name__ == "__main__":
    print("Testing retriever (0 hops)...")
    print(get_context("Nghị định 46 thay thế cho nghị định nào?", hops=0))
    print("-" * 50)
    print("Testing retriever (2 hops)...")
    print(get_context("Nghị định 46 thay thế cho nghị định nào?", hops=2))
