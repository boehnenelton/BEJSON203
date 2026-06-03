"""
Library:      lib_html3_showcase.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      3.0.0 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-29
Description:  BECSS-compliant showcase components and grids.
"""

import html as html_mod

VERSION = "3.0.0"
SCRIPT_NAME = "lib_html3_showcase.py"
RELATIONAL_ID = "88804025-c258-4f77-8406-badb4fe6b21b"

def html_bento_grid(bejson_doc):
    """
    Transforms a BEJSON doc into a BECSS Bento Grid.
    Expects 'label', 'value', and optional 'weight' fields.
    """
    if not isinstance(bejson_doc, dict):
        return ""

    fields = bejson_doc.get("Fields", [])
    values = bejson_doc.get("Values", [])
    
    if not isinstance(fields, list) or not isinstance(values, list):
        return ""

    # Map field indices
    fi = {f["name"]: i for i, f in enumerate(fields) if isinstance(f, dict) and "name" in f}
    
    def safe_get(r, key, default=""):
        idx = fi.get(key)
        if idx is not None and idx < len(r):
            val = r[idx]
            return val if val is not None else default
        return default

    def safe_int(val, default=1):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    items_html = ""
    for row in values:
        if not isinstance(row, list):
            continue

        label = html_mod.escape(str(safe_get(row, "label", "ITEM")))
        value = html_mod.escape(str(safe_get(row, "value", "")))
        weight = safe_int(safe_get(row, "weight", 1))
        
        span_class = ""
        if weight >= 3: span_class = " c-bento-item--w3"
        elif weight == 2: span_class = " c-bento-item--w2"
        
        items_html += f'''
        <div class="c-bento-item{span_class}">
            <div class="c-bento-item__label">{label}</div>
            <div class="c-bento-item__value">{value}</div>
        </div>'''
        
    return f'<section class="c-bento-grid">{items_html}</section>'
