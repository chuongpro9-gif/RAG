import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

def run_step_3():
    print("--- BƯỚC 3: GEMINI ENTITY EXTRACTION & METADATA ENRICHMENT ---")
    base_dir = Path(__file__).parent / "ner_kb"
    in_path = base_dir / "cleaned_documents.csv"
    raw_ent_path = base_dir / "extracted_entities_raw.csv"
    enriched_meta_path = base_dir / "enriched_metadata.csv"

    load_dotenv(Path(__file__).parent / ".env")
    client = genai.Client()

    df = pd.read_csv(in_path)
    
    entities = []
    enriched_rows = []
    
    success_count = 0
    fail_count = 0
    errors = []
    
    # JSON Schema definition for Gemini
    schema = {
        "type": "OBJECT",
        "properties": {
            "co_quan": {"type": "ARRAY", "items": {"type": "STRING"}},
            "nguoi_ky": {"type": "ARRAY", "items": {"type": "STRING"}},
            "doi_tuong_ap_dung": {"type": "ARRAY", "items": {"type": "STRING"}},
            "linh_vuc": {"type": "ARRAY", "items": {"type": "STRING"}},
            "evidence_doi_tuong": {"type": "STRING", "description": "Trích dẫn 1 câu chứng minh đối tượng áp dụng"}
        }
    }
    
    prompt_template = """
    Bạn là một chuyên gia phân tích văn bản pháp luật. Hãy trích xuất các thực thể sau từ đoạn văn bản dưới đây:
    - Cơ quan ban hành (co_quan)
    - Người ký / Chức danh (nguoi_ky)
    - Đối tượng áp dụng (doi_tuong_ap_dung)
    - Lĩnh vực (linh_vuc) ví dụ: Tín dụng, Kiểm toán, Bảo hiểm, Ngân hàng, Chứng khoán...

    VĂN BẢN (5000 ký tự đầu):
    {text}
    """
    
    print(f"Bắt đầu trích xuất cho {len(df)} documents...")
    model_name = os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.5-flash-lite")
    
    for idx, row in df.iterrows():
        doc_id = row['id']
        skh = row['so_ky_hieu']
        text = str(row['content_clean'])[:5000] # Chỉ lấy 5000 ký tự đầu để tránh tốn token và vì metadata thường ở đầu
        
        prompt = prompt_template.format(text=text)
        
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0
                )
            )
            
            data = json.loads(resp.text)
            
            # Xử lý entities
            doc_entities = []
            
            for cq in data.get('co_quan', []):
                doc_entities.append({"entity": cq, "entity_type": "CoQuan", "source_doc_id": doc_id, "method": "gemini", "confidence": 0.9, "evidence": ""})
            for nk in data.get('nguoi_ky', []):
                doc_entities.append({"entity": nk, "entity_type": "NguoiKy", "source_doc_id": doc_id, "method": "gemini", "confidence": 0.9, "evidence": ""})
            for dt in data.get('doi_tuong_ap_dung', []):
                doc_entities.append({"entity": dt, "entity_type": "DoiTuongApDung", "source_doc_id": doc_id, "method": "gemini", "confidence": 0.85, "evidence": data.get('evidence_doi_tuong', '')})
            for lv in data.get('linh_vuc', []):
                doc_entities.append({"entity": lv, "entity_type": "LinhVuc", "source_doc_id": doc_id, "method": "gemini", "confidence": 0.9, "evidence": ""})
                
            entities.extend(doc_entities)
            
            # Làm giàu metadata
            enriched_row = row.copy()
            # Ưu tiên metadata gốc, chỉ bổ sung nếu trống hoặc "Chưa phân loại"
            if pd.isna(row['linh_vuc']) or row['linh_vuc'] == 'Chưa phân loại':
                if data.get('linh_vuc'):
                    enriched_row['linh_vuc'] = ", ".join(data['linh_vuc'])
            
            if pd.isna(row['thong_tin_ap_dung']) or str(row['thong_tin_ap_dung']).strip() == '':
                if data.get('doi_tuong_ap_dung'):
                    enriched_row['thong_tin_ap_dung'] = ", ".join(data['doi_tuong_ap_dung'])
                    
            enriched_rows.append(enriched_row)
            success_count += 1
            print(f"[{success_count}] Đã xử lý: {skh}")
            
        except Exception as e:
            fail_count += 1
            errors.append(f"Doc {doc_id} ({skh}): {str(e)}")
            enriched_rows.append(row) # Fallback to original row
            print(f"[ERROR] Doc {skh} thất bại.")
            
    df_entities = pd.DataFrame(entities)
    df_enriched = pd.DataFrame(enriched_rows)
    
    df_entities.to_csv(raw_ent_path, index=False, encoding='utf-8')
    df_enriched.to_csv(enriched_meta_path, index=False, encoding='utf-8')
    
    print("\n--- BÁO CÁO KẾT QUẢ ---")
    print(f"Số document thành công: {success_count}")
    print(f"Số document thất bại: {fail_count}")
    print(f"Tổng số entity thu được: {len(df_entities)}")
    if not df_entities.empty:
        print(df_entities['entity_type'].value_counts().to_string())
        
    if errors:
        print("\nDanh sách lỗi:")
        for err in errors[:5]:
            print(err)
            
    print("\n[PASS] Bước 3 hoàn thành.")

if __name__ == "__main__":
    run_step_3()
