import os
import sys
import pandas as pd
import re
import glob

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    wiki_dir = os.path.join(os.path.dirname(__file__), "..", "wiki")
    report_file = os.path.join(outputs_dir, "wiki_validation_report.md")
    
    df_entities = pd.read_csv(os.path.join(outputs_dir, "entities.csv")).fillna("")
    df_relations = pd.read_csv(os.path.join(outputs_dir, "relations.csv")).fillna("")
    
    md_files = glob.glob(os.path.join(wiki_dir, "**", "*.md"), recursive=True)
    
    valid_ids = df_entities["id"].tolist()
    
    # 4. Entity duplicate check
    id_counts = df_entities["id"].value_counts()
    duplicates = id_counts[id_counts > 1].index.tolist()
    
    # Pre-parse wiki content
    wiki_links = []
    file_to_id = {}
    id_to_file = {}
    orphan_pages = []
    
    for fpath in md_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        fname = os.path.splitext(os.path.basename(fpath))[0]
        
        # Match ID in frontmatter
        id_match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
        doc_id = id_match.group(1).strip() if id_match else None
        
        if doc_id:
            file_to_id[fname] = doc_id
            id_to_file[doc_id] = fname
            
        # Match wikilinks [[Target]]
        links = re.findall(r'\[\[(.*?)\]\]', content)
        has_outgoing_links = False
        for link in links:
            if link not in ["risks/", "controls/", "events/"]: # Ignore directory links in Home
                wiki_links.append((fname, link))
                has_outgoing_links = True
                
        # We also need to check incoming links later for orphans, but let's just consider a page an orphan if it has no incoming AND no outgoing
        # Or simpler: orphan if it has no wikilinks at all and nothing links to it.
    
    target_links = {tgt for src, tgt in wiki_links}
    
    broken_links = []
    for src, tgt in wiki_links:
        if tgt not in file_to_id and tgt != "Home":
            broken_links.append((src, tgt))
            
    pages_not_in_entities = []
    for fname, doc_id in file_to_id.items():
        if doc_id not in valid_ids:
            pages_not_in_entities.append(fname)
            
    # Orphan check: A page is orphan if it's not Home and has no incoming links and no outgoing links.
    for fname in file_to_id.keys():
        if fname == "Home": continue
        has_in = fname in target_links
        has_out = any(s == fname for s, t in wiki_links)
        if not has_in and not has_out:
            orphan_pages.append(fname)
            
    # 6. Relation check
    invalid_rels = []
    for _, row in df_relations.iterrows():
        if row["source_id"] not in valid_ids or row["target_id"] not in valid_ids:
            invalid_rels.append((row["source_id"], row["target_id"]))
            
    # 7 & 8. RuiRo rules
    risks_with_no_control = []
    risks_with_no_event = []
    
    for _, row in df_entities[df_entities["type"] == "RuiRo"].iterrows():
        eid = row["id"]
        # Check controls
        has_ctrl = any((r["target_id"] == eid and r["relationship_type"] == "MITIGATES") for _, r in df_relations.iterrows())
        if not has_ctrl: risks_with_no_control.append(eid)
        
        # Check events
        has_event = any((r["source_id"] == eid and r["relationship_type"] == "OBSERVED_AS") for _, r in df_relations.iterrows())
        if not has_event: risks_with_no_event.append(eid)
        
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Báo cáo Kiểm tra Wiki Risk Graph\n\n")
        f.write(f"- **1. Tổng số file Markdown:** {len(md_files)}\n")
        f.write(f"- **2. Tổng số wikilink:** {len(wiki_links)}\n\n")
        
        f.write("## 3. Wikilink trỏ tới trang không tồn tại\n")
        if broken_links:
            for s, t in broken_links:
                f.write(f"- `[[{s}]]` -> `[[{t}]]` (Không tồn tại)\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 4. Entity bị trùng ID\n")
        if duplicates:
            f.write(f"- {', '.join(duplicates)}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 5. Trang có ID nhưng không tồn tại trong entities.csv\n")
        if pages_not_in_entities:
            f.write(f"- {', '.join(pages_not_in_entities)}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 6. Relation có source hoặc target không tồn tại\n")
        if invalid_rels:
            for s, t in invalid_rels:
                f.write(f"- Source: {s}, Target: {t}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 7. RuiRo không có bất kỳ KiemSoat nào\n")
        if risks_with_no_control:
            f.write(f"- {', '.join(risks_with_no_control)}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 8. RuiRo không có bất kỳ SuKienRuiRo nào\n")
        if risks_with_no_event:
            f.write(f"- {', '.join(risks_with_no_event)}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
        f.write("\n## 9. Trang không có liên kết với trang khác (orphan page)\n")
        if orphan_pages:
            f.write(f"- {', '.join(orphan_pages)}\n")
        else:
            f.write("- KHÔNG CÓ\n")
            
    print(f"Validation report saved to {report_file}")

if __name__ == "__main__":
    main()
