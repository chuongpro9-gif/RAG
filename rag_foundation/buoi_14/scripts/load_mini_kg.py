import os
import sys
import pandas as pd
from neo4j import GraphDatabase

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "10062002")

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    kb_dir = os.path.join(base_dir, "..", "kb+hops")
    
    print("--- Khởi tạo Neo4j cho Buổi 14 ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Run Schema
    with open(os.path.join(base_dir, "cypher", "schema.cypher"), "r", encoding="utf-8") as f:
        schema_queries = f.read().split(";")
        
    with driver.session() as session:
        for q in schema_queries:
            if q.strip():
                session.run(q.strip())
                print(f"Executed: {q.strip()[:50]}...")
                
    # Load Nodes (VanBan and DieuKhoan)
    df_meta = pd.read_csv(os.path.join(kb_dir, "metadata.csv"))
    df_content = pd.read_csv(os.path.join(kb_dir, "content.csv"))
    
    print("Nạp dữ liệu VanBan...")
    with driver.session() as session:
        for _, row in df_meta.iterrows():
            session.run("""
            MERGE (v:VanBan {id: $id})
            SET v.title = $title, v.loai_van_ban = $loai_van_ban, v.lab_session = 'buoi_14'
            """, id=row['id'], title=row.get('title', ''), loai_van_ban=row.get('loai_van_ban', ''))

    print("Nạp dữ liệu DieuKhoan và tạo quan hệ CONTAINS...")
    with driver.session() as session:
        for _, row in df_content.iterrows():
            # document_id is doc_id or id in content depending on format. Let's assume content.csv has `id` which is actually DieuKhoan ID.
            # wait, how do we know which VanBan it belongs to? We need relationships.csv
            session.run("""
            MERGE (d:DieuKhoan {id: $id})
            SET d.text = $text, d.lab_session = 'buoi_14'
            """, id=row['id'], text=row.get('content_html', ''))
            
    print("Nạp quan hệ từ relationships.csv...")
    if os.path.exists(os.path.join(kb_dir, "relationships.csv")):
        df_rels = pd.read_csv(os.path.join(kb_dir, "relationships.csv"))
        with driver.session() as session:
            for _, row in df_rels.iterrows():
                src = row['doc_id']
                tgt = row['other_doc_id']
                rel_type = row['relationship_type'] if 'relationship_type' in row else 'RELATED_TO'
                
                # Check if they are VanBan or DieuKhoan
                # We can just MERGE both as generic nodes with the relationship if we don't know the label, 
                # but we've already created them. We can use MATCH (s {id: $src}), (t {id: $tgt})
                query = f"""
                MATCH (s {{id: $src}}), (t {{id: $tgt}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.lab_session = 'buoi_14'
                """
                session.run(query, src=src, tgt=tgt)
                
    print("Hoàn tất nạp Mini Knowledge Graph!")
    driver.close()

if __name__ == "__main__":
    main()
