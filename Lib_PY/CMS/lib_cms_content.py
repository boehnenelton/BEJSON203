"""
Library:      lib_cms_content.py
Family:       CMS
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Content handler and transformer for the CMS engine.
"""

import os
import sys
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional

# Ensure local directory is in path for relative imports
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

import lib_bejson_core as BEJSONCore

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

# ---------------------------------------------------------------------------
# PAGE CONTENT OPERATIONS (pages_db/<uuid>.json)
# ---------------------------------------------------------------------------

def _cms_content_init_page_file(file_path: str, title: str, html_body: str = "") -> None:
    """Initialize an individual page content file in 104db format."""
    record_types = ["PageMeta", "Content"]
    fields = [
        {"name": "Record_Type_Parent", "type": "string"},
        {"name": "meta_title", "type": "string", "Record_Type_Parent": "PageMeta"},
        {"name": "meta_description", "type": "string", "Record_Type_Parent": "PageMeta"},
        {"name": "html_body", "type": "string", "Record_Type_Parent": "Content"},
        {"name": "markdown_body", "type": "string", "Record_Type_Parent": "Content"},
    ]
    
    doc = BEJSONCore.bejson_core_create_104db(record_types, fields, [])
    
    # Add Meta record
    meta_row = ["PageMeta", title, ""]
    # Pad to match field count
    meta_row.extend([None] * (len(fields) - len(meta_row)))
    doc = BEJSONCore.bejson_core_add_record(doc, meta_row)
    
    # Add Content record
    # Record_Type_Parent [0], meta_title [1], meta_description [2], html_body [3], markdown_body [4]
    content_row = ["Content", None, None, html_body, ""]
    # Pad to match field count
    content_row.extend([None] * (len(fields) - len(content_row)))
    
    doc = BEJSONCore.bejson_core_add_record(doc, content_row)
    BEJSONCore.bejson_core_atomic_write(file_path, doc)

def cms_content_get_page_body(pages_dir: str, page_uuid: str) -> str:
    """Retrieve html_body from a page's individual JSON file."""
    file_path = os.path.join(pages_dir, f"{page_uuid}.json")
    if not os.path.exists(file_path):
        return ""
    
    doc = BEJSONCore.bejson_core_load_file(file_path)
    hb_idx = BEJSONCore.bejson_core_get_field_index(doc, "html_body")
    records = BEJSONCore.bejson_core_get_records_by_type(doc, "Content")
    
    if records:
        return records[0][hb_idx] or ""
    return ""

# ---------------------------------------------------------------------------
# MASTER INDEX OPERATIONS (site_master.json)
# ---------------------------------------------------------------------------

def cms_content_create_page(
    master_db_path: str, 
    pages_dir: str, 
    title: str, 
    category_ref: str = "Uncategorized", 
    author_ref: str = "Admin",
    html_body: str = "",
    featured_img: str = ""
) -> str:
    """
    Create a new page: generates UUID, updates master index, creates content file.
    Returns the new page_uuid.
    """
    page_uuid = str(uuid.uuid4())
    page_slug = _slugify(title)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Update Master Index
    doc = BEJSONCore.bejson_core_load_file(master_db_path)
    
    # Map fields
    fields_map = {f['name']: i for i, f in enumerate(doc["Fields"])}
    
    new_row = [None] * len(doc["Fields"])
    new_row[fields_map["Record_Type_Parent"]] = "PageRecord"
    new_row[fields_map["page_uuid"]] = page_uuid
    new_row[fields_map["page_title"]] = title
    new_row[fields_map["page_slug"]] = page_slug
    new_row[fields_map["category_ref"]] = category_ref
    new_row[fields_map["item_type"]] = "page"
    new_row[fields_map["created_at"]] = today
    new_row[fields_map["author_ref"]] = author_ref
    new_row[fields_map["featured_img"]] = featured_img
    
    doc = BEJSONCore.bejson_core_add_record(doc, new_row)
    BEJSONCore.bejson_core_atomic_write(master_db_path, doc)
    
    # 2. Create individual content file
    os.makedirs(pages_dir, exist_ok=True)
    page_file = os.path.join(pages_dir, f"{page_uuid}.json")
    _cms_content_init_page_file(page_file, title, html_body)
    
    return page_uuid

