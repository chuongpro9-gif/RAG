import os
import sys
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def inspect_file(filepath):
    print(f"--- Inspecting: {filepath} ---")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}\n")
        return None
    df = pd.read_csv(filepath)
    print(f"Row count: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Null values:\n{df.isnull().sum()}")
    print(f"Duplicates: {df.duplicated().sum()}\n")
    return df

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    files = [
        "risk_profiles_seed.csv",
        "controls_seed.csv",
        "risk_events_seed.csv",
        "relationships_seed.csv"
    ]
    dfs = {}
    for f in files:
        dfs[f] = inspect_file(os.path.join(data_dir, f))
        
    print("--- Relationships check ---")
    df_rel = dfs["relationships_seed.csv"]
    if df_rel is not None:
        print(f"Relationship types: {df_rel['relationship_type'].unique()}")
        
    print("\n--- Missing references check ---")
    # Check if all source_id and target_id exist in nodes
    if all(dfs.values()):
        node_ids = set()
        for k in ["risk_profiles_seed.csv", "controls_seed.csv", "risk_events_seed.csv"]:
            node_ids.update(dfs[k]['id'].tolist())
            
        rel_sources = set(dfs["relationships_seed.csv"]['source_id'].tolist())
        rel_targets = set(dfs["relationships_seed.csv"]['target_id'].tolist())
        
        missing_sources = rel_sources - node_ids
        missing_targets = rel_targets - node_ids
        print(f"Missing source_ids in nodes: {missing_sources}")
        print(f"Missing target_ids in nodes: {missing_targets}")
        
if __name__ == '__main__':
    main()
