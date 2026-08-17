import pandas as pd
import re
from pathlib import Path

def run_step_2():
    print("--- BƯỚC 2: RULE-BASED CANDIDATE EXTRACTION ---")
    base_dir = Path(__file__).parent / "ner_kb"
    in_path = base_dir / "cleaned_documents.csv"
    out_path = base_dir / "relation_candidates.csv"

    df = pd.read_csv(in_path)
    
    # Lấy danh sách tất cả các số hiệu trong tập corpus (dùng làm target hợp lệ)
    valid_targets = df[['id', 'so_ky_hieu']].dropna().to_dict('records')
    
    # Các trigger quan trọng
    triggers = ["căn cứ", "sửa đổi, bổ sung", "bãi bỏ", "thay thế"]
    
    candidates = []
    
    for idx, row in df.iterrows():
        source_id = row['id']
        source_skh = row['so_ky_hieu']
        text = str(row['content_clean'])
        
        # Tìm các văn bản khác được nhắc đến
        for target in valid_targets:
            target_skh = target['so_ky_hieu']
            
            # Bỏ qua tự tham chiếu
            if source_skh == target_skh:
                continue
                
            # Tìm vị trí xuất hiện của target_skh trong text
            # Escaping target_skh vì nó có thể chứa ký hiệu đặc biệt
            escaped_target = re.escape(target_skh)
            
            # Tìm tất cả match
            matches = list(re.finditer(escaped_target, text, re.IGNORECASE))
            
            for m in matches:
                start_idx = m.start()
                end_idx = m.end()
                
                # Lấy evidence window (khoảng 100 ký tự trước và 100 ký tự sau)
                window_start = max(0, start_idx - 150)
                window_end = min(len(text), end_idx + 150)
                evidence = text[window_start:window_end].replace('\n', ' ')
                
                # Xác định trigger
                found_trigger = "nhắc đến"
                evidence_lower = evidence.lower()
                for t in triggers:
                    if t in evidence_lower:
                        found_trigger = t
                        break # Ưu tiên trigger đầu tiên tìm thấy
                        
                candidates.append({
                    "source_id": source_id,
                    "source_so_ky_hieu": source_skh,
                    "target_so_ky_hieu": target_skh,
                    "trigger": found_trigger,
                    "evidence": evidence
                })

    df_cand = pd.DataFrame(candidates)
    
    # Loại bỏ duplicate candidate (giữ lại 1 evidence cho mỗi cặp source-target-trigger)
    if not df_cand.empty:
        df_cand = df_cand.drop_duplicates(subset=['source_so_ky_hieu', 'target_so_ky_hieu', 'trigger'])
    
    print(f"Tổng số candidate tìm thấy: {len(df_cand)}")
    if not df_cand.empty:
        print("Số candidate theo trigger:")
        print(df_cand['trigger'].value_counts().to_string())
        
        print("\n10 Candidate mẫu:")
        print(df_cand[['source_so_ky_hieu', 'trigger', 'target_so_ky_hieu']].head(10).to_string())
        
    df_cand.to_csv(out_path, index=False, encoding='utf-8')
    print("[PASS] Bước 2 hoàn thành.")

if __name__ == "__main__":
    run_step_2()
