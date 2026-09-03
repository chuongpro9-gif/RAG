import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

base_dir = Path(r"D:/du_an_cua_ban/RAG/rag_advanced/buoi_18")
log_file = base_dir / "outputs" / "audit_log.jsonl"

def log_audit_event(
    user_id_demo: str,
    user_role: str,
    action: str,
    query: str,
    retrieved_doc_ids: list = None,
    retrieved_chunk_ids: list = None,
    citation_ids: list = None,
    denied_candidates_count: int = 0,
    status: str = "SUCCESS",
    details: dict = None
) -> str:
    request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "user_id_demo": user_id_demo,
        "user_role": user_role,
        "action": action,
        "query": query,
        "retrieved_doc_ids": retrieved_doc_ids or [],
        "retrieved_chunk_ids": retrieved_chunk_ids or [],
        "citation_ids": citation_ids or [],
        "denied_candidates_count": denied_candidates_count,
        "status": status,
        "details": details or {}
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return request_id
