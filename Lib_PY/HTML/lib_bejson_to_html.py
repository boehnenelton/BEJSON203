"""
Library:      lib_bejson_to_html.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Core transformer for converting BEJSON data into platform-native HTML3 components.
"""

import json
import html as html_mod
from datetime import datetime

# Import components from standard HTML2 family
try:
    from lib_html2_body import html_brutal_card, html_brutal_table, html_subtabs, html_tab_content
except ImportError:
    # Fallback/Dummy for environments where they aren't loaded yet
    def html_brutal_card(title, content): return f"<div class='b-card'><h3>{title}</h3>{content}</div>"
    def html_brutal_table(headers, rows, escape=True): return "<table></table>"
    def html_subtabs(tabs): return ""
    def html_tab_content(id, content, active=False): return content

def bejson_to_html_viewer(bejson_doc):
    """
    Converts a BEJSON document into a high-density HTML viewer.
    :param bejson_doc: The parsed BEJSON dictionary.
    :return: HTML string with tab-switching or multi-table layout.
    """
    fmt = bejson_doc.get("Format_Version", "104")
    record_types = bejson_doc.get("Records_Type", [])
    fields = bejson_doc.get("Fields", [])
    values = bejson_doc.get("Values", [])
    
    # 1. Map fields to record types
    # Index 0 of 104db is always Record_Type_Parent
    rt_idx = -1
    for i, f in enumerate(fields):
        if f.get("name") == "Record_Type_Parent":
            rt_idx = i
            break
            
    # 2. Build sections for each record type
    tabs = []
    tab_contents = []
    
    for i, rt in enumerate(record_types):
        # Filter relevant fields for this RT
        rt_headers = []
        rt_field_indices = []
        
        for j, f in enumerate(fields):
            fname = f.get("name")
            fparent = f.get("Record_Type_Parent")
            
            # Skip Record_Type_Parent in the viewer table itself (per user request)
            if fname == "Record_Type_Parent": continue
            
            # Common fields or specific to this RT
            if not fparent or fparent == rt:
                rt_headers.append(fname)
                rt_field_indices.append(j)
        
        # Filter records for this RT
        rt_rows = []
        for row in values:
            if rt_idx >= 0:
                if row[rt_idx] == rt:
                    rt_rows.append([row[idx] for idx in rt_field_indices])
            else:
                # 104/104a mode - all records belong to the first RT
                if i == 0:
                    rt_rows.append([row[idx] for idx in rt_field_indices])

        # Generate Table HTML
        if rt_rows:
            table_html = html_brutal_table(rt_headers, rt_rows)
        else:
            table_html = "<p style='color:var(--text-muted); padding:20px;'>No records found for this type.</p>"
            
        tab_id = f"tab_{rt.lower().replace(' ', '_')}"
        tabs.append({"label": rt, "id": tab_id, "active": (i == 0)})
        tab_contents.append(html_tab_content(tab_id, table_html, active=(i == 0)))

    # 3. Final Assembly
    # If multiple record types, use tabs. If one, just the card.
    if len(record_types) > 1:
        switcher = html_subtabs(tabs)
        content_stack = "".join(tab_contents)
        return f"{switcher}<div class='b-card' style='margin-top:-2px;'>{content_stack}</div>"
    else:
        # Single type - simple card
        title = record_types[0] if record_types else "RECORDS"
        return html_brutal_card(title, tab_contents[0] if tab_contents else "")

def bejson_schema_viewer(bejson_doc):
    """
    Standard viewer specifically for the Schema definition (Fields).
    """
    fields = bejson_doc.get("Fields", [])
    headers = ["Name", "Type", "Scope"]
    rows = []
    for f in fields:
        rows.append([
            f.get("name", "?"),
            f.get("type", "string"),
            f.get("Record_Type_Parent", "COMMON")
        ])
    
    return html_brutal_card("SCHEMA DEFINITION", html_brutal_table(headers, rows))

