import pandas as pd
from pathlib import Path

def run_step_6():
    print("--- BƯỚC 6: VALIDATE RELATIONSHIPS ---")
    base_dir = Path(__file__).parent / "ner_kb"
    rels_raw_path = base_dir / "relationships_raw.csv"
    docs_path = base_dir / "cleaned_documents.csv"
    ents_path = base_dir / "entities.csv"
    
    out_rels_path = base_dir / "relationships.csv"
    out_report_path = base_dir / "validation_report.csv"

    if not rels_raw_path.exists():
        print(f"File {rels_raw_path} không tồn tại!")
        return

    df_rels_raw = pd.read_csv(rels_raw_path)
    df_docs = pd.read_csv(docs_path)
    df_ents = pd.read_csv(ents_path)
    
    valid_docs = set(df_docs['so_ky_hieu'])
    valid_ents = set(df_ents['canonical_name'])
    
    valid_rel_types = {
        "THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI",
        "BAN_HANH_BOI", "KY_BOI", "AP_DUNG_CHO", "THUOC_LINH_VUC"
    }
    
    valid_relationships = []
    failed_relationships = []
    
    for idx, row in df_rels_raw.iterrows():
        source = row.get('source')
        target = row.get('target')
        rel_type = row.get('relationship_type')
        evidence = str(row.get('evidence', ''))
        
        fail_reasons = []
        
        # 1. Missing fields
        if pd.isna(source) or pd.isna(target) or pd.isna(rel_type):
            fail_reasons.append("Missing source/target/rel_type")
            
        # 2. Check relationship type
        if rel_type not in valid_rel_types:
            fail_reasons.append(f"Invalid relationship_type: {rel_type}")
            
        # 3. Check source (phải là Document)
        if source not in valid_docs:
            fail_reasons.append(f"Source Document không tồn tại: {source}")
            
        # 4. Check target
        if rel_type in ["THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI"]:
            if target not in valid_docs:
                fail_reasons.append(f"Target Document không tồn tại trong corpus: {target}")
            if source == target:
                fail_reasons.append("Self-loop vô nghĩa")
                
            # Document relations must have evidence if they come from text
            if not evidence.strip():
                fail_reasons.append("Missing evidence cho Document relation")
        else:
            if target not in valid_ents:
                fail_reasons.append(f"Target Entity không tồn tại: {target}")
                
        if fail_reasons:
            failed_row = row.copy()
            failed_row['fail_reason'] = " | ".join(fail_reasons)
            failed_relationships.append(failed_row)
        else:
            valid_relationships.append(row)
            
    df_valid = pd.DataFrame(valid_relationships)
    df_failed = pd.DataFrame(failed_relationships)
    
    # Loại bỏ duplicate lần cuối
    if not df_valid.empty:
        df_valid = df_valid.drop_duplicates(subset=['source', 'target', 'relationship_type'])
        
    print(f"Tổng relation raw: {len(df_rels_raw)}")
    print(f"Số PASS: {len(df_valid)}")
    print(f"Số FAIL: {len(df_failed)}")
    
    if not df_valid.empty:
        print("\nThống kê theo relationship_type (PASS):")
        print(df_valid['relationship_type'].value_counts().to_string())
        
        print("\n10 Quan hệ PASS mẫu:")
        print(df_valid[['source', 'relationship_type', 'target']].head(10).to_string())
        
    if not df_failed.empty:
        print("\nNguyên nhân fail phổ biến:")
        print(df_failed['fail_reason'].value_counts().to_string())
        
    df_valid.to_csv(out_rels_path, index=False, encoding='utf-8')
    df_failed.to_csv(out_report_path, index=False, encoding='utf-8')
    print("\n[PASS] Bước 6 hoàn thành.")

if __name__ == "__main__":
    run_step_6()
