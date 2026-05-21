"""
Library:      lib_html2_sidemenu.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Navigation and sidebar component manager for web apps.
"""

import html as html_mod

def _sidebar_html(nav_links, title="Menu"):
    """
    Build sidebar + overlay HTML based on v3.0 standards.
    Returns (top_bar, sidebar, overlay) tuple.
    """
    if not nav_links:
        return "", "", ""
        
    def safe_label(l):
        l_str = str(l)
        if "&" in l_str or "&#" in l_str or any(ord(c) > 127 for c in l_str):
            return l_str
        return html_mod.escape(l_str)

    links = "".join(f'<a href="{html_mod.escape(str(h))}">{safe_label(l)}</a>\n' for l, h in nav_links)
    
    top_bar = f"""<header class="top-bar" role="banner">
<button class="top-bar__toggle" onclick="document.querySelector('.sidebar').classList.toggle('open');document.querySelector('.sidebar-overlay').classList.toggle('open')" aria-label="Toggle navigation" aria-expanded="false">&#9776;</button>
<span class="top-bar__brand">{html_mod.escape(str(title))}</span>
</header>"""

    sidebar = f"""<nav class="sidebar" role="navigation" aria-label="Main navigation">{links}</nav>"""
    overlay = f"""<div class="sidebar-overlay" onclick="document.querySelector('.sidebar').classList.remove('open');document.querySelector('.sidebar-overlay').classList.remove('open')"></div>"""
    
    return top_bar, sidebar, overlay

def html_navbar(links, dark=False):
    """
    [DEPRECATED] Standalone navbar overlay. Use _sidebar_html for v3.0 compatibility.
    """
    link_html = "".join(f'<a href="{html_mod.escape(str(h))}">{html_mod.escape(str(l))}</a>\n' for l, h in links)
    return f"""<button class="top-bar__toggle" onclick="document.querySelector('.sidebar-overlay').classList.toggle('open')">&#9776;</button>
<div class="sidebar-overlay" onclick="if(event.target===this)this.classList.remove('open')">{link_html}</div>"""
