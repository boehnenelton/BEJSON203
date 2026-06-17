"""
Library:      lib_be_pms.py
Family:       System
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.1.0 OFFICIAL
Format_Creator: Elton Boehnen
Date:         2026-06-16
Description:  Core relational Package Management System (PMS) library for version 2.0.
              Implements 104db relational logic, DVRP retention, and issue tracking.
              v2.1.0: Added project_type and relocation logic.
Relational ID: gcli-lib-pms-v2-001
"""

import os
import sys
import json
import time
import hashlib
import zipfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# --- SCRIPT_PATH Resolution (Sec. 7.1) ---
def get_script_path() -> Path:
    return Path(__file__).resolve().parent

SCRIPT_PATH = get_script_path()

# --- Bootstrapping (Sec. 7.2) ---
ADMIN_ROOT = os.environ.get("ADMIN_ROOT", "/storage/emulated/0/Admin")
LIB_CORE_PATH = os.path.join(ADMIN_ROOT, "libraries/Lib_PY/Core")
if LIB_CORE_PATH not in sys.path:
    sys.path.insert(0, LIB_CORE_PATH)

try:
    from lib_bejson_core import (
        bejson_core_load_file,
        bejson_core_atomic_write,
        ResilientPIDLock,
        bejson_core_create_104db,
        bejson_core_get_field_map,
        bejson_core_add_record,
        bejson_core_filter_rows
    )
except ImportError as e:
    print(f"PMS Library Error: Core dependencies missing. {e}")
    sys.exit(1)

# --- Configuration ---
PMS_DB_PATH = os.environ.get("PMS_DATABASE_PATH", os.path.join(ADMIN_ROOT, "data/registry/PMS_v2_Registry.104db.bejson"))
ARCHIVE_ROOT = os.environ.get("ARCHIVE_STAGING_ROOT", os.path.join(ADMIN_ROOT, "dev/Archived_Packages"))
DEV_ROOT = os.path.join(ADMIN_ROOT, "dev")
RETENTION_LIMIT = int(os.environ.get("PMS_RETENTION_LIMIT", 2))

SCHEMA_VERSION = "2.1.0"

# --- Schema Definitions ---
ENTITY_TYPES = ["Project", "Package", "Issue"]

