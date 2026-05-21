"""
Library:      lib_bejson_gemini.py
Family:       AI
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Integration wrapper for Google Gemini API with key rotation support.
"""

import os
import sys
import json
import time
import requests
import random
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Resolve paths
LIB_DIR = os.environ.get("BEJSON_LIB_DIR", str(Path(__file__).resolve().parent))
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

CORE_DIR = str(Path(LIB_DIR).parent / "Core")
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

try:
    from lib_bejson_env import resolve_path
except ImportError:
    def resolve_path(p): return p

STD_ADMIN_ROOT = resolve_path("{INTERNAL_STORAGE}/Admin")

SCHEMA_KEY_REGISTRY = {
    "Format": "BEJSON",
    "Format_Version": "104a",
    "Format_Creator": "Elton Boehnen",
    "Schema_Name": "GeminiKeyRegistry",
    "Records_Type": ["ApiKey"],
    "Fields": [
        {"name": "key_slot", "type": "integer"},
        {"name": "key", "type": "string"}
    ],
    "Values": []
}

SCHEMA_MODEL_REGISTRY = {
    "Format": "BEJSON",
    "Format_Version": "104a",
    "Format_Creator": "Elton Boehnen",
    "Schema_Name": "GeminiModelRegistry",
    "Records_Type": ["GeminiModel"],
    "Fields": [
        {"name": "model_name", "type": "string"},
        {"name": "model_id", "type": "string"},
        {"name": "currently_active", "type": "boolean"},
        {"name": "thinking_enabled", "type": "boolean"},
        {"name": "google_search_enabled", "type": "boolean"}
    ],
    "Values": [
        [
                "Gemini 3.1 Pro (Preview)",
                "gemini-3.1-pro-preview",
                False,
                True,
                True
        ],
        [
                "Gemini 2.5 Pro",
                "gemini-2.5-pro",
                False,
                True,
                True
        ],
        [
                "Gemini 3 Flash (Preview)",
                "gemini-3-flash-preview",
                False,
                False,
                True
        ],
        [
                "Gemini 3.1 Flash-Lite (Preview)",
                "gemini-3.1-flash-lite-preview",
                False,
                False,
                True
        ],
        [
                "Gemini 2.5 Flash",
                "gemini-2.5-flash",
                True,
                False,
                False
        ],
        [
                "Gemini 3 Pro Image (Preview)",
                "gemini-3-pro-image-preview",
                False,
                False,
                False
        ],
        [
                "Gemini 3.1 Flash Image (Preview)",
                "gemini-3.1-flash-image-preview",
                False,
                False,
                False
        ],
        [
                "Gemini 3.1 Flash TTS (Preview)",
                "gemini-3.1-flash-tts-preview",
                False,
                False,
                False
        ],
        [
                "Gemini 3.1 Flash Live (Preview)",
                "gemini-3.1-flash-live-preview",
                False,
                False,
                True
        ],
        [
                "Gemma 4 31B IT",
                "gemma-4-31b-it",
                False,
                False,
                False
        ],
        [
                "Gemma 4 26B MoE IT",
                "gemma-4-26b-a4b-it",
                False,
                False,
                False
        ]
]
}

SCHEMA_AI_PROFILE = {
    "Format": "BEJSON",
    "Format_Version": "104",
    "Format_Creator": "Elton Boehnen",
    "Records_Type": ["AI_Profile"],
    "Parent_Hierarchy": "/LLM_Configuration",
    "Fields": [
        {"name": "Record_Type_Parent", "type": "string"},
        {"name": "Name", "type": "string"},
        {"name": "Archetype", "type": "string"},
        {"name": "Persona", "type": "string"},
        {"name": "SystemInstruction", "type": "string"},
        {"name": "ForbiddenTopics", "type": "array"},
        {"name": "Avatar_Type", "type": "string"},
        {"name": "Avatar_sourceUrl", "type": "string"},
        {"name": "Avatar_Data", "type": "string"},
        {"name": "MaxResponseTokens", "type": "integer"},
        {"name": "Creativity", "type": "number"},
        {"name": "Tone", "type": "array"},
        {"name": "Formality", "type": "string"},
        {"name": "Verbosity", "type": "string"},
        {"name": "EmotionalExpression_Enabled", "type": "boolean"},
        {"name": "EmotionalExpression_Intensity", "type": "number"},
        {"name": "GoogleSearch_Enabled", "type": "boolean"},
        {"name": "CodeInterpreter_Enabled", "type": "boolean"},
        {"name": "EphemeralMemory", "type": "boolean"},
        {"name": "CodeParsing_Mode", "type": "string"},
        {"name": "CodeParsing_Languages", "type": "array"},
        {"name": "CodeParsing_StructureValidation", "type": "boolean"},
        {"name": "CodeParsing_VersionControl", "type": "boolean"},
        {"name": "Thinking_Supported", "type": "boolean"}
    ],
    "Values": [
        [
            "AI_Profile",
            "Gemini_Standard",
            "Assistant",
            "A helpful and professional AI assistant.",
            "You are a helpful assistant. Provide clear, accurate, and concise information.",
            [], "Emoji", "", "🤖", 65536, 0.7, ["Professional", "Helpful"], "Formal", "Balanced", 
            False, 0.0, True, True, True, "complete", ["python", "javascript"], True, True, True
        ]
    ]
}

