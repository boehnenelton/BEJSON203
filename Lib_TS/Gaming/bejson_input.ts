/**
 * Library:      bejson_input.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  User input mapping and handling for interactive BEJSON applications.
 */

// bejson_input.ts
export class BEJSONInput {
  public deadzone: number;
  public keys: Record<string, boolean>;
  public justPressed: Record<string, boolean>;
  public touch: { active: boolean; x: number; y: number; vector: { x: number; y: number } };
  public controls: any;

  constructor(options: any = {}) {
    this.deadzone = options.deadzone || 12;
    this.keys = {};
    this.justPressed = {};
    this.touch = { active: false, x: 0, y: 0, vector: { x: 0, y: 0 } };
    
    this.controls = {
      joystick: { x: 80, y: 0, radius: 50, active: false, handleX: 0, handleY: 0 },
      btnA: { x: 0, y: 0, radius: 30, pressed: false },
      btnB: { x: 0, y: 0, radius: 30, pressed: false }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', (e) => this._onKey(e, true));
      window.addEventListener('keyup', (e) => this._onKey(e, false));
      window.addEventListener('touchstart', (e) => this._onTouch(e, true), { passive: false });
      window.addEventListener('touchmove', (e) => this._onTouch(e, true), { passive: false });
      window.addEventListener('touchend', (e) => this._onTouch(e, false));
    }
  }

  private _onKey(e: KeyboardEvent, isDown: boolean) {
    if (isDown && !this.keys[e.key]) this.justPressed[e.key] = true;
    this.keys[e.key] = isDown;
  }

  private _onTouch(e: TouchEvent, isActive: boolean) {
    if (!isActive) {
      this.touch.active = false;
      this.controls.joystick.active = false;
      this.controls.joystick.handleX = 0;
      this.controls.joystick.handleY = 0;
      this.controls.btnA.pressed = false;
      this.controls.btnB.pressed = false;
      return;
    }

    const canvas = document.querySelector('canvas');
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    for (let i = 0; i < e.touches.length; i++) {
      const t = e.touches[i];
      const tx = t.clientX - rect.left;
      const ty = t.clientY - rect.top;

      // Check Joystick (Floating Joystick / Dynamic Anchor fix)
      const j = this.controls.joystick;
      const distJ = Math.sqrt((tx - j.x)**2 + (ty - j.y)**2);
      
      if (distJ < j.radius * 2 || j.active) {
        j.active = true;
        let dx = tx - j.x;
        let dy = ty - j.y;
        let dist = Math.sqrt(dx*dx + dy*dy);
        const limit = j.radius;

        if (dist > limit) {
          const angle = Math.atan2(dy, dx);
          j.x = tx - Math.cos(angle) * limit;
          j.y = ty - Math.sin(angle) * limit;
          dx = tx - j.x;
          dy = ty - j.y;
          dist = limit;
        }

        j.handleX = dx;
        j.handleY = dy;
        this.touch.vector.x = j.handleX / limit;
        this.touch.vector.y = j.handleY / limit;
      }

      // Check Buttons
      if (this._checkCircle(tx, ty, this.controls.btnA)) {
        if (!this.controls.btnA.pressed) this.justPressed['action'] = true;
        this.controls.btnA.pressed = true;
      }
      if (this._checkCircle(tx, ty, this.controls.btnB)) {
        if (!this.controls.btnB.pressed) this.justPressed['cancel'] = true;
        this.controls.btnB.pressed = true;
      }
    }
    if (e.cancelable) e.preventDefault();
  }

  private _checkCircle(tx: number, ty: number, circle: any) {
    const dist = Math.sqrt((tx - circle.x)**2 + (ty - circle.y)**2);
    return dist < circle.radius;
  }

  private _isBoundDown(action: string) {
    const bindings: Record<string, string[]> = {
      up: ['ArrowUp', 'w', 'W'], down: ['ArrowDown', 's', 'S'],
      left: ['ArrowLeft', 'a', 'A'], right: ['ArrowRight', 'd', 'D'],
      action: ['Enter', ' '], cancel: ['Escape', 'x', 'X'], menu: ['m', 'M', 'Tab']
    };
    return bindings[action].some(k => this.keys[k]);
  }

  public getVector() {
    let vx = 0, vy = 0;
    if (this._isBoundDown('left')) vx -= 1;
    if (this._isBoundDown('right')) vx += 1;
    if (this._isBoundDown('up')) vy -= 1;
    if (this._isBoundDown('down')) vy += 1;

    if (this.controls.joystick.active) {
      vx += this.touch.vector.x;
      vy += this.touch.vector.y;
    }

    const mag = Math.sqrt(vx * vx + vy * vy);
    if (mag > 1) { vx /= mag; vy /= mag; }
    return { x: vx, y: vy, action: this.justPressed['action'], cancel: this.justPressed['cancel'] };
  }

  public update() {
    this.justPressed = {};
  }

  public renderControls(renderer: any) {
    const j = this.controls.joystick;
    const canvas = renderer.canvas;
    const h = canvas.height / renderer.dpr;
    const w = canvas.width / renderer.dpr;

    j.y = h - 80;
    
    renderer.drawCircle(j.x, j.y, j.radius, "rgba(255,255,255,0.2)", true);
    renderer.drawCircle(j.x + j.handleX, j.y + j.handleY, j.radius/2, "rgba(255,255,255,0.5)", true);

    const bA = this.controls.btnA;
    const bB = this.controls.btnB;
    bA.x = w - 60; bA.y = h - 100;
    bB.x = w - 120; bB.y = h - 60;

    renderer.drawCircle(bA.x, bA.y, bA.radius, bA.pressed ? "#f56565" : "rgba(255,255,255,0.3)", true);
    renderer.drawText("A", bA.x - 5, bA.y + 5, { isHUD: true });

    renderer.drawCircle(bB.x, bB.y, bB.radius, bB.pressed ? "#4299e1" : "rgba(255,255,255,0.3)", true);
    renderer.drawText("B", bB.x - 5, bB.y + 5, { isHUD: true });
  }
}
