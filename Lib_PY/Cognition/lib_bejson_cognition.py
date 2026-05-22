"""
Library:      lib_bejson_cognition.py
Family:       Cognition
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.1.0 OFFICIAL (Security Logging)
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-22
Description:  Internal cognition and containment logic for autonomous agents.
REMEDIATED:   Enhanced Sandbox Blocking with diagnostic logging and error codes.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Sibling Path Resolution ---
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in sys.path: sys.path.insert(0, LIB_DIR)

CORE_DIR = os.path.join(os.path.dirname(LIB_DIR), "Core")
if CORE_DIR not in sys.path: sys.path.insert(0, CORE_DIR)

try:
    from lib_bejson_core import bejson_core_atomic_write, bejson_core_load_file
    from lib_mfdb_core import mfdb_core_resolve_path
    from lib_bejson_errors import *
except ImportError:
    pass

# Custom Error Code for Sandbox Violations
E_COGNITION_SANDBOX_VIOLATION = 403

def bejson_cognition_check_sandbox(task_name: str) -> bool:
    """
    Checks if an operation is permitted by the current sandbox state.
    REMEDIATED: Fails loudly with logging and standardized error code.
    """
    sandbox_file = mfdb_core_resolve_path("{INTERNAL_STORAGE}/Admin/data/policy/sandbox_state.json")
    if os.path.exists(sandbox_file):
        try:
            with open(sandbox_file, "r") as f:
                state = json.load(f)
                if state.get("sandbox_enabled"):
                    logging.error(f"[SECURITY_BLOCK] Task '{task_name}' blocked by sandbox. Code: {E_COGNITION_SANDBOX_VIOLATION}")
                    # In a full agent context, this would trigger a callback to a security dashboard
                    return True # Is Blocked
        except Exception as e:
            logging.warning(f"[COGNITION] Sandbox check failed: {e}")
    return False # Not Blocked

# ... rest of the cognition logic remains unchanged
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
