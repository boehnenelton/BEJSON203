"""
Library:      lib_bejson_cognition.py
Family:       AI
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Manager for semantic and episodic memory structures in BEJSON.
"""

import json
import os
import sys
import time
import uuid
import logging
import hashlib
import random
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ===========================================================================
# SIBLING PATH RESOLUTION (Accessing the Locked Core)
# ===========================================================================
CURRENT_SIBLING = os.path.dirname(os.path.abspath(__file__))
PARENT_LIB_DIR = os.path.dirname(CURRENT_SIBLING)
CORE_SIBLING = os.path.join(PARENT_LIB_DIR, "Core")

if CORE_SIBLING not in sys.path:
    sys.path.append(CORE_SIBLING)

try:
    from lib_bejson_core import (
        bejson_core_atomic_write, 
        bejson_core_load_file, 
        bejson_core_acquire_lock, 
        bejson_core_release_lock
    )
    from lib_mfdb_core import mfdb_core_resolve_path
    from lib_bejson_validator import bejson_validator_validate_string
except ImportError:
    logging.warning("[COGNITION_LIB] Core siblings unreachable. Using internal fallbacks.")
    def mfdb_core_resolve_path(p: str) -> str: return os.path.expanduser(p)
    def bejson_core_load_file(p: str):
        p = mfdb_core_resolve_path(p)
        if not os.path.exists(p): return None
        with open(p, 'r') as f: return json.load(f)
    def bejson_core_acquire_lock(p: str, timeout: int=5): return False
    def bejson_core_release_lock(p: str): pass
    def bejson_validator_validate_string(s: str): return False
    def bejson_core_atomic_write(p: str, d: dict):
        p = mfdb_core_resolve_path(p)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p))
        with os.fdopen(fd, 'w') as f:
            json.dump(d, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)

try:
    from lib_bejson_errors import *
except ImportError:
    E_COGNITION_LOCK_TIMEOUT = 275

# SPEC FIX: Changed 'float' to 'number' per BEJSON specification
BEJSON_COGNITION_SCHEMA = [
    {"name": "Record_Type_Parent", "type": "string"},
    {"name": "id", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "timestamp", "type": "number", "Record_Type_Parent": "AgentState"},
    {"name": "last_checkpoint", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "core_directives", "type": "object", "Record_Type_Parent": "AgentState"},
    {"name": "summary_blob", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "agent_id_fk", "type": "string", "Record_Type_Parent": "ExecutionStack"},
    {"name": "task_queue", "type": "array", "Record_Type_Parent": "ExecutionStack"},
    {"name": "pending_context", "type": "object", "Record_Type_Parent": "ExecutionStack"},
    {"name": "user_input", "type": "string", "Record_Type_Parent": "EpisodicLog"},
    {"name": "agent_response", "type": "string", "Record_Type_Parent": "EpisodicLog"},
    {"name": "payloads_used", "type": "array", "Record_Type_Parent": "EpisodicLog"},
    {"name": "target_layer", "type": "string", "Record_Type_Parent": "MetaPatch"},
    {"name": "patch_instruction", "type": "object", "Record_Type_Parent": "MetaPatch"},
    {"name": "status", "type": "string", "Record_Type_Parent": "MetaPatch"} 
]

# ===========================================================================
# SAFE ATOMIC WRITER (Mutex Backoff)
# ===========================================================================
def bejson_cognition_safe_write(filepath: str, data: dict, max_retries: int = 50) -> bool:
    resolved_path = mfdb_core_resolve_path(filepath)
    attempt = 0
    base_sleep = 0.2
    while attempt < max_retries:
        if bejson_core_acquire_lock(resolved_path, timeout=5):
            try:
                bejson_core_atomic_write(resolved_path, data)
                return True
            finally:
                bejson_core_release_lock(resolved_path)
        attempt += 1
        sleep_time = base_sleep * (2 ** attempt) + (random.random() * 0.1)
        logging.warning(f"[COGNITION] Lock contention on {resolved_path}. Retrying in {sleep_time:.2f}s...")
        time.sleep(sleep_time)
    raise RuntimeError(f"[{E_COGNITION_LOCK_TIMEOUT}] FATAL: Could not acquire lock for matrix sync after {max_retries} attempts.")

