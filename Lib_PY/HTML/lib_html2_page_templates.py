"""
Library:      lib_html2_page_templates.py
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
import os
import json
import re
from datetime import datetime

# Import skeletons
from lib_bejson_html2_skeletons import (
    COLOR, CSS_CORE, HTML_SKELETON,
    BRUTAL_COLOR, CSS_BRUTAL, HTML_SKELETON_BRUTAL
)

# ═══════════════════════════════════════════════════════
# 1. CORE PAGE GENERATION
# ═══════════════════════════════════════════════════════

def _is_active(url, active_url):
    """Strictly matches relative URLs for active highlighting."""
    if not active_url: return False
    u = url.strip().rstrip("/")
    a = active_url.strip().rstrip("/")
    if u.startswith("./"): u = u[2:]
    if a.startswith("./"): a = a[2:]
    return u == a

def html_page(title, content, nav_links=None, status_extra="", active_url="", breadcrumbs_html=""): 
    """Standard Dashboard Page."""
    css = CSS_CORE.format(**COLOR)
    nav_html = ""
    if nav_links:
        any_active = False
        for cat in nav_links:
            for item in cat.get("items", []):
                if _is_active(item.get("url", "#"), active_url):
                    any_active = True
                    break
            if any_active: break

        for i, cat in enumerate(nav_links):
            cat_name = cat.get("category", "General")
            is_active_cat = False
            for item in cat.get("items", []):
                if _is_active(item.get("url", "#"), active_url):
                    is_active_cat = True
                    break
            is_open = is_active_cat or (not any_active and i == 0)
            cat_open_class = " sidebar__category-items--open" if is_open else ""
            arrow = "▼" if is_open else "▶"
            nav_html += '<li>\n'
            nav_html += f'  <div class="sidebar__category">{html_mod.escape(cat_name)} <span class="cat-arrow">{arrow}</span></div>\n'
            nav_html += f'  <ul class="sidebar__category-items{cat_open_class}">\n'
            for item in cat.get("items", []):
                label = html_mod.escape(item.get("label", "Link"))
                url = item.get("url", "#")
                active_class = " sidebar__link--active" if _is_active(url, active_url) else ""
                nav_html += f'    <li><a href="{url}" class="sidebar__link{active_class}">> {label}</a></li>\n'
            nav_html += '  </ul>\n'
            nav_html += '</li>\n'
    else:
        nav_html = '<li><div class="sidebar__category">Navigation <span class="cat-arrow">▶</span></div>'
        nav_html += '<ul class="sidebar__category-items"><li><a href="#" class="sidebar__link">> No Links</a></li></ul></li>'

    return HTML_SKELETON.replace("{{title}}", html_mod.escape(title)) \
                       .replace("{{css}}", css) \
                       .replace("{{nav_items}}", nav_html) \
                       .replace("{{content}}", content).replace("{{breadcrumbs}}", breadcrumbs_html or "") \
                       .replace("{{status_extra}}", html_mod.escape(status_extra))

def html_page_brutal(title, content, status_extra="", bg_oklch=None):
    """Generate a Data-Dense Brutalist page."""
    local_colors = BRUTAL_COLOR.copy()
    if bg_oklch:
        local_colors["bg_page"] = bg_oklch
    
    css = CSS_BRUTAL.format(**local_colors)
    return HTML_SKELETON_BRUTAL.replace("{{title}}", html_mod.escape(title)) \
                              .replace("{{css}}", css) \
                              .replace("{{content}}", content) \
                              .replace("{{status_extra}}", html_mod.escape(status_extra))

def html_save(content, path):
    """Unified save function for generated HTML."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
