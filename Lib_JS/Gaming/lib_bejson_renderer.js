/**
 * Library:      lib_bejson_renderer.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Graphics rendering abstraction for BEJSON-based visuals.
 */

window.Core = window.Core || {};

class SwitchRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error("Switch.Renderer: Canvas #" + canvasId + " not found.");
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.dpr = window.devicePixelRatio || 1;
        this.camera = { x: 0, y: 0, width: 256, height: 256, zoom: 1 };
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        this.canvas.width = rect.width * this.dpr;
        this.canvas.height = rect.height * this.dpr;
        
        // Reset transform and apply DPR scaling + Zoom
        this.ctx.setTransform(this.dpr * this.camera.zoom, 0, 0, this.dpr * this.camera.zoom, 0, 0);
    }

    clear(color = "#000") {
        if (!this.ctx) return;
        this.ctx.save();
        this.ctx.setTransform(1, 0, 0, 1, 0, 0); // Reset for full clear
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.restore();
    }

    drawRect(x, y, w, h, color, isHUD = false) {
        if (!this.ctx) return;
        this.ctx.fillStyle = color;
        const tx = isHUD ? x : x - this.camera.x;
        const ty = isHUD ? y : y - this.camera.y;
        this.ctx.fillRect(tx, ty, w, h);
    }

    drawText(text, x, y, options = {}) {
        if (!this.ctx) return;
        this.ctx.fillStyle = options.color || "#fff";
        this.ctx.font = options.font || "16px sans-serif";
        const tx = options.isHUD ? x : x - this.camera.x;
        const ty = options.isHUD ? y : y - this.camera.y;
        this.ctx.fillText(text, tx, ty);
    }

    drawChunkedLayer(chunkManager, tileset, tileSize) {
        if (!this.ctx || !chunkManager || !tileset) return;
        
        const width = this.canvas.width / (this.dpr * this.camera.zoom);
        const height = this.canvas.height / (this.dpr * this.camera.zoom);

        chunkManager.activeChunks.forEach(doc => {
            if (!doc.Values) return;
            
            for (const tile of doc.Values) {
                // BEJSON 104 Tile: [tile_id, level_id, x, y, terrain, object]
                const tx = tile[2] * tileSize;
                const ty = tile[3] * tileSize;
                
                // Frustum Culling
                if (tx + tileSize < this.camera.x || tx > this.camera.x + width || 
                    ty + tileSize < this.camera.y || ty > this.camera.y + height) {
                    continue;
                }

                const terrain = tile[4];
                if (!terrain) continue;

                // Simple tile mapping (assuming 16x16 sheet)
                // This is a placeholder for actual sprite logic
                this.ctx.drawImage(
                    tileset,
                    0, 0, tileSize, tileSize, // Source (stub)
                    tx - this.camera.x,
                    ty - this.camera.y,
                    tileSize, tileSize
                );
            }
        });
    }

    drawTileLayer(grid, tileset, tileSize) {
        // Backward compatibility for non-chunked grids
        if (!this.ctx || !grid || !tileset) return;
        
        const width = this.canvas.width / (this.dpr * this.camera.zoom);
        const height = this.canvas.height / (this.dpr * this.camera.zoom);

        const startCol = Math.max(0, Math.floor(this.camera.x / tileSize));
        const endCol = Math.min(grid.width, Math.ceil((this.camera.x + width) / tileSize));
        const startRow = Math.max(0, Math.floor(this.camera.y / tileSize));
        const endRow = Math.min(grid.height, Math.ceil((this.camera.y + height) / tileSize));

        for (let r = startRow; r < endRow; r++) {
            for (let c = startCol; c < endCol; c++) {
                const tile = grid.data[r * grid.width + c];
                if (tile === 0) continue;
                
                const sx = (tile % 16) * tileSize;
                const sy = Math.floor(tile / 16) * tileSize;
                
                this.ctx.drawImage(
                    tileset, 
                    sx, sy, tileSize, tileSize, 
                    c * tileSize - this.camera.x, 
                    r * tileSize - this.camera.y, 
                    tileSize, tileSize
                );
            }
        }
    }
}

Switch.Renderer = SwitchRenderer;
export default SwitchRenderer;
