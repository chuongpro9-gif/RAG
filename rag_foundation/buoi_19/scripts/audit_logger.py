import os
import json
import datetime

AUDIT_FILE = os.path.join(os.path.dirname(__file__), "..", "outputs", "audit_log.jsonl")

def log_audit_event(user_id, role, action, query, method, retrieved_doc_ids, retrieved_chunk_ids, citation_ids, denied_count, status="SUCCESS"):
    event = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "role": role,
        "action": action,
        "query": query,
        "method": method,
        "retrieved_doc_ids": retrieved_doc_ids,
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "citation_ids": citation_ids,
        "denied_count": denied_count,
        "status": status
    }
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
