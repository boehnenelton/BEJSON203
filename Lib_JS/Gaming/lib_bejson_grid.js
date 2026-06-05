/**
 * Library:      lib_bejson_grid.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Universal grid-based data layout manager.
 */

window.Core = window.Core || {};

class SwitchGrid {
    constructor(name, width, height) {
        this.width = width;
        this.height = height;
        this.bejson = BEJSON_Switch.BEJSON.create104(name, [
            { name: "layer_name", type: "string" },
            { name: "data", type: "array" }
        ], []);
    }

    createLayer(name, initialValue = 0) {
        const data = new Array(this.width * this.height).fill(initialValue);
        this.bejson.Values.push([name, data]);
    }

    getTile(layerName, x, y) {
        const layer = this.bejson.Values.find(v => v[0] === layerName);
        if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return null;
        return layer[1][y * this.width + x];
    }

    setTile(layerName, x, y, val) {
        const layer = this.bejson.Values.find(v => v[0] === layerName);
        if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return;
        layer[1][y * this.width + x] = val;
    }
}

BEJSON_Switch.Grid = SwitchGrid;
export default SwitchGrid;
