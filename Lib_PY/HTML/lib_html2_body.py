"""
Library:      lib_html2_body.py
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

def html_stats_bar(stats_list):
    if not stats_list: return ""
    items = ""
    for s in stats_list:
        label = html_mod.escape(str(s.get("label", "")))
        value = html_mod.escape(str(s.get("value", "")))
        items += f"""
        <div style="flex:1;">
            <div style="font-size: 0.65rem; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">{label}</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: var(--primary);">{value}</div>
        </div>"""
    return f'<div style="display:flex; gap:24px; padding:24px; background:var(--bg-surface); margin-bottom:24px; border-left: 4px solid var(--primary);">{items}</div>'

def html_card(title, body):
    return f"""
    <div class="card">
        <h2 class="card__title">{html_mod.escape(title)}</h2>
        <div style="font-size:0.95rem; color:var(--text-main);">{body}</div>
    </div>"""

def html_brutal_card(title, content):
    """Modernized Brutalist Card."""
    return f"""
    <div class="card">
        <div style="font-size: 0.7rem; font-weight: 800; color:var(--text-muted); font-family: var(--font-mono); margin-bottom: 12px; text-transform: uppercase;">{html_mod.escape(title.upper())}</div>
        <div>{content}</div>
    </div>"""

def html_brutal_table(headers, rows, escape=True):
    """High-Contrast Table."""
    h_html = "".join([f"<th>{html_mod.escape(h)}</th>" for h in headers])
    r_html = ""
    for row in rows:
        cells = []
        for v in row:
            val = str(v)
            if escape: val = html_mod.escape(val)
            cells.append(f"<td>{val}</td>")
        r_html += "<tr>" + "".join(cells) + "</tr>"
    return f'<div class="table-container"><table class="data-table"><thead><tr>{h_html}</tr></thead><tbody>{r_html}</tbody></table></div>'

def html_subtabs(tabs):
    if not tabs: return ""
    items = ""
    for t in tabs:
        active_class = " background:var(--primary); color:white;" if t.get("active") else " color:var(--text-muted);"
        label = html_mod.escape(str(t.get("label", "")))
        tab_id = html_mod.escape(str(t.get("id", "")))
        items += f'<button class="subtabs__btn" style="border:none; padding:10px 20px; border-radius:0; font-weight:800; font-size:0.8rem; cursor:pointer; font-family:var(--font-base);{active_class}" onclick="switchSubTab(\'{tab_id}\'); this.parentElement.querySelectorAll(\'.subtabs__btn\').forEach(b => {{ b.style.background=\'transparent\'; b.style.color=\'var(--text-muted)\' }}); this.style.background=\'var(--primary)\'; this.style.color=\'white\';">{label}</button>\n'
    return f'<div style="display:flex; gap:0; margin-bottom:12px; border: 1px solid var(--border); width: fit-content;">{items}</div>'

def html_tab_content(tab_id, content, active=False):
    style = "display: block;" if active else "display: none;"
    return f'<div id="{html_mod.escape(tab_id)}" class="tab-content" style="{style}">{content}</div>'

def html_description_list(props):
    html_items = ""
    for p in props:
        term = html_mod.escape(p.get("term", ""))
        desc = html_mod.escape(p.get("description", ""))
        html_items += f"<div style='margin-bottom:12px; border-left: 2px solid var(--border); padding-left: 12px;'><dt style='font-size:0.65rem; font-family:var(--font-mono); color:var(--text-muted); text-transform:uppercase;'>{term}</dt><dd style='font-weight:700; font-size:1rem;'>{desc}</dd></div>"
    return f"<dl style='display:grid; grid-template-columns: 1fr 1fr; gap:16px;'>{html_items}</dl>"

def html_badge(text, variant=""):
    color = "var(--text-muted)"
    if variant == "success": color = "#ADFF2F"
    elif variant == "fail": color = "#FF4500"
    return f'<span style="font-family:var(--font-mono); font-size:0.65rem; font-weight:800; color:{color}; padding:2px 8px; background:rgba(255,255,255,0.05); border-radius:0;">{html_mod.escape(text.upper())}</span>'

def html_card_grid(content):
    return f'<div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:24px;">{content}</div>'

def html_code_box(title, content, copy_id=None):
    """
    Renders content in a terminal-style code box with a copy button.
    """
    import time
    if not copy_id:
        copy_id = f"code_{int(time.time() * 1000)}"
        
    return f"""
    <div style="background: #000; border-left: 4px solid var(--primary); margin: 24px 0; position: relative;">
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--primary); font-weight: 800; text-transform: uppercase;">
                FILE // {html_mod.escape(title)}
            </div>
            <button onclick="copyToClipboard('{copy_id}')" style="background: var(--primary); color: white; border: none; padding: 4px 12px; font-size: 0.65rem; font-weight: 800; cursor: pointer; text-transform: uppercase;">
                Copy
            </button>
        </div>
        <pre id="{copy_id}" style="margin: 0; padding: 20px; color: #ADFF2F; font-family: var(--font-mono); font-size: 0.85rem; border: none; border-left: none;"><code>{html_mod.escape(content)}</code></pre>
    </div>
    <script>
        if (typeof copyToClipboard !== 'function') {{
            window.copyToClipboard = (id) => {{
                const el = document.getElementById(id);
                const text = el.innerText;
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = event.target;
                    const oldText = btn.innerText;
                    btn.innerText = 'Copied!';
                    setTimeout(() => btn.innerText = oldText, 2000);
                }});
            }};
        }}
    </script>
    """
