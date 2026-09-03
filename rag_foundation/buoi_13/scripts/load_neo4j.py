import os
import sys
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "10062002")

def run_query(driver, query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters or {})

def main():
    print("--- CONNECTING TO NEO4J ---")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Connected successfully!")
    except Exception as e:
        print(f"[ERROR] Could not connect to Neo4j. Please check if Neo4j is running and credentials are correct.\nError: {e}")
        return

    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    df_entities = pd.read_csv(os.path.join(outputs_dir, "entities.csv")).fillna("")
    df_relations = pd.read_csv(os.path.join(outputs_dir, "relations.csv")).fillna("")

    # 1. Constraints
    print("\n--- CREATING CONSTRAINTS ---")
    run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (r:RuiRo) REQUIRE r.id IS UNIQUE")
    run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (k:KiemSoat) REQUIRE k.id IS UNIQUE")
    run_query(driver, "CREATE CONSTRAINT IF NOT EXISTS FOR (s:SuKienRuiRo) REQUIRE s.id IS UNIQUE")
    print("Constraints created.")

    # 2. Nodes
    print("\n--- IMPORTING NODES ---")
    for _, row in df_entities.iterrows():
        props = row.to_dict()
        node_id = props.pop("id")
        node_type = props.pop("type")
        
        if node_type == "RuiRo":
            q = "MERGE (n:RuiRo {id: $id}) SET n += $props"
        elif node_type == "KiemSoat":
            q = "MERGE (n:KiemSoat {id: $id}) SET n += $props"
        elif node_type == "SuKienRuiRo":
            q = "MERGE (n:SuKienRuiRo {id: $id}) SET n += $props"
        else:
            continue
            
        run_query(driver, q, {"id": node_id, "props": props})
    print(f"Imported {len(df_entities)} nodes.")

    # 3. Relationships
    print("\n--- IMPORTING RELATIONSHIPS ---")
    for _, row in df_relations.iterrows():
        src = row["source_id"]
        tgt = row["target_id"]
        rel_type = row["relationship_type"]
        
        props = row.to_dict()
        
        if rel_type == "MITIGATES":
            q = """
            MATCH (s:KiemSoat {id: $src}), (t:RuiRo {id: $tgt})
            MERGE (s)-[r:MITIGATES]->(t)
            SET r += $props
            """
        elif rel_type == "OBSERVED_AS":
            q = """
            MATCH (s:RuiRo {id: $src}), (t:SuKienRuiRo {id: $tgt})
            MERGE (s)-[r:OBSERVED_AS]->(t)
            SET r += $props
            """
        else:
            continue
            
        run_query(driver, q, {"src": src, "tgt": tgt, "props": props})
        
    print(f"Imported {len(df_relations)} relationships.")
    
    driver.close()
    print("\n--- DONE ---")

if __name__ == "__main__":
    main()