# --- Environment & Setup ---

LIB_DIR = os.environ.get("BEJSON_LIB_DIR", str(Path(__file__).resolve().parent))
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

# Also add sibling Core directory if it exists
CORE_DIR = str(Path(LIB_DIR).parent / "Core")
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

try:
    from lib_bejson_core import bejson_core_load_file, bejson_core_get_field_index, bejson_core_atomic_write
except ImportError:
    # Minimal fallback logic for core operations
    def bejson_core_load_file(p):
        with open(p, 'r') as f: return json.load(f)
    def bejson_core_get_field_index(d, n):
        for i, f in enumerate(d.get("Fields", [])):
            if f["name"] == n: return i
        return -1
    def bejson_core_atomic_write(p, d):
        with open(p, 'w') as f: json.dump(d, f, indent=2)

# --- Registry Managers ---

import logging

class GeminiKeyRegistry:
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.keys = []
        try:
            if not self.file_path.exists():
                self.create_default()
            self.load()
        except Exception as e:
            logging.error(f"[GeminiLib] Fatal error initializing KeyRegistry: {e}")

    def create_default(self):
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            bejson_core_atomic_write(str(self.file_path), SCHEMA_KEY_REGISTRY)
        except Exception as e:
            logging.warning(f"[GeminiLib] Could not create default keys: {e}")

    def load(self):
        try:
            data = bejson_core_load_file(str(self.file_path))
            idx = bejson_core_get_field_index(data, "key")
            if idx != -1:
                self.keys = [row[idx] for row in data["Values"] if "YOUR_GEMINI_KEY" not in str(row[idx])]
            if not self.keys:
                logging.warning(f"[GeminiLib] No valid keys found in {self.file_path}")
        except Exception as e:
            logging.warning(f"[GeminiLib] Failed to load keys from {self.file_path}: {e}")
            self.keys = []

class GeminiModelRegistry:
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.models = []
        self.active_model_id = "gemini-2.5-flash"
        try:
            if not self.file_path.exists():
                self.create_default()
            self.load()
        except Exception as e:
            logging.error(f"[GeminiLib] Error initializing ModelRegistry: {e}")
            self._load_fallbacks()

    def create_default(self):
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            bejson_core_atomic_write(str(self.file_path), SCHEMA_MODEL_REGISTRY)
        except Exception as e:
            logging.warning(f"[GeminiLib] Could not create default models: {e}")

    def _load_fallbacks(self):
        logging.info("[GeminiLib] Loading hardcoded model fallbacks.")
        for row in SCHEMA_MODEL_REGISTRY["Values"]:
            self.models.append({"id": row[1], "thinking": row[3], "search": row[4]})

    def load(self):
        try:
            data = bejson_core_load_file(str(self.file_path))
            fields = [f["name"] for f in data["Fields"]]
            id_idx = fields.index("model_id")
            active_idx = fields.index("currently_active")
            think_idx = fields.index("thinking_enabled") if "thinking_enabled" in fields else -1
            search_idx = fields.index("google_search_enabled") if "google_search_enabled" in fields else -1
            
            self.models = []
            for row in data["Values"]:
                m_info = {
                    "id": row[id_idx],
                    "thinking": row[think_idx] if think_idx != -1 else False,
                    "search": row[search_idx] if search_idx != -1 else False
                }
                self.models.append(m_info)
                if row[active_idx] is True:
                    self.active_model_id = row[id_idx]
        except Exception as e:
            logging.warning(f"[GeminiLib] Failed to load models from {self.file_path}: {e}")
            self._load_fallbacks()

    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        target_id = model_id or self.active_model_id
        for m in self.models:
            if m["id"] == target_id: return m
        return {"id": target_id, "thinking": False, "search": False}

