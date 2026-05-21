/**
 * Library:      bejson_grid.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Universal grid-based data layout manager.
 */

// bejson_grid.ts
import { BEJSONDocument, createEmpty104 } from "./index";

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
    const layer = this.bejson.Values.find(v => v[0] === layerName);
    if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return null;
    return (layer[1] as number[])[y * this.width + x];
  }

  setTile(layerName: string, x: number, y: number, val: number) {
    const layer = this.bejson.Values.find(v => v[0] === layerName);
    if (!layer || x < 0 || x >= this.width || y < 0 || y >= this.height) return;
    (layer[1] as number[])[y * this.width + x] = val;
  }
}
