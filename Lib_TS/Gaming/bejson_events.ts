/**
 * Library:      bejson_events.ts
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Event-driven architecture for BEJSON entity interaction.
 */

// bejson_events.ts
import { BEJSONDocument, createEmpty104 } from "./index";

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
    const ev = this.events.Values.find(v => v[0] === eventId);
    if (!ev) return;
    if (ev[5] && !this._checkCondition(ev[5] as string)) return;
    for (const cmd of ev[4] as any[]) await this._execute(cmd);
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