class GeminiProfile:
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.instruction = ""
        self.config = {}
        try:
            if not self.file_path.exists():
                self.create_default()
            self.load()
        except Exception as e:
            logging.error(f"[GeminiLib] Error initializing Profile: {e}")
            self._load_fallbacks()

    def create_default(self):
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            bejson_core_atomic_write(str(self.file_path), SCHEMA_AI_PROFILE)
        except Exception as e:
            logging.warning(f"[GeminiLib] Could not create default profile: {e}")

    def _load_fallbacks(self):
        logging.info("[GeminiLib] Loading hardcoded profile fallbacks.")
        self.instruction = SCHEMA_AI_PROFILE["Values"][0][4]
        self.config = {f["name"]: SCHEMA_AI_PROFILE["Values"][0][i] for i, f in enumerate(SCHEMA_AI_PROFILE["Fields"])}

    def load(self):
        try:
            data = bejson_core_load_file(str(self.file_path))
            fields = [f["name"] for f in data["Fields"]]
            instr_idx = fields.index("SystemInstruction")
            self.instruction = data["Values"][0][instr_idx]
            self.config = {f["name"]: data["Values"][0][i] for i, f in enumerate(data["Fields"])}
        except Exception as e:
            logging.warning(f"[GeminiLib] Failed to load profile from {self.file_path}: {e}")
            self._load_fallbacks()

# --- Unified Prompter Engine ---

class GeminiStandardPrompter:
    def __init__(
        self, 
        key_registry_path: Union[str, Path],
        model_registry_path: Union[str, Path],
        profile_path: Union[str, Path]
    ):
        self.key_reg = GeminiKeyRegistry(key_registry_path)
        self.model_reg = GeminiModelRegistry(model_registry_path)
        self.profile = GeminiProfile(profile_path)
        self.current_key_idx = 0
        self.last_request_time = 0
        self.request_delay = 1.0

    def _get_next_key(self) -> Optional[str]:
        keys = self.key_reg.keys
        if not keys: return None
        # MANDATE: Random rotation for load balancing and quota preservation
        return random.choice(keys)

    def prompt(self, user_input: str, model_id: Optional[str] = None) -> str:
        now = time.time()
        diff = now - self.last_request_time
        if diff < self.request_delay: time.sleep(self.request_delay - diff)
        
        key = self._get_next_key()
        if not key: return "ERROR: No valid API keys."

        m_info = self.model_reg.get_model_info(model_id)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_info['id']}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": user_input}]}],
            "system_instruction": {"parts": [{"text": self.profile.instruction}]},
            "generationConfig": {
                "maxOutputTokens": self.profile.config.get("MaxResponseTokens", 65536),
                "temperature": self.profile.config.get("Creativity", 0.7)
            }
        }
        if m_info["search"] or self.profile.config.get("GoogleSearch_Enabled", False):
            payload["tools"] = [{"google_search": {}}]
        if m_info["thinking"] or self.profile.config.get("Thinking_Supported", False):
            payload["generationConfig"]["thinking_config"] = {"include_thoughts": True}

        self.last_request_time = time.time()
        try:
            res = requests.post(url, json=payload, timeout=90)
            res.raise_for_status()
            data = res.json()
            if "candidates" in data and data["candidates"]:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return f"ERROR: No candidates. {json.dumps(data)}"
        except Exception as e:
            return f"ERROR: {str(e)}"

# --- Global Standard Paths (2026) ---

STD_ADMIN_ROOT = resolve_path("{INTERNAL_STORAGE}/Admin")
STD_KEY_PATH = os.path.join(STD_ADMIN_ROOT, "data/env/gemini_keys.bejson")
STD_MODEL_PATH = os.path.join(STD_ADMIN_ROOT, "resources/Schemas/gemini_model_registry.104a.bejson")
STD_PROFILE_PATH = os.path.join(STD_ADMIN_ROOT, "resources/Schemas/gemini_standard_profile.bejson")

def get_standard_prompter():
    return GeminiStandardPrompter(STD_KEY_PATH, STD_MODEL_PATH, STD_PROFILE_PATH)
