# Library Instructions: Python (Lib_PY)
**Relational ID:** gcli-lib-py-001

## Python Standards
- **Path Resolution**: Must use the `get_script_path()` pattern defined in the Global Mandate (Sec. 19).
- **Type Safety**: Prefer explicit type hinting and BEJSON-standard error handling.
- **Dependencies**: Resolve via `~/env_file.py` or the Registry MFDB.
- **Data Integrity**: 
    - **Validation**: Enforce structural correctness (Level 1-3). Failures result in hard errors.
    - **Standardization**: Enforce architectural compliance (snake_case, _fk suffixes). Failures result in warnings only.
    - **Structure**: Always use `null` for absent values. Treat field reordering as a breaking change.

---
*Refer to the Project Root GEMINI.md for the Field Map Migration Plan.*
