"""
Library:      lib_bejson_validator_diagram.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Structural integrity checker for positional values and mandatory keys.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import lib_bejson_validator as CoreValidator

E_DIAGRAM_RELATIONAL_ERROR = 100
E_DIAGRAM_INVALID_ANCHOR = 101

# --- High-Fidelity Cyberpunk Template ---
HI_FI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}} · BEJSON 104db</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
{{EXTERNAL_CSS}}
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg: #050b17; --accent: {{ACCENT}}; --text: #e2e8f0; --muted: #64748b; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg); }
  .page { display: flex; flex-direction: column; height: 100vh; font-family: 'JetBrains Mono', monospace; color: var(--text); }
  .title-bar { padding: 14px 28px; background: rgba(5,11,23,0.9); border-bottom: 1px solid rgba(167,139,250,0.2); backdrop-filter: blur(8px); }
  .schema-tag { font-size: 10px; letter-spacing: 3px; color: var(--violet); opacity: 0.7; }
  h1 { font-family: 'Orbitron', sans-serif; font-size: 20px; font-weight: 900; letter-spacing: 2px; color: #fff; }
  .diagram-wrapper { flex: 1; position: relative; overflow: auto; background: var(--bg); display: flex; align-items: center; justify-content: center; }
  #diagram-svg { width: 100%; height: 100%; max-width: 100%; max-height: 100%; }
  .conn-path { stroke-dasharray: 5 4; animation: flow 2s linear infinite; }
  @keyframes flow { from { stroke-dashoffset: 20; } to { stroke-dashoffset: 0; } }
  .meta-bar { padding: 8px 28px; background: #050b17; font-size: 9px; color: var(--muted); display: flex; gap: 20px; }
  {{INTERNAL_CSS}}
</style>
</head>
<body>
<div class="page">
  <header class="title-bar">
    <div class="title-left">
      <span class="schema-tag">BEJSON · 104db · DIAGRAM VIEW</span>
      <h1>{{TITLE}}</h1>
    </div>
  </header>
  <div class="diagram-wrapper">
    <svg id="diagram-svg" viewBox="{{VIEWBOX}}" preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="dots" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="rgba(30,80,160,0.25)"/></pattern>
        <filter id="glow-primary" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="5" result="blur"/><feFlood flood-color="{{ACCENT}}" flood-opacity="0.5" result="c"/>
          <feComposite in="c" in2="blur" operator="in" result="shadow"/><feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="line-glow" x="-30%" y="-200%" width="160%" height="500%"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect width="100%" height="100%" fill="var(--bg)"/><rect width="100%" height="100%" fill="url(#dots)"/>
      <g id="connectors-layer"></g><g id="nodes-layer"></g>
    </svg>
  </div>
  <span>Version: 2.0.1 OFFICIAL</span>
</div>
<script id="bejson-data" type="application/json">{{DIAGRAM_DATA}}</script>
<script>
const THEME = { accent: "{{ACCENT}}" };
function render() {
  const dataEl = document.getElementById("bejson-data");
  if (!dataEl) return;
  const bejson = JSON.parse(dataEl.textContent);
  const fields = bejson.Fields;
  const fi = {}; fields.forEach((f, i) => fi[f.name] = i);
  const shapes = bejson.Values.filter(r => r[fi["Record_Type_Parent"]] === "Shape").map(r => ({
    id: r[fi["id_Shape"]] || r[fi["s_id"]] || r[fi["id"]], 
    label: r[fi["label_Shape"]] || r[fi["s_label"]] || r[fi["label"]],
    x: r[fi["x_Shape"]] || r[fi["s_x"]] || r[fi["x"]] || 0, 
    y: r[fi["y_Shape"]] || r[fi["s_y"]] || r[fi["y"]] || 0,
    w: r[fi["w_Shape"]] || r[fi["w"]] || 150, 
    h: r[fi["h_Shape"]] || r[fi["h"]] || 60, 
    color: r[fi["color_Shape"]] || r[fi["s_color"]] || r[fi["color"]] || THEME.accent
  }));
  const connectors = bejson.Values.filter(r => r[fi["Record_Type_Parent"]] === "Connector").map(r => ({
    from: r[fi["from_Connector"]] || r[fi["c_from"]] || r[fi["from"]], 
    to: r[fi["to_Connector"]] || r[fi["c_to"]] || r[fi["to"]]
  }));
  const shapeMap = Object.fromEntries(shapes.map(s => [s.id, s]));
  const connLayer = document.getElementById("connectors-layer"), nodeLayer = document.getElementById("nodes-layer");
  connectors.forEach(conn => {
    const from = shapeMap[conn.from], to = shapeMap[conn.to];
    if (!from || !to) return;
    const d = `M ${from.x + from.w} ${from.y + from.h/2} C ${from.x + from.w + 50} ${from.y + from.h/2}, ${to.x - 50} ${to.y + to.h/2}, ${to.x} ${to.y + to.h/2}`;
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", from.color); p.setAttribute("class", "conn-path"); p.setAttribute("filter", "url(#line-glow)");
    connLayer.appendChild(p);
  });
  shapes.forEach(s => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${s.x},${s.y})`);
    g.innerHTML = `<rect width="${s.w}" height="${s.h}" rx="8" fill="rgba(0,0,0,0.4)" stroke="${s.color}" stroke-width="2" filter="url(#glow-primary)" />
                   <text x="${s.w/2}" y="${s.h/2 + 5}" text-anchor="middle" fill="${s.color}" font-family="Orbitron" font-size="12">${s.label}</text>`;
    nodeLayer.appendChild(g);
  });
}
document.addEventListener("DOMContentLoaded", render);
</script>
</body>
</html>"""

