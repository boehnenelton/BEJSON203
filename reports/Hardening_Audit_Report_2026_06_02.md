# BEJSON / MFDB Library Ecosystem — Hardening & Improvement Audit Report

**Report Version:** 1.0
**Audit Date:** June 2, 2026
**Scope:** Lib_PY (beta4), Lib_JS (beta4), Lib_TS (beta4), Lib_SH (beta4)
**Authoritative Standards:** MFDB Spec v1.31 · Policy v1.4 · BEJSON Format Spec
**Author:** Elton Boehnen | boehnenelton2024@gmail.com | boehnenelton2024.pages.dev | github.com/boehnenelton

---

## EXECUTIVE SUMMARY

This audit covers all four runtime library families delivered as BEJSON 104db chunk files.
The libraries are in a strong foundational state — atomic writes are implemented, the
unified error code registry exists across all four runtimes, field map caching is actively
being integrated, and several prior bugs (SH3 nounset, SH1 key match, H1–H7 table rendering,
JS1 namespace, SH2 type coercion) have been correctly remediated and documented in changelogs.

However, **23 distinct issues** were identified across correctness, security, cross-runtime
consistency, and architectural hygiene categories. Several are **active bugs** that will
cause failures in production. This report classifies each finding by severity, maps it to
the responsible runtime(s), and prescribes the exact next action.

---

## INVENTORY SNAPSHOT

| Library | Files | Families Covered | Project Version |
| :--- | :---: | :--- | :---: |
| Lib_PY | 74 | AI, CMS, Cognition, Core, Gaming, HTML, System, Utility | 2.0.1 |
| Lib_JS | 25 | Core, External, Gaming, HTML, Utility | 2.0.1 |
| Lib_TS | 19 | Core, Gaming, Utility | 2.0.1 |
| Lib_SH | 12 | Core, System | 2.0.1 |

**Total files under audit:** 130

**Family coverage gaps (PY families not represented in other runtimes):**

| Missing Family | Absent From |
| :--- | :--- |
| AI | JS, TS, SH |
| CMS | JS, TS, SH |
| Cognition | JS, TS, SH |
| HTML | TS, SH |
| System | JS, TS |
| Gaming | SH |
| Utility | SH |

---

## SEVERITY CLASSIFICATIONS

| Label | Meaning |
| :--- | :--- |
| 🔴 CRITICAL | Active bug — will cause failures or security exposure in production |
| 🟠 HIGH | Architectural violation against spec or policy — causes drift or silent inconsistency |
| 🟡 MEDIUM | Standards gap or fragile pattern — will become a problem at scale |
| 🔵 LOW | Hygiene issue — no immediate failure risk, but degrades maintainability |

---

## PART I — CRITICAL FINDINGS (🔴)

These must be addressed before any production deployment or library version freeze.

---

### FINDING 01 — TS: Broken Import Paths in index.ts

**Severity:** 🔴 CRITICAL
**Runtime:** TS
**File:** `index.ts`

The root-level `index.ts` exports Gaming family modules using bare relative paths:

```typescript
export * from "./bejson_assets";
export * from "./bejson_engine";
export * from "./bejson_events";
export * from "./bejson_grid";
export * from "./bejson_input";
export * from "./bejson_physics";
export * from "./bejson_renderer";
```

The actual files reside at `Gaming/bejson_assets.ts`, `Gaming/bejson_engine.ts`, etc.
`index.ts` is at the package root. These paths are wrong — they reference files that do not
exist at `./bejson_*` relative to the index. Unless a `tsconfig.json` path alias maps these
(none is visible in the chunked library), this is a **build-breaking import error** that
will cause `tsc` to fail on every compile and any downstream consumer using this package
to receive a module-not-found error at runtime.

**Required Action:**

Correct all Gaming exports in `index.ts` to use the family subdirectory prefix:

```typescript
export * from "./Gaming/bejson_assets";
export * from "./Gaming/bejson_engine";
// etc.
```

Alternatively, verify whether a `tsconfig.json` `paths` alias exists. If it does, that file
must be included in future chunk deliveries so the aliasing is auditable.

**Version bump required:** `index.ts` → 2.0.2, `Lib_TS` project container → 2.0.2

---

### FINDING 02 — PY: Duplicate Cognition Library — Active Version Skew

**Severity:** 🔴 CRITICAL
**Runtime:** PY
**Files:** `AI/lib_bejson_cognition.py` (v2.0.1) vs `Cognition/lib_bejson_cognition.py` (v2.1.0)

Two copies of `lib_bejson_cognition.py` exist at different paths with different version
numbers and meaningfully different content. The `AI/` copy is v2.0.1 and lacks the
"Security Logging" and enhanced sandbox blocking remediated in the `Cognition/` v2.1.0 copy.

This creates a live split-brain hazard: any script that resolves the library via
`AI/lib_bejson_cognition.py` (by hardcoded path, by directory scan, or by incorrect sibling
resolution) gets the older, less secure version with weaker sandbox enforcement. The
`E_COGNITION_SANDBOX_VIOLATION` code (403) and the diagnostic logging are absent from the
AI/ copy.

The v2.0.1 copy in `AI/` was likely the original placement before the Cognition family
was created as a formal subdirectory. It is now an orphan that should not exist.

**Required Action:**

1. Delete `AI/lib_bejson_cognition.py` (v2.0.1).
2. Any imports currently resolving from the `AI/` path must be updated to `Cognition/`.
3. Audit all scripts that `import lib_bejson_cognition` to confirm they resolve to the
   `Cognition/` directory.
