import re
from bs4 import BeautifulSoup
import hashlib

def clean_html_text(text):
    """Làm sạch các khoảng trắng và ký tự thừa trong văn bản."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_html_to_chunks(html_content, document_name):
    """
    Phân tích file HTML, bóc tách cấu trúc phân cấp:
    - h1 (Chương)
    - h2 (Mục)
    - h3 (Điều)
    - p, table (Nội dung)
    Trả về danh sách các chunk có thông tin cha-con.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    chunks = []
    
    # State tracking cho phân cấp
    current_h1 = None
    current_h2 = None
    current_h3 = None
    
    seq_id = 0
    
    for element in soup.body.descendants if soup.body else soup.descendants:
        if element.name in ['h1', 'h2', 'h3', 'p', 'table']:
            text = clean_html_text(element.get_text(separator=' '))
            if not text:
                continue
                
            chunk_type = element.name
            parent_chunk = None
            
            if chunk_type == 'h1':
                current_h1 = text
                current_h2 = None
                current_h3 = None
                parent_chunk = "DOCUMENT_ROOT"
            elif chunk_type == 'h2':
                current_h2 = text
                current_h3 = None
                parent_chunk = current_h1 if current_h1 else "DOCUMENT_ROOT"
            elif chunk_type == 'h3':
                current_h3 = text
                parent_chunk = current_h2 if current_h2 else (current_h1 if current_h1 else "DOCUMENT_ROOT")
            else:
                # p or table
                parent_chunk = current_h3 if current_h3 else (current_h2 if current_h2 else (current_h1 if current_h1 else "DOCUMENT_ROOT"))
            
            # Tạo unique ID cho chunk
            raw_id = f"{document_name}_{seq_id}_{text[:20]}"
            chunk_id = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
            
            chunk = {
                "chunk_id": chunk_id,
                "document_name": document_name,
                "text": text,
                "type": chunk_type,
                "parent": parent_chunk,
                "seq_id": seq_id
            }
            chunks.append(chunk)
            seq_id += 1
            
    return chunks

def extract_document_relations(chunks):
    """
    Trích xuất quan hệ giữa các tài liệu dựa vào mẫu câu (Căn cứ, Thay thế, Hợp nhất).
    Giả lập một logic đơn giản để tìm tên các luật được nhắc đến.
    """
    relations = []
    # Regex tìm các cụm từ chỉ thị quan hệ
    patterns = {
        "CAN_CU": r"Căn cứ\s+([A-Z][a-z0-9\s]+(?:Luật|Nghị định|Thông tư)[^,.;\n]+)",
        "THAY_THE": r"Thay thế\s+([A-Z][a-z0-9\s]+(?:Luật|Nghị định|Thông tư)[^,.;\n]+)",
        "HOP_NHAT": r"Hợp nhất\s+([A-Z][a-z0-9\s]+(?:Luật|Nghị định|Thông tư)[^,.;\n]+)"
    }
    
    for chunk in chunks:
        for rel_type, pattern in patterns.items():
            matches = re.finditer(pattern, chunk['text'], re.IGNORECASE)
            for match in matches:
                target_doc = clean_html_text(match.group(1))
                if target_doc:
                    relations.append({
                        "source": chunk['document_name'],
                        "target": target_doc,
                        "type": rel_type
                    })
    
    return relations
