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
import shutil
import stat
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
    from lib_bejson_core import bejson_core_atomic_write, bejson_core_load_file, bejson_core_acquire_lock, bejson_core_release_lock
    from lib_mfdb_core import mfdb_core_resolve_path
    from lib_bejson_validator import bejson_validator_validate_string
    
    # AI Sibling for Vectorization
    AI_SIBLING = os.path.join(PARENT_LIB_DIR, "AI")
    if AI_SIBLING not in sys.path: sys.path.append(AI_SIBLING)
    from lib_bejson_genai import GenAIClient
except ImportError:
    logging.critical("[FATAL] Core Sibling is unreachable. Matrix offline.")
    raise RuntimeError("[270] Core Sibling unreachable — cannot initialize Cognition library.")

# ===========================================================================
# COGNITION ERROR CODES (270-289) & SCHEMAS
# ===========================================================================
E_COGNITION_INVALID_MATRIX   = 270
E_COGNITION_AGENT_NOT_FOUND  = 271
E_COGNITION_INDEX_MISSING    = 272
E_COGNITION_PATCH_FAILED     = 273
E_COGNITION_SCHEMA_VIOLATION = 274
E_COGNITION_LOCK_TIMEOUT     = 275

BEJSON_COGNITION_SCHEMA = [
    {"name": "Record_Type_Parent", "type": "string"},
    {"name": "id", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "timestamp", "type": "number", "Record_Type_Parent": "AgentState"},
    {"name": "last_checkpoint", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "core_directives", "type": "object", "Record_Type_Parent": "AgentState"},
    {"name": "summary_blob", "type": "string", "Record_Type_Parent": "AgentState"},
    {"name": "stack_id", "type": "string", "Record_Type_Parent": "ExecutionStack"},
    {"name": "agent_id_fk", "type": "string", "Record_Type_Parent": "ExecutionStack"},
    {"name": "stack_timestamp", "type": "number", "Record_Type_Parent": "ExecutionStack"},
    {"name": "task_queue", "type": "array", "Record_Type_Parent": "ExecutionStack"},
    {"name": "pending_context", "type": "object", "Record_Type_Parent": "ExecutionStack"},
    {"name": "log_id", "type": "string", "Record_Type_Parent": "EpisodicLog"},
    {"name": "log_timestamp", "type": "number", "Record_Type_Parent": "EpisodicLog"},
    {"name": "user_input", "type": "string", "Record_Type_Parent": "EpisodicLog"},
    {"name": "agent_response", "type": "string", "Record_Type_Parent": "EpisodicLog"},
    {"name": "payloads_used", "type": "array", "Record_Type_Parent": "EpisodicLog"},
    {"name": "patch_id", "type": "string", "Record_Type_Parent": "MetaPatch"},
    {"name": "patch_timestamp", "type": "number", "Record_Type_Parent": "MetaPatch"},
    {"name": "target_layer", "type": "string", "Record_Type_Parent": "MetaPatch"},
    {"name": "patch_instruction", "type": "object", "Record_Type_Parent": "MetaPatch"},
    {"name": "status", "type": "string", "Record_Type_Parent": "MetaPatch"}
]

# ===========================================================================
# SAFE ATOMIC WRITER (Mutex Backoff)
# ===========================================================================
def bejson_cognition_safe_write(filepath: str, data: dict, max_retries: int = 50) -> bool:
    """
    High-resilience atomic writer with randomized exponential backoff.
    """
    resolved_path = mfdb_core_resolve_path(filepath)
    attempt = 0
    base_sleep = 0.5
    while attempt < max_retries:
        if bejson_core_acquire_lock(resolved_path, timeout=5):
            try:
                bejson_core_atomic_write(resolved_path, data)
                return True
            finally:
                bejson_core_release_lock(resolved_path)
        attempt += 1
        exp_backoff = min(base_sleep * (2 ** attempt), 20)
        jitter = random.uniform(0, 10)
        sleep_time = exp_backoff + jitter
        logging.warning(f"[COGNITION] Lock contention. Attempt {attempt}/{max_retries}. Retrying in {sleep_time:.2f}s...")
        time.sleep(sleep_time)
    raise RuntimeError(f"[{E_COGNITION_LOCK_TIMEOUT}] FATAL: Lock timeout.")
def bejson_cognition_cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2): return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = sum(a * a for a in vec1) ** 0.5
    norm_b = sum(b * b for b in vec2) ** 0.5
    if norm_a == 0 or norm_b == 0: return 0.0
    return dot_product / (norm_a * norm_b)

# ===========================================================================
# DATABASE ENGINE FUNCTIONS

# ===========================================================================
def bejson_cognition_init_matrix(db_path: str) -> dict:
    resolved_path = mfdb_core_resolve_path(db_path)
    if os.path.exists(resolved_path): doc = bejson_core_load_file(resolved_path)
    else: doc = None
    if doc and doc.get("Format_Version") == "104db": return doc
    return {
        "Format": "BEJSON", "Format_Version": "104db", "Format_Creator": "Elton Boehnen",
        "Records_Type": ["AgentState", "ExecutionStack", "EpisodicLog", "MetaPatch"],
        "Fields": BEJSON_COGNITION_SCHEMA, "Values": []
    }

