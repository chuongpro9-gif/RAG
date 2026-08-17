import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

def run_step_8():
    print("--- BƯỚC 7 & 8: IMPORT KNOWLEDGE GRAPH VÀO NEO4J ---")
    base_dir = Path(__file__).parent / "ner_kb"
    docs_path = base_dir / "cleaned_documents.csv"
    ents_path = base_dir / "entities.csv"
    rels_path = base_dir / "relationships.csv"
    
    load_dotenv(Path(__file__).parent / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    
    # Hàm chạy truy vấn an toàn
    def run_query(query, parameters=None):
        with driver.session() as session:
            session.run(query, parameters or {})

    # 1. Tạo Constraints
    print("1. Đang tạo Uniqueness Constraints...")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.so_ky_hieu IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CoQuan) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:NguoiKy) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (o:DoiTuongApDung) REQUIRE o.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (l:LinhVuc) REQUIRE l.id IS UNIQUE",
    ]
    for c in constraints:
        run_query(c)
        
    # 2. Import Documents
    print("2. Đang Import Documents...")
    df_docs = pd.read_csv(docs_path)
    doc_count = 0
    for _, row in df_docs.iterrows():
        query = """
        MERGE (d:Document {so_ky_hieu: $skh})
        SET d.doc_id = $doc_id,
            d.title = $title,
            d.ngay_ban_hanh = $ngay_bh,
            d.loai_van_ban = $loai
        """
        run_query(query, {
            "skh": str(row['so_ky_hieu']),
            "doc_id": str(row['id']),
            "title": str(row['title']),
            "ngay_bh": str(row['ngay_ban_hanh']),
            "loai": str(row['loai_van_ban'])
        })
        doc_count += 1

    # 3. Import Entities
    print("3. Đang Import Entities...")
    if ents_path.exists():
        df_ents = pd.read_csv(ents_path)
        ent_count = 0
        for _, row in df_ents.iterrows():
            ent_type = str(row['entity_type'])
            canon_name = str(row['canonical_name'])
            # Tạo ID duy nhất bằng canonical name
            query = f"""
            MERGE (e:{ent_type} {{id: $name}})
            SET e.name = $name
            """
            run_query(query, {"name": canon_name})
            ent_count += 1
            
    # 4. Import Relationships
    print("4. Đang Import Relationships...")
    rel_errors = 0
    if rels_path.exists():
        df_rels = pd.read_csv(rels_path)
        for _, row in df_rels.iterrows():
            source = str(row['source'])
            target = str(row['target'])
            rel_type = str(row['relationship_type'])
            
            # Nếu target là document (trong THAM_CHIEU, SUA_DOI_BO_SUNG, THAY_THE_BOI)
            if rel_type in ["THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI"]:
                query = f"""
                MATCH (s:Document {{so_ky_hieu: $source}})
                MATCH (t:Document {{so_ky_hieu: $target}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.method = $method, r.confidence = $conf
                """
            else:
                # Target là Entity
                ent_label = "CoQuan" if rel_type == "BAN_HANH_BOI" else \
                            "NguoiKy" if rel_type == "KY_BOI" else \
                            "DoiTuongApDung" if rel_type == "AP_DUNG_CHO" else \
                            "LinhVuc"
                query = f"""
                MATCH (s:Document {{so_ky_hieu: $source}})
                MATCH (t:{ent_label} {{id: $target}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.method = $method, r.confidence = $conf
                """
            try:
                run_query(query, {
                    "source": source,
                    "target": target,
                    "method": str(row.get('method', 'rule')),
                    "conf": float(row.get('confidence', 1.0))
                })
            except Exception as e:
                rel_errors += 1
                
    # 5. Lấy thống kê từ Graph
    def get_count(query):
        with driver.session() as session:
            res = session.run(query)
            return res.single()[0]
            
    print("\n--- BÁO CÁO KẾT QUẢ IMPORT ---")
    print(f"Số Document nodes: {get_count('MATCH (n:Document) RETURN count(n)')}")
    print(f"Số CoQuan nodes: {get_count('MATCH (n:CoQuan) RETURN count(n)')}")
    print(f"Số NguoiKy nodes: {get_count('MATCH (n:NguoiKy) RETURN count(n)')}")
    print(f"Số DoiTuongApDung nodes: {get_count('MATCH (n:DoiTuongApDung) RETURN count(n)')}")
    print(f"Số LinhVuc nodes: {get_count('MATCH (n:LinhVuc) RETURN count(n)')}")
    
    print("\nRelationships:")
    print(f"THAM_CHIEU: {get_count('MATCH ()-[r:THAM_CHIEU]->() RETURN count(r)')}")
    print(f"SUA_DOI_BO_SUNG: {get_count('MATCH ()-[r:SUA_DOI_BO_SUNG]->() RETURN count(r)')}")
    print(f"THAY_THE_BOI: {get_count('MATCH ()-[r:THAY_THE_BOI]->() RETURN count(r)')}")
    print(f"BAN_HANH_BOI: {get_count('MATCH ()-[r:BAN_HANH_BOI]->() RETURN count(r)')}")
    print(f"KY_BOI: {get_count('MATCH ()-[r:KY_BOI]->() RETURN count(r)')}")
    print(f"AP_DUNG_CHO: {get_count('MATCH ()-[r:AP_DUNG_CHO]->() RETURN count(r)')}")
    print(f"THUOC_LINH_VUC: {get_count('MATCH ()-[r:THUOC_LINH_VUC]->() RETURN count(r)')}")
    
    if rel_errors > 0:
        print(f"\n[WARNING] Có {rel_errors} mối quan hệ bị lỗi khi import.")
    
    driver.close()
    print("\n[PASS] Bước 7 & 8 hoàn thành. Graph đã được đưa lên Neo4j!")

if __name__ == "__main__":
    run_step_8()