4. Bump `Cognition/lib_bejson_cognition.py` → 2.1.1 to mark the deduplication event.

**Risk if unresolved:** Security sandbox bypass — a caller importing from `AI/` gets a
version that does not block sandboxed operations or log violations.

---

### FINDING 03 — PY/Cognition: Dangling Code After Comment — Syntax Error

**Severity:** 🔴 CRITICAL
**Runtime:** PY
**File:** `Cognition/lib_bejson_cognition.py`

The file contains the comment `# ... rest of the cognition logic remains unchanged`
followed by actual production code blocks that appear without a containing function
definition. The code reads:

```python
# ... rest of the cognition logic remains unchanged
                metadata = instr.get("tool_metadata", {})
                filename = metadata.get("filename")
                code = instr.get("code")
```

This is module-level code with indentation that implies it belongs inside a function or
loop body — but no enclosing function is declared. This is either a **SyntaxError** (Python
will reject this file on import) or, if indentation is coincidentally valid, it is dead
unreachable logic. Either way, the file is broken.

The block continues through tool forging, registry writing, agent spawning, and
`bejson_cognition_upsert` calls — this is the core patch-application engine and it has
been left in an unparseable state.

**Required Action:**

1. Restore the complete source of `Cognition/lib_bejson_cognition.py`. The chunk appears
   to have been truncated or improperly merged during the last edit. Retrieve the full file
   from the original source.
2. Once restored, validate with `python3 -m py_compile Cognition/lib_bejson_cognition.py`
   before rechunking.
3. Do not ship a chunk of a library file that has not been syntax-checked.

---

### FINDING 04 — PY: Lock Mechanism Diverges from Policy — No PID Verification

**Severity:** 🔴 CRITICAL
**Runtime:** PY
**File:** `Core/lib_bejson_core.py` — `bejson_core_acquire_lock()`

The current PY lock implementation uses a flat `.lock` file and a **stale age timeout**
(default 60 seconds) to detect orphaned locks:

```python
mtime = os.path.getmtime(lock_path)
if (time.time() - mtime) > stale_age:
    os.unlink(lock_path)
```

Policy v1.4 (Sections 29, 48, 50) mandates **PID-monitored locks** that verify whether
the owning process is still alive via `os.kill(pid, 0)` before breaking the lock. The
stale-age approach is explicitly the *vulnerability* the remediated architecture was
designed to replace — a 60-second stale window means any crash within the window leaves
the registry blocked for up to a minute, and any crash just after 60s can race with a
new acquisition.

Additionally, the lock uses a `.lock` flat file rather than a `.lockdir` atomic directory
creation. A `.lockdir` approach (via `os.mkdir`) gives kernel-level atomicity without the
`O_EXCL` workaround. The `.lock` + `O_EXCL` pattern is valid but the PID verification
step is missing.

The PY `ResilientPIDLock` class defined in the policy documentation (Section 48) has
not been implemented in the actual library.

**Required Action:**

Replace `bejson_core_acquire_lock` / `bejson_core_release_lock` with `ResilientPIDLock`
from Policy Section 48 verbatim. Key differences:

- Use `.lockdir` (atomic `os.mkdir`) not `.lock` + `O_EXCL`
- Write `{"pid": os.getpid(), "timestamp": int(time.time())}` to `lock_meta.json` inside
  the lockdir on acquisition
- On contention, read stored PID and call `os.kill(stored_pid, 0)` — if it throws
  `ProcessLookupError`, the owner is dead; reclaim the lock
- On timeout, raise/return `E_MFDB_CORE_LOCK_FAILED` (code 53)

**Version bump required:** `Core/lib_bejson_core.py` → 2.0.2

---

### FINDING 05 — PY: `from lib_bejson_errors import *` — Wildcard Namespace Pollution

**Severity:** 🔴 CRITICAL (namespace correctness) / 🟠 HIGH (immediate risk)
**Runtime:** PY
**Files:**
- `AI/lib_bejson_cognition.py`
- `Core/lib_mfdb_core.py`
- `Core/lib_bejson_validator.py`
- `Core/lib_mfdb_validator.py`
- `Cognition/lib_bejson_cognition.py`

Five files use `from lib_bejson_errors import *`. This pattern:

1. Imports all 60+ error constants into every module's global namespace simultaneously
2. Makes it impossible for static analyzers, linters, and IDEs to determine where a
   constant originated
3. Will silently break if `lib_bejson_errors.py` adds a new constant with the same name
   as any local variable in the importing module
4. Makes future error code renaming a cascading search-and-hope operation

Note that `lib_bejson_validator.py` partially mitigates this with an `except ImportError`
block that re-declares fallback values — but this means you now have *two* sources of
truth for those constants and the fallback block will drift from the canonical registry.

**Required Action:**

Replace all wildcard imports with explicit named imports. Example for
`lib_bejson_validator.py`:

```python
from lib_bejson_errors import (
    E_INVALID_JSON,
    E_MISSING_MANDATORY_KEY,
    E_INVALID_FORMAT,
    E_INVALID_VERSION,
    E_INVALID_RECORDS_TYPE,
    E_INVALID_FIELDS,
    E_INVALID_VALUES,
    E_TYPE_MISMATCH,
    E_RECORD_LENGTH_MISMATCH,
    E_RESERVED_KEY_COLLISION,
    E_INVALID_RECORD_TYPE_PARENT,
    E_NULL_VIOLATION,
    E_FILE_NOT_FOUND,
    E_PERMISSION_DENIED,
)
```

