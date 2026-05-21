"""
Library:      lib_bejson_assets.py
Family:       Gaming
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Game asset loader and manager for BEJSON-defined resources.
"""

import json

class BEJSONAssetRegistry:
    """
    Mirror of lib_bejson_assets.js
    Python-compatible BEJSON-Native Asset Registry (104a).
    """
    def __init__(self, name="AssetRegistry"):
        self.bejson = {
            "Format": "BEJSON",
            "Format_Creator": "Elton Boehnen",
            "Format_Version": "104a",
            "Schema_Name": name,
            "Records_Type": ["Asset"],
            "Fields": [
                { "name": "id", "type": "string" },
                { "name": "type", "type": "string" },
                { "name": "path", "type": "string" },
                { "name": "loaded", "type": "boolean" }
            ],
            "Values": []
        }
        self.cache = {}

    def register_asset(self, asset_id, asset_type, path):
        """Adds or updates an asset in the registry."""
        idx = next((i for i, v in enumerate(self.bejson["Values"]) if v[0] == asset_id), -1)
        if idx != -1:
            self.bejson["Values"][idx] = [asset_id, asset_type, path, False]
        else:
            self.bejson["Values"].append([asset_id, asset_type, path, False])

    def mark_loaded(self, asset_id, loaded=True):
        idx = next((i for i, v in enumerate(self.bejson["Values"]) if v[0] == asset_id), -1)
        if idx != -1:
            self.bejson["Values"][idx][3] = loaded

    def export_bejson(self):
        return json.dumps(self.bejson, indent=2)
