import os
import sys
import pandas as pd
import re

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def sanitize_filename(name):
    # Obsidian supports spaces in filenames, but we should remove invalid characters
    return re.sub(r'[\\/*?:"<>|]', "", str(name))

def main():
    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    wiki_dir = os.path.join(os.path.dirname(__file__), "..", "wiki")
    
    os.makedirs(os.path.join(wiki_dir, "risks"), exist_ok=True)
    os.makedirs(os.path.join(wiki_dir, "controls"), exist_ok=True)
    os.makedirs(os.path.join(wiki_dir, "events"), exist_ok=True)
    
    df_entities = pd.read_csv(os.path.join(outputs_dir, "entities.csv")).fillna("")
    df_relations = pd.read_csv(os.path.join(outputs_dir, "relations.csv")).fillna("")
    
    # Pre-compute relationship maps
    # RuiRo -> controls, RuiRo -> events
    risk_to_controls = {}
    risk_to_events = {}
    control_to_risks = {}
    event_to_risks = {}
    
    # Store filename for each ID to make wikilinks
    id_to_filename = {}
    for _, row in df_entities.iterrows():
        eid = row["id"]
        type_ = row["type"]
        if type_ == "RuiRo":
            fname = f"{eid} - {sanitize_filename(row['name'])}"
        elif type_ == "KiemSoat":
            fname = f"{eid} - {sanitize_filename(row['name'])}"
        elif type_ == "SuKienRuiRo":
            fname = f"{eid}"
        id_to_filename[eid] = fname

    for _, row in df_relations.iterrows():
        src = row["source_id"]
        tgt = row["target_id"]
        rel_type = row["relationship_type"]
        evidence = row["evidence_quote"]
        status = row["verification_status"]
        
        rel_info = {
            "type": rel_type,
            "evidence": evidence,
            "status": status,
            "src": src,
            "tgt": tgt
        }
        
        if rel_type == "MITIGATES": # KiemSoat -> RuiRo
            if tgt not in risk_to_controls: risk_to_controls[tgt] = []
            risk_to_controls[tgt].append(rel_info)
            if src not in control_to_risks: control_to_risks[src] = []
            control_to_risks[src].append(rel_info)
            
        elif rel_type == "OBSERVED_AS": # RuiRo -> SuKienRuiRo
            if src not in risk_to_events: risk_to_events[src] = []
            risk_to_events[src].append(rel_info)
            if tgt not in event_to_risks: event_to_risks[tgt] = []
            event_to_risks[tgt].append(rel_info)

    stats = {"RuiRo": 0, "KiemSoat": 0, "SuKienRuiRo": 0}
    wikilink_count = 0
    
    def generate_frontmatter(row):
        return f"---\nid: {row['id']}\ntype: {row['type']}\nverification_status: {row['verification_status']}\ndata_origin: {row['data_origin']}\n---\n\n"

    def format_rel(target_id, rel):
        nonlocal wikilink_count
        wikilink_count += 1
        return f"- [[{id_to_filename[target_id]}]] (Quan hệ: {rel['type']}, Trạng thái: {rel['status']}, Bằng chứng: {rel['evidence']})"

    # Generate pages
    for _, row in df_entities.iterrows():
        eid = row["id"]
        type_ = row["type"]
        fname = id_to_filename[eid]
        content = generate_frontmatter(row)
        content += f"# {row['name'] if row['name'] else eid}\n\n"
        
        if type_ == "RuiRo":
            content += f"**Mô tả:** {row['description']}\n\n"
            content += f"- **Category:** {row['category']}\n"
            content += f"- **Cause:** {row['cause']}\n"
            content += f"- **Event:** {row['event']}\n"
            content += f"- **Impact:** {row['impact']}\n"
            content += f"- **Inherent Level:** {row['inherent_level']}\n"
            content += f"- **Residual Level:** {row['residual_level']}\n"
            content += f"- **Owner Unit ID:** {row['owner_unit_id']}\n\n"
            
            content += "## Kiểm soát liên quan\n"
            for rel in risk_to_controls.get(eid, []):
                content += format_rel(rel["src"], rel) + "\n"
                
            content += "\n## Sự kiện liên quan\n"
            for rel in risk_to_events.get(eid, []):
                content += format_rel(rel["tgt"], rel) + "\n"
                
            filepath = os.path.join(wiki_dir, "risks", f"{fname}.md")
            stats["RuiRo"] += 1
            
        elif type_ == "KiemSoat":
            content += f"- **Control Type:** {row['control_type']}\n"
            content += f"- **Frequency:** {row['frequency']}\n"
            content += f"- **Owner Role ID:** {row['owner_role_id']}\n"
            content += f"- **Effectiveness:** {row['effectiveness']}\n\n"
            
            content += "## Rủi ro được giảm thiểu\n"
            for rel in control_to_risks.get(eid, []):
                content += format_rel(rel["tgt"], rel) + "\n"
                
            filepath = os.path.join(wiki_dir, "controls", f"{fname}.md")
            stats["KiemSoat"] += 1
            
        elif type_ == "SuKienRuiRo":
            content += f"**Mô tả:** {row['description']}\n\n"
            content += f"- **Occurred At:** {row['occurred_at']}\n"
            content += f"- **Discovered At:** {row['discovered_at']}\n"
            content += f"- **Severity:** {row['severity']}\n"
            content += f"- **Loss Amount (VND):** {row['loss_amount_vnd']}\n\n"
            
            content += "## Rủi ro tương ứng\n"
            for rel in event_to_risks.get(eid, []):
                content += format_rel(rel["src"], rel) + "\n"
                
            filepath = os.path.join(wiki_dir, "events", f"{fname}.md")
            stats["SuKienRuiRo"] += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
    # Home.md
    home_content = "# Wiki Risk Graph\n\n"
    home_content += "## Danh sách\n"
    home_content += "- [[risks/]] (Danh sách Rủi ro)\n"
    home_content += "- [[controls/]] (Danh sách Kiểm soát)\n"
    home_content += "- [[events/]] (Danh sách Sự kiện)\n\n"
    home_content += "## Thống kê\n"
    home_content += f"- Tổng số Rủi ro: {stats['RuiRo']}\n"
    home_content += f"- Tổng số Kiểm soát: {stats['KiemSoat']}\n"
    home_content += f"- Tổng số Sự kiện: {stats['SuKienRuiRo']}\n"
    home_content += f"- Tổng số Liên kết (Edges): {len(df_relations)}\n"
    
    with open(os.path.join(wiki_dir, "Home.md"), "w", encoding="utf-8") as f:
        f.write(home_content)

    print(f"--- Báo cáo ---")
    print(f"Tổng số trang Wiki đã tạo: {sum(stats.values()) + 1} (bao gồm Home.md)")
    print(f"Tổng số wikilink đã tạo: {wikilink_count}")
    print(f"Ví dụ đường đi: KiemSoat -> RuiRo -> SuKienRuiRo")
    
    # Try finding an example path
    for c_eid, rels in control_to_risks.items():
        r_eid = rels[0]["tgt"]
        if r_eid in risk_to_events:
            e_eid = risk_to_events[r_eid][0]["tgt"]
            print(f"  [[{id_to_filename[c_eid]}]] -> [[{id_to_filename[r_eid]}]] -> [[{id_to_filename[e_eid]}]]")
            break

if __name__ == "__main__":
    main()
