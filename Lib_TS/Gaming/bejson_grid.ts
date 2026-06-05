/**
 * Library:      bejson_grid.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.1.0 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-04
 * Description:  Universal grid-based data layout manager.
 * REMEDIATED:   Implemented Field Map Indexing with Safe Get fallbacks (Migration Phase 3.6).
 */

// bejson_grid.ts
import { BEJSONDocument, createEmpty104, bejson_core_get_field_map } from "../index";

const GRID_LEGACY = {
  layer_name: 0, data: 1
} as const;

export class BEJSONGrid {
  public width: number;
  public height: number;
  public bejson: BEJSONDocument;

  constructor(name: string, width: number, height: number) {
    this.width = width;
    this.height = height;
    this.bejson = createEmpty104(name, [
      { name: "layer_name", type: "string" },
      { name: "data", type: "array" }
    ]);
  }

  createLayer(name: string, initialValue: number = 0) {
    const data = new Array(this.width * this.height).fill(initialValue);
    this.bejson.Values.push([name, data]);
  }

  getTile(layerName: string, x: number, y: number): number | null {
    const fm = bejson_core_get_field_map(this.bejson);
    const lnIdx = fm["layer_name"] ?? GRID_LEGACY.layer_name;
    const dataIdx = fm["data"] ?? GRID_LEGACY.data;

    const layer = this.bejson.Values.find(v => v[lnIdx] === layerName);
    if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return null;
    return (layer[dataIdx] as number[])[y * this.width + x];
  }

  setTile(layerName: string, x: number, y: number, val: number) {
    const fm = bejson_core_get_field_map(this.bejson);
    const lnIdx = fm["layer_name"] ?? GRID_LEGACY.layer_name;
    const dataIdx = fm["data"] ?? GRID_LEGACY.data;

    const layer = this.bejson.Values.find(v => v[lnIdx] === layerName);
    if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return;
    (layer[dataIdx] as number[])[y * this.width + x] = val;
  }
}
