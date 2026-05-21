/**
 * Library:      lib_bejson_state.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  State management and persistence layer for BEJSON documents.
 */

if (typeof window !== 'undefined') {
    window.BEJSON = window.BEJSON || {};
}

class BEJSONState {
    constructor(initialState = {}, options = {}) {
        this.schema_name = options.name || "BEJSONState";
        // Construct BEJSON 104db document directly (no namespace dependency)
        this.bejson = {
            Format: "BEJSON",
            Format_Version: "104db",
            Format_Creator: "Elton Boehnen",
            Records_Type: ["StateNode", "History"],
            Fields: [
            { name: "Record_Type_Parent", type: "string" },
            { name: "key", type: "string", Record_Type_Parent: "StateNode" },
            { name: "value", type: "string", Record_Type_Parent: "StateNode" },
            { name: "timestamp", type: "string", Record_Type_Parent: "History" },
            { name: "snapshot", type: "string", Record_Type_Parent: "History" }
        ],
            Values: []
        };

        this._listeners = new Map();
        this._historyIndex = -1;
        this._activeEffect = null;
        this._dependencyGraph = new Map(); // path -> Set of effects
        this._effectDeps = new Map();      // effect -> Set of paths

        // Reactive Proxy
        this.state = this._createProxy(initialState, '');
        
        // Initialize BEJSON values from initial state
        this._syncToBEJSON();
        this._saveHistory();
    }

    _createProxy(target, path) {
        const self = this;
        return new Proxy(target, {
            get(obj, prop) {
                const fullPath = path ? `${path}.${prop}` : prop;
                if (self._activeEffect) {
                    // Track dependency: path -> effect
                    if (!self._dependencyGraph.has(fullPath)) self._dependencyGraph.set(fullPath, new Set());
                    self._dependencyGraph.get(fullPath).add(self._activeEffect);
                    
                    // Track inverse dependency: effect -> path
                    if (!self._effectDeps.has(self._activeEffect)) self._effectDeps.set(self._activeEffect, new Set());
                    self._effectDeps.get(self._activeEffect).add(fullPath);
                }
                const value = obj[prop];
                if (value && typeof value === 'object') return self._createProxy(value, fullPath);
                return value;
            },
            set(obj, prop, value) {
                const fullPath = path ? `${path}.${prop}` : prop;
                const oldValue = obj[prop];
                if (oldValue !== value) {
                    obj[prop] = value;
                    self._syncToBEJSON();
                    self._saveHistory();
                    self._notify(fullPath, value, oldValue);
                    self._triggerEffects(fullPath);
                }
                return true;
            }
        });
    }

    _cleanupEffect(effect) {
        const paths = this._effectDeps.get(effect);
        if (paths) {
            paths.forEach(path => {
                const effects = this._dependencyGraph.get(path);
                if (effects) {
                    effects.delete(effect);
                    if (effects.size === 0) this._dependencyGraph.delete(path);
                }
            });
            paths.clear();
        }
    }

    _syncToBEJSON() {
        const fields = this.bejson.Fields;
        const fieldCount = fields.length;
        const rtpIdx = fields.findIndex(f => f.name === "Record_Type_Parent");
        const keyIdx = fields.findIndex(f => f.name === "key");
        const valIdx = fields.findIndex(f => f.name === "value");

        // Clear StateNodes
        this.bejson.Values = this.bejson.Values.filter(r => r[0] !== "StateNode");
        
        // Flatten and add
        for (const [key, value] of Object.entries(this.state)) {
            const row = new Array(fieldCount).fill(null);
            if (rtpIdx !== -1) row[rtpIdx] = "StateNode";
            if (keyIdx !== -1) row[keyIdx] = key;
            if (valIdx !== -1) row[valIdx] = JSON.stringify(value);
            this.bejson.Values.push(row);
        }
    }

    _saveHistory() {
        const fields = this.bejson.Fields;
        const fieldCount = fields.length;
        const rtpIdx = fields.findIndex(f => f.name === "Record_Type_Parent");
        const tsIdx = fields.findIndex(f => f.name === "timestamp");
        const snIdx = fields.findIndex(f => f.name === "snapshot");

        const snapshot = JSON.stringify(this.state);
        const row = new Array(fieldCount).fill(null);
        if (rtpIdx !== -1) row[rtpIdx] = "History";
        if (tsIdx !== -1) row[tsIdx] = new Date().toISOString();
        if (snIdx !== -1) row[snIdx] = snapshot;
        
        this.bejson.Values.push(row);
        const historyRows = this.bejson.Values.filter(r => r[0] === "History");
        this._historyIndex = historyRows.length - 1;
    }

    _notify(path, newValue, oldValue) {
        if (this._listeners.has(path)) this._listeners.get(path).forEach(cb => cb(newValue, oldValue, path));
        if (this._listeners.has('*')) this._listeners.get('*').forEach(cb => cb(newValue, oldValue, path));
    }

    _triggerEffects(path) {
        const effectsToRun = new Set();
        if (this._dependencyGraph.has(path)) {
            this._dependencyGraph.get(path).forEach(e => effectsToRun.add(e));
        }
        
        // Handle nested paths (e.g., user.name triggers user)
        const parts = path.split('.');
        let currentPath = '';
        for (let i = 0; i < parts.length - 1; i++) {
            currentPath += (currentPath ? '.' : '') + parts[i];
            if (this._dependencyGraph.has(currentPath)) {
                this._dependencyGraph.get(currentPath).forEach(e => effectsToRun.add(e));
            }
        }
        
        effectsToRun.forEach(effect => effect());
    }

    subscribe(path, callback) {
        if (!this._listeners.has(path)) this._listeners.set(path, new Set());
        this._listeners.get(path).add(callback);
        return () => this._listeners.get(path).delete(callback);
    }

    effect(fn) {
        const runner = () => {
            this._cleanupEffect(runner);
            this._activeEffect = runner;
            try {
                fn(this.state);
            } finally {
                this._activeEffect = null;
            }
        };
        runner();
    }

    undo() {
        const historyRows = this.bejson.Values.filter(r => r[0] === "History");
        if (this._historyIndex <= 0) return false;
        this._historyIndex--;
        this._restore(JSON.parse(historyRows[this._historyIndex][4]));
        return true;
    }

    _restore(snapshot) {
        Object.keys(this.state).forEach(k => delete this.state[k]);
        Object.assign(this.state, snapshot);
        this._notify('*', this.state, null);
    }
}

// --- Exports ---
const StateExports = {
    BEJSONState,
    State: BEJSONState
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateExports;
}
if (typeof window !== 'undefined') {
    window.BEJSON = window.BEJSON || {};
    Object.assign(window.BEJSON, StateExports);
}
