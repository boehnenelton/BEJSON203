/**
 * Library:      bejson_assets.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Game asset loader and manager for BEJSON-defined resources.
 */

// bejson_assets.ts
import { BEJSONDocument, createEmpty104a } from "./index";

export class BEJSONAssets {
  public bejson: BEJSONDocument;
  private cache: Map<string, any>;

  constructor(name: string = "AssetRegistry") {
    this.bejson = createEmpty104a(name, [
      { name: "id", type: "string" },
      { name: "type", type: "string" },
      { name: "path", type: "string" },
      { name: "loaded", type: "boolean" }
    ]);
    this.cache = new Map();
  }

  async load(id: string, type: string, path: string): Promise<any> {
    if (this.cache.has(id)) return this.cache.get(id);
    let asset: any;
    if (type === 'image') asset = await this._loadImage(path);
    else if (type === 'json') asset = await (await fetch(path)).json();
    this.cache.set(id, asset);
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
