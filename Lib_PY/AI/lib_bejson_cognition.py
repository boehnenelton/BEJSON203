"""
Library:      lib_bejson_cognition.py
Family:       AI
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-21
Description:  Manager for semantic and episodic memory structures in BEJSON.
REMEDIATED:   Fixed Amnesia Pattern (Working Memory Gap) and Specification Discipline.
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
# SIBLING PATH RESOLUTION
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
except ImportError as e:
    logging.error(f"[COGNITION_LIB] Critical Error: Core siblings unreachable. {e}")
    raise

try:
    from lib_bejson_errors import *