Remove the fallback re-declaration blocks in validator files. The fallback
`except ImportError` block is acceptable at the module level but should only define
the minimum codes that module actually uses, not a full mirror.

---

## PART II — HIGH SEVERITY FINDINGS (🟠)

These are architectural violations and active policy breaches that do not immediately
crash the system but are accruing technical debt that will cause real failures.

---

### FINDING 06 — SH: `set -o nounset` Persists in Library Files — Partial Fix

**Status:** ✅ RESOLVED (2026-06-02) - Removed `set -o nounset` from `parse.sh`, `mfdb_core.sh`, and `mfdb_validator.sh`. Versions bumped to 2.0.2.

**Severity:** 🟠 HIGH
**Runtime:** SH
**Files with violation:**
- `Core/lib_bejson_parse.sh`
- `Core/lib_mfdb_core.sh`
- `Core/lib_mfdb_validator.sh`

`lib_bejson_core.sh` and `lib_bejson_validator.sh` correctly document the SH3 fix in
their changelogs and do **not** set `nounset`. However, three other Core SH libraries
still use `set -o nounset` at the top level. When any of these files are `source`d into
a host script, `nounset` is applied globally to that host script's shell session. Any
pre-existing unset variable in the host script then throws a fatal error — a side effect
entirely invisible to the library consumer.

This is a real silent corruption vector on Android/Termux environments where many
scripts are sourced in sequence inside a shared shell session.

**Required Action:**

Remove `set -o nounset` from the top level of all three files. `set -o pipefail` is
acceptable and should be retained. The SH3 fix must be applied uniformly across the
entire SH Core family, not just the two files where it was first caught.

**Version bumps required:** All three files → 2.0.2

---

### FINDING 07 — SH: Error Code Registry is Incomplete — Missing MFDB Core Codes

**Status:** ✅ RESOLVED (2026-06-02) - Added missing codes 54-56 and 70-71 to `lib_bejson_errors.sh`.

**Severity:** 🟠 HIGH
**Runtime:** SH
**File:** `Core/lib_bejson_errors.sh`

The SH error registry defines only four MFDB Core error codes (50–53):

```bash
E_MFDB_CORE_LOAD_FAILED   = 50
E_MFDB_CORE_WRITE_FAILED  = 51
E_MFDB_CORE_ENTITY_MISSING = 52
E_MFDB_CORE_LOCK_FAILED   = 53
```

The PY and JS registries define additional codes through 56 and 70–71:

```
E_MFDB_CORE_MANIFEST_NOT_FOUND = 50  (PY name diverges from SH name at same code)
E_MFDB_CORE_ENTITY_NOT_FOUND   = 51
E_MFDB_CORE_WRITE_FAILED       = 52
E_MFDB_CORE_CREATE_FAILED      = 53
E_MFDB_CORE_INVALID_OPERATION  = 54
E_MFDB_CORE_INDEX_OUT_OF_BOUNDS = 55
E_MFDB_CORE_JOIN_FAILED        = 56
E_MFDB_CORE_ARCHIVE_ERROR      = 70
E_MFDB_CORE_MOUNT_CONFLICT     = 71
```

**Name collision at code 50:** PY calls it `E_MFDB_CORE_MANIFEST_NOT_FOUND` while SH
calls it `E_MFDB_CORE_LOAD_FAILED`. These are different concepts mapped to the same
integer. Code 53 is `E_MFDB_CORE_CREATE_FAILED` in PY but `E_MFDB_CORE_LOCK_FAILED`
in SH — a direct collision between two different error meanings.

Additionally, `lib_mfdb_core.sh` uses `E_MFDB_CORE_ARCHIVE_ERROR` (70) and
`E_MFDB_CORE_MOUNT_CONFLICT` (71) via `return $E_MFDB_CORE_ARCHIVE_ERROR` — but these
constants are not defined in `lib_bejson_errors.sh`. They are defined locally inside
`lib_mfdb_core.sh` as separate `readonly` declarations. This is the exact code fragmentation
pattern `lib_bejson_errors.sh` was created to eliminate.

**Required Action:**

1. Resolve the name collision at codes 50–53 between PY and SH. Pick one canonical name
   per code across all runtimes and update both registries. Suggested resolution: follow
   the PY naming (it is more descriptive) and add SH legacy aliases.
2. Add missing codes 54–56, 70–71 to `lib_bejson_errors.sh`.
3. Remove the local `readonly` declarations for 70/71 from `lib_mfdb_core.sh` — have it
   source `lib_bejson_errors.sh` instead (it already sources `lib_bejson_core.sh`, chain
   the dependency).

**Version bump required:** `lib_bejson_errors.sh` → 1.1.0

---

### FINDING 08 — SH: E_VAL_BAD_CREATOR Code 5 Collision — Known, Unresolved

**Severity:** 🟠 HIGH
**Runtime:** SH, but impacts cross-runtime error interpretation
**File:** `Core/lib_bejson_errors.sh`

The SH errors lib documents this explicitly as "see X2" in a comment:

```bash
[[ -v E_VAL_BAD_CREATOR ]] || readonly E_VAL_BAD_CREATOR=5  # SH had 5; JS/PY use 5 for INVALID_RECORDS_TYPE
```

