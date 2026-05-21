"""
Library:      lib_html2_widgets.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Reusable UI micro-components for dashboards.
"""

import html as html_mod
import os
import json
import re
from pathlib import Path

# Widget Size Standards (Fixed Grid PX)
W_SMALL = (220, 200)
W_MEDIUM = (580, 300)
W_LARGE = (1180, 400)

def html_widget(content, title="WIDGET", size="small", container_id=None):
    """
    Standardizes a self-contained, injectable widget with fixed dimensions.
    Sizes: 'small', 'medium', 'large'
    """
    cid = container_id or f"widget_{id(content)}"
    
    if size == "large": width, height = W_LARGE
    elif size == "medium": width, height = W_MEDIUM
    else: width, height = W_SMALL # Default small/sidebar
    
    return f"""
    <div id="{cid}" class="bejson-widget" style="width: {width}px; height: {height}px; min-width: {width}px; min-height: {height}px;">
        <div class="bejson-widget__header">
            <span>{html_mod.escape(title)}</span>
            <span style="opacity: 0.5;">[{size.upper()}]</span>
        </div>
        <div class="bejson-widget__body">
            {content}
        </div>
    </div>
    """

def html_gallery(dir_path, recursive=False, container_id=None):
    """Generate an image gallery widget using .gallery-grid BEM classes."""
    cid = container_id or f"gallery_{id(dir_path)}"
    path = Path(dir_path)
    if not path.exists(): return f"<div>Error: {dir_path} not found</div>"
    
    extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
    pattern = "**/*" if recursive else "*"
    items = ""
    for img in sorted(path.glob(pattern)):
        if img.suffix.lower() in extensions:
            items += f"""
            <div class="gallery-item">
                <a href="{img}" target="_blank">
                    <img src="{img}" alt="{img.name}" loading="lazy">
                </a>
                <div class="gallery-item__label">{img.name}</div>
            </div>"""
            
    return f'<div id="{cid}" class="gallery-grid">{items}</div>'

def html_video_grid(videos, container_id=None):
    """Generate a responsive grid of embedded videos using .video-grid BEM classes."""
    cid = container_id or f"vgrid_{id(videos)}"
    items = ""
    for vid in videos:
        url = vid.get('url', '')
        title = vid.get('title', 'Video')
        
        embed_url = url
        if "youtube.com/watch" in url:
            vid_id = re.search(r'v=([^&]+)', url)
            if vid_id: embed_url = f"https://www.youtube.com/embed/{vid_id.group(1)}"
        elif "youtu.be/" in url:
            vid_id = url.split("youtu.be/")[1]
            embed_url = f"https://www.youtube.com/embed/{vid_id}"

        items += f"""
        <div class="video-card">
            <div class="video-card__header">{html_mod.escape(title)}</div>
            <div class="video-card__embed">
                <iframe src="{embed_url}" allowfullscreen loading="lazy"></iframe>
            </div>
        </div>"""

    return f'<div id="{cid}" class="video-grid">{items}</div>'

def html_info_box(title, content, link_url=None, link_label="View More", container_id=None, escape_content=False):
    """Generate a stylized info box using .info-box BEM classes."""
    cid = container_id or f"infobox_{id(title)}"
    link_html = f"""<a href="{link_url}" class="info-box__link">{link_label}</a>""" if link_url else ""

    display_content = html_mod.escape(content) if escape_content else content

    return f"""
    <div id="{cid}" class="info-box">
        <h3 class="info-box__title">
            <span class="info-box__dot"></span>
            {html_mod.escape(title)}
        </h3>
        <div class="info-box__content">{display_content}</div>
        {link_html}
    </div>
    """

def html_standalone_widget(html_content, title="Widget", container_id=None):
    """Wraps standalone HTML into an isolated iframe. Sandbox restricted for security."""
    cid = container_id or f"standalone_widget_{id(title)}"
    escaped_content = html_mod.escape(html_content, quote=True)

    return f"""
    <div id="{cid}" class="standalone-widget-container" style="width: 100%; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; background: #000;">
        <div class="widget-header" style="background: #111; padding: 10px 15px; border-bottom: 1px solid var(--border-color); font-family: var(--font-family-mono); font-size: 12px; color: var(--text-color); display: flex; justify-content: space-between; align-items: center;">
            <span style="color: var(--primary-color); font-weight: bold;">{html_mod.escape(title)}</span>
            <span style="color: #666;">Isolated Component</span>
        </div>
        <iframe srcdoc="{escaped_content}" style="width: 100%; height: 600px; border: none; display: block;" sandbox="allow-scripts"></iframe>
    </div>
    """
def html_lightbox():
    """Returns the CSS/JS for a global lightbox system."""
    return """
    <div id="bejson-lightbox" class="lightbox" onclick="this.style.display='none'">
        <span class="lightbox__close">&times;</span>
        <img class="lightbox__content" id="lightbox-img">
        <div id="lightbox-caption" class="lightbox__caption"></div>
    </div>
    <style>
    .lightbox { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); }
    .lightbox__content { margin: auto; display: block; width: 80%; max-width: 1200px; max-height: 80%; margin-top: 5%; object-fit: contain; }
    .lightbox__caption { margin: auto; display: block; width: 80%; text-align: center; color: #ccc; padding: 10px 0; font-family: var(--font-mono); }
    .lightbox__close { position: absolute; top: 15px; right: 35px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }
    </style>
    <script>
    function openLightbox(src, caption) {
        document.getElementById('bejson-lightbox').style.display = 'block';
        document.getElementById('lightbox-img').src = src;
        document.getElementById('lightbox-caption').innerHTML = caption;
    }
    </script>
    """

