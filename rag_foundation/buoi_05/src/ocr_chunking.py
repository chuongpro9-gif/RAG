import os
import sys
import json
import asyncio
import unicodedata
import fitz  # PyMuPDF
from dotenv import load_dotenv
import re

# Fix unicode error on windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

def normalize_text(text):
    """Chuẩn hóa văn bản sang Unicode NFC"""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)

def extract_text_pymupdf(pdf_path):
    """Thử lấy text bằng PyMuPDF. Trả về text và boolean cho biết có lỗi hay không."""
    print(f"[PyMuPDF] Bắt đầu đọc file {pdf_path}")
    doc = fitz.open(pdf_path)
    full_text = ""
    has_error = False
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        # Kiểm tra xem trang có bị rỗng hoặc lỗi font không (ví dụ: nhiều ký tự lạ)
        if not text.strip():
            print(f"[CẢNH BÁO] Trang {page_num + 1} trống hoặc không đọc được text. Đánh dấu có lỗi.")
            has_error = True
            break
            
        # Kiểm tra ký tự lạ đơn giản (nhiều ký tự unicode dị thường, hoặc mật độ quá lớn)
        # Trong thực tế có thể dùng heuristic tốt hơn. Ở đây mô phỏng việc kiểm tra
        if len(re.findall(r'[^\w\s\.\,\:\;\"\(\)\-\/\%\!\?\đ\Đ]', text)) > len(text) * 0.2:
            print(f"[CẢNH BÁO] Trang {page_num + 1} có vẻ bị lỗi font/encoding. Đánh dấu có lỗi.")
            has_error = True
            break
            
        full_text += text + "\n"
        
    doc.close()
    return normalize_text(full_text), has_error

async def extract_text_llamaparse(pdf_path):
    """Sử dụng LlamaParse để OCR"""
    if not API_KEY or API_KEY == "KEY CỦA BẠN" or API_KEY == "":
        print("[LỖI] Chưa cấu hình LLAMA_CLOUD_API_KEY. Không thể chạy Llama Parse.")
        return ""
        
    print(f"[LlamaParse] Đang gửi file {pdf_path} lên Llama Cloud để OCR...")
    try:
        from llama_parse import LlamaParse
        parser = LlamaParse(api_key=API_KEY, result_type="markdown")
        
        # Chạy đồng bộ trong hàm async để tránh lỗi cho nhanh (ở đây là demo)
        parsed_doc = parser.load_data(pdf_path)
        text = "\n".join([doc.text for doc in parsed_doc])
        print("[LlamaParse] Đã parse bằng thư viện llama-parse!")
        return normalize_text(text)
    except Exception as e:
        print(f"[LlamaParse] Lỗi trong quá trình OCR: {e}")
        return ""

def chunk_fixed_size(text, chunk_size=500, overlap=50, source_name="Luat TCTD 2024.pdf"):
    """Chiến lược Fixed-size chunking"""
    chunks = []
    # Tokenizer đơn giản bằng split ký tự cho ví dụ (thực tế nên dùng tiktoken)
    words = text.split()
    
    start = 0
    chunk_id = 0
    while start < len(words):
        end = start + chunk_size
        chunk_text = " ".join(words[start:end])
        
        chunks.append({
            "chunk_id": f"fixed_{chunk_id}",
            "strategy": "fixed-size",
            "source": source_name,
            "text": chunk_text,
            "metadata": {
                "word_count": len(chunk_text.split())
            }
        })
        start += (chunk_size - overlap)
        chunk_id += 1
        
    return chunks

def chunk_semantic(text, source_name="Luat TCTD 2024.pdf"):
    """Chiến lược Semantic chunking (cắt theo đoạn văn)"""
    chunks = []
    # Cắt theo 2 dòng trắng trở lên (nghĩa là ngắt đoạn)
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunk_id = 0
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
            
        chunks.append({
            "chunk_id": f"semantic_{chunk_id}",
            "strategy": "semantic",
            "source": source_name,
            "text": para,
            "metadata": {
                "paragraph_index": i
            }
        })
        chunk_id += 1
        
    return chunks