Code 5 is `E_INVALID_RECORDS_TYPE` in PY and JS. Code 5 is `E_VAL_BAD_CREATOR` (wrong
Format_Creator) in legacy SH. These are different validation errors mapped to the same
integer. Any cross-runtime log correlation (a Bash script running a Python validator and
comparing exit codes) will misidentify which error occurred.

The legacy alias approach kicks the problem forward. It must be resolved.

**Required Action:**

Assign a new code to `E_VAL_BAD_CREATOR` outside the already-occupied range. The
suggested code is `16` (the first available slot after the current 1–15 BEJSON Validator
range). Update all SH libraries that currently use code 5 to mean "bad creator" to
use 16. Update `lib_bejson_validator.sh` to check `Format_Creator` and return 16 on
failure. Document the migration in the SH errors lib changelog.

---

### FINDING 09 — PY/JS: `lib_bejson_gemini.py` Uses `requests` — SDK Policy Violation

**Severity:** 🟠 HIGH
**Runtime:** PY
**File:** `AI/lib_bejson_gemini.py`

The Gemini integration library imports `requests` for HTTP operations:

```python
import requests
```

Policy Section 10.1 mandates exclusive use of the `google-genai` SDK:

```
Must use google-genai SDK exclusively.
Import: from google import genai
⚠ google-generativeai (Generative AI) is deprecated — never use it.
```

Direct use of `requests` to hit Gemini endpoints bypasses the SDK's retry logic,
authentication handling, streaming support, and model-version validation. It also
means any SDK-level changes to Gemini's API (model IDs, endpoint structure, auth
token format) must be manually tracked and patched in the library, whereas the SDK
handles this transparently.

**Required Action:**

Refactor `lib_bejson_gemini.py` to use `from google import genai` exclusively. The
`GeminiKeyRegistry` class should pass API keys to the `genai.Client` constructor.
Model selection, request construction, and streaming should use the SDK's native
interfaces. The `requests` import must be removed.

---

### FINDING 10 — PY/SH/JS: Hardcoded Paths in chunker_config.json

**Severity:** 🟠 HIGH
**Runtime:** All four
**File:** `chunker_config.json` (exists in each lib root)

All four `chunker_config.json` files contain a hardcoded `output_base` path:

```json
"output_base": "/storage/emulated/0/Admin/resources/chunks"
```

This is an absolute path to Android internal storage. On any non-Android environment
(desktop Linux, CI pipeline, Termux on a different device with a different user), this
path is wrong and the chunker will either fail or silently write to the wrong location.
The chunker config is supposed to be the component that makes the toolchain portable —
hardcoding Android paths inside it defeats that purpose entirely.

Similarly, `lib_be_core.sh` defaults `SC_ROOT` to:

```bash
/storage/emulated/0/Brain-Container/BEJSON_Core
```

This is only correct on the primary Android device. The fallback should resolve through
the environment file system, not hardcode a device-specific path.

**Required Action:**

1. Replace the `output_base` field in all `chunker_config.json` files with a placeholder
   token (e.g., `"{ADMIN_ROOT}/resources/chunks"`) that `lib_bejson_env.py` / the
   equivalent env resolver can expand at runtime.
2. In `lib_be_core.sh`, replace the hardcoded `SC_ROOT` fallback with a read from
   `env_file.sh` using the standard `${BASH_SOURCE[0]}` sibling resolution. Only fall
   back to a literal path if the env file is also missing (and in that case, emit a
   warning, not a silent default).

---

### FINDING 11 — PY: Cognition `except ImportError: pass` — Silent Security Failure

**Severity:** 🟠 HIGH
**Runtime:** PY
**File:** `Cognition/lib_bejson_cognition.py`

The import block uses a bare `pass` on `ImportError`:

```python
try:
    from lib_bejson_core import bejson_core_atomic_write, bejson_core_load_file
    from lib_mfdb_core import mfdb_core_resolve_path
    from lib_bejson_errors import *
except ImportError:
    pass
```

This library contains the sandbox enforcement engine for autonomous agents. If
`lib_bejson_core` fails to import (missing sibling, wrong path), the sandbox check
function `bejson_cognition_check_sandbox()` silently falls through without any of its
enforcement machinery. All operations that were meant to be blocked will execute
unblocked. The failure is invisible — no log line, no crash, no alert.

**Required Action:**

Replace `pass` with a loud failure that stops the process:

```python
except ImportError as e:
    import logging
    logging.critical(f"[COGNITION] FATAL: Core security dependencies unreachable: {e}")
    raise SystemExit(1)
```

The sandbox is a security boundary. It must fail hard and loud, not soft and silent.

---

## PART III — MEDIUM SEVERITY FINDINGS (🟡)

These are patterns that are fragile, incomplete, or diverging from the spec, but do
not represent active crashes or security holes today.

---

### FINDING 12 — Cross-Runtime: lib_bejson_core.ts at 2.0.1 While JS Core is at 2.0.2

**Severity:** 🟡 MEDIUM
**Runtime:** PY, TS
**Context:** Core version parity

The JS Core family was bumped to 2.0.2 with documented fixes (SH2 in SH, SH3 in SH/JS,
JS1 in JS, H1–H7 in HTML). The TS Core is still at 2.0.1, and PY Core is at 2.0.1.
These families are intended to be functionally equivalent in their core operations.

