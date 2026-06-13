/**
 * Library:      lib_bejson_assets.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Game asset loader and manager for BEJSON-defined resources.
 */

window.Core = window.Core || {};

class SwitchAssets {
    constructor(name = "AssetRegistry") {
        this.bejson = BEJSON_Switch.BEJSON.create104a(name, [
            { name: "id", type: "string" },
            { name: "type", type: "string" },
            { name: "path", type: "string" },
            { name: "loaded", type: "boolean" }
        ], []);
        this.cache = new Map();
    }

    async load(id, type, path) {
        if (this.cache.has(id)) return this.cache.get(id);
        let asset;
        if (type === 'image') asset = await this._loadImage(path);
        else if (type === 'json') asset = await (await fetch(path)).json();
        this.cache.set(id, asset);
        return asset;
    }

    _loadImage(path) {
        return new Promise((res, rej) => {
            const img = new Image();
            img.onload = () => res(img);
            img.onerror = rej;
            img.src = path;
        });
    }

    get(id) { return this.cache.get(id); }
}

BEJSON_Switch.Assets = SwitchAssets;
export default SwitchAssets;
