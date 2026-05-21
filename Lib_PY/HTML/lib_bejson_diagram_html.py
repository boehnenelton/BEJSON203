"""
Library:      lib_bejson_diagram_html.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Visualizer for BEJSON relational structures using high-contrast HTML diagrams.
"""

import json
import os
from datetime import datetime

CYBERPUNK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}} · BEJSON 104db</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
{{EXTERNAL_CSS}}
<style>
  {{INTERNAL_CSS}}
</style>
</head>
<body>
<div class="page">
  <header class="title-bar">
    <div class="title-left">
      <span class="schema-tag">BEJSON · 104db · {{MODE}} VIEW</span>
      <h1>{{TITLE}}</h1>
      <p class="subtitle">{{SUBTITLE}}</p>
    </div>
  </header>

  <div class="diagram-wrapper">
    <svg id="diagram-svg" viewBox="0 0 1440 720" preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="dots" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="1" fill="rgba(30,80,160,0.25)"/>
        </pattern>
        <filter id="glow-primary" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="5" result="blur"/>
          <feFlood flood-color="{{ACCENT_COLOR}}" flood-opacity="0.5" result="c"/>
          <feComposite in="c" in2="blur" operator="in" result="shadow"/>
          <feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="line-glow" x="-30%" y="-200%" width="160%" height="500%">
          <feGaussianBlur stdDeviation="2" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width="100%" height="100%" fill="{{BG_COLOR}}"/>
      <rect width="100%" height="100%" fill="url(#dots)"/>
      <g id="connectors-layer"></g>
      <g id="nodes-layer"></g>
    </svg>
    <div id="tooltip" class="hidden">
      <div class="tt-title" id="tt-title"></div>
      <div id="tt-body"></div>
    </div>
  </div>

  <footer class="meta-bar">
    <span>Format: BEJSON</span>
    <span>Version: 2.0.1 OFFICIAL</span>
    <span>Exported: {{TIMESTAMP}}</span>
  </footer>
</div>

<script id="bejson-data" type="application/json">
{{DIAGRAM_DATA}}
</script>

<script>
/* ── Renderer ────────────────────────────────────────────────────────── */
const THEME = {
    accent: "{{ACCENT_COLOR}}",
    bg: "{{BG_COLOR}}"
};

function render() {
  const dataEl = document.getElementById("bejson-data");
  if (!dataEl) return;
  const bejson = JSON.parse(dataEl.textContent);
  const fields = bejson.Fields;
  const fi = {};
  fields.forEach((f, i) => fi[f.name] = i);

  const shapes = bejson.Values
    .filter(r => r[fi["Record_Type_Parent"]] === "Shape")
    .map(r => ({
      id: r[fi["id_Shape"]] || r[fi["s_id"]],
      label: r[fi["label_Shape"]] || r[fi["s_label"]],
      text: r[fi["text_Shape"]] || r[fi["s_sublabel"]] || "",
      x: r[fi["x_Shape"]] || r[fi["s_x"]] || 0,
      y: r[fi["y_Shape"]] || r[fi["s_y"]] || 0,
      w: r[fi["w_Shape"]] || 150,
      h: r[fi["h_Shape"]] || 60,
      color: r[fi["color_Shape"]] || r[fi["s_color"]] || THEME.accent
    }));

  const connectors = bejson.Values
    .filter(r => r[fi["Record_Type_Parent"]] === "Connector")
    .map(r => ({
      from: r[fi["from_Connector"]] || r[fi["c_from"]],
      to: r[fi["to_Connector"]] || r[fi["c_to"]],
      label: r[fi["label_Connector"]] || r[fi["c_label"]] || ""
    }));

  const shapeMap = Object.fromEntries(shapes.map(s => [s.id, s]));
  const connLayer = document.getElementById("connectors-layer");
  const nodeLayer = document.getElementById("nodes-layer");

  connectors.forEach(conn => {
    const from = shapeMap[conn.from];
    const to = shapeMap[conn.to];
    if (!from || !to) return;
    
    const d = `M ${from.x + from.w} ${from.y + from.h/2} C ${from.x + from.w + 50} ${from.y + from.h/2}, ${to.x - 50} ${to.y + to.h/2}, ${to.x} ${to.y + to.h/2}`;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", from.color);
    path.setAttribute("class", "conn-path");
    path.setAttribute("filter", "url(#line-glow)");
    connLayer.appendChild(path);
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
</html>
"""

DEFAULT_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg: #050b17; --accent: #DE2626; --text: #e2e8f0; --muted: #64748b; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg); }
  .page { display: flex; flex-direction: column; height: 100vh; font-family: 'JetBrains Mono', monospace; color: var(--text); }
  .title-bar { padding: 14px 28px; background: rgba(5,11,23,0.9); border-bottom: 1px solid rgba(222,38,38,0.2); backdrop-filter: blur(8px); }
  h1 { font-family: 'Orbitron', sans-serif; font-size: 20px; letter-spacing: 2px; }
  .diagram-wrapper { flex: 1; position: relative; overflow: hidden; }
  #diagram-svg { width: 100%; height: 100%; }
  .conn-path { stroke-dasharray: 5 4; animation: flow 2s linear infinite; }
  @keyframes flow { from { stroke-dashoffset: 20; } to { stroke-dashoffset: 0; } }
  .meta-bar { padding: 8px 28px; background: #050b17; font-size: 10px; color: var(--muted); display: flex; gap: 20px; }
"""

def export_high_fidelity_diagram(json_data, output_path, title="System Diagram", css_sheets=None):
    """
    Exports a BEJSON 104db diagram as a high-fidelity HTML file.
    :param css_sheets: List of paths or URLs to external CSS files.
    """
    ext_css_html = ""
    if css_sheets:
        for sheet in css_sheets:
            ext_css_html += f'<link rel="stylesheet" href="{sheet}">\\n'
            
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = CYBERPUNK_TEMPLATE.replace("{{TITLE}}", title) \
                             .replace("{{SUBTITLE}}", "Relational logic map generated via BEJSON 104db") \
                             .replace("{{MODE}}", "HIGH-FIDELITY") \
                             .replace("{{ACCENT_COLOR}}", "#DE2626") \
                             .replace("{{BG_COLOR}}", "#050b17") \
                             .replace("{{INTERNAL_CSS}}", DEFAULT_CSS) \
                             .replace("{{EXTERNAL_CSS}}", ext_css_html) \
                             .replace("{{TIMESTAMP}}", timestamp) \
                             .replace("{{DIAGRAM_DATA}}", json.dumps(json_data, indent=2))
                             
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return True