The TS `lib_bejson_core.ts` changelog notes "Removed regex parser crutch and optimized
cryptographic bottlenecks" — but the version is 2.0.1, not 2.0.2. Either those fixes
were incorporated during the initial 2.0.1 release (and TS's v2.0.2 changelog should
document them) or they weren't fully ported.

The field map implementation in TS (`lib_bejson_field_map.ts`) is at version **3.0.0**
while every other TS file is at 2.0.1. A single file being a full major version ahead
of everything else in the same library is a versioning inconsistency that will cause
confusion about what is stable and what is experimental.

**Required Action:**

1. Align TS Core files to 2.0.2 if the JS 2.0.2 fixes have been ported; document what
   was ported in the TS changelog.
2. Pull back `lib_bejson_field_map.ts` to 2.1.0 to signal it is ahead of baseline
   without implying a completely incompatible major revision. Reserve a true 3.0.0 bump
   for when the entire TS library exits the field-map migration.

---

### FINDING 13 — SH: lib_bejson_parse.sh Uses `awk`/`sed` for JSON Extraction

**Severity:** 🟡 MEDIUM
**Runtime:** SH
**File:** `Core/lib_bejson_parse.sh`

The `bejson_parse_json()` function attempts to extract JSON from potentially-dirty strings
(e.g., LLM responses with markdown fences) using `awk` and `sed`:

```bash
clean=$(echo "$text" | awk 'BEGIN { f=0 } /```json/ { f=1; next } /```/ && f { exit } f { print }')
if [[ -z "$clean" ]] || ! echo "$clean" | jq '.' >/dev/null 2>&1; then
    clean=$(echo "$text" | tr '\n' '\f' | sed 's/^[^{]*//; s/}[^}]*$/}/' | tr '\f' '\n')
fi
```

This is fragile in multiple dimensions:
- If JSON content contains a backtick sequence it breaks the awk fence detection
- The `sed` fallback trims from the first `{` to the last `}` — if the JSON contains
  nested `}` followed by trailing non-JSON characters (e.g., a reasoning block), it
  produces malformed JSON
- The `tr '\n' '\f'` pipe mangles multi-line JSON strings that legitimately contain `\f`

The Policy Section 5.1 (BEJSON Best Practices) notes "NO REGEX" — this SH function is
the equivalent of the regex problem that was already remediated in other runtimes.

**Required Action:**

Implement a jq-only extraction path. If the input may contain Markdown fences, strip
them with a simple string-split approach before passing to `jq`, rather than line-scanning
with `awk`. Use `jq -e '.' <<< "$text"` for the final validation. Remove the `tr`/`sed`
pipeline entirely.

---

### FINDING 14 — TS: lib_bejson_list_validator.ts is a Stub

**Severity:** 🟡 MEDIUM
**Runtime:** TS
**File:** `Core/lib_bejson_list_validator.ts`

The TS list validator is 14 lines total and returns `{ valid: true, errors: [] }` after
basic structure checks, with a comment "Hierarchy logic matches JS implementation" — but
no hierarchy logic is actually implemented:

```typescript
// Hierarchy logic matches JS implementation
return { valid: true, errors: [] };
```

The JS implementation (`Core/lib_bejson_list_validator.js`) performs full cycle-detection,
root node validation, and parent reference resolution. The TS version does none of this.
Any caller using the TS validator for hierarchical list validation will receive a false
positive on malformed documents.

**Required Action:**

Port the full hierarchy validation logic from `lib_bejson_list_validator.js` to the TS
implementation. The JS version's core loop and parentRefs map are directly translatable
to TypeScript with proper typing. Do not ship a validator that returns true for documents
it has not actually validated.

---

### FINDING 15 — PY: Project Container Version (2.0.1) Disconnected from File Reality

**Severity:** 🟡 MEDIUM
**Runtime:** PY (most severe), also JS, TS, SH
**File:** `Values[0]` (ProjectMeta record) in all four chunks

All four chunk files declare project version `2.0.1` in the `ProjectMeta` record. But the
actual file versions inside the chunks span a wide range:

| File | Version |
| :--- | :--- |
| `lib_bejson_field_map.ts` | 3.0.0 |
| `HTML/` family (all 25 files) | 3.0.x |
| `lib_bejson_utility.py` / `.js` | 2.2.1 |
| `lib_bejson_schema.py` | 2.1.1 |
| `lib_bejson_gemini.py` | 2.1.0 |
| `lib_bejson_errors.sh` | 1.0.0 |

The container version `2.0.1` is now effectively meaningless. When a consumer queries the
chunk to determine what version of the ecosystem they have, they get a stale number that
doesn't reflect that the HTML family is at 3.x and some files are at 1.0.0.

**Required Action:**

Define a versioning policy for the container chunk:
- The `ProjectMeta.version` field should reflect the **highest** individual file version
  in the chunk, or
- Use a separate `library_ecosystem_version` field (custom header in a 104a config) that
  is explicitly and independently maintained.

The current approach will lead to version-based dependency resolution failures in any
tooling that uses the chunk metadata to determine compatibility.

---

### FINDING 16 — JS: window.Switch Global Namespace Collision Risk

**Severity:** 🟡 MEDIUM
**Runtime:** JS
**File:** `Core/lib_bejson_bejson.js`

The FIX JS1 change initializes `window.Switch` as a global namespace:

```javascript
window.Switch = window.Switch || {};  // FIX JS1: declare before use
```

