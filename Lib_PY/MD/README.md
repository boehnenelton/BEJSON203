# lib_bejson_markdown — Lib_MD v1.0.0

**Author:** Elton Boehnen  
**Contact:** eltonboehnen@gmail.com · boehnenelton2024.pages.dev · [github.com/boehnenelton](https://github.com/boehnenelton)  
**RELATIONAL_ID:** md-lib-readme-20260615-001  
**MFDB Version:** 1.31  
**Date:** 2026-06-15

---

## Overview

`lib_bejson_markdown` is a standalone Python library that treats markdown files as **addressable content stores**. It scans markdown structure, maps every block (headings, code fences, prose, frontmatter) to a stable line-range address, and backs all metadata in BEJSON 104 / MFDB v1.31 format.

The primary use case is **policy and instruction set management**: define chunks once, tag them, toggle them active or inactive, and assemble them on demand into system prompts, policy documents, or any other output format.

**This library does not modify any existing Lib_PY/Lib_JS/Lib_TS libraries.**

---

## Architecture

```
Lib_MD_v1/
├── lib_md_errors.py        — Custom exception classes (error codes 70–89)
├── lib_md_indexer.py       — Markdown scanner and BEJSON 104 index factory
├── lib_md_ops.py           — pull / inject / toggle / assemble operations
├── lib_md_db.py            — MFDB v1.31 wrapper for multi-file management
├── config.json             — BEJSON 104a library configuration
├── demo.py                 — Runnable demonstration script
├── README.md               — This document
└── lib/
    └── (copy Core/*.py from Lib_PY here, or add Core to sys.path)
```

---

## Dependencies

This library requires `lib_bejson_core.py` and `lib_mfdb_core.py` from your **Lib_PY v2 Core** family. There are two ways to satisfy this:

**Option A — local lib/ folder (portable, recommended for standalone scripts):**
```
cp /path/to/Lib_PY/Core/lib_bejson_core.py   Lib_MD_v1/lib/
cp /path/to/Lib_PY/Core/lib_mfdb_core.py     Lib_MD_v1/lib/
cp /path/to/Lib_PY/Core/lib_bejson_env.py    Lib_MD_v1/lib/
cp /path/to/Lib_PY/Core/lib_bejson_errors.py Lib_MD_v1/lib/
cp /path/to/Lib_PY/Core/lib_mfdb_validator.py Lib_MD_v1/lib/
cp /path/to/Lib_PY/Core/lib_bejson_path_guard.py Lib_MD_v1/lib/
```

**Option B — sys.path (when embedded in a larger project):**
```python
import sys
sys.path.insert(0, "/path/to/Lib_PY/Core")
```

---

## BEJSON Document Format

### MarkdownChunk Index (BEJSON 104)

Each markdown file gets its own `*.chunk_index.bejson` document with `Records_Type: ["MarkdownChunk"]`.

| Field        | Type    | Description |
|:-------------|:--------|:------------|
| `chunk_id`   | string  | Stable identifier derived from file stem + type + line + seq |
| `file_path`  | string  | Absolute path to the markdown file |
| `start_line` | integer | 0-based inclusive line start |
| `end_line`   | integer | 0-based exclusive line end (Python slice convention) |
| `chunk_type` | string  | `heading`, `code_block`, `frontmatter`, `policy`, `raw` |
| `label`      | string  | Human-readable chunk name |
| `is_active`  | boolean | Participates in assemble operations when True |
| `tags`       | array   | String tags for filtering |
| `sort_order` | integer | Assembly sequence, independent of line position |
| `injected_at`| string  | ISO 8601 UTC timestamp of last injection |
| `checksum`   | string  | SHA-256[:16] of raw chunk content |

### MarkdownFile Registry (MFDB entity — BEJSON 104)

| Field          | Type    | Description |
|:---------------|:--------|:------------|
| `file_id`      | string  | Stable slug from file stem |
| `file_path`    | string  | Absolute path to markdown file |
| `index_path`   | string  | Path to the per-file chunk index document |
| `last_indexed` | string  | ISO 8601 UTC timestamp |
| `line_count`   | integer | Total lines at last index |
| `chunk_count`  | integer | Number of chunks at last index |
| `description`  | string  | Optional human label |
| `tags`         | array   | File-level tags |

---

## Module Reference

### `lib_md_indexer` — Scanner

#### `md_indexer_scan_file(file_path) -> List[Dict]`
Scan a markdown file and return raw chunk dicts. Pure read — no writes.

#### `md_indexer_build_index_doc(file_path, default_active=True) -> Dict`
Scan file and return a complete BEJSON 104 MarkdownChunk document. Does not write.

#### `md_indexer_save_index(index_doc, index_path) -> bool`
Atomically write an index document to disk.

#### `md_indexer_reindex_file(file_path, index_path, preserve_metadata=True) -> Dict`
Full reindex. Preserves tags, is_active, sort_order from the previous index via best-effort matching (chunk_id first, then proximity ±5 lines). Always recomputes checksums.

#### `md_indexer_list_chunks(index_doc) -> List[Dict]`
Return all chunks as a list of named dicts. Convenience for inspection.

---

### `lib_md_ops` — Operations

#### `md_ops_pull(index_path, chunk_id, verify_checksum=True) -> str`
Pull raw text content of a chunk. Raises `ChunkDriftError` if checksum mismatches and `verify_checksum=True`.

#### `md_ops_inject(index_path, chunk_id, new_content) -> Dict`
Replace a chunk's content. Writes file atomically then performs a full reindex. Returns the new index document.

#### `md_ops_toggle(index_path, chunk_id, active=None) -> bool`
Flip or explicitly set `is_active`. Returns the new value.

#### `md_ops_toggle_by_tag(index_path, tag, active) -> List[str]`
Set `is_active` for every chunk with a matching tag. Returns list of modified chunk_ids.

#### `md_ops_set_tags(index_path, chunk_id, tags)`
Set the `tags` array for a specific chunk.

#### `md_ops_set_sort_order(index_path, chunk_id, sort_order)`
Set the `sort_order` for a specific chunk.

#### `md_ops_assemble(index_path, tags=None, active_only=True, separator="\n", predicate=None) -> str`
Assemble chunks matching filters into a single string. Sorted by sort_order.

#### `md_ops_assemble_by_tag(index_path, tag, separator="\n\n") -> str`
Shorthand: assemble all active chunks with a specific tag.

#### `md_ops_list_chunks(index_path, active_only=False, tag=None) -> List[Dict]`
Return filtered, sorted chunk dicts from an index.

#### `md_ops_reindex(file_path, index_path) -> Dict`
Public reindex wrapper. Safe to call anytime — idempotent.

---

### `lib_md_db` — MFDB Multi-File Manager

#### `md_db_create(db_root, db_name, description) -> str`
Create a new Markdown MFDB database. Returns manifest path.

#### `md_db_exists(db_root) -> bool`
Check if a valid Markdown MFDB exists at db_root.

#### `md_db_register_file(db_root, file_path, description, tags) -> str`
Register and index a markdown file. Returns file_id. Updates in place if already registered.

#### `md_db_list_files(db_root) -> List[Dict]`
Return all registered files.

#### `md_db_get_file(db_root, file_id) -> Optional[Dict]`
Return a file record by file_id.

#### `md_db_reindex_file(db_root, file_id) -> Dict`
Reindex a registered file, syncing the flat chunk entity.

#### `md_db_reindex_all(db_root) -> Dict[str, Dict]`
Reindex all registered files. Returns {file_id: new_doc}.

#### `md_db_unregister_file(db_root, file_id) -> bool`
Remove file from registry and clean up its index. Does NOT delete the markdown file.

#### `md_db_assemble(db_root, tags, active_only, separator, predicate) -> str`
Assemble across all registered files using the flat chunk entity.

#### `md_db_assemble_by_tag(db_root, tag, separator) -> str`
Shorthand cross-file assembly by tag.

#### `md_db_pull(db_root, file_id, chunk_id) -> str`
Pull a chunk using file_id + chunk_id.

#### `md_db_inject(db_root, file_id, chunk_id, new_content) -> Dict`
Inject into a chunk and sync flat entity.

#### `md_db_toggle(db_root, file_id, chunk_id, active) -> bool`
Toggle is_active and sync flat entity.

#### `md_db_set_tags(db_root, file_id, chunk_id, tags)`
Set tags and sync flat entity.

#### `md_db_list_chunks(db_root, file_id, active_only, tag) -> List[Dict]`
List chunks for a specific registered file.

---

## Error Reference

All errors inherit from `MarkdownLibError(Exception)`.

| Code | Class | Trigger |
|:-----|:------|:--------|
| 70 | `ChunkNotFoundError` | chunk_id not in index |
| 71 | `FileNotFoundError` (MD) | markdown file missing from disk |
| 72 | `IndexNotFoundError` | index document missing or unreadable |
| 73 | `ChunkDriftError` | checksum mismatch — file edited out-of-band |
| 74 | `IndexStaleError` | index known stale after failed write |
| 75 | `WriteFailedError` | atomic write failed |
| 76 | `InjectRangeInvalidError` | start/end line out of bounds |
| 77 | `AssembleEmptyError` | no chunks matched filters |
| 78 | `MFDBWrapperError` | MFDB layer error |
| 79 | `InvalidDocumentError` | BEJSON doc fails structural check |

---

## The Offset Drift Problem

Line numbers are a fragile address space. Every external edit to a markdown file can shift every subsequent chunk's address. This library handles drift via:

1. **Checksum detection** — every `pull` verifies the chunk's stored SHA-256[:16] against the actual file content. A mismatch raises `ChunkDriftError`.
2. **Full reindex after write** — every `inject` call performs a complete reindex immediately after the file write, within the same call. There is no incremental offset tracking.
3. **Metadata preservation** — reindex preserves `tags`, `is_active`, and `sort_order` from the previous index via chunk_id matching with proximity fallback (±5 lines).

**The index is ephemeral metadata derived from the file. The file is always the source of truth.**

---

## System Prompt / Policy Use Case

This is the primary motivating use case. Example flow:

```python
from lib_md_ops import (
    md_indexer_reindex_file,
    md_ops_set_tags,
    md_ops_toggle_by_tag,
    md_ops_assemble_by_tag,
    md_ops_list_chunks,
)

INDEX = "my_prompt.chunk_index.bejson"

# 1. Index your system prompt file
md_indexer_reindex_file("GEMINI.md", INDEX)

# 2. Inspect what was found
for chunk in md_ops_list_chunks(INDEX):
    print(chunk["chunk_id"], chunk["chunk_type"], chunk["label"])

# 3. Tag the chunks you want in your active system prompt
md_ops_set_tags(INDEX, "gemini_coding_persona_0_0",  ["gemini_context"])
md_ops_set_tags(INDEX, "gemini_rules_heading_5_1",   ["gemini_context"])
md_ops_set_tags(INDEX, "gemini_python_rules_raw_8_2", ["gemini_context", "python"])

# 4. Toggle a chunk off (e.g., suppress a section)
md_ops_toggle_by_tag(INDEX, "python", active=False)

# 5. Assemble the active system prompt
system_prompt = md_ops_assemble_by_tag(INDEX, "gemini_context")
print(system_prompt)
```

The assembled string can be passed directly to any AI API as the system instruction. Switching context (e.g., from coding to writing) is a `toggle_by_tag` call — not a file edit.

---

## MFDB Database Layout

When using `lib_md_db` for multi-file management:

```
markdown_db/
├── 104a.mfdb.bejson          ← manifest
└── data/
    ├── markdown_file.bejson  ← file registry entity (BEJSON 104)
    ├── markdown_chunk.bejson ← flat cross-file chunk index (BEJSON 104)
    ├── gemini.chunk_index.bejson
    ├── policy.chunk_index.bejson
    └── ...                   ← per-file chunk indexes
```

---

*lib_bejson_markdown v1.0.0 — Elton Boehnen — eltonboehnen@gmail.com — boehnenelton2024.pages.dev — github.com/boehnenelton*
