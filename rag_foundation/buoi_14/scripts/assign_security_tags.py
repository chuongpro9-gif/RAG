import os
import sys
import pandas as pd
import json

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_allowed_roles(text):
    text = str(text).lower()
    # Rules
    if any(kw in text for kw in ["nhân sự", "lương thưởng", "tuyển dụng", "bổ nhiệm"]):
        return ["Admin", "HR"]
    elif any(kw in text for kw in ["tín dụng", "rủi ro", "hạn mức", "vay"]):
        return ["Admin", "Risk_Manager", "Staff"]
    else:
        return ["Admin", "HR", "Risk_Manager", "Staff", "Guest"]

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    in_path = os.path.join(base_dir, "data", "processed", "chunks_normalized.csv")
    out_path = os.path.join(base_dir, "data", "processed", "chunks_secure.csv")
    
    print("--- Đọc dữ liệu normalized ---")
    df = pd.read_csv(in_path)
    
    print("--- Gán nhãn bảo mật (RBAC) ---")
    df["allowed_roles"] = df["content_html"].apply(lambda x: json.dumps(get_allowed_roles(x)))
    
    df.to_csv(out_path, index=False)
    print(f"Đã lưu {len(df)} chunks kèm allowed_roles vào {out_path}")
    
    # Kiểm tra
    print("\n--- Phân phối Roles ---")
    print(df["allowed_roles"].value_counts())

if __name__ == "__main__":
    main()