`Switch` is an extremely common and generic identifier in JavaScript. Any third-party
script, browser extension, or other library component that also uses `window.Switch` for
its own purposes will silently corrupt or be corrupted by this library. The browser global
namespace is shared — generic identifiers are reserved for their normal meanings.

**Required Action:**

Rename the namespace. Use a prefixed, unambiguous identifier:

```javascript
window.BEJSON_Switch = window.BEJSON_Switch || {};
```

Update all internal references. This is a find-and-replace across a single file.

---

### FINDING 17 — Cross-Runtime: Encryption Error Codes Missing in JS/TS/SH

**Severity:** 🟡 MEDIUM
**Runtime:** JS, TS, SH
**Reference:** `lib_bejson_errors.py` codes 28–29

PY defines:
```python
E_CORE_ENCRYPTION_FAILED = 28
E_CORE_DECRYPTION_FAILED = 29
```

The JS `lib_bejson_errors.js` and SH `lib_bejson_errors.sh` registries do not define
codes 28 and 29. The TS types file has no equivalent. If any JS/TS/SH function performs
encryption or decryption and needs to report a standardized error, it currently has no
canonical code to use — so it either returns a generic code (incorrect) or a raw
non-standard number (also incorrect).

**Required Action:**

Add `E_CORE_ENCRYPTION_FAILED = 28` and `E_CORE_DECRYPTION_FAILED = 29` to `lib_bejson_errors.js`,
`lib_bejson_errors.sh`, and the TS error code types. Verify no existing code in any runtime
already uses 28 or 29 for a different purpose before adding.

---

### FINDING 18 — SH: No General-Purpose PID Mutex Library

**Severity:** 🟡 MEDIUM
**Runtime:** SH
**Context:** Policy Sections 29, 47, 50

The SH archive mount (`mfdb_archive_mount`) correctly implements PID-based lock checking:

```bash
old_pid=$(jq -r '.pid' "$lock_file")
if kill -0 "$old_pid" 2>/dev/null; then
    echo "ERROR: Workspace $target_dir is locked by active PID $old_pid"
```

This is good. But this PID verification exists **only** for archive mounts — it is
not available as a reusable locking primitive for general entity writes. The
`resilient_lock_acquire()` function from Policy Section 47 has been drafted but is not
present in the delivered `lib_mfdb_core.sh` or `lib_bejson_core.sh`. Any script that
needs to lock a registry entity file for writing has no access to a PID-aware mutex
and must either reinvent it or go without.

**Required Action:**

Extract the PID lock logic from `mfdb_archive_mount` into a standalone reusable
function (`resilient_lock_acquire` / `resilient_lock_release`) in `lib_bejson_core.sh`,
exactly as specified in Policy Section 47. Then refactor `mfdb_archive_mount` to call
the shared function instead of reimplementing it inline.

---

### FINDING 19 — TS: Missing `lib_bejson_errors.ts` — Error Codes Implicit

**Severity:** 🟡 MEDIUM
**Runtime:** TS
**Context:** Cross-runtime error code parity

The TS library has `lib_bejson_types.ts` which defines typed interfaces and unions, but
there is no standalone `lib_bejson_errors.ts` equivalent to `lib_bejson_errors.js` and
`lib_bejson_errors.py`. The BEJSON error codes in TS are embedded inside
`lib_bejson_types.ts` as part of `BEJSON_VALIDATION_CODES` and `BEJSON_CORE_CODES` enums.

While this is architecturally acceptable for a typed language, the integer values must
still match the canonical registry exactly. There is no dedicated file that enforces this
parity in isolation, making it easy for a TS-only change to drift from the cross-runtime
canonical codes without anyone noticing.

**Required Action:**

Either: add a comment block in `lib_bejson_types.ts` cross-referencing the JS/PY error
registry codes and confirming parity, or extract the numeric codes into a dedicated
`lib_bejson_errors.ts` that can be diffed directly against the JS and PY registries.

---

## PART IV — LOW SEVERITY FINDINGS (🔵)

These are hygiene issues and future-risk patterns. They should be addressed during
normal maintenance cycles, not as emergency fixes.

---

### FINDING 20 — PY: CMS `lib_cms_config.py` Mutates Doc In-Place Before Atomic Write

**Severity:** 🔵 LOW
**Runtime:** PY
**File:** `CMS/lib_cms_config.py`

`cms_config_set()` modifies `records` (which is `doc["Values"]`) via index assignment
before calling `bejson_core_atomic_write`. If the write fails, the in-memory `doc` is
now in a mutated state — any subsequent call to `bejson_core_load_file` will return the
old on-disk version, but the in-memory object passed around in a long-running process
has the partially mutated state. This is a small memory consistency risk.

**Suggested fix:** Deep-copy the doc before mutation, and only replace the original
reference on successful write.

---

### FINDING 21 — JS: `lib_bejson_parse.js` Imports from `window.BEJSON` Without Fallback Guard

**Severity:** 🔵 LOW
**Runtime:** JS
**File:** `Core/lib_bejson_parse.js`

The destructuring import:
```javascript
const { BEJSONCoreError, bejson_core_is_valid, ... } = 
    (typeof require !== 'undefined') ? require('./lib_bejson_core.js') : (window.BEJSON || {});
```

If `window.BEJSON` is defined but does not yet contain `bejson_core_is_valid` (e.g.,
if the script load order is wrong and `lib_bejson_parse.js` loads before
`lib_bejson_core.js`), the destructured variables are silently `undefined`. The first
call to any of these functions will throw a `TypeError: not a function`, with no useful
diagnostic of what went wrong.

