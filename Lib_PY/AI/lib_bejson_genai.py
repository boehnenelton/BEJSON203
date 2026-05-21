"""
Library:      lib_bejson_genai.py
Family:       AI
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Interface for Google Generative AI (GenAI) models.
"""

import os
import json
import time
import random
import sys
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Add Lib directory to path for relative imports
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

CORE_DIR = os.path.join(os.path.dirname(LIB_DIR), "Core")
if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)

try:
    from lib_bejson_env import resolve_path
except ImportError:
    def resolve_path(p): return p

# ANSI Status Colors
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_NC = "\033[0m"
C_BOLD = "\033[1m"

DEFAULT_KEY_FILE = resolve_path("{HOME}/.env/gemini_keys.bejson")

MODELS = [
    "gemini-3-flash-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5",
    "gemini-2.5-pro",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview"
]

class GenAIKeyManager:
    def __init__(self, key_file: str = DEFAULT_KEY_FILE):
        self.key_file = key_file
        self.keys = []
        self.current_index = 0
        self.load_keys()

    def load_keys(self):
        """Load keys from the centralized BEJSON 104a key file."""
        if not os.path.exists(self.key_file):
            return
        try:
            with open(self.key_file, 'r') as f:
                doc = json.load(f)
                
                # Identify 'key' field index
                fields = doc.get("Fields", [])
                key_idx = -1
                for i, field in enumerate(fields):
                    if field.get("name") == "key":
                        key_idx = i
                        break
                
                if key_idx != -1:
                    # Extract keys from Values
                    self.keys = [row[key_idx] for row in doc.get("Values", []) if len(row) > key_idx and row[key_idx]]
                    # Randomize order for true round-robin
                    random.shuffle(self.keys)
        except Exception:
            self.keys = []

    def get_next_key(self) -> Optional[str]:
        """Get the next key in rotation."""
        if not self.keys:
            self.load_keys() # Retry once
        if not self.keys:
            return None
        
        key = self.keys[self.current_index % len(self.keys)]
        self.current_index += 1
        return key

    def get_key_count(self) -> int:
        return len(self.keys)

class GenAIClient:
    def __init__(self, key_manager: GenAIKeyManager = None):
        self.km = key_manager or GenAIKeyManager()
        self.status_callback: Optional[Callable[[str, str], None]] = None
        
        # Try to import SDK
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.sdk_available = True
        except ImportError:
            self.sdk_available = False

    def set_status_callback(self, callback: Callable[[str, str], None]):
        """Set a custom callback for status updates. (state, message)"""
        self.status_callback = callback

    def update_status(self, state: str, message: str):
        """Standardized status updates following policy (ALL CAPS)."""
        msg = message.upper()
        if self.status_callback:
            self.status_callback(state, msg)
        else:
            # Default terminal status bar logic
            color = C_NC
            if state == "error": color = C_RED
            elif state == "success": color = C_GREEN
            elif state == "wait": color = C_YELLOW
            
            # Simple ANSI line overwrite status
            sys.stdout.write(f"\r{C_BOLD}STATUS:{C_NC} {color}{msg}{C_NC} {' ' * 20}\r")
            sys.stdout.flush()

    def embed_content(self, text: str, model: str = "models/gemini-embedding-001") -> Optional[List[float]]:
        """Generate embeddings for the given text."""
        if not self.sdk_available:
            self.update_status("error", "ERROR: google-genai SDK not installed.")
            return None

        key_count = self.km.get_key_count()
        if key_count == 0:
            self.update_status("error", "ERROR: No API keys found.")
            return None

        for i in range(key_count):
            api_key = self.km.get_next_key()
            try:
                client = self.genai.Client(api_key=api_key)
                response = client.models.embed_content(model=model, contents=text)
                return response.embeddings[0].values
            except Exception:
                continue
        return None

    def generate_content(self, prompt: str, model: str = "gemini-3-flash-preview", system_instruction: str = None) -> Optional[str]:
        """Generate content with automatic key rotation and mandatory status feedback."""
        if not self.sdk_available:
            self.update_status("error", "ERROR: google-genai SDK not installed.")
            return None

        if model not in MODELS:
            # Policy: Only 2.5+
            self.update_status("error", f"ERROR: Model {model} not allowed by policy.")
            return None

        key_count = self.km.get_key_count()
        if key_count == 0:
            self.update_status("error", "ERROR: No API keys found in key pool.")
            return None

        # Try keys round-robin
        last_error = ""
        for i in range(key_count):
            api_key = self.km.get_next_key()
            if not api_key: continue

            try:
                self.update_status("wait", f"ATTEMPT {i+1}: DISPATCHING QUERY...")
                client = self.genai.Client(api_key=api_key)
                
                config = None
                if system_instruction:
                    config = self.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7
                    )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                
                self.update_status("success", "QUERY SUCCESSFUL")
                print() # Move past status line
                return response.text

            except Exception as e:
                last_error = str(e)
                self.update_status("error", f"KEY FAILED: {last_error[:50]}...")
                time.sleep(1) # Brief pause before next key
                continue

        self.update_status("error", "ALL KEYS EXHAUSTED")
        return None