def bejson_validator_diagram_validate_string(json_string):
    """Validates a BEJSON string as a valid Diagrammer structure."""
    CoreValidator.bejson_validator_validate_string(json_string)
    return True

def bejson_diagram_export_html(json_string, output_path, title="BEJSON Diagram", css_sheets=None, internal_css=""):
    """
    Generates a high-fidelity standalone HTML diagram viewer with dynamic viewBox.
    """
    ext_css_html = ""
    if css_sheets:
        for sheet in css_sheets:
            ext_css_html += f'<link rel="stylesheet" href="{sheet}">\\n'
            
    doc = json.loads(json_string)
    creator = doc.get("Format_Creator", "BEJSON Engine")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Dynamic ViewBox Calculation (v1.5.3 Robust)
    fields = doc["Fields"]
    fi = {}
    for i, f in enumerate(fields):
        key = f["name"] + "_" + f.get("Record_Type_Parent", "common")
        fi[key] = i
        
    shapes = [v for v in doc["Values"] if v[0] == "Shape"]
    
    if shapes:
        # Safer extraction using Record_Type_Parent qualified keys
        def get_val(r, name):
            idx = fi.get(f"{name}_Shape")
            if idx is None: idx = fi.get(f"{name}_common")
            return r[idx] if idx is not None and idx < len(r) else 0

        min_x = min(get_val(r, "x") or get_val(r, "s_x") for r in shapes)
        min_y = min(get_val(r, "y") or get_val(r, "s_y") for r in shapes)
        max_x = max((get_val(r, "x") or get_val(r, "s_x")) + (get_val(r, "w") or get_val(r, "s_w") or 150) for r in shapes)
        max_y = max((get_val(r, "y") or get_val(r, "s_y")) + (get_val(r, "h") or get_val(r, "s_h") or 60) for r in shapes)
        
        padding = 100
        viewbox = f"{min_x - padding} {min_y - padding} {max_x - min_x + padding*2} {max_y - min_y + padding*2}"
    else:
        viewbox = "0 0 1440 720"
    
    final_html = HI_FI_TEMPLATE.replace("{{TITLE}}", title) \
                               .replace("{{DIAGRAM_DATA}}", json_string.strip()) \
                               .replace("{{ACCENT}}", "#DE2626") \
                               .replace("{{CREATOR}}", creator) \
                               .replace("{{TIMESTAMP}}", timestamp) \
                               .replace("{{EXTERNAL_CSS}}", ext_css_html) \
                               .replace("{{INTERNAL_CSS}}", internal_css) \
                               .replace("{{VIEWBOX}}", viewbox)
                               
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    return True

def bejson_validator_diagram_validate_file(file_path):
    text = Path(file_path).read_text(encoding="utf-8")
    return bejson_validator_diagram_validate_string(text)
