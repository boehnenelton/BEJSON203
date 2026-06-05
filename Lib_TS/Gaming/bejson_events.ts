/**
 * Library:      bejson_events.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.1.0 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-04
 * Description:  Event-driven architecture for BEJSON entity interaction.
 * REMEDIATED:   Implemented Field Map Indexing with Safe Get fallbacks (Migration Phase 3.2).
 */

// bejson_events.ts
import { BEJSONDocument, createEmpty104, bejson_core_get_field_map } from "../index";

const EVENTS_LEGACY = {
  id: 0, type: 1, x: 2, y: 3, script: 4, condition: 5
} as const;

export class BEJSONEvents {
  public events: BEJSONDocument;
  private stateManager: any;

  constructor(stateManager: any) {
    this.stateManager = stateManager;
    this.events = createEmpty104("Events", [
      { name: "id", type: "string" },
      { name: "type", type: "string" },
      { name: "x", type: "number" },
      { name: "y", type: "number" },
      { name: "script", type: "array" },
      { name: "condition", type: "string" }
    ], "Root/System/Events");
  }

  async run(eventId: string): Promise<void> {
    const fm = bejson_core_get_field_map(this.events);
    const idIdx = fm["id"] ?? EVENTS_LEGACY.id;
    const scriptIdx = fm["script"] ?? EVENTS_LEGACY.script;
    const condIdx = fm["condition"] ?? EVENTS_LEGACY.condition;

    const ev = this.events.Values.find(v => v[idIdx] === eventId);
    if (!ev) return;
    if (ev[condIdx] && !this._checkCondition(ev[condIdx] as string)) return;
    for (const cmd of ev[scriptIdx] as any[]) await this._execute(cmd);
  }

  private _checkCondition(c: string): boolean {
    if (c.startsWith("flag:")) return this.stateManager.state[c.split(":")[1]] === true;
    return true;
  }

  private async _execute(cmd: any[]): Promise<void> {
    const [action, ...args] = cmd;
    if (action === "SET_FLAG") this.stateManager.state[args[0]] = args[1];
  }
}
