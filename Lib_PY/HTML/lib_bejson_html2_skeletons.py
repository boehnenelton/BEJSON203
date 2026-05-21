"""
Library:      lib_bejson_html2_skeletons.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Pre-defined HTML structure templates for rapid page generation.
"""

import html as html_mod
import json

# ═══════════════════════════════════════════════════════
# 1. AUTHORITATIVE CSS VARIABLES (Policy v6.0)
# ═══════════════════════════════════════════════════════

COLOR = {
    "primary":    "#DE2626",              # Authority Red
    "bg_dark":    "oklch(12% 0.01 250)",  # Deep Charcoal
    "bg_surface": "oklch(16% 0.01 250)",  # Sleek Surface
    "text_main":  "oklch(92% 0.01 250)",  # Near White
    "text_muted": "oklch(65% 0.01 250)",  # Refined Gray
    "border":     "oklch(22% 0.01 250)",  # Subtle Divider
    "font_base":  "'Inter', 'Roboto', system-ui, sans-serif",
    "font_mono":  "'Roboto Mono', 'Source Code Pro', monospace",
    "transition": "0.15s ease",
}

BRUTAL_COLOR = COLOR.copy()

# ═══════════════════════════════════════════════════════
# 2. CORE STYLESHEET
# ═══════════════════════════════════════════════════════

CSS_CORE = """
:root {{
    --primary: {primary};
    --bg-page: {bg_dark};
    --bg-surface: {bg_surface};
    --text-main: {text_main};
    --text-muted: {text_muted};
    --border: {border};
    --font-base: {font_base};
    --font-mono: {font_mono};
    --transition: {transition};
}}

/* Reset & Base */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ height: 100%; scroll-behavior: smooth; font-size: 16px; }}
body {{
    background-color: var(--bg-page);
    color: var(--text-main);
    font-family: var(--font-base);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    padding-top: 60px;
    padding-bottom: 80px;
}}

/* Typography */
h1 {{ 
    font-size: clamp(1.75rem, 4vw, 2.5rem); 
    font-weight: 800; 
    letter-spacing: -0.02em; 
    color: var(--text-main); 
    line-height: 1.1; 
    margin-bottom: 0.5rem;
    word-break: break-word;
    overflow-wrap: break-word;
}}
h2 {{ 
    font-size: 1.1rem; 
    font-weight: 800; 
    letter-spacing: -0.01em; 
    color: var(--primary); 
    text-transform: uppercase; 
    margin-bottom: 1rem;
    word-break: break-word;
    overflow-wrap: break-word;
}}
h3, h4 {{ 
    font-weight: 700; 
    color: var(--text-main);
    word-break: break-word;
    overflow-wrap: break-word;
}}

a {{ color: var(--primary); text-decoration: none; transition: var(--transition); }}
a:hover {{ opacity: 0.8; }}

/* Navigation */
.top-bar {{
    position: fixed; top: 0; left: 0; width: 100%; height: 60px;
    background: rgba(18, 18, 20, 0.9); backdrop-filter: blur(12px);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; z-index: 1000; border-bottom: 2px solid var(--primary);
}}
.top-bar__brand {{ font-family: var(--font-mono); font-weight: 700; font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; }}
.top-bar__brand span {{ color: var(--primary); }}

.sidebar {{
    position: fixed; top: 60px; left: -280px; width: 280px;
    height: calc(100vh - 60px); background-color: var(--bg-page);
    transition: var(--transition); z-index: 900; overflow-y: auto;
    padding: 20px 0; border-right: 1px solid var(--border);
}}
.sidebar--open {{ left: 0; }}
.sidebar__category {{
    padding: 12px 24px; font-size: 0.65rem; font-weight: 800;
    color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em;
    cursor: pointer; display: flex; justify-content: space-between;
}}
.sidebar__category:hover {{ color: var(--primary); }}
.sidebar__category-items {{ display: none; list-style: none; }}
.sidebar__category-items--open {{ display: block; }}

.sidebar__link {{
    display: block; padding: 10px 24px 10px 40px; color: var(--text-muted);
    font-size: 0.8rem; font-weight: 500;
    word-break: break-all;
}}
.sidebar__link:hover, .sidebar__link--active {{ color: var(--text-main); background: var(--bg-surface); }}
.sidebar__link--active {{ border-left: 4px solid var(--primary); color: var(--primary); }}

/* Layout Components */
.card, .b-card {{ background-color: var(--bg-surface); border-radius: 0; padding: 24px; margin-bottom: 24px; transition: var(--transition); }}
.table-container {{ overflow-x: auto; border-radius: 0; }}
.data-table, .b-table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; background: var(--bg-surface); }}
.data-table th, .b-table th {{ background: var(--primary); padding: 12px 16px; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: #FFFFFF; font-weight: 800; }}
.data-table td, .b-table td {{ padding: 12px 16px; border-top: 1px solid var(--border); word-break: break-word; }}
.data-table tr:hover {{ background: rgba(255,255,255,0.02); }}

pre {{ background: #000; color: #ADFF2F; padding: 20px; border-radius: 0; font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.5; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; border-left: 4px solid var(--primary); }}

/* FOOTER - Authoritative Info */
.status-footer, .footer {{
    position: fixed; bottom: 0; left: 0; width: 100%; height: 50px;
    background: var(--bg-surface); display: flex; align-items: center;
    justify-content: space-between; padding: 0 24px;
    font-size: 0.7rem; color: var(--text_muted); font-family: var(--font-mono);
    border-top: 1px solid var(--border); z-index: 1000;
}}
.footer-link {{ color: var(--text-muted); text-decoration: underline; }}
.footer-link:hover {{ color: var(--primary); }}

/* Square Buttons */
.form__button, .b-button {{ background: var(--primary); color: white; padding: 10px 20px; border-radius: 0; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; cursor: pointer; border: none; transition: var(--transition); }}
.form__button:hover, .b-button:hover {{ background: #B91C1C; }}

/* Responsive */
@media (min-width: 1024px) {{
    .sidebar {{ left: 0; }}
    .main-content {{ margin-left: 280px; }}
    .top-bar__toggle {{ display: none; }}
}}
"""

