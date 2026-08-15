import os
import json
import time
import hashlib
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load configs from .env
load_dotenv(Path(__file__).parent / ".env")

MULTI_QUERY_COUNT = int(os.getenv("MULTI_QUERY_COUNT", 3))
MULTI_QUERY_MAX_CHARS = int(os.getenv("MULTI_QUERY_MAX_CHARS", 300))
MULTI_QUERY_TEMPERATURE = float(os.getenv("MULTI_QUERY_TEMPERATURE", 0.2))
MULTI_QUERY_ORIGINAL_WEIGHT = float(os.getenv("MULTI_QUERY_ORIGINAL_WEIGHT", 1.5))
MULTI_QUERY_VARIANT_WEIGHT = float(os.getenv("MULTI_QUERY_VARIANT_WEIGHT", 1.0))
MULTI_QUERY_RRF_K = int(os.getenv("MULTI_QUERY_RRF_K", 60))
PER_QUERY_CANDIDATES = int(os.getenv("PER_QUERY_CANDIDATES", 12))
PARENT_MAX_CHARS = int(os.getenv("PARENT_MAX_CHARS", 6000))
PARENT_SCORE_CHILD_LIMIT = int(os.getenv("PARENT_SCORE_CHILD_LIMIT", 3))
PARENT_RRF_K = int(os.getenv("PARENT_RRF_K", 60))
PARENT_CANDIDATES = int(os.getenv("PARENT_CANDIDATES", 10))
FINAL_PARENT_TOP_K = int(os.getenv("FINAL_PARENT_TOP_K", 3))
TOTAL_CONTEXT_MAX_CHARS = int(os.getenv("TOTAL_CONTEXT_MAX_CHARS", 16000))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.5-flash-lite")

from rag import load_chunks
from advanced_rag import hybrid_search, rerank_candidates

STORAGE_DIR = Path(__file__).parent / "storage" / "hierarchy"

def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# ==========================================
# STEP 3: HIERARCHY REGISTRY
# ==========================================
def parse_chunk_id(chunk_id: str) -> int:
    try:
        parts = chunk_id.split('_')
        return int(parts[-1])
    except:
        return 0

def infer_heading(text: str) -> dict:
    res = {}
    lines = text.strip().split('\n')
    if not lines:
        return res
    first_line = lines[0].strip()
    match_article = re.match(r'^(Điều\s+\d+)', first_line, re.IGNORECASE)
    if match_article:
        res['article'] = match_article.group(1)
    match_chapter = re.match(r'^(Chương\s+[IVXLCDM\d]+)', first_line, re.IGNORECASE)
    if match_chapter:
        res['chapter'] = match_chapter.group(1)
    return res

def build_hierarchy():
    all_chunks, _ = load_chunks()
    chunks = [c for c in all_chunks if c.get("strategy") == "hierarchical"]
    
    # Group by source
    by_source = {}
    for c in chunks:
        by_source.setdefault(c["source"], []).append(c)
        
    children = {}
    parents = {}
    
    for src, src_chunks in by_source.items():
        src_chunks.sort(key=lambda x: parse_chunk_id(x["chunk_id"]))
        carried_article = None
        
        for c in src_chunks:
            chunk_id = c["chunk_id"]
            text = c["text"]
            
            # Resolve structural path
            meta_struct = c.get("structure", {})
            inferred = infer_heading(text)
            
            resolution = "document_fallback"
            ambiguous = False
            warnings = []
            
            article = None
            if meta_struct.get("article"):
                article = meta_struct["article"]
                resolution = "metadata"
            elif inferred.get("article"):
                article = inferred["article"]
                resolution = "heading_inferred"
            elif carried_article:
                article = carried_article
                resolution = "carried_forward"
            else:
                article = "Fallback_Doc"
                resolution = "document_fallback"
                
            carried_article = article
            
            structural_path = {
                "chapter": meta_struct.get("chapter") or inferred.get("chapter"),
                "article": article,
                "clause": meta_struct.get("clause"),
                "point": meta_struct.get("point")
            }
            
            children[chunk_id] = {
                "child_id": chunk_id,
                "source": src,
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "text": text,
                "structural_path": structural_path,
                "resolution_method": resolution,
                "ambiguous": ambiguous,
                "warnings": warnings,
                "parent_id": None # Will be assigned below
            }
            
    # Build Parents (grouping by source + article_key)
    # Split into windows if > PARENT_MAX_CHARS
    for child_id, child in children.items():
        src = child["source"]
        article = child["structural_path"]["article"]
        parent_base_key = f"{src}::{article}"
        
        if parent_base_key not in parents:
            parents[parent_base_key] = []
            
        current_windows = parents[parent_base_key]
        
        if not current_windows:
            current_windows.append({"child_ids": [], "text": "", "char_count": 0, "page_start": 9999, "page_end": -1})
            
        last_window = current_windows[-1]
        child_len = len(child["text"])
        
        if last_window["char_count"] + child_len > PARENT_MAX_CHARS and last_window["char_count"] > 0:
            # Create new window
            current_windows.append({"child_ids": [], "text": "", "char_count": 0, "page_start": 9999, "page_end": -1})
            last_window = current_windows[-1]
            
        last_window["child_ids"].append(child_id)
        if last_window["text"]:
            last_window["text"] += "\n" + child["text"]
        else:
            last_window["text"] = child["text"]
            
        last_window["char_count"] += child_len
        last_window["page_start"] = min(last_window["page_start"], child["page_start"])
        last_window["page_end"] = max(last_window["page_end"], child["page_end"])
        
    final_parents = {}
    for base_key, windows in parents.items():
        src, article = base_key.split("::")
        for i, win in enumerate(windows):
            parent_id = f"parent_{md5_hash(base_key)}_{i}"
            win["parent_id"] = parent_id
            win["source"] = src
            win["article_key"] = article
            win["window_index"] = i
            win["ambiguous_child_count"] = 0
            win["warnings"] = []
            final_parents[parent_id] = win
            
            for cid in win["child_ids"]:
                children[cid]["parent_id"] = parent_id
                
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_DIR / "children.json", "w", encoding="utf-8") as f:
        json.dump(children, f, ensure_ascii=False, indent=2)
    with open(STORAGE_DIR / "parents.json", "w", encoding="utf-8") as f:
        json.dump(final_parents, f, ensure_ascii=False, indent=2)
        
    print(f"Built {len(children)} children and {len(final_parents)} parents.")

