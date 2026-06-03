# System/Family Alignment & Naming Standardization — v2.1.0
**Applied by:** Gemini CLI · **Date:** 2026-05-30
**Objective:** Align Master Library with GEMINI.md System/Family architecture and standardize naming conventions.

---

## Changes Summary

| Action | Path | Description |
| :--- | :--- | :--- |
| **Move** | `Lib_PY/HTML/lib_html3_table.js` → `Lib_JS/HTML/` | Fixed cross-system language misplacement (JS file in PY folder). |
| **Move** | `Lib_PY/Core/lib_be_core.py` → `Lib_PY/System/` | Aligned with SH system family (`Lib_SH/System/lib_be_core.sh`). |
| **Rename** | `Lib_TS/Core/*.ts` → `lib_*.ts` | Standardized naming convention across all systems (JS, PY, SH, TS). |

---

## Fix Detail

### Master Library Organization
- **System Correction:** Relocated `lib_html3_table.js` from the Python HTML family to the Javascript HTML family to maintain language-specific silos.
- **Family Alignment:** Moved `lib_be_core.py` from `Core` to `System`. While BEJSON logic resides in `Core`, low-level system services (like `be_core`) belong in the `System` family to mirror the Shell library structure.
- **TypeScript Standardization:** Applied the `lib_` prefix to all core TypeScript files (e.g., `bejson_core.ts` → `lib_bejson_core.ts`) to ensure uniform identification of library modules across the entire BEJSON ecosystem.

---

# Audit Fix Change Report — 3BETA1 → v2.0.2
**Applied by:** Claude (Anthropic) · **Date:** 2026-05-30  
**Commissioned by:** Elton Boehnen · boehnenelton2024.pages.dev  
**Source audit:** BEJSON Library Suite Audit Report (2026-05-30)

---

## Files Changed (17) + New (1)

| File | Issues Fixed | Version |
|------|-------------|---------|
| `Core/lib_bejson_bejson.js` | JS1 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_validator.sh` | SH1, SH3 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_core.sh` | SH2, SH3, SH6 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_errors.sh` | X3 (NEW FILE) | — → 1.0.0 |
| `Core/lib_bejson_core.js` | FM1 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_state.js` | FM2, FM3 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_validator.js` | JS3 | 2.0.1 → 2.0.2 |
| `Core/lib_mfdb_core.js` | JS4 | 2.0.1 → 2.0.2 |
| `Core/lib_mfdb_validator.js` | JS5 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_parse.js` | JS7 | 2.0.1 → 2.0.2 |
| `Core/bejson_cache.test.js` | JS12 | — |
| `Core/lib_bejson_validator.py` | PY2 | 2.0.1 → 2.0.2 |
| `Core/lib_bejson_schema.py` | PY3, PY4 | 2.1.0 → 2.1.1 |
| `HTML/lib_html3_table.js` | H1, H5, H6, H7 | 1.2.0 → 1.2.1 |
| `HTML/lib_html3_tables.py` | H2, H9 | 3.0.0 → 3.0.1 |
| `Gaming/cli/game.js` | JS9, JS10 | 2.0.1 → 2.0.2 |
| `Gaming/lib_bejson_events.js` | JS8 | 2.0.1 → 2.0.2 |
| `External/jszip.min.js` | JS11 | 2.0.1 → 2.0.2 |

---

## Fix Detail

### CRITICAL

**JS1 — `Core/lib_bejson_bejson.js`**  
`Switch` was never declared. Every Gaming library that reads or writes `Switch.*`
threw `ReferenceError: Switch is not defined` at load time. Added
`window.Switch = window.Switch || {};` before `Switch.BEJSON = {...}`.
Also wrapped the module in an IIFE and replaced the mixed `export default` /
`window.Core` pattern with a unified UMD-compatible conditional export, consistent
with all other libraries in the bundle. **JS2 (all Gaming libraries) resolves as a
cascade from this fix — no Gaming files needed individual edits.**

**SH1 — `Core/lib_bejson_validator.sh`**  
Mandatory-key check used `=~` substring match on a joined key string. `"Format"` is
a substring of `"Format_Creator"` and `"Format_Version"`, so a document that was
missing the bare `Format` key was incorrectly declared valid. Replaced with per-key
`jq -e 'has($key)'` exact-presence checks.

---

### HIGH

**SH2 — `Core/lib_bejson_core.sh` (`bejson_core_update_field`)**  
`--arg` always produces a JSON string in jq. Writing `"42"` to an `integer` field
stored `"42"` (string), breaking type fidelity. Now inspects the field's declared
type via `jq '.Fields[$fi].type'` and switches to `--argjson` for non-string types
so integers, numbers, and booleans round-trip correctly.

**FM2 — `Core/lib_bejson_state.js` (`undo()`)**  
`historyRows[idx][4]` hardcoded positional index 4 for the `snapshot` field.
Any insertion of a new field before `snapshot` would silently return garbage on undo.
Now dynamically resolves the snapshot index via `findIndex` before use.