CSS_BRUTAL = CSS_CORE

# ═══════════════════════════════════════════════════════
# 3. HTML STRUCTURE
# ═══════════════════════════════════════════════════════

HTML_SKELETON = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>{{css}}</style>
</head>
<body>
    <header class="top-bar">
        <div class="top-bar__brand">BEJSON <span>LIBRARIES</span></div>
        <button class="top-bar__toggle" aria-label="Toggle Menu" style="background:transparent; border:none; color:white; font-size:1.5rem; cursor:pointer;">&#9776;</button>
    </header>

    <nav class="sidebar">
        <ul style="list-style:none;">
            {{nav_items}}
        </ul>
    </nav>
    <div id="overlay" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:850;"></div>

    <main class="main-content">
        <div style="font-size: 0.65rem; color: var(--text-muted); margin-bottom: 20px; font-family: var(--font-mono); text-transform: uppercase;">{{breadcrumbs}}</div>
        {{content}}
    </main>

    <footer class="status-footer">
        <div>SYSTEM // <span>ONLINE</span></div>
        <div>{{status_extra}}</div>
        <div style="text-align: right;">
            <a href="https://github.com/boehnenelton" class="footer-link">GITHUB</a> | 
            <a href="https://boehnenelton2024.pages.dev" class="footer-link">PORTFOLIO</a> | 
            <span>ELTON BOEHNEN</span>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const toggle = document.querySelector('.top-bar__toggle');
            const sidebar = document.querySelector('.sidebar');
            const overlay = document.getElementById('overlay');
            
            if (toggle && sidebar) {{
                toggle.addEventListener('click', () => {{
                    const open = sidebar.classList.toggle('sidebar--open');
                    overlay.style.display = open ? 'block' : 'none';
                }});
                overlay.addEventListener('click', () => {{
                    sidebar.classList.remove('sidebar--open');
                    overlay.style.display = 'none';
                }});
            }}

            document.querySelectorAll('.sidebar__category').forEach(cat => {{
                cat.addEventListener('click', () => {{
                    const items = cat.nextElementSibling;
                    if (items && items.classList.contains('sidebar__category-items')) {{
                        const isOpen = items.classList.toggle('sidebar__category-items--open');
                        const arrow = cat.querySelector('.cat-arrow');
                        if (arrow) arrow.textContent = isOpen ? '▼' : '▶';
                    }}
                }});
            }});

            window.switchSubTab = (tabId) => {{
                document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
                document.querySelectorAll(".subtabs__btn").forEach(b => {{
                   b.style.background = "transparent";
                   b.style.color = "var(--text-muted)";
                }});
                const target = document.getElementById(tabId);
                if (target) target.style.display = "block";
            }};
        }});
    </script>
</body>
</html>"""

HTML_SKELETON_BRUTAL = HTML_SKELETON

