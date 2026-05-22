"""
Library:      lib_be_project_service.py
Family:       System
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.1.0 OFFICIAL (Schema Aligned)
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-22
Description:  Background service for project lifecycle and dependency management.
REMEDIATED:   Aligned with authoritative 22-field Project Schema v1.4.0.
"""

import os
import sys
import json
import time
import shutil
import subprocess
from datetime import datetime
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# --- Sibling Resolution ---
_DEFAULT_BEC_ROOT = str(Path(__file__).resolve().parent.parent.parent)
def get_bec_root():
    root_env = os.environ.get("BEC_ROOT")
    if root_env: return root_env
    return _DEFAULT_BEC_ROOT

BEC_ROOT = get_bec_root()
LIB_DIR = os.path.join(BEC_ROOT, 'libraries/Lib_PY/Core')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

try:
    from lib_bejson_core import bejson_core_acquire_lock, bejson_core_release_lock
    from lib_bejson_schema import SCHEMA_PROJECT_v140
except ImportError as e:
    print(f"Project Service Error: Dependencies missing. {e}")
    sys.exit(1)

_DEFAULT_CC_DB = os.path.join(BEC_ROOT, 'data/centralized')
DB_FILE = os.path.join(os.environ.get('CC_DB', _DEFAULT_CC_DB), 'BE_Tracking.json')
PROJECTS_ROOT = os.environ.get('CC_PROJECTS', os.path.join(BEC_ROOT, 'projects'))

import logging

class ProjectService:
    @staticmethod
    def _create_project_record(proj_id: str, name: str, path: str, p_type: str, created: str) -> List:
        """Helper to create a standardized v1.4.0 Project record (22 fields)."""
        record = [None] * 22
        record[0] = 'Project'
        record[1] = proj_id
        record[2] = name
        record[3] = path
        record[4] = '0.0.1'
        record[5] = created
        record[6] = p_type
        record[7] = True     # is_active
        record[8] = True     # is_visible
        record[9] = False    # is_missing
        record[20] = False   # is_archived
        record[21] = False   # is_reset_protected
        return record

    @staticmethod
    def validate_record(record: List) -> bool:
        """Ensures record strictly adheres to the authoritative 22-field v1.4.0 schema."""
        if not isinstance(record, list) or len(record) != 22:
            logging.error(f"[ProjectService] Schema Violation: Expected 22 fields, got {len(record)}")
            return False
        if record[0] != 'Project':
            logging.error(f"[ProjectService] Record Type Mismatch: {record[0]}")
            return False
        return True

    @staticmethod
    def _load_db():
        if not os.path.exists(DB_FILE): return None
        with open(DB_FILE, 'r') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return None

    @staticmethod
    def _save_db(doc):
        if not doc: return
        with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(DB_FILE), delete=False) as tf:
            json.dump(doc, tf, indent=2)
            tmp_name = tf.name
        os.replace(tmp_name, DB_FILE)

    @staticmethod
    def get_projects(project_type: str = None, include_archived: bool = False) -> List:
        doc = ProjectService._load_db()
        if not doc: return []
        projects = [v for v in doc['Values'] if v[0] == 'Project']
        if project_type:
            projects = [v for v in projects if v[6] == project_type]
        if not include_archived:
            projects = [v for v in projects if len(v) > 20 and v[20] == False]
        return projects

    @staticmethod
    def add_project(name: str, p_type: str, path: str = None) -> bool:
        if not path:
            path = os.path.join(PROJECTS_ROOT, name.replace(" ", "_"))
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return False
            norm_path = os.path.normpath(path)
            exists = any(v[2] == name or os.path.normpath(v[3]) == norm_path 
                         for v in doc['Values'] if v[0] == 'Project')
            if exists: return False
            if not os.path.exists(path): os.makedirs(path, exist_ok=True)
            proj_id = str(int(time.time() * 1000))
            created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            record = ProjectService._create_project_record(proj_id, name, path, p_type, created)
            if ProjectService.validate_record(record):
                doc['Values'].append(record)
                ProjectService._save_db(doc)
                return True
            return False
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def scan_and_sync():
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return
            if os.path.exists(PROJECTS_ROOT):
                for item in os.listdir(PROJECTS_ROOT):
                    full_path = os.path.join(PROJECTS_ROOT, item)
                    if not os.path.isdir(full_path): continue
                    norm_path = os.path.normpath(full_path)
                    exists = any(os.path.normpath(v[3]) == norm_path for v in doc['Values'] if v[0] == 'Project')
                    if not exists:
                        p_type = "python" if any(f.endswith('.py') for f in os.listdir(full_path)) else "bash"
                        proj_id = str(int(time.time() * 1000))
                        created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        record = ProjectService._create_project_record(proj_id, item, full_path, p_type, created)
                        if ProjectService.validate_record(record): doc['Values'].append(record)
            for v in doc['Values']:
                if v[0] == 'Project':
                    v[9] = not os.path.exists(v[3]) # is_missing
            ProjectService._save_db(doc)
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def get_project_path(name: str) -> Optional[str]:
        doc = ProjectService._load_db()
        if not doc: return None
        for v in doc['Values']:
            if v[0] == 'Project' and v[2] == name: return v[3]
        return None

# Legacy Wrappers
def track_project(name, p_type, path=None): return ProjectService.add_project(name, p_type, path)
def list_projects(p_type=None, include_archived=False): return ProjectService.get_projects(p_type, include_archived)
def get_project_path(name): return ProjectService.get_project_path(name)

