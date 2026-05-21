"""
Library:      lib_html2_feed_templates.py
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

# Import siblings
from lib_bejson_html2_skeletons import (
    COLOR, CSS_CORE, HTML_SKELETON
)
from lib_html2_sidemenu import _sidebar_html

def html_card_grid(cards, title="Cards", nav_links=None, dark=False):
    """Generate a card grid page with BEM v3.0 classes."""
    cards_html = '<section class="card-grid" role="region" aria-label="Card grid">\n'
    for c in cards:
        href = html_mod.escape(str(c.get("href", "#")))
        t = html_mod.escape(str(c.get("title", "")))
        sub = html_mod.escape(str(c.get("subtitle", "")))
        count = c.get("count")
        
        # Build card content using BEM-like structure within .card
        count_html = f'<div class="card__count">{count} items</div>' if count else ""
        sub_html = f'<div class="card__subtitle">{sub}</div>' if sub else ''
        
        cards_html += f"""<article class="card">
    <h3 class="card__title"><a href="{href}">{t}</a></h3>
    {sub_html}
    {count_html}
</article>\n"""
    cards_html += '</section>'
    
    if nav_links is not None:
        # Wrap in full page if nav_links provided
        header_html = f'<header class="page-header"><h1>{html_mod.escape(title)}</h1></header>'
        from lib_html2_page_templates import html_page
        return html_page(title, header_html + cards_html, nav_links=nav_links, dark=dark)
        
    return cards_html

def html_feed(entries, title="Feed", nav_links=None, dark=False,
              site_url="https://boehnenelton2024.pages.dev"):
    """Generate an RSS-style feed page."""
    items = ""
    for e in entries:
        t = html_mod.escape(str(e.get("title", "")))
        link = html_mod.escape(str(e.get("link", "#")))
        date = html_mod.escape(str(e.get("date", "")))
        author = html_mod.escape(str(e.get("author", "")))
        body = e.get("body", "") # HTML body
        tags = e.get("tags", [])
        tag_html = ""
        if tags:
            tag_html = '<div class="feed-item__tags">' + " ".join(
                f'<span class="feed-tag">{html_mod.escape(str(tg))}</span>'
                for tg in tags) + '</div>'

        items += f"""<div class="feed-item">
    <h3 class="feed-item__title"><a href="{link}">{t}</a></h3>
    <div class="feed-meta">{date} &middot; {author}</div>
    <div class="feed-body">{body}</div>
    {tag_html}
</div>\n"""
    
    feed_body = f'<header class="page-header"><h1>{html_mod.escape(title)}</h1></header><section class="feed">{items}</section>'
    
    if nav_links is not None:
        from lib_html2_page_templates import html_page
        return html_page(title, feed_body, nav_links=nav_links, dark=dark, site_url=site_url)
        
    return feed_body