def bejson_cognition_init_index(index_path: str) -> dict:
    resolved_index = mfdb_core_resolve_path(index_path)
    if os.path.exists(resolved_index): 
        doc = bejson_core_load_file(resolved_index)
    else: 
        doc = None
    if doc: return doc
    return {
        "Format": "BEJSON", 
        "Format_Version": "104a", 
        "Format_Creator": "Elton Boehnen", 
        "Records_Type": ["ContextIndex"],
        "Fields": [{"name": "placeholder", "type": "string"}],
        "Values": [["placeholder"]],
         "triggers": {}
    }

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
    
    # Identify the ID field name for this record type
    id_field = "id"
    if record_type == "ExecutionStack": id_field = "stack_id"
    elif record_type == "EpisodicLog": id_field = "log_id"
    elif record_type == "MetaPatch": id_field = "patch_id"

    # Identify the timestamp field name for this record type
    ts_field = "timestamp"
    if record_type == "ExecutionStack": ts_field = "stack_timestamp"
    elif record_type == "EpisodicLog": ts_field = "log_timestamp"
    elif record_type == "MetaPatch": ts_field = "patch_timestamp"

    # Search for existing record
    target_idx = -1
    for i, r in enumerate(doc["Values"]):
        if r[0] == record_type and r[field_indices[id_field]] == record_id:
            target_idx = i
            break
    
    row_data = [None] * len(doc["Fields"])
    row_data[0] = record_type
    row_data[field_indices[id_field]] = record_id
    row_data[field_indices[ts_field]] = time.time()
    
    if target_idx != -1: 
        row_data = list(doc["Values"][target_idx])
        row_data[field_indices[ts_field]] = time.time()
        
    for key, val in kwargs.items():
        if key in field_indices: 
            row_data[field_indices[key]] = val
    
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
def bejson_cognition_compact_logs(db_doc: dict, archive_path: str, max_logs: int = 100) -> dict:
    log_rows = [(i, r) for i, r in enumerate(db_doc.get("Values", [])) if r[0] == "EpisodicLog"]
    if len(log_rows) <= max_logs: return db_doc
    # Sort by log_timestamp field (resolved by name for schema safety)
    log_ts_idx = next((i for i, f in enumerate(db_doc["Fields"]) if f["name"] == "log_timestamp"), 2)
    log_rows.sort(key=lambda x: x[1][log_ts_idx] or 0)
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

def bejson_cognition_scan_index(index_doc: dict, text: str, payloads_dir: str, threshold: float = 0.75) -> Tuple[List[str], List[str]]:
    loaded_payloads, payload_names = [], []
    
    # --- PHASE 1: Keyword Scanning (Legacy Fallback) ---
    for keyword, payload_file in index_doc.get("triggers", {}).items():
        if keyword in text.lower():
            payload_data = bejson_core_load_file(mfdb_core_resolve_path(os.path.join(payloads_dir, payload_file)))
            if payload_data: 
                loaded_payloads.append(json.dumps(payload_data))
                payload_names.append(payload_file)
    
    # --- PHASE 2: Semantic Vector Scanning ---
    if index_doc.get("Values"):
        try:
            client = GenAIClient()
            query_vector = client.embed_content(text)
            
            if query_vector:
                field_map = {f["name"]: i for i, f in enumerate(index_doc["Fields"])}
                for row in index_doc["Values"]:
                    trigger_vector = row[field_map["embedding"]]
                    similarity = bejson_cognition_cosine_similarity(query_vector, trigger_vector)
                    
                    if similarity >= threshold:
                        payload_file = row[field_map["payload_file"]]
                        if payload_file not in payload_names:
                            payload_data = bejson_core_load_file(mfdb_core_resolve_path(os.path.join(payloads_dir, payload_file)))
                            if payload_data:
                                loaded_payloads.append(json.dumps(payload_data))
                                payload_names.append(payload_file)
                                logging.info(f"[COGNITION] Semantic match: '{row[field_map['trigger_text']]}' (Score: {similarity:.4f})")
        except Exception as e:
            logging.error(f"[COGNITION] Semantic scan failed: {e}")

    return loaded_payloads, payload_names

