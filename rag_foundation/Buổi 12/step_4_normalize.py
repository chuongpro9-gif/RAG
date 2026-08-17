import pandas as pd
from pathlib import Path
import re
import unicodedata

def normalize_text(text):
    if pd.isna(text):
        return ""
    # Chuẩn hóa Unicode (dựng sẵn)
    text = unicodedata.normalize('NFC', str(text))
    # Bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def apply_alias(text):
    text_lower = text.lower()
    if text_lower in ["nhnn", "nhnnvn", "ngân hàng nhà nước", "ngân hàng nn", "ngân hàng nhà nước vn"]:
        return "Ngân hàng Nhà nước Việt Nam"
    if text_lower in ["bộ tc", "btc"]:
        return "Bộ Tài chính"
    if text_lower in ["cp", "chính phủ vn", "chính phủ nước chxhcnvn"]:
        return "Chính phủ"
    if text_lower in ["qh", "quốc hội nước chxhcnvn"]:
        return "Quốc hội"
    if "quỹ tín dụng nhân dân" in text_lower:
        return "Quỹ tín dụng nhân dân"
    if "ngân hàng thương mại" in text_lower:
        return "Ngân hàng thương mại"
    if "tổ chức tín dụng" in text_lower:
        return "Tổ chức tín dụng"
    if "chi nhánh ngân hàng nước ngoài" in text_lower:
        return "Chi nhánh ngân hàng nước ngoài"
    
    # Capitalize chữ cái đầu tiên cho chuẩn
    if len(text) > 0:
        return text[0].upper() + text[1:]
    return text

def run_step_4():
    print("--- BƯỚC 4: ENTITY NORMALIZATION ---")
    base_dir = Path(__file__).parent / "ner_kb"
    raw_ent_path = base_dir / "extracted_entities_raw.csv"
    out_path = base_dir / "entities.csv"

    if not raw_ent_path.exists():
        print(f"File {raw_ent_path} không tồn tại!")
        return

    df_raw = pd.read_csv(raw_ent_path)
    print(f"Số entity trước normalize: {len(df_raw)}")
    
    entities = []
    seen = set()
    
    for idx, row in df_raw.iterrows():
        orig_name = str(row['entity'])
        norm_name = normalize_text(orig_name)
        canon_name = apply_alias(norm_name)
        
        # Bỏ qua nếu rỗng
        if not canon_name:
            continue
            
        entity_type = row['entity_type']
        
        # Deduplication key
        dedup_key = f"{entity_type}_{canon_name.lower()}"
        
        if dedup_key not in seen:
            seen.add(dedup_key)
            entities.append({
                "entity_id": f"ent_{len(entities) + 1}",
                "entity_type": entity_type,
                "canonical_name": canon_name,
                "original_name": orig_name,
                "source_doc_id": row.get('source_doc_id', ''),
                "method": row.get('method', ''),
                "confidence": row.get('confidence', 0),
                "evidence": row.get('evidence', '')
            })
            
    df_entities = pd.DataFrame(entities)
    print(f"Số entity sau normalize (loại bỏ trùng): {len(df_entities)}")
    
    # In một số alias đã merge (original khác canonical)
    alias_merged = df_raw[df_raw['entity'].apply(lambda x: normalize_text(str(x)) != apply_alias(normalize_text(str(x))))]
    if not alias_merged.empty:
        print("\nMột số trường hợp Alias đã gộp:")
        for _, r in alias_merged.head(5).iterrows():
            orig = r['entity']
            canon = apply_alias(normalize_text(orig))
            print(f" - {orig} -> {canon}")
            
    print("\n10 Entity mẫu:")
    print(df_entities[['entity_type', 'canonical_name']].head(10).to_string())

    df_entities.to_csv(out_path, index=False, encoding='utf-8')
    print("[PASS] Bước 4 hoàn thành.")

if __name__ == "__main__":
    run_step_4()
