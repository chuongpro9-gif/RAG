import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
import os
import re

def clean_html(html_text):
    if pd.isna(html_text) or not str(html_text).strip():
        return ""
    
    # Dùng BeautifulSoup để loại bỏ thẻ HTML
    soup = BeautifulSoup(str(html_text), "html.parser")
    text = soup.get_text(separator="\n")
    
    # Chuẩn hóa khoảng trắng
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'[ \t\r\f\v]+', ' ', line).strip()
        if line:
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)

def run_step_1():
    print("--- BƯỚC 1: KIỂM TRA & LÀM SẠCH DỮ LIỆU ---")
    base_dir = Path(__file__).parent / "ner_kb"
    meta_path = base_dir / "metadata.csv"
    cont_path = base_dir / "content.csv"
    out_path = base_dir / "cleaned_documents.csv"

    # 1. Đọc file
    print("1. Đọc dữ liệu...")
    df_meta = pd.read_csv(meta_path)
    df_cont = pd.read_csv(cont_path)
    
    # 2. Kiểm tra số dòng
    print(f"Số dòng metadata: {len(df_meta)}")
    print(f"Số dòng content: {len(df_cont)}")
    
    # 3. Kiểm tra duplicate id
    meta_dup = df_meta['id'].duplicated().sum()
    cont_dup = df_cont['id'].duplicated().sum()
    print(f"Số duplicate id trong metadata: {meta_dup}")
    print(f"Số duplicate id trong content: {cont_dup}")
    
    # 4. Kiểm tra ID thiếu
    meta_ids = set(df_meta['id'])
    cont_ids = set(df_cont['id'])
    missing_in_meta = cont_ids - meta_ids
    missing_in_cont = meta_ids - cont_ids
    print(f"Số id có trong content nhưng thiếu trong metadata: {len(missing_in_meta)}")
    print(f"Số id có trong metadata nhưng thiếu trong content: {len(missing_in_cont)}")
    
    # 5. Ghép dữ liệu
    print("\n2. Ghép dữ liệu...")
    df = pd.merge(df_meta, df_cont, on="id", how="inner")
    print(f"Số document sau khi ghép: {len(df)}")
    
    # 6. Thống kê missing values
    print("\n3. Thống kê missing values (NaN/Null):")
    print(df.isnull().sum().to_string())
    
    # 7. Phát hiện chuỗi rỗng / "Chưa phân loại"
    print("\n4. Phát hiện giá trị chưa chuẩn:")
    for col in df.columns:
        if df[col].dtype == object:
            empty_count = (df[col].str.strip() == '').sum()
            unclassified = (df[col] == 'Chưa phân loại').sum()
            if empty_count > 0 or unclassified > 0:
                print(f" - Cột '{col}': {empty_count} rỗng, {unclassified} 'Chưa phân loại'")
                
    # 8 & 9. Làm sạch content_html
    print("\n5. Làm sạch HTML...")
    df['content_clean'] = df['content_html'].apply(clean_html)
    
    # Kiểm tra thử 2 mẫu
    print("\n--- MẪU 1 ---")
    print("HTML (đầu):", repr(df['content_html'].iloc[0][:100]))
    print("CLEAN (đầu):", repr(df['content_clean'].iloc[0][:100]))
    
    print("\n--- MẪU 2 ---")
    print("HTML (đầu):", repr(df['content_html'].iloc[1][:100]))
    print("CLEAN (đầu):", repr(df['content_clean'].iloc[1][:100]))
    
    # 10. Lưu file
    print(f"\n6. Lưu file: {out_path.name}")
    df.to_csv(out_path, index=False, encoding='utf-8')
    print("[PASS] Bước 1 hoàn thành.")

if __name__ == "__main__":
    run_step_1()