# ===========================================================================
# DATABASE ENGINE FUNCTIONS
# ===========================================================================
def bejson_cognition_init_matrix(db_path: str) -> dict:
    resolved_path = mfdb_core_resolve_path(db_path)
    doc = bejson_core_load_file(resolved_path)
    if doc and doc.get("Format_Version") == "104db": return doc
    
    # SPEC FIX: Removed custom headers (MFDB_Version, Created_At) which are prohibited in 104db
    return {
        "Format": "BEJSON", 
        "Format_Version": "104db", 
        "Format_Creator": "Elton Boehnen",
        "Records_Type": ["AgentState", "ExecutionStack", "EpisodicLog", "MetaPatch"],
        "Fields": BEJSON_COGNITION_SCHEMA, 
        "Values": []
    }

def bejson_cognition_init_index(index_path: str) -> dict:
    doc = bejson_core_load_file(mfdb_core_resolve_path(index_path))
    if doc: return doc
    return {"Format": "BEJSON", "Format_Version": "104", "Format_Creator": "Elton Boehnen", "triggers": {}}

def bejson_cognition_query(doc: dict, record_type: str, filters: dict = None) -> List[dict]:
    results = []
    if "Fields" not in doc or "Values" not in doc: return results
    field_indices = {f["name"]: i for i, f in enumerate(doc["Fields"])}
    for row in doc.get("Values", []):
        if row[0] == record_type:
            record = {}
            for f in doc["Fields"]:
                if f.get("Record_Type_Parent") in [record_type, None]:
                    val = row[field_indices[f["name"]]]
                    if val is not None: record[f["name"]] = val
            match = True
            if filters:
                for k, v in filters.items():
                    if record.get(k) != v: match = False; break
            if match: results.append(record)
    return results

def bejson_cognition_upsert(doc: dict, record_type: str, record_id: str, **kwargs) -> dict:
    field_indices = {f["name"]: i for i, f in enumerate(doc["Fields"])}
    target_idx = next((i for i, r in enumerate(doc["Values"]) if r[0] == record_type and r[1] == record_id), -1)
    
    row_data = [None] * len(doc["Fields"])
    row_data[0] = record_type; row_data[1] = record_id; row_data[2] = time.time()
    
    if target_idx != -1: row_data = list(doc["Values"][target_idx]); row_data[2] = time.time()
    for key, val in kwargs.items():
        if key in field_indices: row_data[field_indices[key]] = val
    
    if target_idx != -1: doc["Values"][target_idx] = row_data
    else: doc["Values"].append(row_data)
    return doc

# ===========================================================================
# STATE MANAGEMENT & AMNESIA PATTERN
# ===========================================================================
def bejson_cognition_wake(db_doc: dict, agent_id: str, genesis_directives: dict = None) -> dict:
    state = bejson_cognition_query(db_doc, "AgentState", {"id": agent_id})
    stack = bejson_cognition_query(db_doc, "ExecutionStack", {"agent_id_fk": agent_id})
    if not state:
        return {"id": agent_id, "core_directives": genesis_directives or {"persona": "Default"}, "summary_blob": "Init.", "task_queue": [], "pending_context": {}, "active_buffer": []}
    return {"id": agent_id, "core_directives": state[0].get("core_directives", {}), "summary_blob": state[0].get("summary_blob", ""), "task_queue": stack[0].get("task_queue", []) if stack else [], "pending_context": stack[0].get("pending_context", {}) if stack else {}, "active_buffer": []}

def bejson_cognition_sleep(db_path: str, db_doc: dict, agent_state: dict) -> None:
    agent_id = agent_state["id"]
    if agent_state.get("active_buffer"):
        agent_state["summary_blob"] = f"Summary updated {time.ctime()}: Processed {len(agent_state['active_buffer'])} ops."
    db_doc = bejson_cognition_upsert(db_doc, "AgentState", agent_id, core_directives=agent_state.get("core_directives"), summary_blob=agent_state.get("summary_blob"), last_checkpoint=datetime.now(timezone.utc).isoformat())
    db_doc = bejson_cognition_upsert(db_doc, "ExecutionStack", f"STK-{agent_id}", agent_id_fk=agent_id, task_queue=agent_state.get("task_queue"), pending_context=agent_state.get("pending_context"))
    agent_state["active_buffer"] = []
    bejson_cognition_safe_write(db_path, db_doc)