def cms_content_update_page(
    master_db_path: str,
    pages_dir: str,
    page_uuid: str,
    updates: Dict
) -> None:
    """
    Update page metadata in master and/or content in individual file.
    'updates' can contain: title, category_ref, author_ref, featured_img, html_body.
    """
    # 1. Update Master Index if needed
    master_updates = {k: v for k, v in updates.items() if k in ["title", "category_ref", "author_ref", "featured_img"]}
    if master_updates:
        doc = BEJSONCore.bejson_core_load_file(master_db_path)
        t_idx = 0
        u_idx = BEJSONCore.bejson_core_get_field_index(doc, "page_uuid")
        
        found = False
        for i, row in enumerate(doc["Values"]):
            if row[t_idx] == "PageRecord" and row[u_idx] == page_uuid:
                for k, v in master_updates.items():
                    # Handle title -> page_title mapping
                    f_key = "page_title" if k == "title" else k
                    if k == "title":
                        row[BEJSONCore.bejson_core_get_field_index(doc, "page_slug")] = _slugify(v)
                    
                    row[BEJSONCore.bejson_core_get_field_index(doc, f_key)] = v
                found = True
                break
        if found:
            BEJSONCore.bejson_core_atomic_write(master_db_path, doc)

    # 2. Update Content File if needed
    html_body = updates.get("html_body")
    if html_body is not None or "title" in updates:
        page_file = os.path.join(pages_dir, f"{page_uuid}.json")
        if os.path.exists(page_file):
            pdoc = BEJSONCore.bejson_core_load_file(page_file)
            pt_idx = 0
            
            if html_body is not None:
                hb_idx = BEJSONCore.bejson_core_get_field_index(pdoc, "html_body")
                for row in pdoc["Values"]:
                    if row[pt_idx] == "Content":
                        row[hb_idx] = html_body
                        
            if "title" in updates:
                mt_idx = BEJSONCore.bejson_core_get_field_index(pdoc, "meta_title")
                for row in pdoc["Values"]:
                    if row[pt_idx] == "PageMeta":
                        row[mt_idx] = updates["title"]
                        
            BEJSONCore.bejson_core_atomic_write(page_file, pdoc)

def cms_content_delete_page(master_db_path: str, pages_dir: str, page_uuid: str) -> bool:
    """Delete page from master index and remove its content file."""
    # 1. Master Index
    doc = BEJSONCore.bejson_core_load_file(master_db_path)
    t_idx = 0
    u_idx = BEJSONCore.bejson_core_get_field_index(doc, "page_uuid")
    
    new_values = []
    found = False
    for row in doc["Values"]:
        if row[t_idx] == "PageRecord" and row[u_idx] == page_uuid:
            found = True
            continue
        new_values.append(row)
        
    if found:
        doc["Values"] = new_values
        BEJSONCore.bejson_core_atomic_write(master_db_path, doc)
        
        # 2. Content File
        page_file = os.path.join(pages_dir, f"{page_uuid}.json")
        if os.path.exists(page_file):
            os.remove(page_file)
            
    return found

def cms_content_list_pages(master_db_path: str) -> List[Dict]:
    """List all pages from master index as a list of dictionaries."""
    doc = BEJSONCore.bejson_core_load_file(master_db_path)
    records = BEJSONCore.bejson_core_get_records_by_type(doc, "PageRecord")
    fields = BEJSONCore.bejson_core_get_fields(doc)
    
    results = []
    for row in records:
        item = {}
        for i, f in enumerate(fields):
            item[f['name']] = row[i]
        results.append(item)
    return results