FIELDS = [
    {"name": "Record_Type_Parent", "type": "string"},
    # Entity: Project
    {"name": "project_name",      "type": "string",  "Record_Type_Parent": "Project"},
    {"name": "github_url",        "type": "string",  "Record_Type_Parent": "Project"},
    {"name": "description",       "type": "string",  "Record_Type_Parent": "Project"},
    {"name": "category",          "type": "string",  "Record_Type_Parent": "Project"},
    {"name": "project_type",      "type": "string",  "Record_Type_Parent": "Project"},
    {"name": "archive_staging_path", "type": "string", "Record_Type_Parent": "Project"},
    {"name": "dev_path",          "type": "string",  "Record_Type_Parent": "Project"},
    # Entity: Package
    {"name": "package_id",        "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "project_name_fk",   "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "version",           "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "zip_path",          "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "state",             "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "last_updated",      "type": "string",  "Record_Type_Parent": "Package"},
    {"name": "sha256_hash",       "type": "string",  "Record_Type_Parent": "Package"},
    # Entity: Issue
    {"name": "issue_id",          "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "issue_project_fk",  "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "title",             "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "severity",          "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "status",            "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "issue_description", "type": "string",  "Record_Type_Parent": "Issue"},
    {"name": "reported_at",       "type": "string",  "Record_Type_Parent": "Issue"}
]

class PMSManager:
    @staticmethod
    def db_init():
        """Initializes the relational 104db registry if missing or updates schema."""
        if not os.path.exists(PMS_DB_PATH):
            os.makedirs(os.path.dirname(PMS_DB_PATH), exist_ok=True)
            doc = bejson_core_create_104db(ENTITY_TYPES, FIELDS, [])
            doc["Schema_Version"] = SCHEMA_VERSION
            return bejson_core_atomic_write(PMS_DB_PATH, doc)
        
        # Schema Migration Logic
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            
            needs_update = False
            # Check for project_type field
            if "project_type" not in fm:
                print("[*] Migrating PMS Schema: Adding 'project_type' field.")
                # Insert project_type into Fields at correct position for Project entity
                # For simplicity in 104db migration, we append to Fields and pad Records
                doc["Fields"].append({"name": "project_type", "type": "string", "Record_Type_Parent": "Project"})
                for i, row in enumerate(doc["Values"]):
                    doc["Values"][i].append(None)
                needs_update = True
            
            if needs_update:
                doc["Schema_Version"] = SCHEMA_VERSION
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
        return True

    @staticmethod
    def add_project(name: str, github_url: str = None, desc: str = None, cat: str = "tool", p_type: str = None, dev_path: str = None):
        """Registers a new project entity."""
        PMSManager.db_init()
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            
            # Check if exists
            existing = bejson_core_filter_rows(doc, "project_name", name)
            if existing:
                return False
            
            # Map category to staging subfolder
            cat_map = {"python": "Python", "web": "Web", "react": "React", "skill": "Skills", "bash": "Bash"}
            staging_sub = cat_map.get(cat.lower(), "Python")
            arch_path = os.path.join(ARCHIVE_ROOT, staging_sub, name)
            
            record = [None] * len(doc["Fields"])
            record[fm["Record_Type_Parent"]] = "Project"
            record[fm["project_name"]] = name
            record[fm["github_url"]] = github_url
            record[fm["description"]] = desc
            record[fm["category"]] = cat
            record[fm["project_type"]] = p_type
            record[fm["archive_staging_path"]] = arch_path
            record[fm["dev_path"]] = dev_path
            
            if bejson_core_add_record(doc, record):
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
            return False

    @staticmethod
    def update_project(name: str, **kwargs):
        """Updates project attributes."""
        PMSManager.db_init()
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            
            found = False
            for i, row in enumerate(doc["Values"]):
                if row[fm["Record_Type_Parent"]] == "Project" and row[fm["project_name"]] == name:
                    for key, val in kwargs.items():
                        if key in fm:
                            doc["Values"][i][fm[key]] = val
                    found = True
                    break
            
            if found:
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
            return False

    @staticmethod
    def relocate_project(name: str):
        """Moves project directories to target jurisdictional paths based on project_type."""
        PMSManager.db_init()
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            
            rows = [r for r in doc["Values"] if r[fm["Record_Type_Parent"]] == "Project" and r[fm["project_name"]] == name]
            if not rows:
                raise ValueError(f"Project '{name}' not found.")
            
            row = rows[0]
            p_type = row[fm["project_type"]]
            if not p_type:
                raise ValueError(f"Project '{name}' has no project_type set. Set it first.")
            
            # Map type to subfolder
            type_map = {
                "python": "Python",
                "web": "Web",
                "react": "React",
                "bash": "Bash",
                "skill": "Skills"
            }
            sub = type_map.get(p_type.lower(), "Other")
            
            target_dev = os.path.join(DEV_ROOT, sub, name)
            target_arch = os.path.join(ARCHIVE_ROOT, sub, name)
            
            current_dev = row[fm["dev_path"]]
            current_arch = row[fm["archive_staging_path"]]
            
            changes = {}
            
            # Relocate Dev Path
            if current_dev and os.path.exists(current_dev) and os.path.normpath(current_dev) != os.path.normpath(target_dev):
                print(f"[*] Relocating Dev: {current_dev} -> {target_dev}")
                os.makedirs(os.path.dirname(target_dev), exist_ok=True)
                shutil.move(current_dev, target_dev)
                changes["dev_path"] = target_dev
            
            # Relocate Archive Path
            if current_arch and os.path.exists(current_arch) and os.path.normpath(current_arch) != os.path.normpath(target_arch):
                print(f"[*] Relocating Archive: {current_arch} -> {target_arch}")
                os.makedirs(os.path.dirname(target_arch), exist_ok=True)
                shutil.move(current_arch, target_arch)
                changes["archive_staging_path"] = target_arch
            
            # Update Registry
            if changes:
                for i, r in enumerate(doc["Values"]):
                    if r[fm["Record_Type_Parent"]] == "Project" and r[fm["project_name"]] == name:
                        for k, v in changes.items():
                            doc["Values"][i][fm[k]] = v
                        break
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
            
            print(f"[*] Project '{name}' is already in the correct location.")
            return True

    @staticmethod
    def report_issue(project_name: str, title: str, severity: str, description: str):
        """Appends a new issue record linked to a project."""
        PMSManager.db_init()
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            issue_id = str(int(time.time() * 1000))
            now = datetime.now().isoformat()
            
            record = [None] * len(doc["Fields"])
            record[fm["Record_Type_Parent"]] = "Issue"
            record[fm["issue_id"]] = issue_id
            record[fm["issue_project_fk"]] = project_name
            record[fm["title"]] = title
            record[fm["severity"]] = severity
            record[fm["status"]] = "open"
            record[fm["issue_description"]] = description
            record[fm["reported_at"]] = now
            
            if bejson_core_add_record(doc, record):
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
            return False

    @staticmethod
    def release_package(project_name: str, version: str, source_dir: str, state: str = "zipped", skip_zip: bool = False, manual_zip_path: str = None):
        """Packages a project version, applies DVRP, and updates registry."""
        PMSManager.db_init()
        with ResilientPIDLock(PMS_DB_PATH):
            doc = bejson_core_load_file(PMS_DB_PATH)
            fm = bejson_core_get_field_map(doc)
            project_rows = bejson_core_filter_rows(doc, "project_name", project_name)
            if not project_rows:
                raise ValueError(f"Project '{project_name}' not registered.")
            
            staging_path = project_rows[0][fm["archive_staging_path"]]
            os.makedirs(staging_path, exist_ok=True)
            
            zip_filename = f"{project_name}-v{version}.zip"
            zip_dest = manual_zip_path if manual_zip_path else os.path.join(staging_path, zip_filename)
            hash_str = None
            
            if not skip_zip and not manual_zip_path:
                # 1. Perform Zipping
                with zipfile.ZipFile(zip_dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                    src_path = Path(source_dir)
                    for file in src_path.rglob('*'):
                        if file.is_file():
                            z.write(file, file.relative_to(src_path))
                
                # 2. Calculate Hash
                sha256 = hashlib.sha256()
                with open(zip_dest, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256.update(chunk)
                hash_str = sha256.hexdigest()
            
            # 3. DVRP Logic (Keep 2 latest)
            zips = sorted([f for f in os.listdir(staging_path) if f.endswith(".zip")], 
                         key=lambda x: os.path.getmtime(os.path.join(staging_path, x)), 
                         reverse=True)
            if len(zips) > RETENTION_LIMIT:
                for old_zip in zips[RETENTION_LIMIT:]:
                    try:
                        os.remove(os.path.join(staging_path, old_zip))
                    except: pass
            
            # 4. Update Registry
            now = datetime.now().isoformat()
            pkg_id = f"{project_name}_{version}"
            
            record = [None] * len(doc["Fields"])
            record[fm["Record_Type_Parent"]] = "Package"
            record[fm["package_id"]] = pkg_id
            record[fm["project_name_fk"]] = project_name
            record[fm["version"]] = version
            record[fm["zip_path"]] = zip_dest
            record[fm["state"]] = state
            record[fm["last_updated"]] = now
            record[fm["sha256_hash"]] = hash_str
            
            if bejson_core_add_record(doc, record):
                return bejson_core_atomic_write(PMS_DB_PATH, doc)
            return False

# Legacy Wrappers for CLI integration
def pms_init(): return PMSManager.db_init()
def pms_add_project(name, github_url=None, desc=None, cat="tool", p_type=None, dev_path=None):
    return PMSManager.add_project(name, github_url, desc, cat, p_type, dev_path)
def pms_update_project(name, **kwargs):
    return PMSManager.update_project(name, **kwargs)
def pms_relocate(name):
    return PMSManager.relocate_project(name)
def pms_release(name, version, source_dir, skip_zip=False, state="zipped", manual_zip_path=None):
    return PMSManager.release_package(name, version, source_dir, state=state, skip_zip=skip_zip, manual_zip_path=manual_zip_path)
def pms_bug_report(name, title, sev, desc):
    return PMSManager.report_issue(name, title, sev, desc)
