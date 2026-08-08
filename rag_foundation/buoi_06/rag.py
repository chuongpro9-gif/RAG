import os
import json
import sqlite3
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình ChromaDB (Embedded)
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "storage", "chroma")
os.makedirs(CHROMA_PATH, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection_name = "rag_buoi_06"
collection = chroma_client.get_or_create_collection(name=collection_name)

# Khởi tạo Gemini Client (nếu có key)
genai_client = None
if GEMINI_API_KEY:
    genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Thiết lập PostgreSQL / Fallback SQLite
def get_db_connection():
    # Thử kết nối PostgreSQL
    try:
        import psycopg
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "rag_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            connect_timeout=2
        )
        return conn, "postgres"
    except Exception:
        # Fallback sang SQLite local db
        db_path = os.path.join(os.path.dirname(__file__), "rag_db.sqlite")
        conn = sqlite3.connect(db_path)
        return conn, "sqlite"

def init_db():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                chunk_id TEXT PRIMARY KEY,
                text TEXT,
                metadata JSONB
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                chunk_id TEXT PRIMARY KEY,
                text TEXT,
                metadata TEXT
            )
        """)
    conn.commit()
    conn.close()

def _get_embedding(text):
    if not genai_client:
        return [0.0] * 384 # Fallback vector giả nếu không có API key để demo UI
    response = genai_client.models.embed_content(
        model='gemini-embedding-2',
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=384)
    )
    return response.embeddings[0].values

def index():
    """Hàm Index: Đọc JSON từ Buổi 5, tạo embedding và lưu vào DB."""
    init_db()
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # Đọc file chunks
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "buoi_05", "output")
    target_file = os.path.join(input_dir, "chunks_hierarchical.json")
    
    if not os.path.exists(target_file):
         # Thử tìm file JSON nào đó
         files = [f for f in os.listdir(input_dir) if f.endswith(".json")] if os.path.exists(input_dir) else []
         if not files:
             return {"status": "error", "message": f"Không tìm thấy dữ liệu chunk tại {input_dir}"}
         target_file = os.path.join(input_dir, files[0])
         
    with open(target_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    count = 0
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        text = chunk["text"]
        meta = chunk.get("metadata", {})
        
        # 1. Lưu text vào SQL
        try:
            if db_type == "postgres":
                cursor.execute(
                    "INSERT INTO documents (chunk_id, text, metadata) VALUES (%s, %s, %s) ON CONFLICT (chunk_id) DO NOTHING",
                    (chunk_id, text, json.dumps(meta))
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO documents (chunk_id, text, metadata) VALUES (?, ?, ?)",
                    (chunk_id, text, json.dumps(meta))
                )
            conn.commit()
            
            # 2. Lưu vector vào ChromaDB
            emb = _get_embedding(text)
            collection.add(
                ids=[chunk_id],
                embeddings=[emb],
                metadatas=[{"source": chunk.get("source", "unknown")}]
            )
            count += 1
        except Exception as e:
            # Skip if already exists or error
            pass
            
    conn.close()
    return {"status": "success", "indexed": count}

def ask(question, top_k=3):
    """Hàm Ask: Tìm top-k context và sinh câu trả lời"""
    if not genai_client:
        return {"answer": "LỖI: Chưa có GEMINI_API_KEY. Vui lòng cấu hình trong .env", "sources": []}
        
    # 1. Retrieve
    q_emb = _get_embedding(question)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k
    )
    
    if not results["ids"] or not results["ids"][0]:
        return {"answer": "Không tìm thấy thông tin liên quan.", "sources": []}
        
    chunk_ids = results["ids"][0]
    
    # 2. Fetch Text từ DB
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    contexts = []
    
    for cid in chunk_ids:
        if db_type == "postgres":
            cursor.execute("SELECT text FROM documents WHERE chunk_id = %s", (cid,))
        else:
            cursor.execute("SELECT text FROM documents WHERE chunk_id = ?", (cid,))
        row = cursor.fetchone()
        if row:
            contexts.append(row[0])
            
    conn.close()
    
    context_str = "\n\n---\n\n".join(contexts)
    
    # 3. Generate Answer
    prompt = f"Bạn là trợ lý RAG. Dựa vào thông tin sau:\n\n{context_str}\n\nHãy trả lời câu hỏi: {question}"
    
    try:
        response = genai_client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
        answer = response.text
    except Exception as e:
        answer = f"Lỗi gọi LLM: {str(e)}"
        
    return {"answer": answer, "sources": contexts}

def status():
    """Hàm Status: Lấy số lượng chunks"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if db_type == "postgres":
            cursor.execute("SELECT COUNT(*) FROM documents")
        else:
             cursor.execute("SELECT COUNT(*) FROM documents")
        text_count = cursor.fetchone()[0]
        conn.close()
    except:
        text_count = 0
        db_type = "Not Connected"
        
    try:
        vec_count = collection.count()
    except:
        vec_count = 0
        
    return {
        "text_db_type": db_type,
        "text_chunks": text_count,
        "vector_chunks": vec_count
    }
