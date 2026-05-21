"""
Library:      lib_bejson_utility.py
Family:       Utility
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  General-purpose helper functions for the BEJSON ecosystem.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup Sibling Path Resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_LIB_DIR = os.path.dirname(CURRENT_DIR)
CORE_DIR = os.path.join(PARENT_LIB_DIR, "Core")

if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)

try:
    from lib_bejson_core import (
        bejson_core_create_104db,
        bejson_core_load_file,
        bejson_core_get_version,
        bejson_core_get_records_by_type,
        bejson_core_atomic_write
    )
except ImportError:
    print(f"Error: Core sibling not found at {CORE_DIR}")
    sys.exit(1)

DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".sh", ".txt", ".bejson"]
DEFAULT_EXCLUDES = [".git", "__pycache__", "node_modules", "lib", "output", ".mfdb_lock"]

# 104db Project Management Schema (v1.3.1)
CHUNK_SCHEMA = [
    {"name": "Record_Type_Parent", "type": "string"},
    {"name": "id", "type": "string"},
    {"name": "timestamp", "type": "string"},
    {"name": "project_name", "type": "string", "Record_Type_Parent": "Project"},
    {"name": "current_version", "type": "string", "Record_Type_Parent": "Project"},
    {"name": "version_label", "type": "string", "Record_Type_Parent": "Snapshot"},
    {"name": "version_notes", "type": "string", "Record_Type_Parent": "Snapshot"},
    {"name": "changes", "type": "string", "Record_Type_Parent": "Snapshot"},
    {"name": "file_path", "type": "string", "Record_Type_Parent": "File"},
    {"name": "content", "type": "string", "Record_Type_Parent": "File"},
    {"name": "snapshot_id_fk", "type": "string", "Record_Type_Parent": "File"}
]

def bejson_utility_init_project_db(project_name: str) -> Dict[str, Any]:
    """Initialize a new multi-version project matrix."""
    doc = {
        "Format": "BEJSON",
        "Format_Version": "104db",
        "Format_Creator": "Elton Boehnen",
        "Records_Type": ["Project", "Snapshot", "File"],
        "Fields": CHUNK_SCHEMA,
        "Values": []
    }
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Project row (11 fields)
    doc["Values"].append(["Project", f"PROJ-{project_name}", now, project_name, "0.0.0", None, None, None, None, None, None])
    return doc

def bejson_utility_snapshot_project(
    db_doc: Dict[str, Any],
    target_dir: str,
    version_label: str,
    notes: str = "",
    changes: str = ""
) -> Dict[str, Any]:
    """
    Scan a directory and append a new version (snapshot) with change tracking.
    """
    target_path = Path(target_dir).resolve()
    snapshot_id = f"SNAP-{time.strftime('%Y%m%d-%H%M%S')}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    for row in db_doc["Values"]:
        if row[0] == "Project":
            row[4] = version_label
            break

    # Snapshot row (11 fields)
    db_doc["Values"].append(["Snapshot", snapshot_id, now, None, None, version_label, notes, changes, None, None, None])
    
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES]
        for file in files:
            f_path = Path(root) / file
            if f_path.suffix.lower() in DEFAULT_EXTENSIONS:
                try:
                    rel_path = f_path.relative_to(target_path)
                    content = f_path.read_text(encoding="utf-8")
                    # File row (11 fields)
                    db_doc["Values"].append(["File", f"FILE-{rel_path}", now, None, None, None, None, None, str(rel_path), content, snapshot_id])
                except Exception:
                    continue
                    
    return db_doc

def bejson_utility_restore_version(
    db_doc: Dict[str, Any],
    version_label: str,
    output_dir: str
) -> int:
    """
    Extract a specific version from the multi-version matrix.
    """
    fields = [f["name"] for f in db_doc["Fields"]]
    snap_id_idx = fields.index("id")
    vlabel_idx = fields.index("version_label")
    
    snapshot_id = None
    for row in db_doc["Values"]:
        if row[0] == "Snapshot" and row[vlabel_idx] == version_label:
            snapshot_id = row[snap_id_idx]
            break
            
    if not snapshot_id:
        raise ValueError(f"Version '{version_label}' not found.")

    fpath_idx = fields.index("file_path")
    cont_idx = fields.index("content")
    fk_idx = fields.index("snapshot_id_fk")
    
    out_root = Path(output_dir).resolve()
    count = 0
    
    for row in db_doc["Values"]:
        if row[0] == "File" and row[fk_idx] == snapshot_id:
            rel_path = row[fpath_idx]
            content = row[cont_idx]
            if rel_path:
                target_file = out_root / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content, encoding="utf-8")
                count += 1
                
    return count
