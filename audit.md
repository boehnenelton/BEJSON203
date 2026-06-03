# BEJSON Library Suite — Audit Index
**Latest Entry:** [Hardening & Improvement Audit Report (v1.0, 2026-06-02)](reports/Hardening_Audit_Report_2026_06_02.md) - Tracking 23 critical/high findings.

---

# BEJSON Library Suite — Audit Report (Legacy)
**Target:** `Lib_JS`, `Lib_PY`, `Lib_SH`, `Lib_TS` — All v2.0.1 OFFICIAL (3BETA1 Bundle)  
**Focus Areas:** HTML2→HTML3 Integration · Field Map Cache · Full Cross-Runtime Audit  
**Auditor:** Claude (Anthropic) · **Date:** 2026-05-30  
**Commissioned by:** Elton Boehnen · boehnenelton2024.pages.dev · github.com/boehnenelton

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [PRIMARY — HTML2→HTML3 Integration Audit](#primary--html2html3-integration-audit)
3. [PRIMARY — Field Map / Field State Map Implementation](#primary--field-map--field-state-map-implementation)
4. [JavaScript Library (`Lib_JS`) Findings](#javascript-library-lib_js-findings)
5. [Python Library (`Lib_PY`) Findings](#python-library-lib_py-findings)
6. [Bash Library (`Lib_SH`) Findings](#bash-library-lib_sh-findings)
7. [TypeScript Library (`Lib_TS`) Findings](#typescript-library-lib_ts-findings)
8. [Cross-Runtime Inconsistencies](#cross-runtime-inconsistencies)
9. [Architecture & Standards Compliance](#architecture--standards-compliance)
10. [Strengths Worth Documenting](#strengths-worth-documenting)

---

## Executive Summary

The 3BETA1 bundle is structurally sound and represents a significant maturation of the BEJSON ecosystem. The field map cache was correctly implemented in all three primary runtimes (JS, PY, TS) and the MFDB validator was unified into the error registry properly. However, the HTML3 integration has a critical gap: the new field map infrastructure was not wired into the HTML3 rendering libraries that needed it most. There is also a meaningful collection of cross-runtime behavioral divergences, a dangerous attribute-injection pattern in the HTML3 JS table renderer, a version string error in `lib_mfdb_core.js`, two near-identical MFDB validator implementations coexisting in the JS bundle, an undefined `Switch` namespace problem throughout all Gaming libraries, and third-party attribution mishandled in `jszip.min.js`. None of these are individually catastrophic, but several are correctness issues rather than style concerns.

**Severity Legend:**  
`[CRITICAL]` — Data loss risk, crashes, security  
`[HIGH]` — Functional incorrectness, silent failure  
`[MEDIUM]` — Behavioral inconsistency, spec violation  
`[LOW]` — Style, maintainability, polish  
`[GOOD]` — Worthy callout

---

## PRIMARY — HTML2→HTML3 Integration Audit

The two HTML3 table libraries are `HTML/lib_html3_table.js` (v1.2.0, JS) and `HTML/lib_html3_tables.py` (v3.0.0, Python). These are the designated successors to the HTML2 table rendering. They diverge significantly and exhibit the following integration issues.

---

### H1 — Field Map Cache Not Wired Into HTML3 `[HIGH]`

**File:** `HTML/lib_html3_table.js`

The entire motivation for the `bejson_core_get_field_map` / `bejson_core_get_field_index` infrastructure was to eliminate repeated `findIndex` calls on `doc.Fields` — especially in table renderers that traverse every record. Yet `lib_html3_table.js` was not updated to use it. Three direct `findIndex`/`find` calls remain:

```js
// In render():
const rtpIdx = doc.Fields.findIndex(f => f.name === 'Record_Type_Parent');

// In renderCell():
const isB64Idx = doc.Fields.findIndex(fff => fff.name === 'is_base64');
const nameIdx = doc.Fields.findIndex(fff => fff.name === 'file_name');
```

`bejson_core_get_field_map` is exported from `lib_bejson_core.js` and available on `window.BEJSON`, but `lib_html3_table.js` never calls it. For a table rendering 500 records with 15 fields, `rtpIdx` is recomputed once per record — that's 500 unnecessary linear scans that the cache was designed to eliminate. **This is the primary integration gap.**

**Fix:** Import or access `window.BEJSON.bejson_core_get_field_map(doc)` at the top of `render()`, then use the returned map for all subsequent index lookups.

---

### H2 — Rendered JS Inside `lib_html3_tables.py` Also Skips Cache `[HIGH]`

**File:** `HTML/lib_html3_tables.py`

The Python version generates a self-contained `<script>` block. Inside that script, the sort function performs a linear scan:

```js
var fieldIdx = -1;
for (var i = 0; i < bejson.Fields.length; i++) {
    if (bejson.Fields[i].name === currentSort.column) {
        fieldIdx = i; break;
    }
}
```

This is run every time the user clicks a column header to sort. The data is already in-browser, so efficiency matters at table render time. The generated script should build a field index map once on init (a simple `{}` object from a single loop over `bejson.Fields`) and reuse it. No external dependency needed — just a local pre-computation step that was the whole point of the cache concept.

---

### H3 — Version Divergence Between JS and Python HTML3 `[MEDIUM]`

`lib_html3_table.js` is at v1.2.0. `lib_html3_tables.py` is at v3.0.0. These are supposed to be the same component across runtimes. A two-major-version gap means they have been developed independently without synchronization. Feature parity should be tracked. Notably: the Python version added pagination, search, and schema toggle that the JS version lacks. If they're converging to HTML3, there should be a single feature spec they both implement.

---

### H4 — Hardcoded `app` Global Namespace in JS Table `[HIGH]`

**File:** `HTML/lib_html3_table.js`

Nearly every interactive element in the rendered HTML is hardcoded to call `app.*`:

```js
html += `... onchange="app.toggleSelectAll(this.checked)" ...`;
html += `... onclick="app.selectField(${f.orgIdx})" ...`;
html += `... onclick="app.sortData(${currentField.orgIdx}, !appState.sortAsc)" ...`;
html += `... onclick="app.cellExpandOpen(...)" ...`;
html += `... onchange="app.updateValue(...)" ...`;
html += `... ondblclick="app.cellExpandOpen(...)" ...`;
html += `... oncontextmenu="app.inputContextMenu(...)" ...`;
```

Only `onFieldChange` is configurable. Every other callback is hardcoded to `app`. Any host page that doesn't expose a global `app` object with all these exact method names will silently produce dead buttons or throw `TypeError: app is undefined` on user interaction. The `options` object accepted by `render()` should expose callback overrides for all of these.

---

### H5 — Crash on Empty `activeFields` in `showActions` Block `[HIGH]`

**File:** `HTML/lib_html3_table.js`

```js
if (showActions && !mobileMode) {
    html += `<td ...>
        <button ... onclick="app.cellExpandOpen(null, ${row.orgIdx}, ${activeFields[0].orgIdx}, ...)">EDIT</button>
    </td>`;
}
```

If `activeFields` is empty (a schema with only a `Record_Type_Parent` field, or an empty 104 schema), `activeFields[0]` throws `TypeError: Cannot read properties of undefined`. There's no guard. Add `activeFields.length > 0 &&` before the reference.

---

### H6 — `onFieldChange` Option Is Injection-Vulnerable `[HIGH]`

**File:** `HTML/lib_html3_table.js`

```js
const { onFieldChange = "app.setViewField" } = options;
// ...
html += `<select onchange="${onFieldChange}(parseInt(this.value))" ...>`;
```

The `onFieldChange` string is interpolated directly into an HTML attribute with no escaping. If a caller passes a string containing `"`, the attribute is broken. If passed something like `app.fn); alert(1); //`, the rendered HTML becomes an XSS vector. Even under trusted-caller assumptions, this should use a data attribute and an attached event listener, not inline handler injection.

---

### H7 — `renderCell` Attribute-Injection via Field Name `[HIGH]`

**File:** `HTML/lib_html3_table.js`

```js
const fn = field.name.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
// ...
return `<input ... ondblclick="app.cellExpandOpen(this, ${rowIdx}, ${field.orgIdx}, '${fn}')"
               oncontextmenu="app.inputContextMenu(event, this, ${rowIdx}, ${field.orgIdx}, '${fn}')">`;
```

Only backslashes and single quotes are escaped. If a field name contains `"` (double-quote), it will break the surrounding HTML attribute. Since field names come from user-supplied BEJSON data, this is a data→HTML injection path. The `esc()` method exists on `HTML3_Table` for exactly this purpose but isn't used here.

---

### H8 — Global Namespace Pollution in Rendered JS `[MEDIUM]`

**File:** `HTML/lib_html3_tables.py`

```js
window['sort_' + cid] = function(col) { ... };
window['navigate_page_' + cid] = function(dir) { ... };
window['schema_toggle_' + cid] = function() { ... };
```

Each table component attaches three functions to `window`. With 10 table instances on a page, that's 30 global function slots. This was already the pattern in HTML2. HTML3 should have moved to closures or component-local event delegation — the `cid` uniqueness only mitigates collision, it doesn't eliminate global pollution.

---

### H9 — No Null Guard for `filteredFields` When Type Has No Fields `[MEDIUM]`

**File:** `HTML/lib_html3_tables.py` (rendered JS)

```js
var filteredFields = (bejson.Format_Version === '104db') ?
    bejson.Fields.filter(function(f, i) {
        return i === 0 || f.Record_Type_Parent === selectedType;
    }) :
    bejson.Fields;
```

If `selectedType` is set to an entity name that exists in `Records_Type` but has no associated fields in `Fields` (malformed document), `filteredFields` will contain only the discriminator field at index 0. The table renders but displays a single-column `Record_Type_Parent`-only view with no indication of the schema gap. A check for `filteredFields.length <= 1` (only discriminator) should produce a warning row.

---

## PRIMARY — Field Map / Field State Map Implementation

---

### FM1 — JS Cache Has No Invalidation or Clear Function `[MEDIUM]`

**File:** `Core/lib_bejson_core.js`

```js
const _FIELD_MAP_CACHE = new Map();
```

The cache is a module-level Map that grows unboundedly and has no exported `clearCache()` or `invalidate()` function. The TS version correctly adds `bejson_core_clear_field_map_cache()`. If a document's `Fields` array is mutated in-place after a cache entry was built (which `appendRecord` in TS does immutably, but direct mutation by callers does not prevent), the stale cache entry will return wrong indices indefinitely. Expose `bejson_core_clear_field_map_cache()` from the JS exports.

---

### FM2 — `BEJSONState._restore()` Uses Hardcoded Field Index `[HIGH]`

**File:** `Core/lib_bejson_state.js`

```js
undo() {
    const historyRows = this.bejson.Values.filter(r => r[0] === "History");
    if (this._historyIndex <= 0) return false;
    this._historyIndex--;
    this._restore(JSON.parse(historyRows[this._historyIndex][4]));
    return true;
}
```

Position `[4]` for the `snapshot` field is hardcoded. This assumes the History entity's field layout never changes. The correct approach is to look up the snapshot index using `bejson_core_get_field_index`. Since the field map cache is available in the same module, this should use it. If the schema definition is ever reordered (or a new field is inserted before `snapshot`), `undo()` silently returns garbage data.

The Python `lib_bejson_state_management.py` has the same issue at `history_rows[self._history_index][4]`.

---

### FM3 — `_syncToBEJSON()` Uses `findIndex` Instead of Cache `[LOW]`

**File:** `Core/lib_bejson_state.js`

```js
const rtpIdx = fields.findIndex(f => f.name === "Record_Type_Parent");
const keyIdx = fields.findIndex(f => f.name === "key");
const valIdx = fields.findIndex(f => f.name === "value");
```

`_syncToBEJSON()` is called on every state mutation. That's three `findIndex` calls per mutation on a document whose schema never changes at runtime. These should use the field map cache (`bejson_core_get_field_map`) and cache the indices at construction time.

---

### FM4 — TS `bejson_core.ts` `getFieldIndex` Throws; JS/PY Return -1 `[MEDIUM]`

**File:** `Core/bejson_core.ts`

```ts
export function getFieldIndex(doc: BEJSONDocument, name: string): number {
  const idx = doc.Fields.findIndex((f) => f.name === name);
  if (idx === -1) {
    throw new BEJSONCoreError(BEJSON_CORE_CODES.FIELD_NOT_FOUND, "Field not found: " + name);
  }
  return idx;
}
```

JS and Python return -1 on missing field. TS throws. Any code ported between TS and JS/PY must handle this divergence with try/catch vs. -1 checks. The field map module (`bejson_field_map.ts`) returns -1 on miss. The core module throws. This internal inconsistency within the TS bundle will surprise consumers.

---

### FM5 — TS Core Does Not Import or Use `bejson_field_map.ts` `[MEDIUM]`

**File:** `Core/bejson_core.ts`

`bejson_field_map.ts` (v3.0.0) is a separate dedicated module with the cache implementation. But `bejson_core.ts` (v2.0.1) uses `doc.Fields.findIndex()` directly without importing the field map. This fragments the ecosystem: to get cached behavior in TS, you must import `bejson_field_map.ts` explicitly rather than just using the core API. The JS version at least puts the cache in core.

---

## JavaScript Library (`Lib_JS`) Findings

---

### JS1 — `lib_bejson_bejson.js`: `Switch` Namespace Undefined `[CRITICAL]`

**File:** `Core/lib_bejson_bejson.js`

```js
window.Core = window.Core || {};
Switch.BEJSON = { ... };      // ReferenceError: Switch is not defined
export default Switch.BEJSON; // Fails if not a module context
```

`Switch` is never declared. `window.Switch` is never initialized. Every call site that `import`s or includes this file will throw `ReferenceError: Switch is not defined` on load. This file is referenced by all Gaming libraries. It needs either `window.Switch = window.Switch || {}` before the assignment, or a local `const Switch = {}` pattern.

The `export default` mixes ES module syntax with browser-global (`window.Core`) assignment. In a non-module `<script>` tag this will throw a SyntaxError. In a module context, `window.Core` assignment is fine but `window` may not be the right export target.

---

### JS2 — All Gaming Libraries Reference Undefined `Switch` `[CRITICAL]`

**Files:** `Gaming/lib_bejson_assets.js`, `lib_bejson_events.js`, `lib_bejson_grid.js`, `lib_bejson_input.js`, `lib_bejson_physics.js`, `lib_bejson_renderer.js`, `lib_bejson_ui_screens.js`, `lib_bejson_engine_core.js`

Every Gaming library writes to or reads from `Switch.*`. Every single one will throw at module load time until `lib_bejson_bejson.js` is fixed. This is a cascading breakage covering the entire Gaming family.

---

### JS3 — `lib_bejson_validator.js` and `lib_mfdb_validator.js` Are Near-Duplicate `[HIGH]`

Both `lib_bejson_validator.js` (MFDB section, appended) and `lib_mfdb_validator.js` define identical functions: `mfdb_validator_validate_manifest`, `mfdb_validator_validate_entity_file`, `mfdb_validator_validate_database`, `mfdb_validator_get_report`, and all supporting helpers (`_loadJson`, `_rowsAsDicts`, `_resolveEntityPath`, `_fileExists`). They also both declare `_mErrors` and `_mWarnings` module-level arrays.

If both files are loaded in a browser context, the global `window.BEJSON_VALIDATOR` and `window.MFDB_VALIDATOR` both exist with different state arrays. `_mErrors` in each are isolated from each other — calling `mfdb_validator_validate_manifest` from one module and checking errors from the other always returns empty. This is a maintenance burden and a silent state-split bug.

The appended MFDB section in `lib_bejson_validator.js` should be removed. `lib_mfdb_validator.js` is the canonical location.

---

### JS4 — `lib_mfdb_core.js` Reports Version `"1.21"` `[MEDIUM]`

**File:** `Core/lib_mfdb_core.js`

```js
window.MFDB_CORE = {
    ...window.MFDB_CORE,
    MFDBArchive,
    version: "1.21"    // Should be "1.31"
};
```

The spec is MFDB v1.31. All file headers declare `MFDB Version: 1.31`. The runtime version string is wrong. Any feature gate code checking `MFDB_CORE.version` against "1.31" will fail.

---

### JS5 — `lib_mfdb_validator.js` Uses `require()` Inside Browser-Only Class `[HIGH]`

**File:** `Core/lib_mfdb_validator.js`

The `MFDBArchive` class in `lib_mfdb_core.js` uses `FileSystemDirectoryHandle`, `JSZip`, and browser-only APIs. But the helper functions used by the validator (`_loadJson`, `_fileExists`) use `require('fs')` and `require('path')` with no fallback. In browser environments, these silently return errors or throw, making `mfdb_validator_validate_manifest` (which calls `_loadJson`) completely non-functional in browser. The validator was ported from Node.js but not properly adapted for the dual-environment pattern established by the core library.

---

### JS6 — `lib_bejson_parse.js`: Legacy HTML2 Field Names Not Cleaned Up `[MEDIUM]`

**File:** `Core/lib_bejson_parse.js`

```js
for (const key of ['projectname', 'zipfilename', 'containername']) {
    const v = getVal(row, key);
```

These key names (`zipfilename`, `containername`) are not BEJSON field naming conventions (should be snake_case with proper domain names) and appear to be legacy HTML2 fields that survived the HTML3 migration. The BEJSON spec's field naming convention is snake_case; these look like flat form field names from an older generation of the tool. If the chunker config changed its schema, these lookups will silently return nothing and fall through to `'My_Project'`.

---

### JS7 — `lib_bejson_parse.js`: `AdmZip` Used After Catch-Swallowed Import Failure `[HIGH]`

**File:** `Core/lib_bejson_parse.js`

```js
let AdmZip;
try { AdmZip = require('adm-zip'); } catch (e) { /* optional dependency */ }
// ...
const zip = new AdmZip();   // Throws TypeError if require failed above
```

If `adm-zip` is not installed, `AdmZip` is `undefined` and `new AdmZip()` throws `TypeError: AdmZip is not a constructor` at runtime, after files have already been written to disk. The function should guard: `if (!AdmZip) { return { success: false, message: 'adm-zip not installed' }; }` before attempting zip creation.

---

### JS8 — `lib_bejson_events.js`: `Parent_Hierarchy` Set to Non-Path Value `[MEDIUM]`

**File:** `Gaming/lib_bejson_events.js`

```js
this.events.Parent_Hierarchy = "Root/System/Events";
```

Per MFDB spec §15.4, `Parent_Hierarchy` must be a relative path from the entity file's directory back to the manifest file (`104a.mfdb.bejson`). "Root/System/Events" is neither relative nor pointing to a manifest. The MFDB discovery algorithm (§15.5 Step 4) uses this field to identify entity files; a bad value makes this entity unresolvable as MFDB. For in-memory use this is harmless, but it's a spec violation that would make any serialized version of this document fail MFDB validation.

---

### JS9 — `game.js`: Broken Import Path `[HIGH]`

**File:** `Gaming/cli/game.js`

```js
import SwitchRenderer from './lib_bejson_engine_renderer';
```

The actual file is `Gaming/lib_bejson_renderer.js` (not `lib_bejson_engine_renderer`). This import will fail at module resolution time. The engine file is `lib_bejson_engine_core.js`, not the renderer. These were likely confused during the naming pass.

---

### JS10 — `game.js`: Silent Exception Swallow in `deserialize` `[MEDIUM]`

**File:** `Gaming/cli/game.js`

```js
deserialize(data) {
    try {
        const parsed = JSON.parse(data);
        // ...
    } catch (e) {}   // Silent failure
}
```

If deserialization fails (corrupted save, schema version mismatch), the game continues running with stale/partial state. No error is logged, no user feedback is given. At minimum, `console.error` the failure. Better: expose it via the `emit` system so the UI can display a "Load failed" message.

---

### JS11 — `jszip.min.js`: Third-Party Code Misattributed `[MEDIUM]`

**File:** `External/jszip.min.js`

The file header states `Author: Elton Boehnen` and `Version: 2.0.1 OFFICIAL`. JSZip v3.10.1 is authored by Stuart Knightley and licensed MIT. The inline license comment within the minified code correctly attributes the original author. But the outer header block is false attribution. Under the Crediting Policy, Elton's credit block should appear only on Elton's code. Wrapping third-party code in Elton's standard header creates an authorship conflict. Correct this to: `Author: Stuart Knightley (JSZip) | Bundled by: Elton Boehnen`.

---

### JS12 — `bejson_cache.test.js`: Method Name Typo `[LOW]`

**File:** `Core/bejson_cache.test.js`

```js
function test_cache_collission() {
```

"Collision" is misspelled as "collission". Minor, but test names matter for grep and CI output readability. The Python test file uses `test_cache_collission_safety` with the same typo — copy-paste artifact.

---

## Python Library (`Lib_PY`) Findings

---

### PY1 — `bejson_core_acquire_lock`: TOCTOU Race Condition `[HIGH]`

**File:** `Core/lib_bejson_core.py`

```python
if os.path.exists(lock_path):
    mtime = os.path.getmtime(lock_path)
    if (time.time() - mtime) > stale_age:
        os.unlink(lock_path)   # Race: another process could recreate between unlink and our O_EXCL open
```

Between `os.unlink(lock_path)` and the subsequent `os.open(..., os.O_CREAT | os.O_EXCL | ...)`, another process can create the lock file. On Android with Termux running multiple script instances, this window is real. The code handles the resulting `FileExistsError` gracefully (loops back), so the race doesn't cause data corruption — but it can cause the stale-lock override to fail to acquire. The comment says "REMEDIATED" but the race was not fully closed.

---

### PY2 — `number` Type Accepts `True`/`False` `[HIGH]`

**File:** `Core/lib_bejson_validator.py`

```python
elif ftype == "number" and not isinstance(val, (int, float)):
    raise BEJSONValidationError(...)
```

In Python, `bool` is a subclass of `int`. `isinstance(True, (int, float))` is `True`, so `True` and `False` pass a `number` type check without error. The spec defines `number` as a numeric value, not boolean. Add `isinstance(val, bool)` exclusion: `not isinstance(val, (int, float)) or isinstance(val, bool)`.

The same issue exists for `integer`: `isinstance(True, int)` is `True`, so `True` would pass an integer field check. The code already guards this with `or isinstance(val, bool)` — but not for `number`.

---

### PY3 — `SCHEMA_PROJECT_v140` Field Names Violate snake_case Convention `[MEDIUM]`

**File:** `Core/lib_bejson_schema.py`

Fields like `Project_ID`, `Project_Name`, `Created_At`, `Is_Active`, `Git_Enabled`, `Internal_Notes` use PascalCase with underscores — not snake_case. The BEJSON spec (§14.7) explicitly states: "Use snake_case for all field names." These should be `project_id`, `project_name`, `created_at`, `is_active`, `git_enabled`, `internal_notes`. Because schema fields define positional integrity, changing them is a breaking migration, but they're wrong as shipped.

---

### PY4 — `SCHEMA_MODEL_REGISTRY` in 104a Has Unnecessary `Record_Type_Parent` Field `[MEDIUM]`

**File:** `Core/lib_bejson_schema.py`

```python
"Format_Version": "104a",
"Fields": [
    {"name": "Record_Type_Parent", "type": "string"},   # Not needed for 104a
    ...
],
"Values": [
    ["AI_Model", "gemini-2.5-flash", ...],
```

For BEJSON 104a, `Record_Type_Parent` as a field is meaningless — it's only required as the first field in 104db for the discriminator. Having it in a 104a schema forces every record to carry an extra positional slot. The validator won't reject it, but it creates unnecessary bulk and confusion. Strip `Record_Type_Parent` from this schema and its values.

---

### PY5 — `lib_bejson_mfdb_core.py` and `lib_bejson_mfdb_validator.py` Are Single-Line Re-Exports `[LOW]`

```python
# lib_bejson_mfdb_core.py
from lib_mfdb_core import *
```

These files exist solely to provide an alternative import path. They add zero logic. If `lib_mfdb_core.py` moves or renames, these silently become ImportError bombs. If they're needed for namespace compatibility, they should at minimum have a `__all__` and a docstring explaining why they exist. Consider whether they're necessary at all.

---

### PY6 — `lib_html3_tables.py`: `window['sort_' + cid]` Pattern Generates Global Pollution `[MEDIUM]`

**File:** `HTML/lib_html3_tables.py`

The rendered JavaScript registers sort, paginate, and schema-toggle handlers as global `window` properties. Every table instance adds 3 globals. On a page with a live BEJSON editor and multiple table components (manifest + entity views), this adds up fast. ES5-safe alternatives exist: delegate click handlers from a wrapper `div` using event bubbling, eliminating global function registration entirely.

---

### PY7 — Cognition Error Codes Present in JS but No JS Cognition Library Exists `[LOW]`

**File:** `Core/lib_bejson_errors.js` (JS bundle)

Error codes 270–275 (`E_COGNITION_*`) are defined in the JS error registry, mirroring the Python registry. However, there is no `lib_bejson_cognition.js` in the JS bundle — only `AI/lib_bejson_cognition.py` in Python. These error codes are dead symbols in the JS context, adding confusion to the registry without serving any function. Either add the JS cognition library or remove the cognition codes from the JS error registry.

---

## Bash Library (`Lib_SH`) Findings

---

### SH1 — Mandatory Key Check Uses Substring Match `[CRITICAL]`

**File:** `Core/lib_bejson_validator.sh`

```bash
local keys=$(jq -r 'keys | join(",")' "$file_path")
for k in Format Format_Version Format_Creator Records_Type Fields Values; do
    if [[ ! "$keys" =~ "$k" ]]; then
        return $E_VAL_MISSING_KEY
    fi
done
```

`=~` tests substring presence in the joined key string. The key `"Format"` is a substring of `"Format_Creator"` and `"Format_Version"`. Therefore a document with only `Format_Creator`, `Format_Version`, `Records_Type`, `Fields`, and `Values` — but missing `Format` — would still pass this check because `"Format"` appears inside `"Format_Creator"`. A document legitimately missing the `Format` key would be declared valid. The check must be exact-match, not substring. Use `jq` directly: `jq -e '.Format != null' "$file_path"` per key.

---

### SH2 — `bejson_core_update_field` Always Writes Strings `[HIGH]`

**File:** `Core/lib_bejson_core.sh`

```bash
bejson_core_update_field() {
    # ...
    echo "$doc" | jq ... --arg nv "$new_val" '(.Values[$ri][$fi]) = $nv'
}
```

`--arg` in jq always produces a JSON string. Updating an `integer` field with `bejson_core_update_field "$doc" 0 "count" "42"` writes `"42"` (string), not `42` (integer). Use `--argjson` when the target field type is not string, or inspect the field type and conditionally use `--arg` vs `--argjson`.

---

### SH3 — `set -o nounset` in Library Files Affects Host Script `[MEDIUM]`

**Files:** `Core/lib_bejson_core.sh`, `Core/lib_bejson_validator.sh`

Both set `set -o nounset` at the top level. When sourced with `source lib_bejson_core.sh`, these options are applied to the calling script. Any pre-existing unset variables in the host script will then immediately cause fatal errors. Library files should not modify global shell options; these `set` calls belong in the entry-point scripts, not the sourced libraries.

---

### SH4 — `export -f` Used Inconsistently `[MEDIUM]`

**File:** `Core/lib_bejson_validator.sh`

Validator functions are exported with `export -f`. Core functions (`lib_bejson_core.sh`) are not exported at all. If a caller runs a subshell (e.g., `bash -c "bejson_core_atomic_write ..."`) expecting core functions to be available, they won't be. Either export all public-API functions from both libraries, or document that the libraries must always be re-sourced inside subshells.

---

### SH5 — Bash-Level Field Map Has No Cache — Correct, but Needs Documentation `[LOW]`

The Bash library correctly uses `jq` for every field lookup rather than attempting to cache. Given Bash's lack of persistent in-process state, this is the right approach. However, there's no comment acknowledging this design decision or pointing out that heavy use (hundreds of lookups) should switch to `jq` scripts rather than repeated shell function calls. A note in the library header would help consumers understand the performance profile.

---

### SH6 — `bejson_core_atomic_write`: Silent `sync` Failure on Android SD Card `[LOW]`

**File:** `Core/lib_bejson_core.sh`

```bash
sync "$temp_file" 2>/dev/null || true
```

On Android SD card paths (`/storage/7B30-0E0B/...`) formatted as exFAT, the `sync` utility may be a no-op or unavailable. The `|| true` swallows any error. This is intentional and documented behavior given Android constraints, but the fallback silent pattern means writes to SD card have weaker durability guarantees than writes to internal storage. A comment noting this environment-specific limitation would be appropriate.

---

## TypeScript Library (`Lib_TS`) Findings

---

### TS1 — `bejson_core.ts`: `appendRecord` Mutates via `_cloneWith` but Description Says Immutable `[MEDIUM]`

**File:** `Core/bejson_core.ts`

The TS core uses an immutable-style API (`appendRecord` returns a new doc via `_cloneWith`). This is good design. However, `getFieldIndex` throws on miss (see FM4) while the field map module returns -1. Consumers who copy patterns from the field map module and then switch to core functions will get unexpected exceptions.

---

### TS2 — `bejson_validators.ts`: `validate104a()` Runs Full Validation Including 104db Steps Before Version Check `[LOW]`

**File:** `Core/bejson_validators.ts`

```ts
export function validate104a(doc: unknown): ValidationResult {
    const result = validateDocument(doc);   // Runs ALL steps including 104db-specific
    if (result.valid) {
        if (bej.Format_Version !== "104a") {
            _err(result, ...);
        }
    }
    return result;
}
```

If `doc` is actually a 104db document and `validate104a` is called, it runs 104db-specific validation (discriminator checks, null-padding checks), succeeds at step 6, then checks and fails the version assertion. This is not incorrect — it reports an error — but it does unnecessary work. Minor issue in the current codebase, but could become confusing when extending.

---

### TS3 — `BEJSONDocument` Index Signature Accepts Arbitrary Keys `[MEDIUM]`

**File:** `Core/bejson_types.ts`

```ts
export interface BEJSONDocument {
    // ...
    [key: string]: unknown;
}
```

The index signature `[key: string]: unknown` is necessary for 104a custom headers, but it makes TypeScript unable to catch typos in known property access. `doc.Format_Vesion` (typo) compiles cleanly and returns `undefined`. Consider a discriminated union approach: a strict base type plus an intersection `& Record<string, unknown>` only for 104a documents. This is non-trivial but would significantly improve compile-time safety for the TS library.

---

## Cross-Runtime Inconsistencies

---

### X1 — `getFieldIndex` / `bejson_core_get_field_index` Behavior on Miss

| Runtime | Behavior on missing field |
|---------|--------------------------|
| JS | Returns `-1` |
| Python | Returns `-1` |
| Bash | Returns `-1` (via `// -1` jq fallback) |
| TS (core) | **Throws `BEJSONCoreError`** |
| TS (field_map) | Returns `-1` |

Any cross-language documentation or generated port code must account for this divergence. The TS core module is the outlier.

---

### X2 — Error Code Mapping Diverges Between SH and Other Runtimes

| Condition | JS/PY code | SH code |
|-----------|-----------|---------|
| Bad Format | 3 | 3 (as `E_VAL_BAD_FORMAT`) |
| Bad Creator | 3 | **5** (as `E_VAL_BAD_CREATOR`) |
| Schema Mismatch | 9 | **6** (as `E_VAL_SCHEMA_MISMATCH`) |
| Invalid Type | 8 | **7** (as `E_VAL_INVALID_TYPE`) |

The Bash validator defines its own error codes independently rather than sourcing `lib_bejson_errors.sh` (which doesn't exist — there is no shell error registry file). A `lib_bejson_errors.sh` should be created, mirroring `lib_bejson_errors.js` and `lib_bejson_errors.py` with `readonly` variable assignments.

---

### X3 — No `lib_bejson_errors.sh` File in the Shell Bundle

The JS, PY, and TS bundles all have a centralized error registry. The SH bundle has no equivalent — each `.sh` file defines its own error codes with a `[[ -v ... ]] || readonly` guard pattern. This is functional but not unified. A shared `lib_bejson_errors.sh` with all the same codes (1–275) would complete the runtime parity.

---

### X4 — `BEJSONState` Undo History Uses Positional Index `[4]` in Both JS and PY

Both `lib_bejson_state.js` and `lib_bejson_state_management.py` hardcode position 4 for the snapshot field. Both were written with the same schema, so both have the same fragility. This should be fixed in both runtimes simultaneously when addressed.

---

## Architecture & Standards Compliance

---

### A1 — `lib_bejson_bejson.js` Has No Meaningful Role `[MEDIUM]`

**File:** `Core/lib_bejson_bejson.js`

This file's purpose is "Recursive BEJSON utility for managing BEJSON files within BEJSON" — but it only provides thin wrappers (`create104`, `create104a`, `create104db`, `getFieldIndex`, `query`, `isValid`) that duplicate functions already in `lib_bejson_core.js`. The `isValid` check is weaker (only checks `Format`, `Format_Version`, and `Format_Creator`) compared to the full validator. The `Switch.BEJSON` namespace definition here is what breaks every Gaming library (see JS1). This file should either be deleted and Gaming libraries updated to use `window.BEJSON` directly, or promoted as the official entry-point namespace with the `Switch` undefined issue fixed.

---

### A2 — `lib_html3_table.js` Version (1.2.0) vs `lib_html3_tables.py` (3.0.0) Needs Alignment `[MEDIUM]`

If HTML3 is a single concept spanning runtimes, there should be a single version number (or at least synchronized major versions). The Python version has pagination and schema toggle; the JS version does not. The JS version has mobile mode; the Python version does not. These are different products wearing the same name. Define a feature matrix for HTML3 Table and track which runtime implements which features.

---

### A3 — Gaming Family Has No BEJSON Validation at Load Time `[MEDIUM]`

`ChunkManager.loadChunk()` in `lib_bejson_engine_core.js` does:

```js
const response = await fetch(url);
const data = await response.json();
this.activeChunks.set(key, data);
```

There is no call to `bejson_validator_validate_string` after parsing. Malformed chunk files (wrong field count, bad types) are loaded silently and then crash later when `getNearbyTiles()` or the renderer tries to access positional indices. At minimum, validate the `Records_Type` and `Fields` length before accepting a chunk.

---

## Strengths Worth Documenting

---

### GOOD1 — Field Map Cache Architecture Is Correct in JS and Python

The implementation in `lib_bejson_core.js` and `lib_bejson_core.py` is well-designed. The cache key incorporates both `Format_Version` and field names as a tuple/string, ensuring documents with identical field names but different versions don't collide. The Python version correctly uses a `tuple` as the dict key (hashable, immutable). The JS version uses string concatenation which is functionally equivalent. The logic is tight and the test coverage (`bejson_cache.test.js`, `test_bejson_field_cache.py`) actually exercises collision safety with `doc1` and `doc2` having reversed field order.

---

### GOOD2 — TS `bejson_field_map.ts` Has the Only `clearCache()` Function

The TS field map module exports `bejson_core_clear_field_map_cache()` — the only runtime that provides explicit cache invalidation. This should be replicated in JS and Python.

---

### GOOD3 — Atomic Write Implementation Is Thorough

The Python `bejson_core_atomic_write` uses `tempfile.mkstemp`, `os.fdopen`, `f.flush()`, `os.fsync()`, and `os.replace()` — all the right steps for true atomic writes. The Bash version mirrors this with a `mv`-based swap and includes a backup pass. Both include cleanup on failure. This is production-grade file I/O.

---

### GOOD4 — Stale Lock Override in Python Is a Real Fix

```python
if (time.time() - mtime) > stale_age:
    logging.warning(f"Overriding stale lock ...")
    os.unlink(lock_path)
```

The comment says "REMEDIATED" and it genuinely is. Previous versions of this pattern without stale detection would deadlock if a process died holding the lock. The 60-second default is reasonable for Android usage patterns.

---

### GOOD5 — BEJSON 104db Null-Padding Validation Is Correct and Complete

In `lib_bejson_validator.js`, the 104db check in `bejson_validator_check_values` correctly identifies field ownership and enforces that non-applicable fields are `null`:

```js
if (version === '104db' && fieldParent && j > 0) {
    if (fieldParent !== recordType) {
        if (value !== null) {
            _state.addError(...);
            throw new BEJSONValidationError('Null violation', E_NULL_VIOLATION);
        }
        continue;
    }
}
```

This is the most subtle part of 104db validation and it's implemented correctly across JS, Python, and TS. The `j > 0` guard correctly skips the discriminator field.

---

### GOOD6 — `lib_html3_tables.py` Is Genuinely ES5-Safe

The generated JavaScript in `lib_html3_tables.py` uses `var`, `function() {}`, and no arrow functions, template literals, or destructuring. This was the point of `ES5_SAFE = True` and it holds up in inspection. Older Android WebView versions will not choke on this output.

---

### GOOD7 — Error Code Ranges Are Well-Structured

The 1–15 / 20–29 / 30–49 / 50–69 / 270–289 range split across BEJSON Validator, Core, MFDB Validator, MFDB Core, and Cognition is clean and leaves room for expansion in each zone. The centralized `lib_bejson_errors.js` and `lib_bejson_errors.py` ensure all runtimes share the same numeric contract. Adding a Bash equivalent would complete this.

---

### GOOD8 — MFDB Bidirectional Path Check Fully Implemented

The bidirectional validation (manifest→entity path must equal entity→manifest resolution) is correctly implemented in all three environments that have an MFDB validator (JS, PY, TS). This is the hardest MFDB consistency check to get right and it's solid across the board.

---

*End of Audit Report — BEJSON Library Suite v3BETA1*  
*Elton Boehnen · boehnenelton2024@gmail.com · boehnenelton2024.pages.dev · github.com/boehnenelton*