def bejson_cognition_log_turn(db_doc: dict, user_input: str, agent_response: str, payloads_used: list) -> dict:
    return bejson_cognition_upsert(db_doc, "EpisodicLog", f"LOG-{uuid.uuid4().hex[:8]}", user_input=user_input, agent_response=agent_response, payloads_used=payloads_used)

# ===========================================================================
# COMPACTION & INDEXING
# ===========================================================================
def bejson_cognition_prune_logs(db_doc: dict, max_logs: int = 100) -> dict:
    """Slices the EpisodicLog matrix to prevent infinite disk bloat."""
    log_rows = [(i, r) for i, r in enumerate(db_doc.get("Values", [])) if r[0] == "EpisodicLog"]
    if len(log_rows) <= max_logs: return db_doc
    log_rows.sort(key=lambda x: x[1][2])
    to_remove_count = len(log_rows) - max_logs
    remove_indices = {x[0] for x in log_rows[:to_remove_count]}
    db_doc["Values"] = [row for i, row in enumerate(db_doc["Values"]) if i not in remove_indices]
    return db_doc

def bejson_cognition_compact_logs(db_doc: dict, archive_path: str, max_logs: int = 100) -> dict:
    log_rows = [(i, r) for i, r in enumerate(db_doc.get("Values", [])) if r[0] == "EpisodicLog"]
    if len(log_rows) <= max_logs: return db_doc
    log_rows.sort(key=lambda x: x[1][2])
    to_archive = len(log_rows) - max_logs
    archive_rows = [x[1] for x in log_rows[:to_archive]]
    remove_indices = {x[0] for x in log_rows[:to_archive]}

    resolved_archive = mfdb_core_resolve_path(archive_path)
    try: archive_doc = bejson_core_load_file(resolved_archive)
    except: archive_doc = None
    if not archive_doc or archive_doc.get("Format_Version") != "104db":
        archive_doc = {"Format": "BEJSON", "Format_Version": "104db", "Format_Creator": "Elton Boehnen", "Records_Type": ["EpisodicLog"], "Fields": db_doc.get("Fields", []), "Values": []}
    archive_doc["Values"].extend(archive_rows)
    bejson_cognition_safe_write(resolved_archive, archive_doc)
    
    db_doc["Values"] = [r for i, r in enumerate(db_doc["Values"]) if i not in remove_indices]
    return db_doc

def bejson_cognition_scan_index(index_doc: dict, text: str, payloads_dir: str) -> Tuple[List[str], List[str]]:
    loaded_payloads, payload_names = [], []
    for keyword, payload_file in index_doc.get("triggers", {}).items():
        if keyword in text.lower():
            payload_data = bejson_core_load_file(mfdb_core_resolve_path(os.path.join(payloads_dir, payload_file)))
            if payload_data: loaded_payloads.append(json.dumps(payload_data)); payload_names.append(payload_file)
    return loaded_payloads, payload_names

# ===========================================================================
# SELF-PATCHING (Meta-Cognitive Loop)
# ===========================================================================
def bejson_cognition_integrate_patches(db_path: str, db_doc: dict, index_path: str, index_doc: dict) -> None:
    pending_patches = bejson_cognition_query(db_doc, "MetaPatch", {"status": "pending"})
    if not pending_patches:
        db_doc = bejson_cognition_prune_logs(db_doc)
        bejson_cognition_safe_write(db_path, db_doc)
        return

    resolved_index = mfdb_core_resolve_path(index_path)
    if os.path.exists(resolved_index): shutil.copy2(resolved_index, f"{resolved_index}.bak")
    pre_patch_hash = hashlib.md5(json.dumps(index_doc, sort_keys=True).encode('utf-8')).hexdigest()

    for patch in pending_patches:
        instr = patch.get("patch_instruction", {})
        if patch["target_layer"] == "context_index" and instr.get("action") == "APPEND":
            if "triggers" not in index_doc: index_doc["triggers"] = {}
            index_doc["triggers"][instr["target_key"]] = instr["target_value"]
            db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["id"], status="applied")

    try: bejson_validator_validate_string(json.dumps(index_doc))
    except Exception as e: logging.error(f"[FATAL] Schema corrupted during patch integration. {e}"); return

    db_doc = bejson_cognition_prune_logs(db_doc)
    bejson_cognition_safe_write(index_path, index_doc)
    bejson_cognition_safe_write(db_path, db_doc)
