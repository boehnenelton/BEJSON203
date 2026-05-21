"""
Library:      build_ebook.py
Family:       Core
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Specialized generator for e-book formatted outputs.
"""

import os
import sys
import json
import html as html_mod
from pathlib import Path

# Add current py dir to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

HTML_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "HTML")
if HTML_DIR not in sys.path:
    sys.path.append(HTML_DIR)

try:
    from lib_html2_page_templates import html_page, html_save as html_write
    from lib_html2_body import html_brutal_table as html_table
except ImportError:
    # Stubs
    def html_page(**kwargs): return ""
    def html_write(p, c): pass
    def html_table(*args, **kwargs): return ""

def build_ebook():
    # Use environment variable or default to parent directory
    lib_root = os.environ.get("BEJSON_LIB_ROOT", os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(lib_root, "library_manifest.bejson")
    output_root = os.path.join(lib_root, "doc")
    
    os.makedirs(output_root, exist_ok=True)
    
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    fields = manifest.get("Fields", [])
    values = manifest.get("Values", [])
    
    # Map fields to indices
    f_idx = {f["name"]: i for i, f in enumerate(fields)}
    
    # Runtimes to process
    runtimes = ["py", "sh", "js"]
    for rt in runtimes:
        os.makedirs(os.path.join(output_root, rt), exist_ok=True)

    # 1. Build Global Navigation Structure
    # Format: {"py": [(label, url), ...], "sh": [...]}
    nav_data = []
    for row in values:
        name = row[f_idx["name"]]
        lib_id = row[f_idx["id"]]
        runtime = row[f_idx["runtime"]]
        
        # Determine relative directory based on extension or explicit runtime
        rt_dir = "py" if name.endswith(".py") else "sh" if name.endswith(".sh") else "js"
        nav_data.append({
            "name": name,
            "id": lib_id,
            "rt": rt_dir,
            "filename": f"{os.path.splitext(name)[0]}.html"
        })

    # 2. Generate Individual Library Pages
    for item in nav_data:
        # Find raw data from values
        row = next(r for r in values if r[f_idx["id"]] == item["id"])
        
        name = item["name"]
        rt_dir = item["rt"]
        target_filename = item["filename"]
        path = row[f_idx["path"]]
        description = row[f_idx["description"]]
        functions = row[f_idx["functions"]]
        
        print(f"Generating page for {rt_dir}/{name}...")
        
        # Read source code
        code_content = ""
        if os.path.exists(path):
            with open(path, 'r') as cf:
                code_content = cf.read()
        else:
            code_content = f"Error: Source file not found at {path}"

        # Build Page-Specific Navigation (Relative to Subdir)
        page_nav = [("Home", "../index.html")]
        for nav_item in nav_data:
            if nav_item["rt"] == rt_dir:
                url = nav_item["filename"]
            else:
                url = f"../{nav_item['rt']}/{nav_item['filename']}"
            page_nav.append((nav_item["name"], url))

        # Build page body
        body = f"""
        <article class="lib-reference">
            <header class="lib-header">
                <span class="badge badge-{rt_dir}">{rt_dir.upper()}</span>
                <h1>{html_mod.escape(name)}</h1>
                <p class="description">{html_mod.escape(description)}</p>
                <code class="path">{html_mod.escape(path)}</code>
            </header>
            
            <section class="functions-list">
                <h2>Public API / Functions</h2>
                <ul>
                    {"".join(f"<li><code>{html_mod.escape(fn)}</code></li>" for fn in functions)}
                </ul>
            </section>
            
            <section class="code-view">
                <h2>Source Code</h2>
                <div class="code-container">
                    <pre><code>{html_mod.escape(code_content)}</code></pre>
                </div>
            </section>
        </article>
        """
        
        extra_css = """
        .lib-header { margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
        .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 0.5rem; }
        .badge-py { background: #3776ab; color: white; }
        .badge-sh { background: #4eaa25; color: white; }
        .badge-js { background: #f7df1e; color: black; }
        .description { font-size: 1.2rem; color: var(--text_mut); margin-bottom: 0.5rem; }
        .path { display: block; font-size: 0.9rem; color: var(--accent); margin-bottom: 1rem; }
        .functions-list ul { list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 0.5rem; }
        .functions-list li code { background: var(--surface); border: 1px solid var(--border); padding: 0.2rem 0.4rem; display: block; }
        .code-container { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 8px; overflow-x: auto; margin-top: 1rem; border: 1px solid #333; }
        .code-container pre { font-family: 'Source Code Pro', 'Roboto Mono', monospace; font-size: 13px; line-height: 1.4; }
        h2 { margin: 2rem 0 1rem 0; border-left: 4px solid var(--accent); padding-left: 1rem; }
        """
        
        full_html = html_page(
            title=f"Reference: {name}",
            body=body,
            nav_links=page_nav,
            dark=True,
            extra_css=extra_css,
            template_sections={"code": True}
        )
        
        html_write(os.path.join(output_root, rt_dir, target_filename), full_html)

    # 3. Generate Index Page (Root)
    print("Generating Index page...")
    
    # Build Index Navigation
    index_nav = [("Home", "index.html")]
    for nav_item in nav_data:
        index_nav.append((nav_item["name"], f"{nav_item['rt']}/{nav_item['filename']}"))

    # Prepare table data for index
    table_headers = ["Runtime", "Name", "Description"]
    table_rows = []
    for item in nav_data:
        row = next(r for r in values if r[f_idx["id"]] == item["id"])
        desc = row[f_idx["description"]]
        link = f'<a href="{item["rt"]}/{item["filename"]}">{html_mod.escape(item["name"])}</a>'
        table_rows.append([item["rt"].upper(), link, html_mod.escape(desc)])

    index_body = f"""
    <header class="index-header">
        <h1>BECore Library E-Book</h1>
        <p>Comprehensive documentation and source reference mirroring the official library structure.</p>
    </header>
    
    <section class="library-grid">
        {html_table(table_rows, table_headers, title="Library Manifest", dark=True, raw_cols=[1])}
    </section>
    """
    
    index_html = html_page(
        title="BECore Library Index",
        body=index_body,
        nav_links=index_nav,
        dark=True
    )
    
    html_write(os.path.join(output_root, "index.html"), index_html)
    print(f"E-book successfully built in {output_root}")

if __name__ == "__main__":
    build_ebook()