def chunk_hierarchical(text, source_name="Luat TCTD 2024.pdf"):
    """Chiến lược Hierarchical chunking (Dành cho Luật: Chương -> Điều -> Khoản)"""
    chunks = []
    
    # Tìm tất cả các Điều.
    # Trong luật thường có chữ "Điều XX. Tên điều"
    dieu_pattern = re.compile(r'(Điều\s+\d+[\.\:]?\s+.*?)(?=(?:Điều\s+\d+[\.\:]?\s+)|$)', re.IGNORECASE | re.DOTALL)
    
    # Do regex trên text thô có thể không hoàn hảo, đây là mô phỏng
    matches = dieu_pattern.findall(text)
    
    if not matches:
        print("[CẢNH BÁO] Hierarchical: Không tìm thấy từ khóa 'Điều' trong văn bản để chia chunk. Sẽ dùng fallback cắt đoạn.")
        return chunk_semantic(text, source_name)
        
    chunk_id = 0
    for match in matches:
        match_text = match.strip()
        # Trích xuất số điều
        dieu_name = "Điều ?"
        title_match = re.search(r'Điều\s+\d+', match_text, re.IGNORECASE)
        if title_match:
            dieu_name = title_match.group(0)
            
        chunks.append({
            "chunk_id": f"hierarchical_{chunk_id}",
            "strategy": "hierarchical",
            "source": source_name,
            "text": match_text,
            "metadata": {
                "legal_unit": dieu_name
            }
        })
        chunk_id += 1
        
    return chunks

async def process_pdf(pdf_path, output_dir):
    source_name = os.path.basename(pdf_path)
    
    # 1. Đọc text
    text, has_error = extract_text_pymupdf(pdf_path)
    
    # 2. Xử lý lỗi (nếu có thì dùng OCR)
    if has_error or not text.strip():
        print("[INFO] Bắt đầu gọi LlamaParse để xử lý lỗi text/scan...")
        text = await extract_text_llamaparse(pdf_path)
        
    if not text.strip():
        print(f"[LỖI] Không thể trích xuất văn bản từ {source_name}. Hãy kiểm tra file hoặc API Key.")
        return
        
    # Lưu text raw
    raw_path = os.path.join(output_dir, "raw_text.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[OK] Đã lưu raw text vào {raw_path}")
        
    # 3. Tiến hành chunking
    print("[INFO] Tiến hành Fixed-size chunking...")
    fixed_chunks = chunk_fixed_size(text, source_name=source_name)
    
    print("[INFO] Tiến hành Semantic chunking...")
    semantic_chunks = chunk_semantic(text, source_name=source_name)
    
    print("[INFO] Tiến hành Hierarchical chunking...")
    hierarchical_chunks = chunk_hierarchical(text, source_name=source_name)
    
    # 4. Lưu kết quả ra file JSON
    def save_json(data, filename):
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    save_json(fixed_chunks, "chunks_fixed.json")
    save_json(semantic_chunks, "chunks_semantic.json")
    save_json(hierarchical_chunks, "chunks_hierarchical.json")
    
    print(f"[OK] Đã hoàn tất và lưu các chunk vào {output_dir}")
    print(f"       - Fixed-size: {len(fixed_chunks)} chunks")
    print(f"       - Semantic: {len(semantic_chunks)} chunks")
    print(f"       - Hierarchical: {len(hierarchical_chunks)} chunks")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "datademo", "Luat TCTD 2024.pdf")
    output_dir = os.path.join(base_dir, "output")
    
    if not os.path.exists(pdf_path):
        print(f"[LỖI] Không tìm thấy file {pdf_path}")
    else:
        asyncio.run(process_pdf(pdf_path, output_dir))