# ===========================================================================
# SELF-PATCHING (Meta-Cognitive Loop)
# ===========================================================================
def bejson_cognition_integrate_patches(db_path: str, db_doc: dict, index_path: str, index_doc: dict) -> None:
    pending_patches = bejson_cognition_query(db_doc, "MetaPatch", {"status": "pending"})
    if not pending_patches:
        bejson_cognition_safe_write(db_path, bejson_cognition_compact_logs(db_doc, "{SC_ROOT}/resources/Archives/episodic_archive.104db.bejson"))
        return

    resolved_index = mfdb_core_resolve_path(index_path)
    if os.path.exists(resolved_index): shutil.copy2(resolved_index, f"{resolved_index}.bak")

    for patch in pending_patches:
        instr = patch.get("patch_instruction", {})
        
        # --- LAYER: Context Index ---
        if patch["target_layer"] == "context_index" and instr.get("action") == "APPEND":
            if "triggers" not in index_doc: index_doc["triggers"] = {}
            index_doc["triggers"][instr["target_key"]] = instr["target_value"]
            db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="applied")
            
        # --- LAYER: Tooling (Generative Tool Forging) ---
        elif patch["target_layer"] == "Tooling" and instr.get("action") == "FORGE_TOOL":
            # SANDBOX CONTAINMENT CHECK
            sandbox_state_file = mfdb_core_resolve_path("{INTERNAL_STORAGE}/Admin/data/policy/sandbox_state.json")
            if os.path.exists(sandbox_state_file):
                with open(sandbox_state_file, "r") as sf:
                    state = json.load(sf)
                    if state.get("sandbox_enabled"):
                        logging.warning(f"[CONTAINMENT] Sandbox active. Refusing to forge tool.")
                        db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="blocked_by_sandbox")
                        continue
            try:
                metadata = instr.get("tool_metadata", {})
                filename = metadata.get("filename")
                code = instr.get("code")
                
                if not filename or not code:
                    logging.error(f"[COGNITION] Patch {patch['patch_id']} missing filename or code.")
                    continue
                
                # 1. Forge the physical tool
                # Using portable path resolution
                tools_dir = mfdb_core_resolve_path("{INTERNAL_STORAGE}/Admin/tools")
                tool_path = os.path.join(tools_dir, os.path.basename(filename))
                
                with open(tool_path, "w") as f:
                    f.write(code)
                
                # 2. Apply executable permissions
                st = os.stat(tool_path)
                os.chmod(tool_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                
                # 3. Register in CLITool Registry
                registry_path = mfdb_core_resolve_path("{INTERNAL_STORAGE}/Admin/init/registry/mfdb_layers/data/clitool.bejson")
                registry_doc = bejson_core_load_file(registry_path)
                
                if registry_doc and "Values" in registry_doc:
                    # [name, identifier, path_or_url, version, description, is_active, owner_email, website, clitool_guid, timestamp, session]
                    new_record = [
                        metadata.get("name", "Generated Tool"),
                        metadata.get("identifier", uuid.uuid4().hex),
                        tool_path,
                        metadata.get("version", "1.0.0"),
                        metadata.get("description", "Autonomously forged tool."),
                        True,
                        "boehnenelton2024@gmail.com",
                        "",
                        f"guid-forge-{uuid.uuid4().hex[:8]}",
                        datetime.now(timezone.utc).isoformat(),
                        "forge-session"
                    ]
                    registry_doc["Values"].append(new_record)
                    bejson_core_atomic_write(registry_path, registry_doc)
                
                db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="applied")
                logging.info(f"[COGNITION] Tool '{filename}' forged and registered successfully.")
                
            except Exception as e:
                logging.error(f"[COGNITION] Failed to forge tool in patch {patch['patch_id']}: {e}")
                db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="failed")

        # --- LAYER: Orchestration (The Hive Mind) ---
        elif patch["target_layer"] == "Orchestration" and instr.get("action") == "SPAWN_AGENT":
            try:
                agent_id = instr.get("agent_id")
                persona = instr.get("persona", "Worker")
                initial_task = instr.get("initial_task")
                
                if not agent_id or not initial_task:
                    logging.error(f"[COGNITION] SPAWN_AGENT patch {patch['patch_id']} missing agent_id or task.")
                    db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="failed")
                    continue
                
                # 1. Initialize AgentState
                db_doc = bejson_cognition_upsert(
                    db_doc, "AgentState", agent_id,
                    core_directives={"persona": persona, "status": "active"},
                    summary_blob="Initialized by Orchestrator.",
                    last_checkpoint=datetime.now(timezone.utc).isoformat()
                )
                
                # 2. Initialize ExecutionStack with task
                db_doc = bejson_cognition_upsert(
                    db_doc, "ExecutionStack", f"STK-{agent_id}",
                    agent_id_fk=agent_id,
                    task_queue=[{"task_id": uuid.uuid4().hex[:8], "description": initial_task, "status": "pending", "result": None}],
                    pending_context={}
                )
                
                logging.info(f"[COGNITION] Hive Mind: Spawned sub-agent {agent_id}.")
                db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="applied")
                
            except Exception as e:
                logging.error(f"[COGNITION] Failed to spawn agent in patch {patch['patch_id']}: {e}")
                db_doc = bejson_cognition_upsert(db_doc, "MetaPatch", patch["patch_id"], status="failed")


    try: bejson_validator_validate_string(json.dumps(index_doc))
    except Exception as e: logging.error(f"[FATAL] Schema corrupted. {e}"); return

    bejson_cognition_safe_write(index_path, index_doc)
    bejson_cognition_safe_write(db_path, bejson_cognition_compact_logs(db_doc, "{SC_ROOT}/resources/Archives/episodic_archive.104db.bejson"))
