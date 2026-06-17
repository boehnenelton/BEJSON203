# System Manual: Package Management System (PMS) v2.1
**Version**: 2.1.0  
**Author**: Elton Boehnen  
**Date**: Tuesday, June 16, 2026  
**Relational ID**: gcli-pms-system-manual-v2

## 1. Overview
The BEJSON Package Management System (PMS) v2.1 is a professional-grade development infrastructure designed for 2026-standard agentic workflows. It leverages a relational **BEJSON 104db** architecture to track projects, versioned packages, and issues (bugs) within a unified ecosystem.

## 2. Architecture
The system consists of three core components:
1.  **Relational Registry**: A single 104db file (`PMS_v2_Registry.104db.bejson`) containing `Project`, `Package`, and `Issue` entities.
2.  **Core Library (`lib_be_pms.py`)**: The logic engine handling schema migrations, Dual-Version Retention, and relational integrity.
3.  **CLI Interface (`pms.py`)**: The unified command-line tool for project management.

### 2.1 Jurisdictional Staging
PMS v2.1 enforces strict folder hierarchies for project artifacts:
- **Dev Root**: `/storage/emulated/0/Admin/dev/`
- **Archive Staging Root**: `/storage/emulated/0/Admin/dev/Archived_Packages/`

Projects are automatically organized into subfolders based on their **Project Type**:
- `python` -> `Python/`
- `web` -> `Web/`
- `react` -> `React/`
- `bash` -> `Bash/`
- `skill` -> `Skills/`

## 3. Configuration & Path Resolution
The system utilizes a hierarchy for resolving database and staging paths:
1.  **Primary**: Environment Variables (defined in `env_file.json`).
2.  **Fallback**: Defaults hardcoded in the library (relative to `ADMIN_ROOT`).
3.  **Root Authority**: All development paths are resolved relative to the `dev/` root.

### Required Environment Variables
- `PMS_DATABASE_PATH`: Absolute path to the relational registry.
- `ARCHIVE_STAGING_ROOT`: Absolute path to the `Archived_Packages/` hierarchy.

## 4. Policy: Dual-Version Retention (DVRP)
To optimize mobile storage, PMS v2.1 mandates the **"Two-Latest-Zips"** policy:
- The staging area for each project maintains exactly the two most recent versions.
- Older versions are automatically purged during the `release` operation.
- **Rollback Safety**: This ensures a 1-step rollback is always immediately available on-disk.

## 5. CLI Usage Guide
The PMS CLI is located at: `libraries/Lib_PY/System/cli/pms.py`

### Commands
#### 5.1 Initialize / Migrate
```bash
python3 pms.py init
```
Initializes a fresh database or migrates an existing v2.0 database to include the `project_type` field.

#### 5.2 Project Registration
```bash
python3 pms.py add-project "ProjectName" --type "python" --url "https://github.com/..." --desc "Description"
```

#### 5.3 Type Management & Relocation
```bash
# Set project type
python3 pms.py set-type "ProjectName" "web"

# Physically move project to correct jurisdictional folders
python3 pms.py relocate "ProjectName"
```

#### 5.4 Versioned Releases
```bash
python3 pms.py release "ProjectName" "1.2.3" "/path/to/source"
```
Automates zipping, hashing, and DVRP rotation.

#### 5.5 Issue Reporting
```bash
python3 pms.py bug "ProjectName" "Bug Title" "high" "Reproduction steps..."
```

#### 5.6 Project Listing
```bash
python3 pms.py list
```

## 6. Implementation Notes
- **Atomic Writes**: All registry updates use the `bejson_core_atomic_write` primitive.
- **Mutex Locking**: Concurrent access is managed via `ResilientPIDLock`.
- **Relational IDs**: Packages are linked to projects via `project_name_fk`.

---
*Elton Boehnen · boehnenelton2024@gmail.com · [boehnenelton2024.pages.dev](https://boehnenelton2024.pages.dev)*
