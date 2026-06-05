/**
 * Library:      bejson_physics.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.1.0 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-04
 * Description:  2D/3D physics calculation engine for BEJSON-based simulations.
 * REMEDIATED:   Implemented Field Map Indexing with Safe Get fallbacks (Migration Phase 3.1).
 */

import { BEJSONDocument, createEmpty104, bejson_core_get_field_map } from "../index";

const PHYSICS_LEGACY = {
  id: 0, x: 1, y: 2, w: 3, h: 4, vx: 5, vy: 6, isStatic: 7, mass: 8
} as const;

export class BEJSONPhysics {
  public gravity: { x: number; y: number };
  public bodies: BEJSONDocument;

  constructor(options: any = {}) {
    this.gravity = options.gravity || { x: 0, y: 9.8 };
    this.bodies = createEmpty104("PhysicsWorld", [
      { name: "id", type: "string" },
      { name: "x", type: "number" },
      { name: "y", type: "number" },
      { name: "w", type: "number" },
      { name: "h", type: "number" },
      { name: "vx", type: "number" },
      { name: "vy", type: "number" },
      { name: "isStatic", type: "boolean" },
      { name: "mass", type: "number" }
    ]);
  }

  addBody(id: string, x: number, y: number, w: number, h: number, options: any = {}) {
    this.bodies.Values.push([
      id, x, y, w, h, 
      options.vx || 0, options.vy || 0, 
      options.isStatic || false, 
      options.mass || 1
    ]);
  }

  applyImpulse(id: string, ix: number, iy: number) {
    const fm = bejson_core_get_field_map(this.bodies);
    const idIdx = fm["id"] ?? PHYSICS_LEGACY.id;
    const vxIdx = fm["vx"] ?? PHYSICS_LEGACY.vx;
    const vyIdx = fm["vy"] ?? PHYSICS_LEGACY.vy;
    const massIdx = fm["mass"] ?? PHYSICS_LEGACY.mass;

    const b = this.bodies.Values.find(v => v[idIdx] === id);
    if (!b) return;
    const mass = (b[massIdx] as number) || 1;
    (b[vxIdx] as number) += ix / mass;
    (b[vyIdx] as number) += iy / mass;
  }

