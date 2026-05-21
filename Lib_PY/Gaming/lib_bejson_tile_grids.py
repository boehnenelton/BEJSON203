"""
Library:      lib_bejson_tile_grids.py
Family:       Gaming
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Grid-based world and map manager for BEJSON gaming data.
"""

class BEJSONTileGrid:
    """
    Mirror of lib_bejson_tile_grids.js
    Python/Flask-compatible tile grid manager using BEJSON 104.
    """
    def __init__(self, grid_name="UntitledGrid", width=0, height=0):
        self.width = width
        self.height = height
        self.bejson = {
            "Format": "BEJSON",
            "Format_Creator": "Elton Boehnen",
            "Format_Version": "104",
            "Records_Type": ["Layer"],
            "Fields": [
                { "name": "layer_name", "type": "string" },
                { "name": "data", "type": "array" }
            ],
            "Values": []
        }

    def create_layer(self, name, initial_value=0):
        data = [initial_value] * (self.width * self.height)
        self.bejson["Values"].append([name, data])

    def get_tile(self, layer_name, x, y):
        layer = next((row for row in self.bejson["Values"] if row[0] == layer_name), None)
        if not layer or x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        return layer[1][y * self.width + x]

    def set_tile(self, layer_name, x, y, value):
        layer = next((row for row in self.bejson["Values"] if row[0] == layer_name), None)
        if not layer or x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        layer[1][y * self.width + x] = value

    def export_bejson(self):
        import json
        return json.dumps(self.bejson, indent=2)