def html_carousel(items, container_id=None):
    """Generate a horizontal carousel/rotator."""
    cid = container_id or f"carousel_{id(items)}"
    slides = ""
    for i, item in enumerate(items):
        slides += f'<div class="carousel__slide"> {item} </div>'
        
    return f"""
    <div id="{cid}" class="carousel">
        <div class="carousel__track">{slides}</div>
        <div class="carousel__controls">
            <button class="carousel__btn" onclick="moveCarousel('{cid}', -1)">&lt; PREV</button>
            <button class="carousel__btn" onclick="moveCarousel('{cid}', 1)">NEXT &gt;</button>
        </div>
    </div>
    <style>
    .carousel {{ position: relative; overflow: hidden; width: 100%; border: 1px solid var(--border); background: var(--bg-surface); }}
    .carousel__track {{ display: flex; transition: transform 0.3s ease; }}
    .carousel__slide {{ min-width: 100%; padding: 20px; box-sizing: border-box; }}
    .carousel__controls {{ display: flex; justify-content: space-between; padding: 10px; background: rgba(0,0,0,0.05); }}
    .carousel__btn {{ background: none; border: 1px solid var(--primary-red); color: var(--primary-red); font-family: var(--font-mono); padding: 5px 10px; cursor: pointer; }}
    </style>
    <script>
    if(!window.carouselPos) window.carouselPos = {{}};
    function moveCarousel(id, dir) {{
        const track = document.getElementById(id).querySelector('.carousel__track');
        const count = track.children.length;
        if(!window.carouselPos[id]) window.carouselPos[id] = 0;
        window.carouselPos[id] = (window.carouselPos[id] + dir + count) % count;
        track.style.transform = `translateX(-${{window.carouselPos[id] * 100}}%)`;
    }}
    </script>
    """

def html_code_block(code, title="Source Code", container_id=None):
    """Stylized code block with copy button."""
    cid = container_id or f"code_{id(code)}"
    escaped = html_mod.escape(code)
    return f"""
    <div id="{cid}" class="code-block">
        <div class="code-block__header">
            <span>{html_mod.escape(title)}</span>
            <button class="code-block__copy" onclick="copyCode('{cid}')">COPY</button>
        </div>
        <pre class="code-block__pre"><code>{escaped}</code></pre>
    </div>
    <style>
    .code-block {{ border: 1px solid var(--border); background: #0a0a0a; margin: 10px 0; }}
    .code-block__header {{ background: #1a1a1a; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); font-family: var(--font-mono); font-size: 11px; }}
    .code-block__copy {{ background: none; border: 1px solid #444; color: #888; cursor: pointer; font-size: 10px; padding: 2px 6px; }}
    .code-block__copy:hover {{ color: #fff; border-color: #fff; }}
    .code-block__pre {{ padding: 15px; margin: 0; overflow-x: auto; color: #dcdcdc; font-family: var(--font-mono); font-size: 13px; }}
    </style>
    <script>
    function copyCode(id) {{
        const code = document.getElementById(id).querySelector('code').innerText;
        navigator.clipboard.writeText(code);
        const btn = document.getElementById(id).querySelector('.code-block__copy');
        btn.innerText = 'COPIED';
        setTimeout(() => btn.innerText = 'COPY', 2000);
    }}
    </script>
    """

def html_dialog(dialog_id, title, content, actions_html=""):
    """
    Generate a standardized modal dialog component.
    :param actions_html: HTML for buttons in the footer (e.g., <button class='form__button'>OK</button>)
    """
    return f"""
    <div id="{dialog_id}" class="dialog-mask">
        <div class="dialog">
            <div class="dialog__header">
                <span class="dialog__title">{html_mod.escape(title)}</span>
                <button class="dialog__close" onclick="closeDialog('{dialog_id}')">&times;</button>
            </div>
            <div class="dialog__body">{content}</div>
            <div class="dialog__footer">{actions_html}</div>
        </div>
    </div>
    <style>
    .dialog-mask {{
        display: none; position: fixed; z-index: 4000; left: 0; top: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.8); backdrop-filter: blur(4px);
    }}
    .dialog {{
        position: relative; background-color: #fff; margin: 10% auto; padding: 0;
        border: 2px solid var(--primary-red); width: 80%; max-width: 600px;
        box-shadow: 10px 10px 0px rgba(0,0,0,0.2);
    }}
    .dialog__header {{
        padding: 12px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border);
        display: flex; justify-content: space-between; align-items: center;
    }}
    .dialog__title {{ font-family: var(--font-mono); font-weight: bold; font-size: 14px; text-transform: uppercase; color: var(--primary-red); }}
    .dialog__close {{ background: none; border: none; font-size: 24px; cursor: pointer; color: #888; }}
    .dialog__body {{ padding: 25px 20px; font-family: var(--font-base); line-height: 1.6; color: #333; }}
    .dialog__footer {{
        padding: 12px 20px; background: #f8f8f8; border-top: 1px solid var(--border);
        display: flex; justify-content: flex-end; gap: 10px;
    }}
    </style>
    <script>
    function openDialog(id) {{ document.getElementById(id).style.display = 'block'; }}
    function closeDialog(id) {{ document.getElementById(id).style.display = 'none'; }}
    </script>
    """

def html_load_widget(widget_name, components_dir=None, container_id=None):
    """Loads an external HTML component."""
    if not components_dir:
        components_dir = os.environ.get("CC_COMPONENTS", "{SC_ROOT}/Templates/Components")
    
    path = Path(components_dir) / f"{widget_name}.html"
    if not path.exists():
        return f"<div>Error: Widget component '{widget_name}' not found in {components_dir}</div>"
        
    try:
        content = path.read_text(encoding='utf-8')
        return html_standalone_widget(content, title=widget_name, container_id=container_id)
    except Exception as e:
        return f"<div>Error loading widget '{widget_name}': {e}</div>"
