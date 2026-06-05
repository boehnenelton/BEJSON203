# Project Instructions: BEJSON Production Mirror (SLAVE)
**Relational ID:** gcli-lib-mirror-mandate-001

## ⚠ MASTER/SLAVE FEDERATION MANDATE
This directory is a **VERIFIED SLAVE MIRROR** of the authoritative Termux library source.

### AUTHORITATIVE SOURCE
- **Path**: `~/libraries`
- **Role**: All development, refinement, and testing MUST occur at this path.

### MIRROR STATUS
- **Path**: `/storage/emulated/0/Admin/libraries`
- **Role**: Read-only production target for cross-platform interoperability.
- **Automation**: Managed by `library-mirror-service.py`.

### MANDATORY BEHAVIOR
1. **Never Edit Directly**: Any changes made directly to the Admin Mirror will be **OVERWRITTEN** by the next synchronization cycle.
2. **Atomic Synchronization**: Updates to the Admin Mirror are pushed only after a task is logged as "COMPLETED" in the Termux environment.

---
*Refer to the Project Root GEMINI.md for the Field Map Migration Plan.*
