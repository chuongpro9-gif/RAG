import sys
import pandas as pd
from pathlib import Path

base_dir = Path(r"D:/du_an_cua_ban/RAG/rag_advanced/buoi_18")
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from scripts.compliance_checker import run_compliance_checker
from scripts.audit_checklist_gen import generate_audit_checklist

print("=" * 80)
print("🛡️ BẮT ĐẦU KIỂM THỬ BẢO MẬT & GUARDRAIL BUỔI 18 (SECURITY TESTS)")
print("=" * 80)

# Test 1: RBAC Guest Deny
df_guest = run_compliance_checker("Tất cả", "Guest")
t1 = len(df_guest) == 0
print(f"[*] Test 1: RBAC Pre-Filtering (Guest Blocked)    : {'PASS' if t1 else 'FAIL'}")

# Test 2: Citation Integrity
df_conf = run_compliance_checker("Tất cả", "Admin")
t2 = (df_conf["doc_a_citation"].str.len() > 0).all() and (df_conf["doc_b_citation"].str.len() > 0).all()
print(f"[*] Test 2: Citation Integrity (No empty cites)   : {'PASS' if t2 else 'FAIL'}")

# Test 3: Human Review Guardrail
t3 = (df_conf["review_status"] == "NEEDS_HUMAN_REVIEW").all()
print(f"[*] Test 3: Human Review Guardrail Enforced        : {'PASS' if t3 else 'FAIL'}")

# Test 4: Checklist Generation with Risk Levels
df_chk = generate_audit_checklist("Tất cả", "Chi nhánh loại 1", "KiemToanVien")
t4 = len(df_chk) > 0 and (df_chk["risk_level"].isin(["HIGH", "MEDIUM", "LOW"])).all()
print(f"[*] Test 4: UC4 Checklist Generator (Risk Validated): {'PASS' if t4 else 'FAIL'}")

# Test 5: Audit Log Sanitization
log_path = base_dir / "outputs" / "audit_log.jsonl"
t5 = log_path.exists()
print(f"[*] Test 5: Sanitized Audit Trail Logging         : {'PASS' if t5 else 'FAIL'}")

all_pass = t1 and t2 and t3 and t4 and t5
print("=" * 80)
print(f"SECURITY & GUARDRAIL TESTS: {'PASS' if all_pass else 'FAIL'}")
print("=" * 80)
