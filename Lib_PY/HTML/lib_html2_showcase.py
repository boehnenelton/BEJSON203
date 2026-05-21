"""
Library:      lib_html2_showcase.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Debugged and standardized library component.
"""

import html as html_mod

BENTO_STYLE = """
<style>
.bento-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    grid-auto-rows: 200px;
    gap: 15px;
    padding: 15px;
    width: 100%;
}

.bento-item {
    background: #fff;
    border: 1px solid #E1E1E1;
    padding: 20px;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.bento-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.bento-item--w2 { grid-column: span 2; }
.bento-item--w3 { grid-column: span 2; grid-row: span 2; }

.bento-item__label {
    font-family: 'Source Code Pro', monospace;
    font-size: 11px;
    color: #DE2626;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.bento-item__value {
    font-family: 'Inter', sans-serif;
    font-size: 24px;
    font-weight: bold;
    color: #111;
}

.bento-item--w3 .bento-item__value {
    font-size: 48px;
}
</style>
"""

def html_bento_grid(bejson_doc):
    """
    Transforms a BEJSON doc into a Bento Grid.
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
        if weight >= 3: span_class = " bento-item--w3"
        elif weight == 2: span_class = " bento-item--w2"
        
        items_html += f'''
        <div class="bento-item{span_class}">
            <div class="bento-item__label">{label}</div>
            <div class="bento-item__value">{value}</div>
        </div>'''
        
    return f'<section class="bento-grid">{BENTO_STYLE}{items_html}</section>'

