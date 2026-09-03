import os
import sys
import pandas as pd
import json
from neo4j import GraphDatabase

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "10062002")

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    in_path = os.path.join(base_dir, "data", "processed", "chunks_secure.csv")
    
    print("--- Khởi tạo Neo4j cho Buổi 15 ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    df = pd.read_csv(in_path)
    
    print("Nạp dữ liệu bảo mật (allowed_roles) vào các node DieuKhoan...")
    with driver.session() as session:
        for _, row in df.iterrows():
            roles = json.loads(row["allowed_roles"])
            # DieuKhoan id mapped to row['id']
            session.run("""
            MATCH (d:DieuKhoan {id: $id, lab_session: 'buoi_14'})
            SET d.allowed_roles = $roles
            """, id=row['id'], roles=roles)
            
    print("Kiểm tra dữ liệu sau khi nạp:")
    with driver.session() as session:
        res = session.run("MATCH (d:DieuKhoan) WHERE d.allowed_roles IS NOT NULL RETURN count(d) as c")
        print(f"Số lượng DieuKhoan có allowed_roles: {res.single()['c']}")
        
    driver.close()
    print("Hoàn tất cập nhật Security Tags!")

if __name__ == "__main__":
    main()