**Suggested fix:** Add a post-import guard that verifies at least one critical function
was successfully imported, and throws a descriptive error if not.

---

### FINDING 22 — SH: `lib_be_deps.sh` Dependency List Missing `python3` and `git`

**Severity:** 🔵 LOW
**Runtime:** SH
**File:** `System/lib_be_deps.sh`

The dependency list in `install_dependencies()` checks only `rsync`, `jq`, `figlet`,
and `toilet`. `python3` and `git` are implicit dependencies of the broader BEJSON
ecosystem but are not verified. On a clean Termux install, these may not be present.

**Suggested fix:** Add `python3` and `git` to the required dependency list. Consider
adding `unzip` (used by `mfdb_archive_mount`) and verifying the Python `google-genai`
package is installed.

---

### FINDING 23 — All Libs: GEMINI.md Field-Map Migration Has No Completion Tracker

**Severity:** 🔵 LOW
**Runtime:** All
**File:** `GEMINI.md` (present in all four libs)

The GEMINI.md files instruct: "you may integrate FIELD MAP INDEXING options going
forward slowly into the libraries but you are not to break the array based indexing yet."
This is an in-progress migration with no formal tracker, no completion criteria, and no
timeline. The migration exists in parallel across four runtimes at different depths:
- TS: dedicated `lib_bejson_field_map.ts` at v3.0.0
- JS: `bejson_core_get_field_map` exists in core
- PY: present as a cache in core (implementation partially truncated in chunk)
- SH: no field map support at all

Without a tracker, this migration will stall indefinitely, with some runtimes fully
migrated and others still on array-index fallbacks. The "leave array indexing as fallback"
instruction is appropriate for now, but a deadline or milestone for completing the migration
must be set.

**Suggested fix:** Create a `migration_tracker.104a.bejson` file in the MFDB Admin system
that logs each library + runtime's field map status (`pending`, `in_progress`, `complete`)
and the target completion version. Reference it in GEMINI.md.

---

## PART V — PRIORITIZED ACTION PLAN

Listed in recommended execution order. Complete each step before moving to the next.

### Tier 1 — Fix Before Anything Else (This Session)

These are live breakage items. Do not rechunk or redistribute these libraries until
all Tier 1 items are resolved.

| # | Action | Runtime | Files |
| :--- | :--- | :--- | :--- |
| 1 | Fix broken Gaming import paths in `index.ts` | TS | `index.ts` |
| 2 | Delete `AI/lib_bejson_cognition.py` (v2.0.1 orphan) | PY | `AI/lib_bejson_cognition.py` |
| 3 | Restore full source of `Cognition/lib_bejson_cognition.py` (dangling code) | PY | `Cognition/lib_bejson_cognition.py` |
| 4 | Replace all `from lib_bejson_errors import *` with explicit imports | PY | 5 files |

### Tier 2 — Security & Policy Compliance (Next Session)

| # | Action | Runtime | Files |
| :--- | :--- | :--- | :--- |
| 5 | Upgrade PY lock to PID-verified ResilientPIDLock | PY | `Core/lib_bejson_core.py` |
| 6 | Replace `requests` with `google-genai` SDK in Gemini lib | PY | `AI/lib_bejson_gemini.py` |
| 7 | Fix Cognition `except ImportError: pass` → `SystemExit(1)` | PY | `Cognition/lib_bejson_cognition.py` |
| 8 | Add general-purpose `resilient_lock_acquire` to SH core | SH | `Core/lib_bejson_core.sh` |

### Tier 3 — Cross-Runtime Consistency (Hardening Sprint)

| # | Action | Runtime | Files |
| :--- | :--- | :--- | :--- |
| 9 | Remove `set -o nounset` from remaining 3 SH library files | SH | `parse.sh`, `mfdb_core.sh`, `mfdb_validator.sh` |
| 10 | Resolve E_VAL_BAD_CREATOR / code-5 collision — assign code 16 | SH | `lib_bejson_errors.sh` |
| 11 | Complete MFDB Core error codes 54–56, 70–71 in SH registry | SH | `lib_bejson_errors.sh` |
| 12 | Fix local `readonly` declarations in `lib_mfdb_core.sh` | SH | `Core/lib_mfdb_core.sh` |
| 13 | Add encryption error codes 28–29 to JS, TS, SH registries | JS/TS/SH | errors files |
| 14 | Rename `window.Switch` → `window.BEJSON_Switch` | JS | `lib_bejson_bejson.js` |

### Tier 4 — Quality & Architecture (Ongoing)

| # | Action | Runtime | Files |
| :--- | :--- | :--- | :--- |
| 15 | Port full hierarchy validation logic to TS list validator | TS | `lib_bejson_list_validator.ts` |
| 16 | Replace `awk`/`sed` pipeline in SH parse.sh with jq-only | SH | `Core/lib_bejson_parse.sh` |
| 17 | Replace hardcoded `output_base` paths in all chunker configs | All | `chunker_config.json` (×4) |
| 18 | Fix `lib_be_core.sh` hardcoded SC_ROOT fallback | SH | `System/lib_be_core.sh` |
| 19 | Align TS version numbers — field_map.ts back to 2.1.0 | TS | `lib_bejson_field_map.ts` |
| 20 | Define container ProjectMeta version policy | All | Chunker tooling |
| 21 | Expand `lib_be_deps.sh` dependency list | SH | `System/lib_be_deps.sh` |
| 22 | Fix in-place mutation before atomic write in CMS config | PY | `CMS/lib_cms_config.py` |
| 23 | Create `migration_tracker.104a.bejson` for field map status | All | MFDB Admin system |