def load_hierarchy():
    if not (STORAGE_DIR / "children.json").exists():
        build_hierarchy()
    with open(STORAGE_DIR / "children.json", "r", encoding="utf-8") as f:
        children = json.load(f)
    with open(STORAGE_DIR / "parents.json", "r", encoding="utf-8") as f:
        parents = json.load(f)
    return children, parents

# ==========================================
# STEP 4: MULTI-QUERY GENERATOR
# ==========================================
_query_cache = {}

def expand_query(question: str) -> dict:
    question = question.strip()
    cache_key = md5_hash(question + GEMINI_GENERATION_MODEL)
    if cache_key in _query_cache:
        res = _query_cache[cache_key]
        res["cache_hit"] = True
        return res
        
    q0 = {
        "query_id": "Q0",
        "text": question,
        "origin": "original",
        "focus": "original_intent"
    }
    
    if not GEMINI_API_KEY:
        return {"original_question": question, "queries": [q0], "status": "query_generation_unavailable"}
        
    client = genai.Client()
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "queries": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING"},
                        "focus": {"type": "STRING"}
                    },
                    "required": ["text", "focus"]
                }
            }
        },
        "required": ["queries"]
    }
    
    prompt = f"Bạn là chuyên gia pháp lý. Hãy tạo tối đa {MULTI_QUERY_COUNT} cách truy vấn khác nhau cho câu hỏi sau để cải thiện việc tìm kiếm trong CSDL luật. Câu hỏi gốc: '{question}'. Lưu ý: không trả lời câu hỏi, chỉ sinh truy vấn tìm kiếm khác cách diễn đạt hoặc thuật ngữ pháp lý. Output bằng JSON."
    
    try:
        resp = client.models.generate_content(
            model=GEMINI_GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=MULTI_QUERY_TEMPERATURE
            )
        )
        
        data = json.loads(resp.text)
        queries = [q0]
        
        for i, q in enumerate(data.get("queries", [])[:MULTI_QUERY_COUNT]):
            queries.append({
                "query_id": f"Q{i+1}",
                "text": q["text"][:MULTI_QUERY_MAX_CHARS].strip(),
                "origin": "generated",
                "focus": q.get("focus", "paraphrase")
            })
            
        res = {
            "original_question": question,
            "queries": queries,
            "model": GEMINI_GENERATION_MODEL,
            "status": "ready"
        }
        _query_cache[cache_key] = res
        return res
    except Exception as e:
        print(f"Error expanding query: {e}")
        return {"original_question": question, "queries": [q0], "status": "query_generation_unavailable"}