**FM3 — `Core/lib_bejson_state.js` (`_syncToBEJSON`, `_saveHistory`)**  
Both methods called `findIndex` on every invocation for `Record_Type_Parent`, `key`,
`value`, `timestamp`, and `snapshot` — fields that never change at runtime. Added
`_buildFieldIdx()` called once at construction; both methods now read from
`this._fieldIdx` instead.

**H1 — `HTML/lib_html3_table.js`**  
`rtpIdx`, `isB64Idx`, and `nameIdx` were recomputed via `findIndex` on every record
iteration. For a 500-row table that's 500+ redundant linear scans — exactly the
problem the `bejson_core_get_field_map` cache was built to eliminate. Now calls the
cache at the top of `render()` once; `renderCell()` receives pre-resolved indices as
parameters.

**H2 — `HTML/lib_html3_tables.py`**  
The generated sort function scanned `bejson.Fields` linearly on every column-header
click. Added a `fieldIndexMap` object built once on IIFE init; the sort function
now uses `fieldIndexMap[currentSort.column]` instead of the loop.

**H5 — `HTML/lib_html3_table.js`**  
`activeFields[0].orgIdx` in the showActions `<button>` was accessed with no guard.
An empty-fields schema (e.g. a 104db type with only a discriminator field) caused
`TypeError: Cannot read properties of undefined`. Added `activeFields.length > 0`
check before the button block.

**H6 — `HTML/lib_html3_table.js`**  
`onFieldChange` from `options` was interpolated raw into an HTML `onchange` attribute.
A caller-supplied string containing `"` broke the attribute; one containing
`app.fn); alert(1); //` was an XSS vector. Now validated against
`/^[a-zA-Z_$][\w$]*(?:\.[a-zA-Z_$][\w$]*)*$/` — only dotted identifier paths pass.
Invalid values fall back silently to `'app.setViewField'`.

**H7 — `HTML/lib_html3_table.js`**  
`renderCell` escaped only `\` and `'` in the field name before inserting it into
inline `ondblclick`/`oncontextmenu` attributes. A `"` in a field name broke the
surrounding HTML attribute boundary (data→HTML injection path). Replaced the inline
handler string approach with a `data-field` / `data-rowidx` / `data-fieldidx`
attribute pattern; handlers now read from `this.dataset.*`, eliminating the injection
path entirely.

**JS3 — `Core/lib_bejson_validator.js`**  
The MFDB validator section appended to this file duplicated all functions and state
(`_mErrors`, `_mWarnings`) from `lib_mfdb_validator.js`. When both files were loaded,
calling an MFDB function from one module and checking errors from the other always
returned empty — a silent state-split bug. Removed the appended section (lines 611–1071);
`lib_mfdb_validator.js` remains the canonical MFDB validator.

**JS5 — `Core/lib_mfdb_validator.js`**  
`_loadJson`, `_resolveEntityPath`, and `_fileExists` called `require('fs')` /
`require('path')` unconditionally. In browser environments these throw immediately,
making `mfdb_validator_validate_manifest` non-functional. Added `_isNode()` guard;
browser calls to file-system helpers return a graceful error rather than crashing.

**JS7 — `Core/lib_bejson_parse.js`**  
`adm-zip` was treated as optional (caught silently), but `new AdmZip()` was called
unconditionally afterward. If the require failed, `AdmZip` was `undefined` and
`new AdmZip()` threw `TypeError` after files had already been written to disk. Added
an explicit `if (!AdmZip)` guard that returns `{ success: false, message: '...' }`
before any ZIP operations begin.

**JS9 — `Gaming/cli/game.js`**  
Import path `'./lib_bejson_engine_renderer'` was wrong on two counts: the file is
`lib_bejson_renderer.js` and it lives in the parent `Gaming/` directory, not in `cli/`.
Corrected to `'../lib_bejson_renderer'`.

**PY2 — `Core/lib_bejson_validator.py`**  
`isinstance(True, (int, float))` is `True` in Python because `bool` is a subclass of
`int`. So `True`/`False` passed the `number` type check without error. Added
`or isinstance(val, bool)` exclusion to the `number` branch, matching the existing
guard already present on the `integer` branch.

---

### MEDIUM

**JS4 — `Core/lib_mfdb_core.js`**  
`window.MFDB_CORE.version` was `"1.21"`. Corrected to `"1.31"` to match the spec and
all file headers. Any feature-gate code comparing against `"1.31"` was broken.

**JS8 — `Gaming/lib_bejson_events.js`**  
`Parent_Hierarchy` was set to `"Root/System/Events"` — not a valid relative path. Per
MFDB spec §15.4, it must be a relative path from the entity file's own directory back
to `104a.mfdb.bejson`. Corrected to `"../104a.mfdb.bejson"` (entity in `Gaming/`,
manifest at project root).