---

## PART VI — WHAT IS WORKING WELL

This section calls out the patterns that are solid and should be preserved as templates
for the fixes described above.

**Atomic writes (PY, SH):** Both `bejson_core_atomic_write` in Python and the archive
commit in Bash use temp-file-then-rename on the same filesystem with explicit `fsync`/`sync`.
This matches the Policy Section 28 hardened standard exactly.

**SH guard pattern for error codes:** The `[[ -v VAR ]] || readonly VAR=N` pattern in all
SH error definitions is correct and allows safe re-sourcing without re-definition errors.
This should be the template for all future SH constant declarations.

**JS H1–H7 table renderer fixes:** The `lib_html3_table.js` changelog is thorough and
the fixes are correctly applied — field map cache used at render time, XSS injection
vectors closed, `activeFields` length guard added, `data-field` attribute usage for
injecting field names instead of inline handler interpolation. This is production-quality
remediation work.

**JS1 fix in lib_bejson_bejson.js:** The conditional export pattern that avoids mixing
ES module syntax with browser-global assignment is correct and consistent with how other
JS libraries in the family export.

**SH3 fix in lib_bejson_core.sh and lib_bejson_validator.sh:** These two files correctly
removed `set -o nounset` and documented it. The pattern needs to be replicated to the
three remaining files.

**PY lib_bejson_env.py resolve_path():** The path resolver correctly handles
`{SC_ROOT}`, `{INTERNAL_STORAGE}`, `{HOME}`, legacy Android absolute paths,
`os.path.expanduser`, and `os.path.expandvars`. Sorting mappings by key length descending
to prevent partial-match replacement is a correct and subtle implementation detail.

**SH mfdb_archive_mount PID check:** The archive session lock that reads a stored PID
and calls `kill -0 "$old_pid"` before deciding whether to honor a conflicting lock is
exactly the right approach and should be generalized.

---

## APPENDIX A — FINDINGS CROSS-REFERENCE TABLE

| # | Severity | Runtime | Category | Finding Summary |
| :---: | :---: | :--- | :--- | :--- |
| 01 | 🔴 | TS | Correctness | Broken Gaming import paths in index.ts |
| 02 | 🔴 | PY | Security | Duplicate cognition lib — version skew |
| 03 | 🔴 | PY | Correctness | Dangling/orphaned code — syntax error |
| 04 | 🔴 | PY | Security | Lock uses stale-age, not PID verification |
| 05 | 🔴 | PY | Architecture | Wildcard `import *` from error registry |
| 06 | 🟠 | SH | Portability | `set -o nounset` in 3 library files |
| 07 | 🟠 | SH | Consistency | Error registry incomplete — codes 54–56, 70–71 missing |
| 08 | 🟠 | SH | Consistency | E_VAL_BAD_CREATOR / code-5 collision unresolved |
| 09 | 🟠 | PY | Policy | `requests` used instead of `google-genai` SDK |
| 10 | 🟠 | All | Portability | Hardcoded paths in chunker_config.json |
| 11 | 🟠 | PY | Security | Silent ImportError in sandbox enforcement library |
| 12 | 🟡 | PY/TS | Versioning | Core version divergence and field_map major-version spike |
| 13 | 🟡 | SH | Correctness | `awk`/`sed` JSON extraction fragile |
| 14 | 🟡 | TS | Correctness | List validator is a non-validating stub |
| 15 | 🟡 | All | Versioning | Project container version disconnected from file reality |
| 16 | 🟡 | JS | Safety | `window.Switch` namespace collision risk |
| 17 | 🟡 | JS/TS/SH | Consistency | Encryption error codes 28–29 absent |
| 18 | 🟡 | SH | Architecture | No reusable PID mutex primitive in SH |
| 19 | 🟡 | TS | Consistency | No standalone `lib_bejson_errors.ts` for parity |
| 20 | 🔵 | PY | Correctness | In-place mutation before atomic write in CMS config |
| 21 | 🔵 | JS | Safety | Import destructure has no post-load guard |
| 22 | 🔵 | SH | Completeness | `lib_be_deps.sh` missing `python3`, `git`, `unzip` |
| 23 | 🔵 | All | Process | Field-map migration has no tracker or completion criteria |

---

## APPENDIX B — FILE COUNT AND COVERAGE BY RUNTIME

| Family | PY Files | JS Files | TS Files | SH Files |
| :--- | :---: | :---: | :---: | :---: |
| Core | 17 | 12 | 8 | 8 |
| HTML | 25 | 1 | — | — |
| Gaming | 5 | 8 | 8 | — |
| AI | 10 | — | — | — |
| CMS | 7 | — | — | — |
| Cognition | 1 | — | — | — |
| System | 6 | — | — | 2 |
| Utility | 1 | 1 | 1 | — |
| External | — | 1 | — | — |
| **Total** | **74** | **25** | **19** | **12** |

---

*Report v1.0 — Elton Boehnen — boehnenelton2024@gmail.com — boehnenelton2024.pages.dev — github.com/boehnenelton*
elton*
elton*
on*
 github.com/boehnenelton*
