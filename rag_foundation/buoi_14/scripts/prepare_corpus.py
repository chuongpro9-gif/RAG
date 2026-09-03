import os
import sys
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    kb_dir = os.path.join(base_dir, "..", "kb+hops")
    out_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    
    print("--- Đọc dữ liệu thô ---")
    df_meta = pd.read_csv(os.path.join(kb_dir, "metadata.csv"))
    df_content = pd.read_csv(os.path.join(kb_dir, "content.csv"))
    
    print(f"Metadata: {len(df_meta)} dòng")
    print(f"Content: {len(df_content)} dòng")
    
    # Merge content with metadata
    # content.csv usually has document_id or similar, metadata.csv has id
    if "id" in df_content.columns and "id" in df_meta.columns:
        df_merged = df_content.merge(df_meta, on="id", how="left")
    else:
        print("Không tìm thấy cột để map, giữ nguyên content")
        df_merged = df_content.copy()
        
    out_path = os.path.join(out_dir, "chunks_normalized.csv")
    df_merged.to_csv(out_path, index=False)
    print(f"Đã lưu {len(df_merged)} chunks đã chuẩn hóa vào {out_path}")

if __name__ == "__main__":
    main()
