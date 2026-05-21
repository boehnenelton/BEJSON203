"""
Library:      lib_bejson_schema.py
Family:       Core
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-21
Description:  Schema management and enforcement. Provides tools to extract,
             store, and validate BEJSON documents against registered schemas.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from lib_bejson_core import bejson_core_load_file
    from lib_bejson_validator import validate_bejson, ValidationResult
except ImportError:
    # Minimal stubs if running outside the library environment
    def bejson_core_load_file(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    class ValidationResult:
        def __init__(self):
            self.valid = True
            self.errors = []
        def add_error(self, msg):
            self.valid = False
            self.errors.append(msg)

def bejson_schema_extract(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts the schema (structure) from a BEJSON document.
    Returns a copy of the document with an empty Values array.
    """
    schema = doc.copy()
    schema["Values"] = []
    return schema

def bejson_schema_validate_against(doc: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
    """
    Validates a BEJSON document against a specific schema.
    Checks for:
    - Version mismatch
    - Records_Type mismatch
    - Field name and type mismatch
    - Positional integrity
    """
    res = ValidationResult()
    
    # 1. Structural Basic Validation
    # (Assuming the doc itself is valid BEJSON)
    
    # 2. Version Check
    if doc.get("Format_Version") != schema.get("Format_Version"):
        res.add_error(f"Version mismatch: Document is {doc.get('Format_Version')}, Schema is {schema.get('Format_Version')}")
    
    # 3. Records_Type Check
    if doc.get("Records_Type") != schema.get("Records_Type"):
        res.add_error(f"Records_Type mismatch: Document types do not match schema types.")
    
    # 4. Fields Check (Names and Types)
    doc_fields = doc.get("Fields", [])
    sch_fields = schema.get("Fields", [])
    
    if len(doc_fields) != len(sch_fields):
        res.add_error(f"Field count mismatch: Document has {len(doc_fields)}, Schema has {len(sch_fields)}")
    else:
        for i, (df, sf) in enumerate(zip(doc_fields, sch_fields)):
            if df.get("name") != sf.get("name"):
                res.add_error(f"Field name mismatch at index {i}: expected '{sf.get('name')}', found '{df.get('name')}'")
            if df.get("type") != sf.get("type"):
                res.add_error(f"Field type mismatch for '{sf.get('name')}': expected '{sf.get('type')}', found '{df.get('type')}'")
            if sf.get("Record_Type_Parent") != df.get("Record_Type_Parent"):
                res.add_error(f"Record_Type_Parent mismatch for '{sf.get('name')}': expected '{sf.get('Record_Type_Parent')}', found '{df.get('Record_Type_Parent')}'")

    return res

def bejson_schema_get_field_map(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Returns a mapping of field names to their definitions.
    """
    return {f["name"]: f for f in schema.get("Fields", [])}

def bejson_schema_infer_from_data(records_type: Union[str, List[str]], fields: List[Dict[str, str]], version: str = "104a") -> Dict[str, Any]:
    """
    Utility to create a schema object from scratch.
    """
    if isinstance(records_type, str):
        records_type = [records_type]
        
    return {
        "Format": "BEJSON",
        "Format_Version": version,
        "Format_Creator": "Elton Boehnen",
        "Records_Type": records_type,
        "Fields": fields,
        "Values": []
    }

