# BEJSON Library — Field Map Indexing Migration Plan
**Version:** 1.0  
**Author:** Elton Boehnen  
**Contact:** eltonboehnen@gmail.com · boehnenelton2024.pages.dev · github.com/boehnenelton  
**Spec Reference:** BEJSON v104/104a/104db · MFDB v1.31  
**Applies To:** Lib_PY v2.0.1 · Lib_TS v2.0.1 · Lib_JS v2.0.2 · Lib_SH v2.0.3

---

## Table of Contents

1. [Overview & Mandate](#1-overview--mandate)
2. [Non-Negotiable Ground Rules](#2-non-negotiable-ground-rules)
3. [Pattern Reference Guide](#3-pattern-reference-guide)
4. [Phase 1 — Environment & Infrastructure Baseline](#4-phase-1--environment--infrastructure-baseline)
5. [Phase 2 — Core Family Verification](#5-phase-2--core-family-verification)
6. [Phase 3 — Gaming Family (TS)](#6-phase-3--gaming-family-ts)
7. [Phase 4 — AI Family (PY)](#7-phase-4--ai-family-py)
8. [Phase 5 — HTML3 Family (PY · JS)](#8-phase-5--html3-family-py--js)
9. [Phase 6 — System Family (PY · SH)](#9-phase-6--system-family-py--sh)
10. [Phase 7 — Utility Family (TS · PY)](#10-phase-7--utility-family-ts--py)
11. [Phase 8 — CMS Family (PY)](#11-phase-8--cms-family-py)
12. [Phase 9 — Global Positional Integrity Audit](#12-phase-9--global-positional-integrity-audit)
13. [Completion Criteria & Sign-Off](#13-completion-criteria--sign-off)
14. [Migration Status Dashboard](#14-migration-status-dashboard)

---

## 1. Overview & Mandate

### 1.1 What This Migration Is

The BEJSON library ecosystem currently relies on **positional (array-based) indexing** as the sole method for reading record values from `Values` arrays. A record field is accessed by its integer position — for example, `row[3]` for `timestamp`. This works when schemas are frozen, but becomes fragile the moment a field is inserted, reordered, or a schema is extended. A single field insertion shifts every downstream index by one, causing silent data corruption across the entire library stack with no runtime error thrown.

The **Field Map Indexing** migration introduces a second access layer: **key-based lookup by field name**, resolved at runtime from the document's `Fields` array. The resolved integer index is used for actual access — so the underlying positional mechanics do not change — but the resolution is **semantic and name-driven**, not hardcoded.

### 1.2 What This Migration Is NOT

This migration does **not**:

- Remove or replace positional indexing. Legacy array positions remain as fallbacks throughout Phase 1–9.
- Change any field position within any existing schema. Schema layouts are frozen; new fields are append-only.
- Introduce a query language or runtime database engine.
- Affect document serialization or BEJSON file format compliance in any way.

### 1.3 Source of Authority

The GEMINI.md embedded in each library package (`Lib_PY`, `Lib_TS`, `Lib_JS`, `Lib_SH`) states:

> "You may integrate FIELD MAP INDEXING options going forward slowly into the libraries but you are not to break the array based indexing yet. As you update the libraries to use the new field mapping, leave the previous index based fallbacks in place for the time being so that it can fall back on the array base."

This plan operationalizes that mandate. Every task in this checklist is traceable to that directive.

---

## 2. Non-Negotiable Ground Rules

These rules override every other consideration. Violation of any rule during migration is grounds for immediate rollback.

### Rule 1 — Never Break Existing Positional Indices
No field position in any existing schema may shift. If a field is currently at index `3`, it must remain at index `3` after migration. New fields may only be appended to the end of `Fields` arrays.

### Rule 2 — The "Safe Get" Fallback Is Mandatory
Every call-site that resolves a field index via the map **must** implement a fallback to the known legacy positional index. The pattern is:

```
resolved_idx = field_map.get("field_name")
if resolved_idx == -1:
    resolved_idx = LEGACY_POSITION_CONSTANT
```

There are no exceptions. If a map lookup returns `-1` (field not found), code must continue functioning via the legacy constant.

### Rule 3 — Resolve Once Per Operation, Not Per Row
Field maps are built from `doc["Fields"]` and the computation is O(n) in the number of fields. Never call the map builder inside a loop over `Values`. Resolve the map once at the start of the function, then use the cached result for every row.

### Rule 4 — No Hardcoded Paths
Per the GEMINI.md, all paths must be sourced from `~/env_file.py`, `env_file.sh`, or `env_file.json`. If a required environment variable does not exist, create it. Never fall back to a hardcoded absolute path string like `/storage/emulated/0`.

### Rule 5 — Append-Only Schemas
If migration work reveals a need for a new field in any schema, that field is added **only at the end** of `Fields`. This is the one architectural constraint that directly enables the "Safe Get" fallback to remain reliable.

### Rule 6 — Version Bump on Every Touch
Per the project delivery policy, every file edited during migration receives a version bump. No exceptions. The version variable at the top of the file is authoritative; no hardcoded version strings elsewhere.

### Rule 7 — Inject, Don't Recompute
Where the platform supports it, resolved field maps are injected back into the document object under an internal key (`_bejson_field_map` or equivalent). Subsequent calls within the same session can detect the cached map and skip recomputation entirely, achieving O(1) amortized lookup.

---

## 3. Pattern Reference Guide

This section defines the canonical patterns for each platform. Every task in Phases 3–8 produces code that matches one of these patterns exactly.

### 3.1 Python — Standard Field Map Resolution

**Before (manual enumerate — to be replaced):**
```python
fields = [f["name"] for f in doc["Fields"]]
id_idx = fields.index("model_id")           # raises ValueError if not found
act_idx = fields.index("currently_active")  # raises ValueError if not found
```

**After (Core utility — canonical pattern):**
```python
from lib_bejson_core import bejson_core_get_field_index

# Resolve once per function
id_idx  = bejson_core_get_field_index(doc, "model_id")
act_idx = bejson_core_get_field_index(doc, "currently_active")

# Mandatory "Safe Get" fallback constants (freeze current positions)
_LEGACY_MODEL_ID_IDX  = 1
_LEGACY_ACT_IDX       = 2

if id_idx  == -1: id_idx  = _LEGACY_MODEL_ID_IDX
if act_idx == -1: act_idx = _LEGACY_ACT_IDX

# Access row values
for row in doc["Values"]:
    mid  = row[id_idx]
    active = row[act_idx]
```

**Field Map variant (multiple fields, one call):**
```python
# Build map once at function entry
fi = bejson_core_get_field_map(doc)  # returns {field_name: index, ...}

# Resolve with fallbacks
id_idx  = fi.get("model_id",       _LEGACY_MODEL_ID_IDX)
act_idx = fi.get("currently_active", _LEGACY_ACT_IDX)
```

### 3.2 TypeScript — Standard Field Map Resolution

**Before (indexOf — to be replaced):**
```typescript
const fields = doc.Fields.map(f => f.name);
const snapIdIdx = fields.indexOf("id");            // -1 on miss, no fallback
const vlabelIdx = fields.indexOf("version_label"); // -1 on miss, no fallback
```

**After (canonical pattern):**
```typescript
// Legacy position constants — frozen at current schema positions
const LEGACY = { id: 1, version_label: 5, file_path: 8, content: 9, snapshot_id_fk: 10 } as const;

// Resolve map once at function entry
const fm = bejson_core_get_field_map(doc); // returns Record<string, number>

const snapIdIdx  = fm["id"]             ?? LEGACY.id;
const vlabelIdx  = fm["version_label"]  ?? LEGACY.version_label;
const fpathIdx   = fm["file_path"]      ?? LEGACY.file_path;
const contIdx    = fm["content"]        ?? LEGACY.content;
const fkIdx      = fm["snapshot_id_fk"] ?? LEGACY.snapshot_id_fk;
```

**Constructor-cache variant (for long-lived objects):**
```typescript
class MyService {
    private _fm: Record<string, number> = {};

    constructor(private doc: BEJSONDocument) {
        this._fm = bejson_core_get_field_map(doc);
    }

    getFieldIdx(name: string, legacy: number): number {
        return this._fm[name] ?? legacy;
    }
}
```

### 3.3 JavaScript — _buildFieldIdx Pattern (Reference Implementation)

The canonical JS example is already live in `lib_bejson_state.js`. It is the model for all other JS files in the ecosystem:

```javascript
// In constructor — call once
this._fieldIdx = this._buildFieldIdx();

_buildFieldIdx() {
    const fields = this.bejson.Fields;
    return {
        rtp:       fields.findIndex(f => f.name === "Record_Type_Parent"),
        key:       fields.findIndex(f => f.name === "key"),
        value:     fields.findIndex(f => f.name === "value"),
        timestamp: fields.findIndex(f => f.name === "timestamp"),
        snapshot:  fields.findIndex(f => f.name === "snapshot"),
    };
}

// Usage with Safe Get fallback
const { rtp: rtpIdx, key: keyIdx, value: valIdx } = this._fieldIdx;
// If rtpIdx === -1, fallback: rtpIdx = 0  (Record_Type_Parent always at 0 in 104db)
```

All other JS files that process BEJSON documents must adopt this `_buildFieldIdx()` or equivalent top-of-function map construction.

### 3.4 Shell — bejson_core_get_field_index (Already Available)

The shell Core already provides the canonical utility. No new function is needed — only call-site migrations:

```bash
# Already defined in lib_bejson_core.sh (DO NOT REDEFINE)
bejson_core_get_field_index() {
    local doc="$1"
    local field_name="$2"
    echo "$doc" | jq --arg fn "$field_name" '.Fields | map(.name) | index($fn) // -1'
}

# Usage pattern at call sites
DOC=$(cat "$file_path")
ENTITY_NAME_IDX=$(bejson_core_get_field_index "$DOC" "entity_name")
FILE_PATH_IDX=$(bejson_core_get_field_index "$DOC" "file_path")

# Safe Get fallback
[[ "$ENTITY_NAME_IDX" == "-1" ]] && ENTITY_NAME_IDX=0
[[ "$FILE_PATH_IDX"   == "-1" ]] && FILE_PATH_IDX=1

# Access
ENTITY=$(echo "$DOC" | jq -r --argjson fi "$ENTITY_NAME_IDX" '.Values[0][$fi]')
```

---

## 4. Phase 1 — Environment & Infrastructure Baseline

**Goal:** Confirm that foundational prerequisites are in place before touching any library logic. This phase has no library code changes. It is verification only.

**Verify criteria before proceeding to Phase 2:**

- [ ] **1.1** Confirm `bejson_core_get_field_index(doc, field_name)` exists and is importable in `Lib_PY/Core/lib_bejson_core.py`. It must return an integer; `-1` on miss.
- [ ] **1.2** Confirm `bejson_core_get_field_map(doc)` exists in `Lib_PY/Core/lib_bejson_core.py`. It must return a `dict[str, int]` mapping every field name to its index.
- [ ] **1.3** Confirm `bejson_core_get_field_map(doc)` exists in `Lib_TS/Core/lib_bejson_core.ts`. It must return `Record<string, number>`.
- [ ] **1.4** Confirm `bejson_core_get_field_index` is exported from `Lib_SH/Core/lib_bejson_core.sh` via `export -f`. This is already present in v2.0.3 — verify it was not accidentally removed.
- [ ] **1.5** Confirm `env_file.py` exists at `~/env_file.py` on the target runtime. If absent, create it with at minimum `BEJSON_STORAGE_ROOT`, `BEJSON_LIB_ROOT`, and `CC_COMPONENTS` entries.
- [ ] **1.6** Confirm `env_file.sh` exists and defines `BEJSON_STORAGE_ROOT`. If absent, create it. Confirm it is sourced by `lib_be_core.sh` before any path resolution.
- [ ] **1.7** Confirm `env_file.json` exists. If absent, create it as a valid JSON object with the same keys as the `.py` and `.sh` variants.
- [ ] **1.8** Document the **current legacy positional index** for every field in every schema that will be touched during migration. This table is the reference for all "Safe Get" fallback constants throughout Phases 3–8. See Appendix A format below.

### Appendix A — Legacy Index Reference Table (Fill Before Starting Phase 3)

For each schema being migrated, record the current field positions here before touching any code. This table is frozen once recorded.

| Library | Schema / Entity | Field Name | Current Legacy Index |
|---------|-----------------|------------|---------------------|
| `lib_bejson_gemini.py` | `GeminiModel` | `model_name` | 0 |
| `lib_bejson_gemini.py` | `GeminiModel` | `model_id` | 1 |
| `lib_bejson_gemini.py` | `GeminiModel` | `currently_active` | 2 |
| `lib_bejson_gemini.py` | `GeminiModel` | `thinking_enabled` | 3 |
| `lib_bejson_gemini.py` | `GeminiModel` | `google_search_enabled` | 4 |
| `lib_bejson_utility.ts` | `Snapshot` | `Record_Type_Parent` | 0 |
| `lib_bejson_utility.ts` | `Snapshot` | `id` | 1 |
| `lib_bejson_utility.ts` | `Snapshot` | `timestamp` | 2 |
| `lib_bejson_utility.ts` | `Snapshot` | `project_name` | 3 |
| `lib_bejson_utility.ts` | `Snapshot` | `current_version` | 4 |
| `lib_bejson_utility.ts` | `Snapshot` | `version_label` | 5 |
| `lib_bejson_utility.ts` | `Snapshot` | `version_notes` | 6 |
| `lib_bejson_utility.ts` | `Snapshot` | `changes` | 7 |
| `lib_bejson_utility.ts` | `File` | `file_path` | 8 |
| `lib_bejson_utility.ts` | `File` | `content` | 9 |
| `lib_bejson_utility.ts` | `File` | `snapshot_id_fk` | 10 |
| `lib_bejson_static_backend.py` | `mfdb manifest` | `entity_name` | (resolved by headers.index) |
| `lib_bejson_static_backend.py` | `mfdb manifest` | `file_path` | (resolved by headers.index) |

> Fill in remaining rows by running `enumerate(doc["Fields"])` against each live schema before migration begins.

---

## 5. Phase 2 — Core Family Verification

**Goal:** Confirm the Core libraries across all four platforms are fully capable of serving downstream families. No new migration logic is written here — only verification and gap-filling.

**Rationale:** If the Core utility functions are missing, broken, or not exported, every downstream phase fails silently. Core must be confirmed green before touching any consumer family.

### 5.1 Python Core (`Lib_PY/Core/`)

- [ ] **2.1.1** Verify `bejson_core_get_field_index(doc, field_name)` is defined and returns `int`. If absent, add it using the pattern: `next((i for i, f in enumerate(doc["Fields"]) if f["name"] == field_name), -1)`.
- [ ] **2.1.2** Verify `bejson_core_get_field_map(doc)` is defined and returns `dict[str, int]`. If absent, add it: `{f["name"]: i for i, f in enumerate(doc["Fields"])}`. This is the batch variant of `get_field_index`.
- [ ] **2.1.3** Verify both functions are exported/importable from the package `__init__` or directly from `lib_bejson_core.py`.
- [ ] **2.1.4** Verify `bejson_core_atomic_write()` is present and functional (already confirmed in source — spot-check only).
- [ ] **2.1.5** Verify `lib_bejson_errors.py` is present with the full error code range (1–15 BEJSON, 30–49 MFDB). Required by `lib_bejson_validator.py` at import time.
- [ ] **2.1.6** Bump `lib_bejson_core.py` version if any gap-filling additions were made.

### 5.2 TypeScript Core (`Lib_TS/Core/`)

- [ ] **2.2.1** Verify `bejson_core_get_field_map(doc: BEJSONDocument): Record<string, number>` is exported from `lib_bejson_core.ts`.
- [ ] **2.2.2** Verify the function handles 104, 104a, and 104db documents without error. For 104db documents the `Record_Type_Parent` field must be included in the map at index `0`.
- [ ] **2.2.3** Verify `bejson_core_get_field_index(doc, fieldName): number` exists as a convenience single-field variant. If absent, add: `return bejson_core_get_field_map(doc)[fieldName] ?? -1`.
- [ ] **2.2.4** Verify both functions are re-exported from `index.ts` so consumers can import directly from the package root.
- [ ] **2.2.5** Confirm the `BEJSONDocument` interface in `lib_bejson_types.ts` has an optional `[key: string]: any` index signature to allow `_bejson_field_map` injection without TypeScript errors.
- [ ] **2.2.6** Bump `lib_bejson_core.ts` version if any gap-filling additions were made.

### 5.3 JavaScript Core (`Lib_JS/Core/`)

- [ ] **2.3.1** Note that `lib_bejson_state.js` already implements `_buildFieldIdx()` using `findIndex` — this is the JS reference implementation. It does not need to be changed.
- [ ] **2.3.2** Verify `lib_bejson_core.js` (if it exists separately from state) exposes a global `bejson_core_get_field_index(doc, fieldName)` function compatible with browser and Node environments.
- [ ] **2.3.3** Confirm the function is attached to `window.BEJSON` in browser contexts and exported via `module.exports` in Node contexts, matching the pattern used by all other JS library exports.
- [ ] **2.3.4** Bump version if changes were made.

### 5.4 Shell Core (`Lib_SH/Core/`)

- [ ] **2.4.1** Verify `bejson_core_get_field_index` is defined in `lib_bejson_core.sh` (confirmed present in v2.0.3 source — spot-check that it was not removed in later edits).
- [ ] **2.4.2** Verify the function uses `jq` with `--arg fn "$field_name" '.Fields | map(.name) | index($fn) // -1'` — exact key match, not substring match.
- [ ] **2.4.3** Verify `export -f bejson_core_get_field_index` is present at the bottom of `lib_bejson_core.sh` so it propagates to subshells.
- [ ] **2.4.4** Confirm `resilient_lock_acquire` and `resilient_lock_release` are present and exported (already in v2.0.3 — verify).
- [ ] **2.4.5** Confirm `lib_bejson_validator.sh` uses **exact** jq key matching (`.key == $val`, not `contains`). The "Format" vs "Format_Creator" substring collision bug was a known issue — confirm it is fixed.

---

## 6. Phase 3 — Gaming Family (TS)

**Priority: HIGH.** The Gaming family is the most index-heavy and therefore most fragile against schema changes. Physics, event, and asset logic all use numeric array positions with no fallback whatsoever.

**Files in scope:** `bejson_physics.ts` · `bejson_events.ts` · `bejson_assets.ts` · `bejson_engine.ts` · `bejson_renderer.ts` · `bejson_grid.ts`

**Before starting:** Record all legacy positional indices for every field accessed in gaming logic (see Phase 1, Appendix A). These become the `LEGACY` constants in the migrated code.

### 6.1 bejson_physics.ts

The physics `step()` function currently accesses body fields by hardcoded integer positions (e.g., `b[5]` for `vx`, `b[6]` for `vy`, `b[7]` for `isStatic`). These must be migrated to named resolution.

- [ ] **3.1.1** At the top of the file (module level), define a `PHYSICS_LEGACY` constant object mapping every field name used in physics calculations to its current positional index. Example: `const PHYSICS_LEGACY = { x: 0, y: 1, w: 2, h: 3, vx: 5, vy: 6, is_static: 7 } as const;`
- [ ] **3.1.2** In the `step(dt)` method, call `bejson_core_get_field_map(this.bodies)` at the **top of the method**, before any loop. Store in a local `const fm`.
- [ ] **3.1.3** Resolve all indices from `fm` with `PHYSICS_LEGACY` fallback: `const vxIdx = fm["vx"] ?? PHYSICS_LEGACY.vx;`
- [ ] **3.1.4** Replace all `b[hardcoded_int]` accesses in velocity integration with the resolved variables: `b[vxIdx] *= this.friction;` instead of `b[5] *= this.friction;`
- [ ] **3.1.5** Repeat the pattern for `_checkAABB()`: resolve `xIdx`, `yIdx`, `wIdx`, `hIdx` from the map with legacy fallbacks before the collision detection loop.
- [ ] **3.1.6** Repeat for `_resolveCollision()` and `_checkStaticCollisions()`.
- [ ] **3.1.7** Verify: if the schema has `Record_Type_Parent` at index 0 (104db format for body data), ensure the map lookup for `Record_Type_Parent` still resolves to `0`, and that the collision logic correctly filters by record type if applicable.
- [ ] **3.1.8** Bump version.

### 6.2 bejson_events.ts

The event execution system accesses event record fields (script content, condition expression, event ID) by hardcoded positions.

- [ ] **3.2.1** Define `EVENTS_LEGACY` constants for all fields: `{ event_id: 1, event_name: 2, condition: 4, script: 5 }` (adjust to match the actual current schema).
- [ ] **3.2.2** In `run_event(event_id)`, resolve `bejson_core_get_field_map(this.bejson)` once at entry.
- [ ] **3.2.3** Replace `ev[4]` (condition) with `ev[fm["condition"] ?? EVENTS_LEGACY.condition]`.
- [ ] **3.2.4** Replace `ev[5]` (script) with `ev[fm["script"] ?? EVENTS_LEGACY.script]`.
- [ ] **3.2.5** In `_check_condition()`, resolve any field positions used to evaluate condition strings.
- [ ] **3.2.6** Bump version.

### 6.3 bejson_assets.ts

The asset registry uses fixed-position lookups for `id`, `type`, `path`, and `loaded` fields.

- [ ] **3.3.1** Define `ASSETS_LEGACY` constants.
- [ ] **3.3.2** In `register_asset()`, call `bejson_core_get_field_map(this.bejson)` once and cache it as `this._fm` in the constructor (long-lived object — constructor cache is appropriate).
- [ ] **3.3.3** In `mark_loaded()`, use `this._fm["loaded"] ?? ASSETS_LEGACY.loaded` rather than hardcoded index.
- [ ] **3.3.4** In `get_asset(id)`, use `this._fm["id"] ?? ASSETS_LEGACY.id` for the filter comparison.
- [ ] **3.3.5** Ensure no path strings inside the asset registry are hardcoded. Any `path` field values must be relative paths. Resolution to absolute paths must happen via `env_file.json`'s `BEJSON_STORAGE_ROOT`. If the asset loader currently concatenates a hardcoded base path, replace it with an env-variable-driven base.
- [ ] **3.3.6** Bump version.

### 6.4 bejson_renderer.ts

The renderer reads tile layer and HUD data from BEJSON grid documents. It runs per-frame, making it the highest-frequency consumer of field access in the entire ecosystem.

- [ ] **3.4.1** Because rendering is per-frame, the field map **must** use the Internal Registry pattern: after the first resolution, inject the map back into the document: `doc._bejson_field_map = fm;`. On subsequent calls, check for `doc._bejson_field_map` before recomputing.
- [ ] **3.4.2** In `drawTileLayer()`, implement the injection check at entry: `const fm = doc._bejson_field_map ?? (doc._bejson_field_map = bejson_core_get_field_map(doc));`
- [ ] **3.4.3** Replace any `grid.Values[i][1]` style accesses with `grid.Values[i][fm["data"] ?? RENDERER_LEGACY.data]`.
- [ ] **3.4.4** Repeat for HUD layer rendering.
- [ ] **3.4.5** Verify the injection pattern does not cause TypeScript strict-mode errors. The `BEJSONDocument` interface must allow `_bejson_field_map` as an optional index signature key (confirmed in Phase 2.2.5).
- [ ] **3.4.6** Bump version.

### 6.5 bejson_engine.ts

The engine orchestrates physics, events, assets, and the renderer. It is the top-level consumer that instantiates the other classes.

- [ ] **3.5.1** Verify the engine does not perform its own independent field lookups outside of the subsystems. If it does, apply the same map + legacy pattern.
- [ ] **3.5.2** Confirm that entity filtering logic (e.g., selecting only records where `row[0] === "Body"` in 104db format) uses `fm["Record_Type_Parent"] ?? 0` rather than hardcoded `0`. While `Record_Type_Parent` is guaranteed to be at index 0 in all 104db documents, using the map is consistent practice.
- [ ] **3.5.3** Bump version if any changes were made.

### 6.6 bejson_grid.ts

- [ ] **3.6.1** Identify all integer literal indices used to access grid cell data.
- [ ] **3.6.2** Define `GRID_LEGACY` constants for each.
- [ ] **3.6.3** Apply the top-of-function map resolution with legacy fallbacks.
- [ ] **3.6.4** Bump version.

---

## 7. Phase 4 — AI Family (PY)

**Priority: HIGH.** The AI family has a partially completed migration. `GeminiKeyRegistry` already uses `bejson_core_get_field_index`. `GeminiModelRegistry` does not. The goal is to complete the AI family and eliminate all manual `list.index()` calls.

**Files in scope:** `lib_bejson_gemini.py` · `lib_bejson_gemprofiles.py` · `lib_bejson_genai.py` · `lib_bejson_groq.py`

### 7.1 lib_bejson_gemini.py — GeminiModelRegistry

The `GeminiModelRegistry.load()` method currently uses `fields.index("model_id")` and `fields.index("currently_active")`. These raise `ValueError` on a miss and have no fallback.

- [ ] **4.1.1** Add `from lib_bejson_core import bejson_core_get_field_map` to the imports block (note: `bejson_core_get_field_index` is already imported — add `bejson_core_get_field_map` alongside it).
- [ ] **4.1.2** Define legacy index constants at module level (outside the class):
  ```python
  _GEMINI_MODEL_LEGACY = {
      "model_name": 0, "model_id": 1, "currently_active": 2,
      "thinking_enabled": 3, "google_search_enabled": 4
  }
  ```
- [ ] **4.1.3** In `GeminiModelRegistry.load()`, replace the three `fields.index()` calls with:
  ```python
  fi = bejson_core_get_field_map(data)
  id_idx    = fi.get("model_id",             _GEMINI_MODEL_LEGACY["model_id"])
  act_idx   = fi.get("currently_active",     _GEMINI_MODEL_LEGACY["currently_active"])
  think_idx = fi.get("thinking_enabled",     _GEMINI_MODEL_LEGACY["thinking_enabled"])
  search_idx = fi.get("google_search_enabled", _GEMINI_MODEL_LEGACY["google_search_enabled"])
  ```
- [ ] **4.1.4** The existing `-1` guard for `think_idx` and `search_idx` (`if think_idx != -1`) should be **preserved** as a runtime safety check even after migration, because these fields are optional in older registry files.
- [ ] **4.1.5** Verify the `except` block fallback that reads directly from `SCHEMA_MODEL_REGISTRY["Values"]` still uses positional indices. This fallback must remain untouched — it is intentionally position-based for the static schema constant.
- [ ] **4.1.6** Bump version to next minor (e.g., `2.1.1 → 2.1.2`).

### 7.2 lib_bejson_gemprofiles.py

This library contains a function `bejson_profiles_get_field_index` that duplicates Core logic via a manual `enumerate` loop.

- [ ] **4.2.1** Locate `bejson_profiles_get_field_index` (the manual enumerate implementation).
- [ ] **4.2.2** Do **not** delete it yet. Instead, rewrite its body to delegate to Core:
  ```python
  def bejson_profiles_get_field_index(doc, name):
      """Deprecated: delegates to bejson_core_get_field_index."""
      return bejson_core_get_field_index(doc, name)
  ```
  This preserves the public API while eliminating the duplicate logic.
- [ ] **4.2.3** Add a deprecation comment noting the function is a thin wrapper and will be removed in a future cleanup phase.
- [ ] **4.2.4** Identify all call-sites of `bejson_profiles_get_field_index` within this file. Each must have a legacy fallback constant added alongside the call, following the "Safe Get" pattern.
- [ ] **4.2.5** Confirm the profile schema's field positions and add `_PROFILES_LEGACY` constants at module level for every field accessed.
- [ ] **4.2.6** Bump version.

### 7.3 lib_bejson_genai.py

- [ ] **4.3.1** Audit all `row[N]` and `fields.index()` occurrences.
- [ ] **4.3.2** Add `_GENAI_LEGACY` constants for each field accessed by position.
- [ ] **4.3.3** Replace `fields.index(name)` calls with `bejson_core_get_field_map(doc).get(name, _GENAI_LEGACY[name])`.
- [ ] **4.3.4** Bump version.

### 7.4 lib_bejson_groq.py

This library contains local "stub" implementations of `bejson_core_get_field_index` inside an `ImportError` catch block as a fallback when Core is unavailable.

- [ ] **4.4.1** Locate the `ImportError` block that defines the local stub.
- [ ] **4.4.2** Keep the stub for now — do **not** remove it. The stub is a safety net for environments where the Core library fails to import. This is acceptable during the transition period.
- [ ] **4.4.3** Add a comment: `# TRANSITION STUB — remove only after confirming Core is always importable in all runtime environments.`
- [ ] **4.4.4** Replace all manual `enumerate` loops in the main (non-stub) code path with `bejson_core_get_field_map(doc)` lookups plus legacy fallbacks.
- [ ] **4.4.5** Bump version.

---

## 8. Phase 5 — HTML3 Family (PY · JS)

**Priority: MEDIUM.** HTML3 is the most user-visible family. Several components already use a local `fi` dict pattern (e.g., `lib_html3_showcase.py`). The migration goal is to replace these local dict builds with Core-delegated calls and ensure all rendering paths have proper Safe Get fallbacks.

**Files in scope:** `lib_html3_showcase.py` · `lib_html3_tables.py` · `lib_html3_list_renderer.py` · `lib_html3_bejson_renderer.py` · `lib_html3_table.js`

### 8.1 lib_html3_showcase.py

This file already uses `{f["name"]: i for i, f in enumerate(fields)}` with a `safe_get()` helper. This is a good pattern but not using Core, so it cannot benefit from the global cache or document injection.

- [ ] **5.1.1** Add import: `from lib_bejson_core import bejson_core_get_field_map`.
- [ ] **5.1.2** In `html_bento_grid()`, replace the manual `fi` dict construction with:
  ```python
  fi = bejson_core_get_field_map(bejson_doc)
  ```
  The existing `safe_get(r, key, default)` helper can remain unchanged — it already reads from `fi` by key lookup.
- [ ] **5.1.3** Add legacy fallback constants for `label`, `value`, and `weight` fields. The `safe_get` helper currently returns `""` on a miss; add `_BENTO_LEGACY = {"label": 0, "value": 1, "weight": 2}` and update `safe_get` to use it: `idx = fi.get(key, _BENTO_LEGACY.get(key, -1))`.
- [ ] **5.1.4** Apply the Internal Registry pattern: inject `bejson_doc._bejson_field_map = fi` after building the map so repeated renders of the same document skip map reconstruction.
- [ ] **5.1.5** Bump version.

### 8.2 lib_html3_tables.py

- [ ] **5.2.1** Audit every function that receives a `bejson_doc` parameter and builds a field index internally.
- [ ] **5.2.2** For each such function, replace the local dict build with `bejson_core_get_field_map(doc)`.
- [ ] **5.2.3** Add `_TABLES_LEGACY` constants for every field accessed.
- [ ] **5.2.4** Implement the Internal Registry injection pattern (check `doc._bejson_field_map` before recomputing).
- [ ] **5.2.5** Bump version.

### 8.3 lib_html3_list_renderer.py

This file already uses a `_resolve_field()` helper that handles semantic aliases (`parent_id` vs `parent_id_fk`). This is a best-practice pattern that must be preserved and standardized.

- [ ] **5.3.1** Verify `_resolve_field()` is calling `bejson_core_get_field_index()` internally rather than reimplementing its own loop. If it reimplements the loop, update it to delegate to Core.
- [ ] **5.3.2** Add legacy constants for all FK-resolved fields. Because FK fields use the `_fk` suffix convention, the legacy constant must cover both variants: `_LIST_LEGACY = {"parent_id": 3, "parent_id_fk": 3}` (same index, two keys).
- [ ] **5.3.3** Confirm `_resolve_field()` is used by all other HTML3 components that need FK-aware resolution, not just list_renderer. Add a comment marking it as the canonical FK resolver for the HTML3 family.
- [ ] **5.3.4** Bump version.

### 8.4 lib_html3_bejson_renderer.py

The `render_bejson()` function builds a manual `fi` dict: `{f["name"]: i for i, f in enumerate(doc["Fields"])}`. This is the pattern to replace.

- [ ] **5.4.1** Import `bejson_core_get_field_map`.
- [ ] **5.4.2** Replace the manual dict build in `render_bejson()` with `fi = bejson_core_get_field_map(doc)`.
- [ ] **5.4.3** Add legacy fallbacks for any field accessed with a numeric literal elsewhere in the function.
- [ ] **5.4.4** Bump version.

### 8.5 lib_html3_table.js

- [ ] **5.5.1** If `lib_html3_table.js` does not already use `_buildFieldIdx()` (the canonical JS pattern from `lib_bejson_state.js`), add it.
- [ ] **5.5.2** In the `render()` function, check for `doc._bejson_field_map` at entry before building the map: `const fm = doc._bejson_field_map || (doc._bejson_field_map = buildFieldIdx(doc));` This is O(1) on repeated renders of the same document.
- [ ] **5.5.3** Replace all numeric array accesses inside table cell rendering with named lookups via `fm`.
- [ ] **5.5.4** Bump version.

---

## 9. Phase 6 — System Family (PY · SH)

**Priority: HIGH.** The System family manages project metadata and environment paths. Errors here can cause data loss or silent schema misreads on project startup.

**Files in scope:** `lib_be_project_service.py` · `lib_be_core.py` · `lib_be_core.sh` · `lib_be_deps.sh`

### 9.1 lib_be_project_service.py

This library enforces an authoritative 22-field Project Schema (v1.4.0). It currently uses hardcoded positional indices throughout project creation, filtering, and sync operations.

- [ ] **6.1.1** At module level, define the full `PROJECT_LEGACY` index map covering all 22 fields of the Project schema. This is the most critical constant block in the entire migration — take time to get it right. Example format:
  ```python
  _PROJECT_LEGACY = {
      "project_id": 0, "project_name": 1, "project_path": 2, "created_at": 3,
      "updated_at": 4, "is_archived": 5, "is_reset_protected": 6,
      # ... all 22 fields
  }
  ```
- [ ] **6.1.2** In `_create_project_record()`, replace the positional assignments (`record[5] = False`, `record[6] = False`) with map-resolved assignments:
  ```python
  fi = bejson_core_get_field_map(doc)
  archived_idx        = fi.get("is_archived",        _PROJECT_LEGACY["is_archived"])
  reset_protect_idx   = fi.get("is_reset_protected",  _PROJECT_LEGACY["is_reset_protected"])
  record[archived_idx]      = False
  record[reset_protect_idx] = False
  ```
- [ ] **6.1.3** In `get_projects()`, the filter `v == False` must use the resolved `is_archived` index, not a hardcoded literal.
- [ ] **6.1.4** In `scan_and_sync()`, replace `v = not os.path.exists(v)` with properly resolved index variables for `is_missing` and `path` fields.
- [ ] **6.1.5** Verify `PROJECTS_ROOT` and `DB_FILE` are sourced from `env_file.py` (via `os.environ.get("CC_PROJECTS")` and `os.environ.get("CC_DB")`). If they currently use `os.path.join` with a local fallback, replace the fallback with an environment variable creation step and a clear error message if the variable is absent.
- [ ] **6.1.6** Bump version.

### 9.2 lib_be_core.py

- [ ] **6.2.1** Confirm `SimpleLock` is present. If the codebase has access to `ResilientPIDLock` from `lib_bejson_core.py`, add a note (but do not forcibly replace `SimpleLock` unless it is actively causing stale-lock issues — this is a maintenance note, not a migration blocker).
- [ ] **6.2.2** Ensure `get_bec_root()` does not fall back to a hardcoded path. If it does, replace the fallback with `env_file.py` resolution.
- [ ] **6.2.3** Bump version only if changes were made.

### 9.3 lib_be_core.sh

- [ ] **6.3.1** Locate `bec_core_get_root` (or equivalent path resolution function). Confirm it does **not** contain the string `/storage/emulated/0` as a hardcoded fallback.
- [ ] **6.3.2** If a hardcoded path exists, remove it. Replace with:
  ```bash
  local root="${BEJSON_STORAGE_ROOT:-}"
  if [[ -z "$root" ]]; then
      echo "ERROR: BEJSON_STORAGE_ROOT is not set. Define it in env_file.sh." >&2
      return 1
  fi
  echo "$root"
  ```
- [ ] **6.3.3** Verify `env_file.sh` is sourced at the top of any script that calls `bec_core_get_root`, not inside the function itself.
- [ ] **6.3.4** If `manager_state` files ever transition from `key=value` to BEJSON format, note here that `save_state`/`load_state` must use `bejson_core_get_field_index` for any field access. For now, this is a future-state note only.
- [ ] **6.3.5** Bump version if changes were made.

### 9.4 lib_be_deps.sh

- [ ] **6.4.1** Audit for any hardcoded paths. Replace with `$BEJSON_STORAGE_ROOT` references.
- [ ] **6.4.2** Verify dependency checks use exact `jq` key matching, not substring patterns.
- [ ] **6.4.3** Bump version if changes were made.

---

## 10. Phase 7 — Utility Family (TS · PY)

**Priority: HIGH.** The Utility family handles project snapshotting, versioning, and file chunking. `lib_bejson_utility.ts` contains the most concrete instances of raw `indexOf` on field arrays with no fallback whatsoever.

**Files in scope:** `lib_bejson_utility.ts` · `lib_bejson_utility.py` · `lib_bejson_provider.py`

### 10.1 lib_bejson_utility.ts — bejson_utility_restore_version()

This function has five sequential `fields.indexOf()` calls with no fallback. It is the highest-priority individual function in the entire migration.

- [ ] **7.1.1** Add legacy constants at module level for the 11-field `CHUNK_SCHEMA` layout:
  ```typescript
  const CHUNK_LEGACY = {
      Record_Type_Parent: 0, id: 1, timestamp: 2, project_name: 3,
      current_version: 4, version_label: 5, version_notes: 6, changes: 7,
      file_path: 8, content: 9, snapshot_id_fk: 10
  } as const;
  ```
- [ ] **7.1.2** In `bejson_utility_restore_version()`, replace all five `fields.indexOf()` calls with:
  ```typescript
  const fm = bejson_core_get_field_map(dbDoc);
  const snapIdIdx  = fm["id"]             ?? CHUNK_LEGACY.id;
  const vlabelIdx  = fm["version_label"]  ?? CHUNK_LEGACY.version_label;
  const fpathIdx   = fm["file_path"]      ?? CHUNK_LEGACY.file_path;
  const contIdx    = fm["content"]        ?? CHUNK_LEGACY.content;
  const fkIdx      = fm["snapshot_id_fk"] ?? CHUNK_LEGACY.snapshot_id_fk;
  ```
- [ ] **7.1.3** Fix the existing bug: the function references `fk_idx` (snake_case) in the filter `row[fk_idx] === snapshotId` but the variable is declared as `fkIdx` (camelCase). This is a latent `ReferenceError`. Fix the variable name during migration.
- [ ] **7.1.4** Verify `bejson_core_get_field_map` is imported from the Core package.
- [ ] **7.1.5** Bump version.

### 10.2 lib_bejson_utility.ts — bejson_utility_snapshot_project()

This function uses `row[0]` and `row[4]` hardcoded.

- [ ] **7.2.1** The `row[0] === "Project"` check accesses `Record_Type_Parent`. This is always at index 0 in 104db documents. The access is safe but should still use a constant: `if (row[CHUNK_LEGACY.Record_Type_Parent] === "Project")`.
- [ ] **7.2.2** The `row[4] = versionLabel` assignment (updating `current_version`) must be replaced with a map-resolved index: `const verIdx = fm["current_version"] ?? CHUNK_LEGACY.current_version; row[verIdx] = versionLabel;`
- [ ] **7.2.3** Resolve `bejson_core_get_field_map(dbDoc)` at the top of the function and reuse for both the `forEach` filter and the version update.
- [ ] **7.2.4** Bump version (same bump as 7.1.5 if both are done in one pass).

### 10.3 lib_bejson_utility.py

- [ ] **7.3.1** Identify any hardcoded positional access to the `FileContent` or `ProjectMeta` schemas in the Python utility library.
- [ ] **7.3.2** Define `_UTILITY_PY_LEGACY` constants for each field accessed.
- [ ] **7.3.3** Replace with `bejson_core_get_field_map` calls plus Safe Get fallbacks.
- [ ] **7.3.4** Ensure chunk creation functions (`bejson_utility_create_mfdb_version`, `bejson_utility_create_cli_chunk`) resolve field positions dynamically rather than assuming a fixed field count. The `FileContent` schema currently has 8 fields — if the schema grows, these functions must continue to work.
- [ ] **7.3.5** Bump version.

### 10.4 lib_bejson_provider.py

This file contains a redundant `get_fields_map(db)` static method that duplicates Core logic.

- [ ] **7.4.1** Locate `get_fields_map(db)`.
- [ ] **7.4.2** Rewrite its body to delegate to Core (do not delete the method yet — it may have external callers):
  ```python
  @staticmethod
  def get_fields_map(db):
      """Deprecated: delegates to bejson_core_get_field_map."""
      return bejson_core_get_field_map(db)
  ```
- [ ] **7.4.3** Add a deprecation comment.
- [ ] **7.4.4** Identify all internal callers and confirm they now benefit from Core's global cache transparently.
- [ ] **7.4.5** Bump version.

---

## 11. Phase 8 — CMS Family (PY)

**Priority: MEDIUM.** The CMS family manages site masters, page databases, and taxonomies. It has already begun the transition in some functions but still builds manual `fields_map` dicts in several critical code paths.

**Files in scope:** `lib_cms_content.py` · `lib_cms_config.py` · `lib_cms_taxonomy.py` · `lib_cms_mfdb.py`

### 11.1 lib_cms_content.py

- [ ] **8.1.1** Locate `cms_content_create_page()`. It currently builds `fields_map = {f['name']: i for i, f in enumerate(doc["Fields"])}`.
- [ ] **8.1.2** Replace with `fields_map = bejson_core_get_field_map(doc)`. This one-line change activates Core's global cache.
- [ ] **8.1.3** Apply the Internal Registry injection: `doc._bejson_field_map = fields_map` immediately after building.
- [ ] **8.1.4** Define `_CMS_PAGE_LEGACY` constants for all page schema fields accessed by position.
- [ ] **8.1.5** Replace `fields_map["field_name"]` direct access (which raises `KeyError` on miss) with `fields_map.get("field_name", _CMS_PAGE_LEGACY["field_name"])`.
- [ ] **8.1.6** Bump version.

### 11.2 lib_cms_config.py

- [ ] **8.2.1** In `cms_config_get_all()` and `cms_config_set()`, resolve `config_key` and `config_value` field indices once at function entry using `bejson_core_get_field_map`.
- [ ] **8.2.2** Add `_CMS_CONFIG_LEGACY` constants.
- [ ] **8.2.3** Replace any inline `enumerate`-based resolution with Core delegation.
- [ ] **8.2.4** Bump version.

### 11.3 lib_cms_taxonomy.py

- [ ] **8.3.1** In `cms_taxonomy_get_categories()` and `cms_taxonomy_get_authors()`, resolve the complete field map once at function entry. These functions currently call `get_field_index` multiple times, which recomputes the scan for each call.
- [ ] **8.3.2** Use `bejson_core_get_field_map(doc)` once and dereference all needed fields (`name`, `slug`, `bio`, `parent_id`, etc.) from the map.
- [ ] **8.3.3** Apply Safe Get fallbacks for each.
- [ ] **8.3.4** Bump version.

### 11.4 lib_cms_mfdb.py

- [ ] **8.4.1** Audit manifest lookups for `entity_name` and `file_path`. These should already be using field names (see `lib_bejson_static_backend.py` reference which uses `headers.index()` with a PascalCase fallback). Migrate to Core: `fi = bejson_core_get_field_map(manifest_data)`.
- [ ] **8.4.2** Add `_CMS_MANIFEST_LEGACY = {"entity_name": 0, "file_path": 1}` fallback constants (adjust to actual schema positions).
- [ ] **8.4.3** Remove or clearly document the PascalCase fallback (`Entity_Name`, `Entity_File_Path`) — this is an old non-standard schema. The fallback can remain for backward compatibility but must be subordinate to the primary snake_case lookup.
- [ ] **8.4.4** Bump version.

---

## 12. Phase 9 — Global Positional Integrity Audit

**This phase is not optional. It runs after all family migrations are complete.**

**Goal:** Confirm that no field position in any schema has shifted during migration, and that all "Safe Get" fallback constants in Phases 3–8 still point to the correct legacy indices.

### 12.1 Schema Freeze Verification

For every schema modified or touched during the migration:

- [ ] **9.1.1** Run `enumerate(doc["Fields"])` against the live file and compare the output against the Appendix A table recorded in Phase 1.
- [ ] **9.1.2** Confirm no field was inserted before an existing field. Only append-to-end additions are acceptable.
- [ ] **9.1.3** If any discrepancy is found, it is a critical regression. Stop. Identify the commit that caused the shift. Restore the correct order before proceeding.

### 12.2 Fallback Constant Cross-Check

- [ ] **9.2.1** For every `LEGACY` constant block defined in Phases 3–8, verify that the integer value matches the actual current index in the live schema. Mismatched constants are silent bugs — they will not error, but they will return wrong data when the map lookup misses.
- [ ] **9.2.2** For 104db documents, confirm `Record_Type_Parent` is at index `0` in every schema. This is a spec invariant.
- [ ] **9.2.3** For every function that contains the Safe Get pattern, manually trace at least one code path to confirm the resolved index produces the correct value on a sample record.

### 12.3 Internal Registry Injection Verification

- [ ] **9.3.1** For every location where `doc._bejson_field_map` injection was applied (renderer, HTML3 tables, showcase), confirm the injection does not break document serialization. Specifically: `json.dumps(doc)` in Python and `JSON.stringify(doc)` in TS/JS must not include `_bejson_field_map` in their output. If the document is ever serialized after injection, the internal key must be stripped before write: `clean = {k: v for k, v in doc.items() if not k.startswith("_")}`.
- [ ] **9.3.2** Confirm that `bejson_core_atomic_write()` in Python and its TS/SH equivalents strip internal keys before writing. Add a stripping step if absent.

### 12.4 Environment Path Audit

- [ ] **9.4.1** Run a `grep -r "/storage/emulated/0"` across all four library directories. Any remaining hardcoded instances are policy violations. Replace each with the appropriate env variable.
- [ ] **9.4.2** Run a `grep -r "os.path.join.*fallback"` and similar patterns in Python to catch any remaining join-with-hardcoded-string patterns.
- [ ] **9.4.3** Confirm `env_file.py`, `env_file.sh`, and `env_file.json` are all consistent with one another — the same variable names resolve to the same paths across all three formats.

### 12.5 jq Key-Match Audit (SH)

- [ ] **9.5.1** Run a grep for `=~` patterns in all `.sh` library files. Substring matches (`=~`) on field names risk collisions (e.g., "Format" matching inside "Format_Creator"). Every field name comparison must use exact equality (`==`).
- [ ] **9.5.2** Confirm `lib_bejson_validator.sh` uses exact `jq` key checks for all mandatory key validations.

### 12.6 Version Consistency Check

- [ ] **9.6.1** Confirm every file touched during Phases 3–8 had its version variable bumped.
- [ ] **9.6.2** Confirm no file has a version string that differs between its header comment and its `VERSION` variable.
- [ ] **9.6.3** Confirm any ZIP package names generated for deliverables match the internal version strings.

---

## 13. Completion Criteria & Sign-Off

The migration is complete when all of the following are true:

- [ ] **C.1** All checklist items in Phases 1–9 are marked complete.
- [ ] **C.2** The Legacy Index Reference Table (Appendix A) is fully populated and frozen.
- [ ] **C.3** No hardcoded path strings remain in any library file (grep confirmed).
- [ ] **C.4** No `list.index()` or `Array.indexOf()` call remains without a Safe Get fallback constant alongside it.
- [ ] **C.5** Every function that resolves field indices does so at function entry (one map call), not inside a loop.
- [ ] **C.6** High-frequency render paths (renderer, tables) use the Internal Registry injection pattern and confirm O(1) amortized lookup.
- [ ] **C.7** `lib_bejson_gemprofiles.py::bejson_profiles_get_field_index` and `lib_bejson_provider.py::get_fields_map` are both marked deprecated and delegate to Core.
- [ ] **C.8** The `fk_idx` / `fkIdx` typo bug in `lib_bejson_utility.ts::bejson_utility_restore_version()` is fixed.
- [ ] **C.9** The `/storage/emulated/0` hardcoded fallback in shell System libraries is removed.
- [ ] **C.10** All version bumps are applied and consistent within each file.
- [ ] **C.11** GEMINI.md in each library package is updated to note that Field Map Indexing is now the primary lookup standard, with array-based indexing retained as a transitional fallback.

---

## 14. Migration Status Dashboard

Track overall progress here. Update as phases are completed.

| Phase | Scope | Status | Notes |
|-------|-------|--------|-------|
| Phase 1 | Environment & Infrastructure | `[ ] Not Started` | |
| Phase 2 | Core Family Verification (All) | `[ ] Not Started` | |
| Phase 3 — 3.1 | Gaming / bejson_physics.ts | `[ ] Not Started` | |
| Phase 3 — 3.2 | Gaming / bejson_events.ts | `[ ] Not Started` | |
| Phase 3 — 3.3 | Gaming / bejson_assets.ts | `[ ] Not Started` | |
| Phase 3 — 3.4 | Gaming / bejson_renderer.ts | `[ ] Not Started` | |
| Phase 3 — 3.5 | Gaming / bejson_engine.ts | `[ ] Not Started` | |
| Phase 3 — 3.6 | Gaming / bejson_grid.ts | `[ ] Not Started` | |
| Phase 4 — 4.1 | AI / lib_bejson_gemini.py | `[ ] Not Started` | GeminiModelRegistry.load() |
| Phase 4 — 4.2 | AI / lib_bejson_gemprofiles.py | `[ ] Not Started` | Deprecate manual enumerate |
| Phase 4 — 4.3 | AI / lib_bejson_genai.py | `[ ] Not Started` | |
| Phase 4 — 4.4 | AI / lib_bejson_groq.py | `[ ] Not Started` | Stub preservation |
| Phase 5 — 5.1 | HTML3 / lib_html3_showcase.py | `[ ] Not Started` | |
| Phase 5 — 5.2 | HTML3 / lib_html3_tables.py | `[ ] Not Started` | |
| Phase 5 — 5.3 | HTML3 / lib_html3_list_renderer.py | `[ ] Not Started` | FK resolver audit |
| Phase 5 — 5.4 | HTML3 / lib_html3_bejson_renderer.py | `[ ] Not Started` | |
| Phase 5 — 5.5 | HTML3 / lib_html3_table.js | `[ ] Not Started` | |
| Phase 6 — 6.1 | System / lib_be_project_service.py | `[ ] Not Started` | 22-field schema |
| Phase 6 — 6.2 | System / lib_be_core.py | `[ ] Not Started` | |
| Phase 6 — 6.3 | System / lib_be_core.sh | `[ ] Not Started` | Remove /storage hardcode |
| Phase 6 — 6.4 | System / lib_be_deps.sh | `[ ] Not Started` | |
| Phase 7 — 7.1 | Utility / lib_bejson_utility.ts (restore) | `[ ] Not Started` | Fix fk_idx typo |
| Phase 7 — 7.2 | Utility / lib_bejson_utility.ts (snapshot) | `[ ] Not Started` | |
| Phase 7 — 7.3 | Utility / lib_bejson_utility.py | `[ ] Not Started` | |
| Phase 7 — 7.4 | Utility / lib_bejson_provider.py | `[ ] Not Started` | Deprecate get_fields_map |
| Phase 8 — 8.1 | CMS / lib_cms_content.py | `[ ] Not Started` | |
| Phase 8 — 8.2 | CMS / lib_cms_config.py | `[ ] Not Started` | |
| Phase 8 — 8.3 | CMS / lib_cms_taxonomy.py | `[ ] Not Started` | |
| Phase 8 — 8.4 | CMS / lib_cms_mfdb.py | `[ ] Not Started` | |
| Phase 9 | Global Integrity Audit | `[ ] Not Started` | Run last |
| Sign-Off | All Completion Criteria | `[ ] Not Started` | |

---

*Policy v1.2 — Elton Boehnen — eltonboehnen@gmail.com — boehnenelton2024.pages.dev — github.com/boehnenelton*
