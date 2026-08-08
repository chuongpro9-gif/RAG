"""
Core logic for Advanced RAG with Hybrid Search (BM25 + Semantic) and Cross-Encoder Reranking.
"""
import os
import argparse
import sys
import json
import re
import unicodedata
import time
from pathlib import Path
from dotenv import load_dotenv

# Optional imports cho Reranker (lazy load)
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    pass

# Load cấu hình
current_dir = Path(__file__).parent.resolve()
load_dotenv(current_dir / ".env")

def get_config(key, default, cast_type=str):
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return cast_type(val)
    except:
        return default

BM25_CANDIDATES = get_config("BM25_CANDIDATES", 20, int)
SEMANTIC_CANDIDATES = get_config("SEMANTIC_CANDIDATES", 20, int)
RRF_K = get_config("RRF_K", 60, int)
RRF_BM25_WEIGHT = get_config("RRF_BM25_WEIGHT", 1.0, float)
RRF_SEMANTIC_WEIGHT = get_config("RRF_SEMANTIC_WEIGHT", 1.0, float)
RERANK_CANDIDATES = get_config("RERANK_CANDIDATES", 20, int)
FINAL_TOP_K = get_config("FINAL_TOP_K", 5, int)
RERANKER_MODEL = get_config("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANKER_MAX_LENGTH = get_config("RERANKER_MAX_LENGTH", 512, int)
RERANK_BATCH_SIZE = get_config("RERANK_BATCH_SIZE", 4, int)
RERANK_MIN_SCORE = get_config("RERANK_MIN_SCORE", 0.50, float)
RERANK_DEVICE = get_config("RERANK_DEVICE", "auto")

def validate_config():
    if not (0 < BM25_CANDIDATES <= 100): raise ValueError("BM25_CANDIDATES invalid")
    if not (0 < SEMANTIC_CANDIDATES <= 100): raise ValueError("SEMANTIC_CANDIDATES invalid")
    if not (0 < RERANK_CANDIDATES <= 100): raise ValueError("RERANK_CANDIDATES invalid")
    if not (0 < FINAL_TOP_K <= 100): raise ValueError("FINAL_TOP_K invalid")
    if FINAL_TOP_K > RERANK_CANDIDATES: raise ValueError("FINAL_TOP_K <= RERANK_CANDIDATES required")
    if RRF_K <= 0: raise ValueError("RRF_K > 0 required")
    if RRF_BM25_WEIGHT < 0 or RRF_SEMANTIC_WEIGHT < 0: raise ValueError("Weights >= 0 required")
    if RRF_BM25_WEIGHT == 0 and RRF_SEMANTIC_WEIGHT == 0: raise ValueError("Weights cannot be both 0")
    if not (64 <= RERANKER_MAX_LENGTH <= 4096): raise ValueError("RERANKER_MAX_LENGTH invalid")
    if not (1 <= RERANK_BATCH_SIZE <= 64): raise ValueError("RERANK_BATCH_SIZE invalid")
    if not (0.0 <= RERANK_MIN_SCORE <= 1.0): raise ValueError("RERANK_MIN_SCORE invalid")
    if RERANK_DEVICE not in ["auto", "cpu", "cuda"]: raise ValueError("RERANK_DEVICE invalid")
    if not RERANKER_MODEL: raise ValueError("RERANKER_MODEL empty")

validate_config()

def tokenize_vi_legal(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    # Giữ chữ tiếng Việt và số
    tokens = re.findall(r'[a-z0-9_àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+', text)
    return [t for t in tokens if t.strip()]

def bm25_search(question: str, chunks: list[dict], candidate_k: int) -> list[dict]:
    if not question or not isinstance(question, str):
        raise ValueError("Question cannot be empty")
    tokens = tokenize_vi_legal(question)
    if not tokens:
        raise ValueError("Question contains no valid tokens")
    
    if not chunks:
        return []

    # Sort chunks by chunk_id for deterministic tie-breaking later
    sorted_chunks = sorted(chunks, key=lambda c: c["chunk_id"])
    
    corpus_tokens = [tokenize_vi_legal(c["text"]) for c in sorted_chunks]
    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(tokens)
    
    # Pack scores with index
    scored_chunks = [(score, i, sorted_chunks[i]) for i, score in enumerate(scores)]
    # Sort by score desc, then by chunk_id asc
    scored_chunks.sort(key=lambda x: (-x[0], x[2]["chunk_id"]))
    
    candidate_k = min(candidate_k, len(sorted_chunks))
    top_chunks = scored_chunks[:candidate_k]
    
    results = []
    for rank, (score, _, chunk) in enumerate(top_chunks, start=1):
        results.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "source": chunk["source"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "bm25_rank": rank,
            "bm25_score": float(score)
        })
    return results

# Import helper từ Buổi 07 để lấy chunk thật
sys.path.append(str(current_dir))
try:
    from rag import load_chunks
except ImportError:
    pass

def cli_bm25(args):
    question = args.question
    strategy = args.strategy
    chunks, _ = load_chunks()
    strategy_chunks = [c for c in chunks if c.get("strategy") == strategy]
    print(f"BM25 Search cho câu hỏi: '{question}' (Strategy: {strategy})")
    print(f"Corpus size: {len(strategy_chunks)}")
    
    t0 = time.perf_counter()
    res = bm25_search(question, strategy_chunks, BM25_CANDIDATES)
    t1 = time.perf_counter()
    
    for c in res:
        print(f"[{c['bm25_rank']}] Score: {c['bm25_score']:.4f} | ID: {c['chunk_id']} | Source: {c['source']} p.{c['page_start']}")
        print(f" Preview: {c['text'][:100]}...\n")
    print(f"Thời gian: {(t1-t0)*1000:.2f}ms")

def semantic_search(question: str, candidate_k: int, strategy: str) -> list[dict]:
    if not question or not isinstance(question, str):
        raise ValueError("Question cannot be empty")
    from rag import get_chroma_client, get_collection_name, get_embedding
    
    client = get_chroma_client()
    col_name = get_collection_name(strategy)
    
    try:
        collection = client.get_collection(name=col_name, embedding_function=None)
    except Exception:
        raise ValueError(f"Collection {col_name} chưa tồn tại. Vui lòng chạy prepare-semantic.")
        
    emeta = collection.metadata
    if emeta:
        if emeta.get("strategy") != strategy or int(emeta.get("embedding_dim", 0)) != get_config("GEMINI_EMBEDDING_DIM", 768, int):
            raise ValueError("Collection mismatch.")
            
    q_emb = get_embedding(question, task_type="retrieval_query")
    count = collection.count()
    if count == 0:
        return []
    n_results = min(candidate_k, count)
    
    res = collection.query(
        query_embeddings=[q_emb],
        n_results=n_results
    )
    
    results = []
    if res and res["ids"] and len(res["ids"]) > 0:
        ids = res["ids"][0]
        distances = res["distances"][0]
        documents = res["documents"][0]
        metadatas = res["metadatas"][0]
        for rank in range(len(ids)):
            results.append({
                "chunk_id": ids[rank],
                "text": documents[rank],
                "source": metadatas[rank]["source"],
                "page_start": metadatas[rank]["page_start"],
                "page_end": metadatas[rank]["page_end"],
                "semantic_rank": rank + 1,
                "semantic_distance": distances[rank]
            })
    return results

def cli_status(args):
    strategy = args.strategy
    chunks, _ = load_chunks()
    strategy_chunks = [c for c in chunks if c.get("strategy") == strategy]
    corpus_size = len(strategy_chunks)
    
    from rag import get_chroma_client, get_collection_name
    client = get_chroma_client()
    col_name = get_collection_name(strategy)
    try:
        col = client.get_collection(name=col_name, embedding_function=None)
        col_exists = True
        col_count = col.count()
    except Exception:
        col_exists = False
        col_count = 0
        
    print(f"--- STATUS ---")
    print(f"Strategy: {strategy}")
    print(f"Corpus size: {corpus_size}")
    print(f"Semantic collection: {col_name}")
    print(f"Collection exists: {col_exists} (Count: {col_count})")
    print(f"Embedding model/dim: {get_config('GEMINI_EMBEDDING_MODEL', 'gemini-embedding-2')} / {get_config('GEMINI_EMBEDDING_DIM', 768, int)}")
    print(f"BM25 ready: True")
    
    # Check reranker cache
    reranker = get_config("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    cache_dir = Path(__file__).parent / "storage" / "huggingface"
    cache_exists = cache_dir.exists() and any(cache_dir.iterdir())
    print(f"Reranker model: {reranker}")
    print(f"Reranker cache exists: {cache_exists}")

def cli_prepare_semantic(args):
    from rag import index_data
    print("Preparing semantic index...")
    index_data(args.strategy, reset=False)
    print("Done prepare.")

def hybrid_search(question: str, strategy: str, chunks: list[dict]):
    t_start = time.perf_counter()
    
    # 1. BM25 Search
    t_bm25_start = time.perf_counter()
    bm25_candidates = bm25_search(question, chunks, BM25_CANDIDATES)
    t_bm25 = time.perf_counter() - t_bm25_start
    
    # 2. Semantic Search
    t_sem_start = time.perf_counter()
    semantic_candidates = semantic_search(question, SEMANTIC_CANDIDATES, strategy)
    t_sem = time.perf_counter() - t_sem_start
    
    # 3. Fusion
    t_fusion_start = time.perf_counter()
    
    # Group by chunk_id
    fusion_map = {}
    
    for c in bm25_candidates:
        cid = c["chunk_id"]
        fusion_map[cid] = {
            "chunk_id": cid,
            "text": c["text"],
            "source": c["source"],
            "page_start": c["page_start"],
            "page_end": c["page_end"],
            "bm25_rank": c["bm25_rank"],
            "bm25_score": c["bm25_score"],
            "semantic_rank": None,
            "semantic_distance": None,
            "matched_by": ["bm25"]
        }
        
    for c in semantic_candidates:
        cid = c["chunk_id"]
        if cid in fusion_map:
            # Check metadata mismatch
            if fusion_map[cid]["text"] != c["text"]:
                raise ValueError(f"Metadata mismatch for chunk {cid}")
            fusion_map[cid]["semantic_rank"] = c["semantic_rank"]
            fusion_map[cid]["semantic_distance"] = c["semantic_distance"]
            fusion_map[cid]["matched_by"].append("semantic")
        else:
            fusion_map[cid] = {
                "chunk_id": cid,
                "text": c["text"],
                "source": c["source"],
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "bm25_rank": None,
                "bm25_score": None,
                "semantic_rank": c["semantic_rank"],
                "semantic_distance": c["semantic_distance"],
                "matched_by": ["semantic"]
            }
            
    # Calculate RRF Score
    fused_list = []
    for cid, data in fusion_map.items():
        rrf = 0.0
        best_rank = 999999
        if data["bm25_rank"] is not None:
            rrf += RRF_BM25_WEIGHT / (RRF_K + data["bm25_rank"])
            if data["bm25_rank"] < best_rank:
                best_rank = data["bm25_rank"]
        if data["semantic_rank"] is not None:
            rrf += RRF_SEMANTIC_WEIGHT / (RRF_K + data["semantic_rank"])
            if data["semantic_rank"] < best_rank:
                best_rank = data["semantic_rank"]
                
        data["rrf_score"] = rrf
        
        # for tie-breaking
        s_rank = data["semantic_rank"] if data["semantic_rank"] is not None else 999999
        b_rank = data["bm25_rank"] if data["bm25_rank"] is not None else 999999
        fused_list.append((rrf, best_rank, s_rank, b_rank, cid, data))
        
    # Sort
    # 1. rrf_score desc
    # 2. best_rank asc
    # 3. semantic_rank asc
    # 4. bm25_rank asc
    # 5. chunk_id asc
    fused_list.sort(key=lambda x: (-x[0], x[1], x[2], x[3], x[4]))
    
    results = []
    for rank, item in enumerate(fused_list, start=1):
        data = item[5]
        data["fused_rank"] = rank
        results.append(data)
        
    t_fusion = time.perf_counter() - t_fusion_start
    t_total = time.perf_counter() - t_start
    
    trace = {
        "bm25_candidate_count": len(bm25_candidates),
        "semantic_candidate_count": len(semantic_candidates),
        "union_count": len(results),
        "overlap_count": sum(1 for r in results if len(r["matched_by"]) == 2),
        "fused_count": len(results),
        "config": {
            "RRF_K": RRF_K,
            "RRF_BM25_WEIGHT": RRF_BM25_WEIGHT,
            "RRF_SEMANTIC_WEIGHT": RRF_SEMANTIC_WEIGHT
        },
        "latency_ms": {
            "bm25": t_bm25 * 1000,
            "semantic": t_sem * 1000,
            "fusion": t_fusion * 1000,
            "total": t_total * 1000
        }
    }
    
    return results, trace

def cli_hybrid(args):
    question = args.question
    strategy = args.strategy
    chunks, _ = load_chunks()
    strategy_chunks = [c for c in chunks if c.get("strategy") == strategy]
    
    res, trace = hybrid_search(question, strategy, strategy_chunks)
    print(f"--- HYBRID SEARCH ---")
    print(json.dumps(trace, indent=2))
    
    for c in res:
        print(f"[{c['fused_rank']}] RRF: {c['rrf_score']:.4f} | ID: {c['chunk_id']} | Matched: {c['matched_by']}")
        print(f"  BM25 Rank: {c['bm25_rank']} | Sem Rank: {c['semantic_rank']}")

_reranker_model_cache = None
_reranker_tokenizer_cache = None

def get_reranker():
    global _reranker_model_cache, _reranker_tokenizer_cache
    
    if _reranker_model_cache is not None and _reranker_tokenizer_cache is not None:
        return _reranker_tokenizer_cache, _reranker_model_cache
        
    print(f"INFO: Đang tải mô hình Reranker {RERANKER_MODEL} (Có thể lớn, mất thời gian, cần RAM/VRAM)...")
    
    os.environ["HF_HOME"] = str(Path(__file__).parent / "storage" / "huggingface")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
    except ImportError:
        raise RuntimeError("Thiếu thư viện transformers hoặc torch.")
        
    tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL)
    
    device = RERANK_DEVICE
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    elif device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA không khả dụng, nhưng RERANK_DEVICE được cấu hình là 'cuda'.")
        
    model.to(device)
    model.eval()
    
    _reranker_tokenizer_cache = tokenizer
    _reranker_model_cache = model
    
    return tokenizer, model

def sigmoid(x):
    import math
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

def rerank_candidates(question: str, candidates: list[dict], fake_reranker=None):
    if not candidates:
        return [], 0.0
        
    t_start = time.perf_counter()
    
    limit = min(RERANK_CANDIDATES, len(candidates))
    to_rerank = candidates[:limit]
    others = candidates[limit:] # Sẽ bị loại bỏ, vì chỉ trả về FINAL_TOP_K sau khi rerank
    
    try:
        if fake_reranker:
            scores = fake_reranker(question, [c["text"] for c in to_rerank])
        else:
            tokenizer, model = get_reranker()
            import torch
            
            pairs = [[question, c["text"]] for c in to_rerank]
            device = next(model.parameters()).device
            
            scores = []
            with torch.no_grad():
                for i in range(0, len(pairs), RERANK_BATCH_SIZE):
                    batch_pairs = pairs[i:i+RERANK_BATCH_SIZE]
                    inputs = tokenizer(batch_pairs, padding=True, truncation=True, max_length=RERANKER_MAX_LENGTH, return_tensors='pt').to(device)
                    outputs = model(**inputs, return_dict=True)
                    logits = outputs.logits.view(-1).float().cpu().tolist()
                    if isinstance(logits, float):
                        logits = [logits]
                    scores.extend(logits)
    except Exception as e:
        raise RuntimeError(f"reranker_unavailable: {e}")
                
    for i, score in enumerate(scores):
        c = to_rerank[i]
        c["rerank_raw_score"] = float(score)
        c["rerank_score"] = sigmoid(float(score))
        c["reranker_model"] = RERANKER_MODEL
        
    # Sort
    # 1. rerank_score desc
    # 2. fused_rank asc
    # 3. chunk_id asc
    to_rerank.sort(key=lambda x: (-x["rerank_score"], x["fused_rank"], x["chunk_id"]))
    
    results = []
    for rank, c in enumerate(to_rerank, start=1):
        c["rerank_rank"] = rank
        c["rank_change"] = c["fused_rank"] - rank
        results.append(c)
        
    t_total = time.perf_counter() - t_start
    
    for c in results:
        c["rerank_latency_ms"] = t_total * 1000
        
    final_results = results[:FINAL_TOP_K]
    return final_results, t_total * 1000

def cli_rerank(args):
    question = args.question
    strategy = args.strategy
    chunks, _ = load_chunks()
    strategy_chunks = [c for c in chunks if c.get("strategy") == strategy]
    
    res, trace = hybrid_search(question, strategy, strategy_chunks)
    print("--- Hybrid Results (Before Rerank) ---")
    print(f"Total: {len(res)}, limit to rerank: {RERANK_CANDIDATES}")
    
    try:
        final_res, latency = rerank_candidates(question, res)
    except Exception as e:
        print(f"Rerank Failed: {e}")
        return
        
    print(f"\n--- RERANK RESULTS ---")
    print(f"Rerank latency: {latency:.2f}ms")
    for c in final_res:
        print(f"[{c['rerank_rank']}] (change {c['rank_change']:+}) Score: {c['rerank_score']:.4f} | ID: {c['chunk_id']}")
        print(f"  Fused Rank: {c['fused_rank']} | RRF: {c['rrf_score']:.4f}")

def query_advanced(question: str, strategy: str, mode: str, skip_generation: bool = False):
    """
    mode: bm25, semantic, hybrid, hybrid_rerank
    """
    t_start = time.perf_counter()
    chunks = []
    
    from rag import load_chunks
    all_chunks, _ = load_chunks()
    strategy_chunks = [c for c in all_chunks if c.get("strategy") == strategy]
    
    res = []
    trace = {"mode": mode, "strategy": strategy}
    
    if mode == "bm25":
        res = bm25_search(question, strategy_chunks, BM25_CANDIDATES)
        # Sort and take top k
        res.sort(key=lambda x: x["bm25_rank"])
        res = res[:FINAL_TOP_K]
    elif mode == "semantic":
        res = semantic_search(question, SEMANTIC_CANDIDATES, strategy)
        # Filter max distance
        res = [c for c in res if c["semantic_distance"] <= get_config("RAG_MAX_DISTANCE", 0.45, float)]
        res.sort(key=lambda x: x["semantic_rank"])
        res = res[:FINAL_TOP_K]
    elif mode == "hybrid":
        hybrid_res, h_trace = hybrid_search(question, strategy, strategy_chunks)
        trace["hybrid_trace"] = h_trace
        hybrid_res.sort(key=lambda x: x["fused_rank"])
        res = hybrid_res[:FINAL_TOP_K]
    elif mode == "hybrid_rerank":
        hybrid_res, h_trace = hybrid_search(question, strategy, strategy_chunks)
        trace["hybrid_trace"] = h_trace
        reranked_res, r_latency = rerank_candidates(question, hybrid_res)
        trace["rerank_latency_ms"] = r_latency
        # Filter min score
        res = [c for c in reranked_res if c["rerank_score"] >= RERANK_MIN_SCORE]
    else:
        raise ValueError(f"Unknown mode: {mode}")
        
    t_retrieval = time.perf_counter() - t_start
    trace["retrieval_latency_ms"] = t_retrieval * 1000
    
    if skip_generation:
        return "", res, trace
        
    # Generate Answer
    t_gen_start = time.perf_counter()
    
    if not res:
        answer = "Không tìm thấy thông tin phù hợp trong tài liệu."
    else:
        # Build prompt
        context_str = ""
        for i, chunk in enumerate(res, start=1):
            context_str += f"[E{i}] {chunk['text']}\n"
            
        prompt = f"""Bạn là trợ lý AI pháp lý. Dựa vào NGỮ CẢNH dưới đây, hãy trả lời CÂU HỎI.
Nếu thông tin không có trong ngữ cảnh, hãy nói "Tôi không biết dựa trên tài liệu được cung cấp".
Luôn trích dẫn nguồn theo định dạng [E1], [E2] tương ứng với đoạn văn.

NGỮ CẢNH:
{context_str}

CÂU HỎI:
{question}
"""
        from google import genai
        from google.genai import types
        client = genai.Client()
        gen_model = get_config("GEMINI_GENERATION_MODEL", "gemini-3.5-flash-lite")
        try:
            response = client.models.generate_content(
                model=gen_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            answer = response.text
        except Exception as e:
            answer = f"Lỗi tạo câu trả lời: {e}"
            
    t_gen = time.perf_counter() - t_gen_start
    trace["generation_latency_ms"] = t_gen * 1000
    
    return answer, res, trace

def cli_query(args):
    question = args.question
    strategy = args.strategy
    mode = args.mode
    
    print(f"Querying [{mode}] on {strategy}: {question}")
    ans, chunks, trace = query_advanced(question, strategy, mode)
    
    print("\n=== TRACE ===")
    print(json.dumps(trace, indent=2))
    
    print("\n=== CITATIONS ===")
    for i, c in enumerate(chunks, start=1):
        score_info = []
        if "bm25_score" in c and c["bm25_score"] is not None: score_info.append(f"BM25:{c['bm25_score']:.2f}")
        if "semantic_distance" in c and c["semantic_distance"] is not None: score_info.append(f"Sem:{c['semantic_distance']:.2f}")
        if "rrf_score" in c: score_info.append(f"RRF:{c['rrf_score']:.4f}")
        if "rerank_score" in c: score_info.append(f"Rerank:{c['rerank_score']:.4f}")
        print(f"[E{i}] ID: {c['chunk_id']} | Source: {c['source']} p.{c['page_start']}")
        print(f"      Scores: {', '.join(score_info)}")
        
    print("\n=== ANSWER ===")
    print(ans)

def cli_compare(args):
    question = args.question
    strategy = args.strategy
    modes = ["bm25", "semantic", "hybrid", "hybrid_rerank"]
    
    print(f"Comparing 4 modes for: {question}")
    print(f"Strategy: {strategy}")
    
    results = {}
    for m in modes:
        _, chunks, trace = query_advanced(question, strategy, m, skip_generation=True)
        results[m] = {
            "chunks": chunks,
            "latency": trace.get("retrieval_latency_ms", 0.0)
        }
        
    for m in modes:
        print(f"\n--- {m.upper()} ({results[m]['latency']:.2f}ms) ---")
        for i, c in enumerate(results[m]["chunks"], start=1):
            print(f" {i}. {c['chunk_id']} (Source: {c['source']} p.{c['page_start']})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    bm25_p = subparsers.add_parser("bm25")
    bm25_p.add_argument("--strategy", required=True)
    bm25_p.add_argument("--question", required=True)
    
    status_p = subparsers.add_parser("status")
    status_p.add_argument("--strategy", required=True)
    
    prep_p = subparsers.add_parser("prepare-semantic")
    prep_p.add_argument("--strategy", required=True)
    
    hybrid_p = subparsers.add_parser("hybrid")
    hybrid_p.add_argument("--strategy", required=True)
    hybrid_p.add_argument("--question", required=True)
    
    rerank_p = subparsers.add_parser("rerank")
    rerank_p.add_argument("--strategy", required=True)
    rerank_p.add_argument("--question", required=True)
    
    query_p = subparsers.add_parser("query")
    query_p.add_argument("--mode", required=True, choices=["bm25", "semantic", "hybrid", "hybrid_rerank"])
    query_p.add_argument("--strategy", required=True)
    query_p.add_argument("--question", required=True)
    
    cmp_p = subparsers.add_parser("compare")
    cmp_p.add_argument("--strategy", required=True)
    cmp_p.add_argument("--question", required=True)
    
    args = parser.parse_args()
    if args.command == "bm25":
        cli_bm25(args)
    elif args.command == "status":
        cli_status(args)
    elif args.command == "prepare-semantic":
        cli_prepare_semantic(args)
    elif args.command == "hybrid":
        cli_hybrid(args)
    elif args.command == "rerank":
        cli_rerank(args)
    elif args.command == "query":
        cli_query(args)
    elif args.command == "compare":
        cli_compare(args)