# ==========================================
# STEP 5 & 6 & 7: RETRIEVAL & RERANK
# ==========================================
def generate_answer(question: str, context_text: str) -> str:
    if not GEMINI_API_KEY:
        return "Lỗi: Không tìm thấy GEMINI_API_KEY"
    
    client = genai.Client()
    
    prompt = f"""Bạn là trợ lý AI pháp lý. Dựa vào NGỮ CẢNH dưới đây, hãy trả lời CÂU HỎI.
Nếu thông tin không có trong ngữ cảnh, hãy nói "Tôi không biết dựa trên tài liệu được cung cấp".

NGỮ CẢNH:
{context_text}

CÂU HỎI:
{question}
"""
    try:
        resp = client.models.generate_content(
            model=GEMINI_GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        return resp.text
    except Exception as e:
        return f"Lỗi sinh câu trả lời: {e}"

def get_strategy_chunks():
    all_chunks, _ = load_chunks()
    return [c for c in all_chunks if c.get("strategy") == "hierarchical"]

def run_multi_query_pipeline(question: str, mode: str):
    """
    mode: single_flat, multi_flat, single_parent, multi_parent
    """
    t_start = time.perf_counter()
    chunks = get_strategy_chunks()
    
    if "multi" in mode:
        expanded = expand_query(question)
        queries = expanded.get("queries", [])
    else:
        queries = [{"query_id": "Q0", "text": question, "origin": "original", "focus": "original_intent"}]
        
    child_hits = {}
    
    for q in queries:
        qid = q["query_id"]
        qtext = q["text"]
        qweight = MULTI_QUERY_ORIGINAL_WEIGHT if qid == "Q0" else MULTI_QUERY_VARIANT_WEIGHT
        
        # Inner hybrid search
        h_res_tuple = hybrid_search(qtext, "hierarchical", chunks)
        h_res = h_res_tuple[0]
        
        for rank, c in enumerate(h_res, 1):
            cid = c["chunk_id"]
            if cid not in child_hits:
                child_hits[cid] = {
                    "child_id": cid,
                    "text": c["text"],
                    "source": c["source"],
                    "page_start": c.get("page_start", 0),
                    "page_end": c.get("page_end", 0),
                    "multi_query_rrf_score": 0.0,
                    "support_query_count": 0,
                    "support_query_ids": [],
                    "per_query_ranks": {},
                    "chunk": c
                }
            hit = child_hits[cid]
            hit["multi_query_rrf_score"] += qweight / (MULTI_QUERY_RRF_K + rank)
            hit["support_query_count"] += 1
            hit["support_query_ids"].append(qid)
            hit["per_query_ranks"][qid] = rank
            
    # Sort child hits
    fused_children = list(child_hits.values())
    fused_children.sort(key=lambda x: (-x["multi_query_rrf_score"], -x["support_query_count"], min(x["per_query_ranks"].values()), x["child_id"]))
    
    for i, c in enumerate(fused_children, 1):
        c["multi_query_rank"] = i
        
    trace = {"mode": mode, "queries": queries, "fusion": fused_children}
    
    if "flat" in mode:
        # Evaluate flat (baseline-like) but on fused children
        top_candidates = [c["chunk"] for c in fused_children[:PARENT_CANDIDATES]]
        reranked_tuple = rerank_candidates(question, top_candidates)
        final_docs = reranked_tuple[0][:FINAL_PARENT_TOP_K]
        
        # Build context
        context_parts = []
        for d in final_docs:
            context_parts.append(f"Nguồn: {d['source']} (Trang {d['page_start']})\n{d['text']}")
        context_text = "\n\n---\n\n".join(context_parts)
        
        ans = generate_answer(question, context_text)
        return ans, final_docs, trace
        
    elif "parent" in mode:
        children_db, parents_db = load_hierarchy()
        
        parent_scores = {}
        for c in fused_children:
            cid = c["child_id"]
            if cid not in children_db:
                continue
            pid = children_db[cid]["parent_id"]
            
            if pid not in parent_scores:
                parent_scores[pid] = {"parent_id": pid, "aggregated_score": 0.0, "anchor_children": [], "count": 0}
                
            if parent_scores[pid]["count"] < PARENT_SCORE_CHILD_LIMIT:
                parent_scores[pid]["aggregated_score"] += c["multi_query_rrf_score"]
                parent_scores[pid]["anchor_children"].append(cid)
                parent_scores[pid]["count"] += 1
                
        # Sort parents
        parent_candidates = list(parent_scores.values())
        parent_candidates.sort(key=lambda x: -x["aggregated_score"])
        
        top_parents = parent_candidates[:PARENT_CANDIDATES]
        
        # Prepare for reranking
        rerank_input = []
        for p in top_parents:
            pdb = parents_db[p["parent_id"]]
            rerank_input.append({
                "parent_id": p["parent_id"],
                "text": pdb["text"],
                "source": pdb["source"],
                "page_start": pdb["page_start"],
                "page_end": pdb["page_end"]
            })
            
        reranked_parents_tuple = rerank_candidates(question, rerank_input)
        final_parents = reranked_parents_tuple[0][:FINAL_PARENT_TOP_K]
        
        context_parts = []
        for p in final_parents:
            context_parts.append(f"Nguồn: {p['source']} (Trang {p['page_start']})\n{p['text']}")
        context_text = "\n\n---\n\n".join(context_parts)
        
        ans = generate_answer(question, context_text)
        trace["parent_candidates"] = parent_candidates
        return ans, final_parents, trace

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "build-hierarchy":
            build_hierarchy()
        elif cmd == "hierarchy-audit":
            print("Audit not fully implemented in CLI.")
        elif cmd == "expand-query":
            q = sys.argv[2]
            res = expand_query(q)
            print(json.dumps(res, ensure_ascii=False, indent=2))
