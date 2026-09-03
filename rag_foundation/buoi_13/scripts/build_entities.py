import os
import sys
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # 1. Read files
    df_risks = pd.read_csv(os.path.join(data_dir, "risk_profiles_seed.csv"))
    df_controls = pd.read_csv(os.path.join(data_dir, "controls_seed.csv"))
    df_events = pd.read_csv(os.path.join(data_dir, "risk_events_seed.csv"))
    df_rels = pd.read_csv(os.path.join(data_dir, "relationships_seed.csv"))
    
    # 2. Build entities
    # Schema: id, type, name, description, source_file, data_origin, verification_status
    # + other attributes
    
    entities = []
    
    for _, row in df_risks.iterrows():
        entities.append({
            "id": row["id"],
            "type": "RuiRo",
            "name": row["name"],
            "description": row["description"],
            "source_file": "risk_profiles_seed.csv",
            "data_origin": row["data_origin"],
            "verification_status": row["verification_status"],
            "category": row["category"],
            "cause": row["cause"],
            "event": row["event"],
            "impact": row["impact"],
            "inherent_level": row["inherent_level"],
            "residual_level": row["residual_level"],
            "owner_unit_id": row["owner_unit_id"]
        })
        
    for _, row in df_controls.iterrows():
        entities.append({
            "id": row["id"],
            "type": "KiemSoat",
            "name": row["name"],
            "description": "", # Controls don't have description in seed, just name
            "source_file": "controls_seed.csv",
            "data_origin": row["data_origin"],
            "verification_status": row["verification_status"],
            "control_type": row["control_type"],
            "frequency": row["frequency"],
            "owner_role_id": row["owner_role_id"],
            "effectiveness": row["effectiveness"]
        })
        
    for _, row in df_events.iterrows():
        entities.append({
            "id": row["id"],
            "type": "SuKienRuiRo",
            "name": row["id"], # Name is id since no name column
            "description": row["description"],
            "source_file": "risk_events_seed.csv",
            "data_origin": row["data_origin"],
            "verification_status": row["verification_status"],
            "risk_id": row["risk_id"],
            "occurred_at": row["occurred_at"],
            "discovered_at": row["discovered_at"],
            "severity": row["severity"],
            "loss_amount_vnd": row["loss_amount_vnd"]
        })
        
    df_entities = pd.DataFrame(entities)
    
    # Check valid references for relationships
    valid_ids = set(df_entities["id"].tolist())
    
    valid_rels = []
    orphan_errors = 0
    for _, row in df_rels.iterrows():
        source_id = row["source_id"]
        target_id = row["target_id"]
        if source_id not in valid_ids or target_id not in valid_ids:
            print(f"Orphan reference found: {source_id} -> {target_id}")
            orphan_errors += 1
        else:
            valid_rels.append(row.to_dict())
            
    df_relations = pd.DataFrame(valid_rels)
    
    # Save
    df_entities.to_csv(os.path.join(outputs_dir, "entities.csv"), index=False)
    df_relations.to_csv(os.path.join(outputs_dir, "relations.csv"), index=False)
    
    # Print reports
    print("--- Entities Summary ---")
    print(df_entities["type"].value_counts())
    
    print("\n--- Relations Summary ---")
    print(df_relations["relationship_type"].value_counts())
    
    if orphan_errors > 0:
        print(f"\n[ERROR] Found {orphan_errors} orphan references in relationships.")
        
    print("\nDone building entities and relations.")

if __name__ == "__main__":
    main()
