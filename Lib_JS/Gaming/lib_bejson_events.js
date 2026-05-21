/**
 * Library:      lib_bejson_events.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Event-driven architecture for BEJSON entity interaction.
 */

window.Core = window.Core || {};

class SwitchEvents {
    constructor(stateManager) {
        this.state = stateManager;
        this.events = Switch.BEJSON.create104("Events", [
            { name: "id", type: "string" },
            { name: "type", type: "string" },
            { name: "x", type: "number" },
            { name: "y", type: "number" },
            { name: "script", type: "array" },
            { name: "condition", type: "string" }
        ], []);
        // Enforce MFDB 1.3 L2 Mandatory Header
        this.events.Parent_Hierarchy = "Root/System/Events";
    }

    async run(eventId) {
        const ev = this.events.Values.find(v => v[0] === eventId);
        if (!ev) return;
        if (ev[5] && !this._checkCondition(ev[5])) return;
        for (const cmd of ev[4]) await this._execute(cmd);
    }

    _checkCondition(c) {
        if (c.startsWith("flag:")) return this.state.state[c.split(":")[1]] === true;
        return true;
    }

    async _execute(cmd) {
        const [action, ...args] = cmd;
        if (action === "SET_FLAG") this.state.state[args[0]] = args[1];
    }
}

Switch.Events = SwitchEvents;
export default SwitchEvents;
