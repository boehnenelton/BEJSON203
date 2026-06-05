/**
 * Library:      bejson_assets.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.1.0 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-04
 * Description:  Game asset loader and manager for BEJSON-defined resources.
 * REMEDIATED:   Implemented Field Map Indexing with Safe Get fallbacks (Migration Phase 3.3).
 */

// bejson_assets.ts
import { BEJSONDocument, createEmpty104a, bejson_core_get_field_map } from "../index";

const ASSETS_LEGACY = {
  id: 0, type: 1, path: 2, loaded: 3
} as const;

export class BEJSONAssets {
  public bejson: BEJSONDocument;
  private cache: Map<string, any>;
  private _fm: Record<string, number>;

  constructor(name: string = "AssetRegistry") {
    this.bejson = createEmpty104a(name, [
      { name: "id", type: "string" },
      { name: "type", type: "string" },
      { name: "path", type: "string" },
      { name: "loaded", type: "boolean" }
    ]);
    this.cache = new Map();
    this._fm = bejson_core_get_field_map(this.bejson);
  }

  async load(id: string, type: string, path: string): Promise<any> {
    const idIdx = this._fm["id"] ?? ASSETS_LEGACY.id;
    const typeIdx = this._fm["type"] ?? ASSETS_LEGACY.type;
    const pathIdx = this._fm["path"] ?? ASSETS_LEGACY.path;
    const loadedIdx = this._fm["loaded"] ?? ASSETS_LEGACY.loaded;

    if (this.cache.has(id)) return this.cache.get(id);

    // Register in BEJSON if not present
    let record = this.bejson.Values.find(v => v[idIdx] === id);
    if (!record) {
      record = [id, type, path, false];
      this.bejson.Values.push(record);
    }

    let asset: any;
    if (type === 'image') asset = await this._loadImage(path);
    else if (type === 'json') asset = await (await fetch(path)).json();
    
    this.cache.set(id, asset);
    record[loadedIdx] = true;

    return asset;
  }

  private _loadImage(path: string): Promise<HTMLImageElement> {
    return new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => res(img);
      img.onerror = rej;
      img.src = path;
    });
  }

  get(id: string): any { return this.cache.get(id); }
}
