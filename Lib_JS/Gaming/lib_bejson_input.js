/**
 * Library:      lib_bejson_input.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  User input mapping and handling for interactive BEJSON applications.
 */

window.Core = window.Core || {};

class SwitchInput {
    constructor(options = {}) {
        this.deadzone = options.deadzone || 12;
        this.bindings = {
            up: ['ArrowUp', 'w'], down: ['ArrowDown', 's'],
            left: ['ArrowLeft', 'a'], right: ['ArrowRight', 'd'],
            action: ['Enter', ' '], cancel: ['Escape', 'x'], menu: ['m', 'Tab']
        };

        this.keys = {};
        this.justPressed = {};
        this.touch = { active: false, startX: 0, startY: 0, currentX: 0, currentY: 0, vector: { x: 0, y: 0 } };

        window.addEventListener('keydown', (e) => this._onKey(e, true));
        window.addEventListener('keyup', (e) => this._onKey(e, false));
        window.addEventListener('touchstart', (e) => this._onTouchStart(e), { passive: false });
        window.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
        window.addEventListener('touchend', (e) => this._onTouchEnd(e));
    }

    _onKey(e, isDown) {
        if (isDown && !this.keys[e.key]) this.justPressed[e.key] = true;
        this.keys[e.key] = isDown;
    }

    _onTouchStart(e) {
        const t = e.touches[0];
        this.touch.active = true;
        this.touch.startX = t.clientX; this.touch.startY = t.clientY;
        this.touch.currentX = t.clientX; this.touch.currentY = t.clientY;
    }

    _onTouchMove(e) {
        if (!this.touch.active) return;
        const t = e.touches[0];
        this.touch.currentX = t.clientX; this.touch.currentY = t.clientY;
        
        let dx = this.touch.currentX - this.touch.startX;
        let dy = this.touch.currentY - this.touch.startY;
        let dist = Math.sqrt(dx * dx + dy * dy);

        // Floating Joystick (Dynamic Anchor) fix
        const maxRadius = 40; 
        if (dist > maxRadius) {
            const angle = Math.atan2(dy, dx);
            this.touch.startX = this.touch.currentX - Math.cos(angle) * maxRadius;
            this.touch.startY = this.touch.currentY - Math.sin(angle) * maxRadius;
            dx = this.touch.currentX - this.touch.startX;
            dy = this.touch.currentY - this.touch.startY;
            dist = maxRadius;
        }

        if (dist > this.deadzone) {
            this.touch.vector.x = dx / maxRadius;
            this.touch.vector.y = dy / maxRadius;
        } else {
            this.touch.vector.x = 0; this.touch.vector.y = 0;
        }
    }

    _onTouchEnd(e) { this.touch.active = false; this.touch.vector.x = 0; this.touch.vector.y = 0; }

    getVector() {
        let vx = 0, vy = 0;
        if (this._isBoundDown('left')) vx -= 1;
        if (this._isBoundDown('right')) vx += 1;
        if (this._isBoundDown('up')) vy -= 1;
        if (this._isBoundDown('down')) vy += 1;
        if (this.touch.active) { vx += this.touch.vector.x; vy += this.touch.vector.y; }
        const mag = Math.sqrt(vx * vx + vy * vy);
        if (mag > 1) { vx /= mag; vy /= mag; }
        return { x: vx, y: vy, action: this._isBoundJustPressed('action'), cancel: this._isBoundJustPressed('cancel'), menu: this._isBoundJustPressed('menu') };
    }

    _isBoundDown(a) { return this.bindings[a].some(k => this.keys[k]); }
    _isBoundJustPressed(a) { return this.bindings[a].some(k => this.justPressed[k]); }
    update() { this.justPressed = {}; }
}

Switch.Input = SwitchInput;
export default SwitchInput;