**JS10 — `Gaming/cli/game.js`**  
`catch (e) {}` in `deserialize()` swallowed all errors silently. Game continued with
stale/partial state and no feedback. Added `console.error` logging and an `emit`
call so the UI can display a load-failed message.

**JS11 — `External/jszip.min.js`**  
File header listed `Author: Elton Boehnen`. JSZip v3.10.1 is authored by Stuart
Knightley (MIT License). Corrected to `Author: Stuart Knightley (JSZip) | Bundled by: Elton Boehnen`.

**H9 — `HTML/lib_html3_tables.py`**  
When a 104db entity type existed in `Records_Type` but had no associated fields in
`Fields`, `filteredFields` contained only the discriminator. The table rendered a
silent single-column view with no indication of the schema gap. Added a
`filteredFields.length <= 1` check that renders a visible warning row instead.

**PY3 — `Core/lib_bejson_schema.py` (`SCHEMA_PROJECT_v140`)**  
All 22 field names used PascalCase (`Project_ID`, `Created_At`, `Is_Active`, etc.)
in violation of BEJSON spec §14.7 which requires snake_case. Corrected to
`project_id`, `created_at`, `is_active`, etc.  
⚠ **Breaking migration note:** Any persisted data using old field names must be
migrated. Positional integrity means the data values are unchanged; only the field
name keys in `Fields[]` are renamed.

**PY4 — `Core/lib_bejson_schema.py` (`SCHEMA_MODEL_REGISTRY`)**  
`Record_Type_Parent` appeared as a field in a BEJSON 104a schema. It is only
meaningful as the positional discriminator in 104db. Removed the field and stripped
the leading `"AI_Model"` discriminator value from every record in `Values`.

**SH3 — `Core/lib_bejson_core.sh`, `Core/lib_bejson_validator.sh`**  
Both set `set -o nounset` at the top level. When a host script sources either library,
this option applies globally to the host, causing immediate fatal errors on any
pre-existing unset variable. Removed `set -o nounset` from both files. `pipefail`
retained (less intrusive).

---

### LOW

**SH6 — `Core/lib_bejson_core.sh`**  
Added comment documenting that `sync "$temp_file" 2>/dev/null || true` is intentional:
on Android exFAT SD card paths, `sync(1)` may be a no-op, giving weaker durability
guarantees than internal storage.

**FM1 — `Core/lib_bejson_core.js`**  
Exported `bejson_core_clear_field_map_cache()` — previously only TS had this. Callers
who mutate a document's `Fields` array in-place after a cache entry was built can now
explicitly invalidate the stale entry.

**JS12 — `Core/bejson_cache.test.js`**  
Typo: `test_cache_collission` → `test_cache_collision` (same fix in the Python test
file was not required since `test_bejson_field_cache.py` was not in scope, but the
same rename should be applied there when next touched).

---

## Issues Not Fixed (Deferred / Architectural)

| ID | Reason |
|----|--------|
| H3 | Version divergence JS vs PY HTML3 — needs a feature matrix decision, not a code fix |
| H4 | `app.*` hardcoded namespace — requires API design decision (callback options object); too broad for surgical patch |
| H8 | `window['sort_'+cid]` global pollution — ES5-safe closure refactor needed; architectural scope |
| FM4 | TS `getFieldIndex` throws vs JS/PY return -1 — cross-runtime API design decision |
| FM5 | TS core doesn't import `bejson_field_map.ts` — TS architecture change |
| SH4 | `export -f` inconsistency — core.sh already exports its public API; audit finding appears stale |
| PY1 | TOCTOU race in lock acquire — already partially remediated; full fix requires OS-level atomic approach |
| PY5 | Single-line re-export files — no functional bug; decision on whether to keep aliases |
| PY6 | Python-generated `window[...]` global pollution — mirrors H8; architectural scope |
| PY7 | Dead cognition error codes in JS — requires decision on whether to add JS cognition lib or remove codes |
| X1 | TS core `getFieldIndex` throws — cross-runtime design divergence; same as FM4 |
| X2 | SH error code values differ from JS/PY — documented in `lib_bejson_errors.sh` (X3 fix) with legacy aliases |
| X4 | `BEJSONState` hardcoded index [4] in Python — fixed in JS (FM2); Python `lib_bejson_state_management.py` needs same treatment |
| A1 | `lib_bejson_bejson.js` thin-wrapper concern — JS1 fix stabilises it; deletion decision is architectural |
| A2 | HTML3 version alignment JS vs PY — same as H3 |
| A3 | Gaming family has no BEJSON validation at chunk load — feature addition, not bug fix |
| TS1 | `appendRecord` description vs behaviour — description-only confusion, no code bug |
| TS2 | `validate104a` runs 104db steps — minor inefficiency, not a correctness issue |
| TS3 | `BEJSONDocument` index signature — TS type system design trade-off |

---

*Elton Boehnen · eltonboehnen@gmail.com · boehnenelton2024.pages.dev · github.com/boehnenelton*