  moveBody(id: string, dx: number, dy: number, staticColliders: any[] = []) {
    const fm = bejson_core_get_field_map(this.bodies);
    const idIdx = fm["id"] ?? PHYSICS_LEGACY.id;
    const xIdx = fm["x"] ?? PHYSICS_LEGACY.x;
    const yIdx = fm["y"] ?? PHYSICS_LEGACY.y;

    const b = this.bodies.Values.find(v => v[idIdx] === id);
    if (!b) return;

    const oldX = b[xIdx] as number;
    (b[xIdx] as number) += dx;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[xIdx] as number) = oldX;
    }

    const oldY = b[yIdx] as number;
    (b[yIdx] as number) += dy;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[yIdx] as number) = oldY;
    }
  }

  step(dt: number, staticColliders: any[] = []) {
    const fm = bejson_core_get_field_map(this.bodies);
    const xIdx = fm["x"] ?? PHYSICS_LEGACY.x;
    const yIdx = fm["y"] ?? PHYSICS_LEGACY.y;
    const vxIdx = fm["vx"] ?? PHYSICS_LEGACY.vx;
    const vyIdx = fm["vy"] ?? PHYSICS_LEGACY.vy;
    const isStaticIdx = fm["isStatic"] ?? PHYSICS_LEGACY.isStatic;

    const values = this.bodies.Values;
    for (let i = 0; i < values.length; i++) {
      const b = values[i];
      if (b[isStaticIdx]) continue;

      (b[vxIdx] as number) += this.gravity.x * dt;
      (b[vyIdx] as number) += this.gravity.y * dt;
      
      (b[vxIdx] as number) *= 0.9;
      (b[vyIdx] as number) *= 0.9;

      const oldX = b[xIdx] as number;
      (b[xIdx] as number) += (b[vxIdx] as number) * dt;
      if (this._checkStaticCollisions(b, staticColliders)) {
          (b[xIdx] as number) = oldX;
          (b[vxIdx] as number) = 0;
      }

      const oldY = b[yIdx] as number;
      (b[yIdx] as number) += (b[vyIdx] as number) * dt;
      if (this._checkStaticCollisions(b, staticColliders)) {
          (b[yIdx] as number) = oldY;
          (b[vyIdx] as number) = 0;
      }
    }

    for (let i = 0; i < values.length; i++) {
      const bA = values[i];
      for (let j = i + 1; j < values.length; j++) {
        const bB = values[j];
        if (this._checkAABB(bA, bB)) {
          this._resolveCollision(bA, bB);
        }
      }
    }
  }

  private _checkStaticCollisions(b: any[], colliders: any[]) {
    const fm = bejson_core_get_field_map(this.bodies);
    const xIdx = fm["x"] ?? PHYSICS_LEGACY.x;
    const yIdx = fm["y"] ?? PHYSICS_LEGACY.y;
    const wIdx = fm["w"] ?? PHYSICS_LEGACY.w;
    const hIdx = fm["h"] ?? PHYSICS_LEGACY.h;

    for (const c of colliders) {
      const cx = Array.isArray(c) ? c[0] : c.x;
      const cy = Array.isArray(c) ? c[1] : c.y;
      const cw = Array.isArray(c) ? c[2] : (c.w || c.width);
      const ch = Array.isArray(c) ? c[3] : (c.h || c.height);

      if ((b[xIdx] as number) < cx + cw && (b[xIdx] as number) + (b[wIdx] as number) > cx && 
          (b[yIdx] as number) < cy + ch && (b[yIdx] as number) + (b[hIdx] as number) > cy) {
        return true;
      }
    }
    return false;
  }

  private _checkAABB(a: any[], b: any[]) {
    const fm = bejson_core_get_field_map(this.bodies);
    const xIdx = fm["x"] ?? PHYSICS_LEGACY.x;
    const yIdx = fm["y"] ?? PHYSICS_LEGACY.y;
    const wIdx = fm["w"] ?? PHYSICS_LEGACY.w;
    const hIdx = fm["h"] ?? PHYSICS_LEGACY.h;

    return ((a[xIdx] as number) < (b[xIdx] as number) + (b[wIdx] as number) && 
            (a[xIdx] as number) + (a[wIdx] as number) > (b[xIdx] as number) && 
            (a[yIdx] as number) < (b[yIdx] as number) + (b[hIdx] as number) && 
            (a[yIdx] as number) + (a[hIdx] as number) > (b[yIdx] as number));
  }

  private _resolveCollision(a: any[], b: any[]) {
    const fm = bejson_core_get_field_map(this.bodies);
    const vxIdx = fm["vx"] ?? PHYSICS_LEGACY.vx;
    const vyIdx = fm["vy"] ?? PHYSICS_LEGACY.vy;
    const isStaticIdx = fm["isStatic"] ?? PHYSICS_LEGACY.isStatic;
    const massIdx = fm["mass"] ?? PHYSICS_LEGACY.mass;

    if (a[isStaticIdx] && b[isStaticIdx]) return;
    
    const m1 = (a[massIdx] as number) || 1;
    const m2 = (b[massIdx] as number) || 1;
    const totalMass = m1 + m2;

    const v1x = a[vxIdx] as number;
    const v1y = a[vyIdx] as number;
    const v2x = b[vxIdx] as number;
    const v2y = b[vyIdx] as number;

    if (a[isStaticIdx]) {
        (b[vxIdx] as number) = -v2x; 
        (b[vyIdx] as number) = -v2y;
        return;
    }
    if (b[isStaticIdx]) {
        (a[vxIdx] as number) = -v1x; 
        (a[vyIdx] as number) = -v1y;
        return;
    }

    (a[vxIdx] as number) = ((v1x * (m1 - m2)) + (2 * m2 * v2x)) / totalMass;
    (b[vxIdx] as number) = ((v2x * (m2 - m1)) + (2 * m1 * v1x)) / totalMass;

    (a[vyIdx] as number) = ((v1y * (m1 - m2)) + (2 * m2 * v2y)) / totalMass;
    (b[vyIdx] as number) = ((v2y * (m2 - m1)) + (2 * m1 * v1y)) / totalMass;
  }
}
