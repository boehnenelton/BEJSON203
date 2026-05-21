/**
 * Library:      lib_bejson_engine_core.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  State-machine driven game engine utilizing BEJSON for entity state.
 */

window.Core = window.Core || {};

class ChunkManager {
    constructor(engine, options = {}) {
        this.engine = engine;
        this.chunkSize = options.chunkSize || 256; // Pixels
        this.loadRadius = options.loadRadius || 1; // 1 = 3x3 grid
        this.activeChunks = new Map(); // key -> bejson
        this.loadingChunks = new Set();
        this.basePath = options.basePath || 'data/chunks/';
    }

    getChunkKey(x, y) {
        const cx = Math.floor(x / this.chunkSize);
        const cy = Math.floor(y / this.chunkSize);
        return "" + cx + "_" + cy;
    }

    async update(camera) {
        const centerCX = Math.floor((camera.x + camera.width / 2) / this.chunkSize);
        const centerCY = Math.floor((camera.y + camera.height / 2) / this.chunkSize);

        const needed = new Set();
        for (let dy = -this.loadRadius; dy <= this.loadRadius; dy++) {
            for (let dx = -this.loadRadius; dx <= this.loadRadius; dx++) {
                const cx = centerCX + dx;
                const cy = centerCY + dy;
                needed.add("" + cx + "_" + cy);
            }
        }

        // 1. Unload distant chunks
        for (const key of this.activeChunks.keys()) {
            if (!needed.has(key)) {
                this.activeChunks.delete(key);
                console.log("[ChunkManager] Deallocated: " + key);
            }
        }

        // 2. Load new chunks
        for (const key of needed) {
            if (!this.activeChunks.has(key) && !this.loadingChunks.has(key)) {
                this.loadChunk(key);
            }
        }
    }

    async loadChunk(key) {
        this.loadingChunks.add(key);
        const url = this.basePath + "tile_chunk_" + key + ".bejson";
        try {
            console.log("[ChunkManager] Asynchronously fetching: " + url);
            const response = await fetch(url);
            if (!response.ok) throw new Error("HTTP " + response.status);
            const data = await response.json();
            this.activeChunks.set(key, data);
        } catch (e) {
            console.warn("[ChunkManager] Failed to load chunk " + key + ": " + e.message);
        } finally {
            this.loadingChunks.delete(key);
        }
    }

    getNearbyTiles() {
        const tiles = [];
        this.activeChunks.forEach(doc => {
            if (doc.Values) {
                // Assuming Tile entity in 104/104a format
                tiles.push(...doc.Values);
            }
        });
        return tiles;
    }
}

class CoreEngine {
    constructor(options = {}) {
        this.systems = new Map();
        this.state = 'BOOT';
        this.dependencies = ['ObjectRules', 'ActorStats'];
        this.chunkManager = null;
    }

    initChunking(options) {
        this.chunkManager = new ChunkManager(this, options);
    }

    checkDependencies(mfdb) {
        // Enforce inclusion order: Rules must be present before world execution
        for (const dep of this.dependencies) {
            const manifest = mfdb["104a.mfdb.bejson"];
            const entry = manifest && manifest.Values ? manifest.Values.find(v => v[0] === dep) : null;
            const path = entry ? entry[1] : null;
            if (!path || !mfdb[path]) {
                console.error("[CoreEngine] Dependency Violation: " + dep + " not loaded.");
                return false;
            }
        }
        return true;
    }

    registerSystem(name, system) {
        this.systems.set(name, system);
    }

    loop(dt) {
        if (this.state !== 'PLAYING') return;

        // 1. Gather Input & Impulse stage
        this.systems.forEach(s => {
            if (s.handleInput) s.handleInput(dt);
            if (s.gatherImpulses) s.gatherImpulses(dt);
        });

        // 2. Physics Step (with independent axis resolution)
        const physics = this.systems.get('physics');
        if (physics) {
            const colliders = this.chunkManager ? this.chunkManager.getNearbyTiles() : [];
            physics.step(dt, colliders);
        }

        // 3. General Update
        this.systems.forEach((s, name) => {
            if (name !== 'physics' && s.update) s.update(dt);
        });
    }
}

Core.Engine = CoreEngine;
Core.ChunkManager = ChunkManager;
export { CoreEngine, ChunkManager };
