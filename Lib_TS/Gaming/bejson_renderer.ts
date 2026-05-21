/**
 * Library:      bejson_renderer.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Graphics rendering abstraction for BEJSON-based visuals.
 */

// bejson_renderer.ts
export class BEJSONRenderer {
  public canvas: HTMLCanvasElement | null;
  public ctx: CanvasRenderingContext2D | null;
  public dpr: number;
  public camera: { x: number; y: number; zoom: number };

  constructor(canvasId: string) {
    if (typeof document === 'undefined') {
        this.canvas = null;
        this.ctx = null;
        this.dpr = 1;
        this.camera = { x: 0, y: 0, zoom: 1 };
        return;
    }
    this.canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!this.canvas) {
      console.error(`BEJSON.Renderer: Canvas #${canvasId} not found.`);
      this.ctx = null;
      this.dpr = 1;
      this.camera = { x: 0, y: 0, zoom: 1 };
      return;
    }
    this.ctx = this.canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    this.camera = { x: 0, y: 0, zoom: 1 };
    
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas || !this.ctx) return;
    const rect = this.canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    this.canvas.width = rect.width * this.dpr;
    this.canvas.height = rect.height * this.dpr;
    
    this.ctx.setTransform(this.dpr * this.camera.zoom, 0, 0, this.dpr * this.camera.zoom, 0, 0);
  }

  clear(color: string = "#000") {
    if (!this.ctx || !this.canvas) return;
    this.ctx.save();
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.fillStyle = color;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.restore();
  }

  drawRect(x: number, y: number, w: number, h: number, color: string, isHUD: boolean = false) {
    if (!this.ctx) return;
    this.ctx.fillStyle = color;
    const tx = isHUD ? x : x - this.camera.x;
    const ty = isHUD ? y : y - this.camera.y;
    this.ctx.fillRect(tx, ty, w, h);
  }

  drawCircle(x: number, y: number, radius: number, color: string, isHUD: boolean = false) {
    if (!this.ctx) return;
    this.ctx.fillStyle = color;
    const tx = isHUD ? x : x - this.camera.x;
    const ty = isHUD ? y : y - this.camera.y;
    this.ctx.beginPath();
    this.ctx.arc(tx, ty, radius, 0, Math.PI * 2);
    this.ctx.fill();
  }

  drawText(text: string, x: number, y: number, options: any = {}) {
    if (!this.ctx) return;
    this.ctx.fillStyle = options.color || "#fff";
    this.ctx.font = options.font || "16px sans-serif";
    const tx = options.isHUD ? x : x - this.camera.x;
    const ty = options.isHUD ? y : y - this.camera.y;
    this.ctx.fillText(text, tx, ty);
  }

  drawTileLayer(grid: any, tileset: HTMLImageElement, tileSize: number) {
    if (!this.ctx || !grid || !tileset || !this.canvas) return;
    
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
