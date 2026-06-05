# Library Instructions: Bash (Lib_SH)
**Relational ID:** gcli-lib-sh-001

## Bash Standards
- **Path Resolution**: Must use the `get_script_path()` pattern with the Sec. 20.1 fallback logic.
- **Error Handling**: Standardize exit codes using the Unified Error Map (Sec. 45).
- **Environment**: Source from fallback hierarchy (Sec. 54) when secrets are required.
- **Data Integrity**: 
    - **Validation**: Enforce structural correctness (Level 1-3). Failures result in hard errors.
    - **Standardization**: Enforce architectural compliance (snake_case, _fk suffixes). Failures result in warnings only.
    - **Structure**: Always use `null` for absent values. Treat field reordering as a breaking change.
- **Field Mapping**: Field Map Indexing is the primary standard for field access. Array-based indexing is retained as a transitional fallback only.

---
*Refer to the Project Root GEMINI.md for the Field Map Migration Plan.*
