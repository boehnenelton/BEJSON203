/**
 * Library:      lib_bejson_physics.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  2D/3D physics calculation engine for BEJSON-based simulations.
 */

window.Core = window.Core || {};

class SwitchPhysics {
    constructor(options = {}) {
        this.gravity = options.gravity || { x: 0, y: 0 }; // Default to top-down (no gravity)
        this.friction = options.friction || 0.9;
        this.bodies = Switch.BEJSON.create104("PhysicsWorld", [
            { name: "id", type: "string" },
            { name: "x", type: "number" },
            { name: "y", type: "number" },
            { name: "w", type: "number" },
            { name: "h", type: "number" },
            { name: "vx", type: "number" },
            { name: "vy", type: "number" },
            { name: "isStatic", type: "boolean" },
            { name: "mass", type: "number" }
        ], []);
        
        // Impulse queue to be applied during step
        this.impulses = new Map();
    }

    addBody(id, x, y, w, h, options = {}) {
        this.bodies.Values.push([
            id, x, y, w, h, 
            options.vx || 0, options.vy || 0, 
            options.isStatic || false, 
            options.mass || 1
        ]);
    }

    moveBody(id, dx, dy, staticColliders = []) {
        const b = this.bodies.Values.find(v => v[0] === id);
        if (!b) return;

        const oldX = b[1];
        b[1] += dx;
        if (this._checkStaticCollisions(b, staticColliders)) {
            b[1] = oldX;
        }

        const oldY = b[2];
        b[2] += dy;
        if (this._checkStaticCollisions(b, staticColliders)) {
            b[2] = oldY;
        }
    }

    applyImpulse(id, ix, iy) {
        const b = this.bodies.Values.find(v => v[0] === id);
        if (!b) return;
        const mass = b[8] || 1;
        if (!this.impulses.has(id)) this.impulses.set(id, { x: 0, y: 0 });
        const imp = this.impulses.get(id);
        imp.x += ix / mass;
        imp.y += iy / mass;
    }

    step(dt, staticColliders = []) {
        const values = this.bodies.Values;

        for (let i = 0; i < values.length; i++) {
            const b = values[i];
            if (b[7]) continue; // isStatic

            // 1. Apply Impulses
            if (this.impulses.has(b[0])) {
                const imp = this.impulses.get(b[0]);
                b[5] += imp.x;
                b[6] += imp.y;
                this.impulses.delete(b[0]);
            }

            // 2. Apply Gravity & Friction
            b[5] += this.gravity.x * dt;
            b[6] += this.gravity.y * dt;
            b[5] *= this.friction;
            b[6] *= this.friction;

            // 3. Resolve X Axis
            const oldX = b[1];
            b[1] += b[5] * dt;
            if (this._checkStaticCollisions(b, staticColliders)) {
                b[1] = oldX;
                b[5] = 0;
            }

            // 4. Resolve Y Axis
            const oldY = b[2];
            b[2] += b[6] * dt;
            if (this._checkStaticCollisions(b, staticColliders)) {
                b[2] = oldY;
                b[6] = 0;
            }
        }

        // 5. Resolve Dynamic Collisions (Simple Swap)
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

    _checkStaticCollisions(b, colliders) {
        for (const c of colliders) {
            const cx = Array.isArray(c) ? c[0] : c.x;
            const cy = Array.isArray(c) ? c[1] : c.y;
            const cw = Array.isArray(c) ? c[2] : (c.w || c.width);
            const ch = Array.isArray(c) ? c[3] : (c.h || c.height);

            if (b[1] < cx + cw && b[1] + b[3] > cx && b[2] < cy + ch && b[2] + b[4] > cy) {
                return true;
            }
        }
        return false;
    }

    _checkAABB(a, b) {
        return (a[1] < b[1] + b[3] && a[1] + a[3] > b[1] && a[2] < b[2] + b[4] && a[2] + a[4] > b[2]);
    }

    _resolveCollision(a, b) {
        if (a[7] && b[7]) return;
        
        const m1 = a[8] || 1;
        const m2 = b[8] || 1;
        const totalMass = m1 + m2;

        const v1x = a[5];
        const v1y = a[6];
        const v2x = b[5];
        const v2y = b[6];

        if (a[7]) { // a is static
            b[5] = -v2x; b[6] = -v2y;
            return;
        }
        if (b[7]) { // b is static
            a[5] = -v1x; a[6] = -v1y;
            return;
        }

        // Elastic collision formula for 1D applied to each axis
        a[5] = ((v1x * (m1 - m2)) + (2 * m2 * v2x)) / totalMass;
        b[5] = ((v2x * (m2 - m1)) + (2 * m1 * v1x)) / totalMass;

        a[6] = ((v1y * (m1 - m2)) + (2 * m2 * v2y)) / totalMass;
        b[6] = ((v2y * (m2 - m1)) + (2 * m1 * v1y)) / totalMass;
    }
}

Switch.Physics = SwitchPhysics;
export default SwitchPhysics;
