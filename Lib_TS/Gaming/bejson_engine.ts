/**
 * Library:      bejson_engine.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  State-machine driven game engine utilizing BEJSON for entity state.
 */

// bejson_engine.ts
export class BEJSONEngine {
  public systems: Map<string, any>;
  public state: string;

  constructor() {
    this.systems = new Map();
    this.state = 'BOOT';
  }

  registerSystem(name: string, system: any) {
    this.systems.set(name, system);
  }

  getSystem(name: string): any {
    return this.systems.get(name);
  }

  loop(dt: number) {
    this.systems.forEach(s => {
      if (s.step) s.step(dt);
      if (s.update) s.update(dt);
    });
  }
}
