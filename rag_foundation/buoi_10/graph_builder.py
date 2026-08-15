import os
from pathlib import Path
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from html_parser import parse_html_to_chunks, extract_document_relations

# Cấu hình Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
# Mặc định lấy từ biến môi trường, hoặc bạn tự điền tay vào đây
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "10062002")

# Khởi tạo mô hình Embedding (chạy trên CPU)
EMBEDDING_MODEL_NAME = "thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5"

def get_embedding_model():
    print(f"Loading embedding model {EMBEDDING_MODEL_NAME} on CPU...")
    # Tự động tải từ HuggingFace
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
    return model

def ingest_to_neo4j(chunks, doc_relations):
    print("Kết nối Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Xóa dữ liệu cũ để tránh trùng lặp
        print("Xóa dữ liệu cũ trong Neo4j...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # 1. Tạo các nút Document
        docs = set(c["document_name"] for c in chunks)
        for doc in docs:
            session.run("""
                MERGE (d:Document {id: $doc_id, title: $doc_id})
            """, doc_id=doc)
            
        # 2. Tạo các nút Chunk và liên kết PART_OF
        print("Đang nạp các phân đoạn (Chunks) vào Neo4j...")
        for c in chunks:
            # Tham số cho Cypher
            session.run("""
                MERGE (ck:Chunk {id: $chunk_id})
                SET ck.text = $text,
                    ck.type = $type,
                    ck.seq_id = $seq_id,
                    ck.embedding = $embedding
                
                WITH ck
                MATCH (d:Document {id: $doc_id})
                MERGE (ck)-[:PART_OF]->(d)
            """, 
            chunk_id=c["chunk_id"], 
            text=c["text"], 
            type=c["type"],
            seq_id=c["seq_id"],
            embedding=c["embedding"],
            doc_id=c["document_name"])
            
        # 3. Xây dựng cấu trúc phân cấp PARENT_OF
        print("Đang xây dựng cây phân cấp (PARENT_OF)...")
        # Ta cần tìm Chunk ID của parent dựa trên text.
        # Ở bài này, để đơn giản, ta tìm parent có nội dung khớp trong cùng 1 Document
        for c in chunks:
            if c["parent"] and c["parent"] != "DOCUMENT_ROOT":
                session.run("""
                    MATCH (child:Chunk {id: $child_id})
                    MATCH (parent:Chunk {text: $parent_text})-[:PART_OF]->(d:Document {id: $doc_id})
                    MERGE (parent)-[:PARENT_OF]->(child)
                """,
                child_id=c["chunk_id"],
                parent_text=c["parent"],
                doc_id=c["document_name"])
                
        # 4. Tạo quan hệ NEXT (đọc tuần tự)
        print("Đang tạo liên kết tuần tự (NEXT)...")
        for doc in docs:
            doc_chunks = sorted([c for c in chunks if c["document_name"] == doc], key=lambda x: x["seq_id"])
            for i in range(len(doc_chunks) - 1):
                session.run("""
                    MATCH (c1:Chunk {id: $id1})
                    MATCH (c2:Chunk {id: $id2})
                    MERGE (c1)-[:NEXT]->(c2)
                """, id1=doc_chunks[i]["chunk_id"], id2=doc_chunks[i+1]["chunk_id"])
                
        # 5. Tạo quan hệ cấp tài liệu (CAN_CU, THAY_THE, vv)
        print("Đang tạo liên kết cấp tài liệu...")
        for rel in doc_relations:
            session.run(f"""
                MATCH (source:Document {{id: $source_id}})
                MERGE (target:Document {{id: $target_id}})
                MERGE (source)-[:{rel["type"]}]->(target)
            """, source_id=rel["source"], target_id=rel["target"])
            
    driver.close()
    print("Nạp dữ liệu hoàn tất!")

def main():
    data_dir = Path(__file__).parent.parent / "data_html"
    if not data_dir.exists():
        print(f"Thư mục {data_dir} không tồn tại. Vui lòng tạo và thả các file HTML vào đây.")
        return
        
    html_files = list(data_dir.glob("*.html")) + list(data_dir.glob("*.htm"))
    if not html_files:
        print(f"Không tìm thấy file .html hoặc .htm nào trong {data_dir}.")
        return
        
    print(f"Đã tìm thấy {len(html_files)} tài liệu HTML.")
    
    all_chunks = []
    
    # Bước 1: Phân tách HTML
    for f in html_files:
        doc_name = f.stem
        content = f.read_bytes()
        chunks = parse_html_to_chunks(content, doc_name)
        all_chunks.extend(chunks)
        print(f"Đã phân tách '{doc_name}' thành {len(chunks)} chunks.")
        
    # Trích xuất quan hệ văn bản
    doc_relations = extract_document_relations(all_chunks)
    
    # Bước 2: Nhúng Vector (Embedding)
    model = get_embedding_model()
    print(f"Đang tiến hành tạo Vector Nhúng cho {len(all_chunks)} chunks...")
    
    # Tối ưu nhúng theo batch
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    for i, chunk in enumerate(all_chunks):
        chunk["embedding"] = embeddings[i].tolist()
        
    # Bước 3 & 4: Nạp vào Neo4j
    ingest_to_neo4j(all_chunks, doc_relations)

if __name__ == "__main__":
    main()
