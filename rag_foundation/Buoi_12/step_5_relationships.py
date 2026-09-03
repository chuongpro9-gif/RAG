import pandas as pd
from pathlib import Path

def run_step_5():
    print("--- BƯỚC 5: RELATIONSHIP EXTRACTION ---")
    base_dir = Path(__file__).parent / "ner_kb"
    cands_path = base_dir / "relation_candidates.csv"
    ents_path = base_dir / "entities.csv"
    out_path = base_dir / "relationships_raw.csv"

    relationships = []

    # 1. Document -> Document (Từ candidates)
    if cands_path.exists():
        df_cands = pd.read_csv(cands_path)
        for _, row in df_cands.iterrows():
            trigger = str(row['trigger']).lower()
            source = row['source_so_ky_hieu']
            target = row['target_so_ky_hieu']
            evidence = row['evidence']
            
            rel_type = "THAM_CHIEU"
            if "sửa đổi" in trigger or "bổ sung" in trigger:
                rel_type = "SUA_DOI_BO_SUNG"
            elif "thay thế" in trigger or "bãi bỏ" in trigger:
                rel_type = "THAY_THE_BOI"
                # QUAN TRỌNG: Chiều của THAY_THE_BOI là từ Văn bản cũ -> Văn bản mới
                # Nếu source nói "thay thế target", tức là target (cũ) bị thay thế bởi source (mới)
                # Vậy chiều đúng là: target -[:THAY_THE_BOI]-> source
                source, target = target, source
            
            relationships.append({
                "source": source,
                "target": target,
                "relationship_type": rel_type,
                "method": "rule_based",
                "confidence": 0.9,
                "evidence": evidence
            })
            
    # 2. Document -> Entity (Từ entities)
    if ents_path.exists():
        df_ents = pd.read_csv(ents_path)
        # Vì entities.csv không có source_so_ky_hieu mà chỉ có source_doc_id (id văn bản),
        # ta cần map id -> so_ky_hieu từ enriched_metadata.csv
        meta_path = base_dir / "enriched_metadata.csv"
        df_meta = pd.read_csv(meta_path)
        id_to_skh = {str(k): v for k, v in zip(df_meta['id'], df_meta['so_ky_hieu'])}
        
        for _, row in df_ents.iterrows():
            doc_id = str(row['source_doc_id'])
            # Bỏ qua nếu không có doc_id hợp lệ
            if pd.isna(row['source_doc_id']) or doc_id not in id_to_skh:
                continue
                
            source_skh = id_to_skh[doc_id]
            ent_type = row['entity_type']
            target = row['canonical_name']
            method = row['method']
            evidence = row.get('evidence', '')
            
            rel_type = None
            if ent_type == "CoQuan": rel_type = "BAN_HANH_BOI"
            elif ent_type == "NguoiKy": rel_type = "KY_BOI"
            elif ent_type == "DoiTuongApDung": rel_type = "AP_DUNG_CHO"
            elif ent_type == "LinhVuc": rel_type = "THUOC_LINH_VUC"
            
            if rel_type:
                relationships.append({
                    "source": source_skh,
                    "target": target,
                    "relationship_type": rel_type,
                    "method": method,
                    "confidence": row.get('confidence', 0.8),
                    "evidence": evidence
                })

    df_rels = pd.DataFrame(relationships)
    
    # Loại duplicate
    if not df_rels.empty:
        df_rels = df_rels.drop_duplicates(subset=['source', 'target', 'relationship_type'])
        
    print(f"Tổng số quan hệ đã trích xuất: {len(df_rels)}")
    if not df_rels.empty:
        print("\nThống kê theo relationship type:")
        print(df_rels['relationship_type'].value_counts().to_string())
        
        print("\n10 Quan hệ mẫu:")
        print(df_rels[['source', 'relationship_type', 'target']].head(10).to_string())

    df_rels.to_csv(out_path, index=False, encoding='utf-8')
    print("\n[PASS] Bước 5 hoàn thành.")

if __name__ == "__main__":
    run_step_5()
