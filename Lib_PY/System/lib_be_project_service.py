"""
Library:      lib_be_project_service.py
Family:       System
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Background service for project lifecycle and dependency management.
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
_DEFAULT_BEC_ROOT = str(Path(__file__).resolve().parent.parent.parent)

def get_bec_root():
    root_env = os.environ.get("BEC_ROOT")
    if root_env:
        return root_env
    root_file = os.path.join(_DEFAULT_BEC_ROOT, "data/state/BEC_ROOT.txt")
    if os.path.exists(root_file):
        with open(root_file, 'r') as f:
            return f.read().strip()
    return _DEFAULT_BEC_ROOT

BEC_ROOT = get_bec_root()
LIB_DIR = os.path.join(BEC_ROOT, 'Lib/py')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from lib_bejson_core import bejson_core_acquire_lock, bejson_core_release_lock

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
        record[21] = False   # is_deleted
        return record

    @staticmethod
    def validate_record(record: List) -> bool:
        """Ensures record strictly adheres to the 22-field v1.4.0 schema."""
        if not isinstance(record, list) or len(record) != 22:
            logging.error(f"[ProjectService] Schema Violation: Expected 22 fields, got {len(record) if isinstance(record, list) else 'N/A'}")
            return False
        if record[0] != 'Project':
            logging.error(f"[ProjectService] Record Type Mismatch: {record[0]}")
            return False
        return True

    @staticmethod
    def _load_db():
        if not os.path.exists(DB_FILE):
            return None
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None

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
            
            # Deduplicate by name or normalized path
            norm_path = os.path.normpath(path)
            exists = any(v[2] == name or os.path.normpath(v[3]) == norm_path 
                         for v in doc['Values'] if v[0] == 'Project')
            if exists:
                print(f"Project '{name}' already tracked at {path}")
                return False

            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            
            proj_id = str(int(time.time() * 1000))
            created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            record = ProjectService._create_project_record(proj_id, name, path, p_type, created)
            if ProjectService.validate_record(record):
                doc['Values'].append(record)
                ProjectService._save_db(doc)
                print(f"Tracked new project: {name}")
                return True
            return False
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def scan_and_sync():
        print(f"--- Project Service: Syncing {PROJECTS_ROOT} ---")
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return
            
            # 1. Discovery: Find new folders in Projects_ROOT
            if os.path.exists(PROJECTS_ROOT):
                for item in os.listdir(PROJECTS_ROOT):
                    full_path = os.path.join(PROJECTS_ROOT, item)
                    if not os.path.isdir(full_path): continue
                    
                    norm_path = os.path.normpath(full_path)
                    exists = any(os.path.normpath(v[3]) == norm_path 
                                 for v in doc['Values'] if v[0] == 'Project')
                    
                    if not exists:
                        # Infer type
                        p_type = "bash"
                        try:
                            if any(f.endswith('.py') for f in os.listdir(full_path)):
                                p_type = "python"
                        except PermissionError: pass
                        
                        proj_id = str(int(time.time() * 1000))
                        created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        record = ProjectService._create_project_record(proj_id, item, full_path, p_type, created)
                        if ProjectService.validate_record(record):
                            print(f"Discovered: {item} ({p_type})")
                            doc['Values'].append(record)

            # 2. Audit: Check for missing files and update flags
            for v in doc['Values']:
                if v[0] == 'Project':
                    p_path = v[3]
                    if not os.path.exists(p_path):
                        if not v[9]:
                            print(f"Flagging missing project: {v[2]}")
                            v[9] = True
                    else:
                        if v[9]:
                            print(f"Project restored: {v[2]}")
                            v[9] = False

            ProjectService._save_db(doc)
            print("Sync complete.")
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def archive_project(name: str) -> bool:
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return False
            for v in doc['Values']:
                if v[0] == 'Project' and v[2] == name:
                    v[20] = True
            ProjectService._save_db(doc)
            return True
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def expel_project(name: str, p_type: str) -> bool:
        doc = ProjectService._load_db()
        if not doc: return False
        
        proj = next((v for v in doc['Values'] if v[0] == 'Project' and v[2] == name), None)
        if not proj: return False
        
        p_path = proj[3]
        expelled_root = os.path.join(BEC_ROOT, f"management/expelled/expelled_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        target_dir = os.path.join(expelled_root, p_type, name)
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        
        print(f"Expelling {name} to {target_dir}...")
        if os.path.exists(p_path):
            try:
                shutil.move(p_path, target_dir)
            except Exception as e:
                print(f"Move failed: {e}")
        
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db() 
            doc['Values'] = [v for v in doc['Values'] if not (v[0] == 'Project' and v[2] == name)]
            ProjectService._save_db(doc)
            return True
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def toggle_reset_protection(name: str) -> bool:
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return False
            for v in doc['Values']:
                if v[0] == 'Project' and v[2] == name:
                    if len(v) <= 21: v.append(True)
                    else: v[21] = not v[21]
            ProjectService._save_db(doc)
            return True
        finally:
            bejson_core_release_lock(DB_FILE)

    @staticmethod
    def get_reset_protection(name: str) -> str:
        doc = ProjectService._load_db()
        if not doc: return "OFF"
        for v in doc['Values']:
            if v[0] == 'Project' and v[2] == name:
                return "ON" if (len(v) > 21 and v[21]) else "OFF"
        return "OFF"

    @staticmethod
    def get_project_path(name: str) -> Optional[str]:
        doc = ProjectService._load_db()
        if not doc: return None
        for v in doc['Values']:
            if v[0] == 'Project' and v[2] == name:
                return v[3]
        return None

    @staticmethod
    def get_project_type(name: str) -> Optional[str]:
        doc = ProjectService._load_db()
        if not doc: return None
        for v in doc['Values']:
            if v[0] == 'Project' and v[2] == name:
                return v[6]
        return None

    @staticmethod
    def delete_record(name: str) -> bool:
        bejson_core_acquire_lock(DB_FILE)
        try:
            doc = ProjectService._load_db()
            if not doc: return False
            doc['Values'] = [v for v in doc['Values'] if not (v[0] == 'Project' and v[2] == name)]
            ProjectService._save_db(doc)
            return True
        finally:
            bejson_core_release_lock(DB_FILE)

# Legacy Wrappers for backward compatibility during transition
def track_project(name, p_type, path=None): return ProjectService.add_project(name, p_type, path)
def list_projects(p_type=None, include_archived=False): return ProjectService.get_projects(p_type, include_archived)
def get_project_path(name): return ProjectService.get_project_path(name)
def track_project_archive(name): return ProjectService.archive_project(name)
def track_project_expel(name, p_type): return ProjectService.expel_project(name, p_type)
def track_project_toggle_reset_protection(name): return ProjectService.toggle_reset_protection(name)
def track_project_get_reset_protection(name): return ProjectService.get_reset_protection(name)
def track_project_delete_record(name): return ProjectService.delete_record(name)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--sync":
            ProjectService.scan_and_sync()
        elif sys.argv[1] == "--list":
            projects = ProjectService.get_projects()
            for p in projects:
                print(f"{p[2]} ({p[6]})")
