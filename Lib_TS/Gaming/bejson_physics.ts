/**
 * Library:      bejson_physics.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  2D/3D physics calculation engine for BEJSON-based simulations.
 */

// bejson_physics.ts
import { BEJSONDocument, createEmpty104 } from "./index";

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

    if (!b) return;
    (b[5] as number) += ix;
    (b[6] as number) += iy;
  }

    if (!b) return;

    const oldX = b[1] as number;
    (b[1] as number) += dx;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[1] as number) = oldX;
    }

    const oldY = b[2] as number;
    (b[2] as number) += dy;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[2] as number) = oldY;
    }
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
    const b = this.bodies.Values.find(v => v[0] === id);
    if (!b) return;
    (b[5] as number) += ix;
    (b[6] as number) += iy;
  }

  moveBody(id: string, dx: number, dy: number, staticColliders: any[] = []) {
    const b = this.bodies.Values.find(v => v[0] === id);
    if (!b) return;

    const oldX = b[1] as number;
    (b[1] as number) += dx;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[1] as number) = oldX;
    }

    const oldY = b[2] as number;
    (b[2] as number) += dy;
    if (this._checkStaticCollisions(b, staticColliders)) {
        (b[2] as number) = oldY;
    }
  }


  step(dt: number, staticColliders: any[] = []) {
    const values = this.bodies.Values;
    // 1. Integrate & Resolve Static
    for (let i = 0; i < values.length; i++) {
      const b = values[i];
      if (b[7]) continue; // isStatic

      (b[5] as number) += this.gravity.x * dt; // vx
      (b[6] as number) += this.gravity.y * dt; // vy
      
      // Friction (Standardized 0.9)
      (b[5] as number) *= 0.9;
      (b[6] as number) *= 0.9;

      // X Axis
      const oldX = b[1] as number;
      (b[1] as number) += (b[5] as number) * dt;
      if (this._checkStaticCollisions(b, staticColliders)) {
          (b[1] as number) = oldX;
          (b[5] as number) = 0;
      }

      // Y Axis
      const oldY = b[2] as number;
      (b[2] as number) += (b[6] as number) * dt;
      if (this._checkStaticCollisions(b, staticColliders)) {
          (b[2] as number) = oldY;
          (b[6] as number) = 0;
      }
    }

    // 2. Resolve Dynamic (Simple Swap)
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
    for (const c of colliders) {
      const cx = Array.isArray(c) ? c[0] : c.x;
      const cy = Array.isArray(c) ? c[1] : c.y;
      const cw = Array.isArray(c) ? c[2] : (c.w || c.width);
      const ch = Array.isArray(c) ? c[3] : (c.h || c.height);

      if ((b[1] as number) < cx + cw && (b[1] as number) + (b[3] as number) > cx && 
          (b[2] as number) < cy + ch && (b[2] as number) + (b[4] as number) > cy) {
        return true;
      }
    }
    return false;
  }

  private _checkAABB(a: any[], b: any[]) {
    return ((a[1] as number) < (b[1] as number) + (b[3] as number) && 
            (a[1] as number) + (a[3] as number) > (b[1] as number) && 
            (a[2] as number) < (b[2] as number) + (b[4] as number) && 
            (a[2] as number) + (a[4] as number) > (b[2] as number));
  }

  private _resolveCollision(a: any[], b: any[]) {
    if (a[7] && b[7]) return; // both static
    
    // Simple push-apart logic would go here, 
    // for now we just swap velocities for dynamic-dynamic
    const tempVx = a[5]; a[5] = b[5]; b[5] = tempVx;
    const tempVy = a[6]; a[6] = b[6]; b[6] = tempVy;
  }
}
