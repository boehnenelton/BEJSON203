# Library Instructions: TypeScript (Lib_TS)
**Relational ID:** gcli-lib-ts-001

## TS Standards
- **Typing**: Use strong typing for all BEJSON document structures.
- **Error Handling**: Use the Unified Error Map integer codes for custom exceptions.
- **Modularity**: Prioritize composition over inheritance as per Global Mandate.
- **Data Integrity**: 
    - **Validation**: Enforce structural correctness (Level 1-3). Failures result in hard errors.
    - **Standardization**: Enforce architectural compliance (snake_case, _fk suffixes). Failures result in warnings only.
    - **Structure**: Always use `null` for absent values. Treat field reordering as a breaking change.

---
*Refer to the Project Root GEMINI.md for the Field Map Migration Plan.*
