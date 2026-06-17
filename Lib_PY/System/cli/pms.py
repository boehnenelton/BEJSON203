#!/usr/bin/env python3
"""
CLI_Package_Updater v2.1.0
Description: Relational Package Management System (PMS) interface for version 2.1.
              Handles project registration, versioned releases, and automated relocation logic.
Author: Elton Boehnen · eltonboehnen@gmail.com · boehnenelton2024.pages.dev · github.com/boehnenelton
Relational ID: gcli-tool-pkg-updater-v2-001
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

VERSION = "2.1.0"

# --- PORTABILITY MANDATE ---
def get_script_path() -> Path:
    return Path(__file__).resolve().parent

SCRIPT_PATH = get_script_path()

# Setup library paths
ADMIN_ROOT = os.environ.get("ADMIN_ROOT", "/storage/emulated/0/Admin")
LIB_SYS_PATH = os.path.join(ADMIN_ROOT, "libraries/Lib_PY/System")
LIB_CORE_PATH = os.path.join(ADMIN_ROOT, "libraries/Lib_PY/Core")

sys.path.append(LIB_SYS_PATH)
sys.path.append(LIB_CORE_PATH)

try:
    import lib_bejson_core as BEJSONCore
    import lib_be_pms as PMS
except ImportError as e:
    print(f"CRITICAL: System libraries not found. {e}")
    sys.exit(1)

def cmd_init():
    if PMS.pms_init():
        print("[SUCCESS] PMS v2.1 relational database initialized and migrated.")
    else:
        print("[ERROR] Failed to initialize PMS database.")

def cmd_add_project(args):
    if PMS.pms_add_project(args.name, args.url, args.desc, args.cat, args.type, args.dev):
        print(f"[SUCCESS] Registered project: {args.name} (Type: {args.type})")
    else:
        print(f"[ERROR] Project '{args.name}' already exists or failed to register.")

def cmd_set_type(args):
    if PMS.pms_update_project(args.name, project_type=args.type):
        print(f"[SUCCESS] Project '{args.name}' type updated to: {args.type}")
    else:
        print(f"[ERROR] Failed to update project type.")

def cmd_relocate(args):
    try:
        if PMS.pms_relocate(args.name):
            print(f"[SUCCESS] Project '{args.name}' relocated successfully.")
        else:
            print(f"[ERROR] Relocation failed.")
    except Exception as e:
        print(f"[FATAL] {e}")

def cmd_release(args):
    try:
        if PMS.pms_release(args.name, args.version, args.source):
            print(f"[SUCCESS] Released {args.name} v{args.version}.")
        else:
            print(f"[ERROR] Release failed.")
    except Exception as e:
        print(f"[FATAL] {e}")

def cmd_bug(args):
    if PMS.pms_bug_report(args.name, args.title, args.sev, args.desc):
        print(f"[SUCCESS] Bug reported for {args.name}: {args.title}")
    else:
        print(f"[ERROR] Failed to record bug report.")

def cmd_list():
    PMS.pms_init() # Ensure schema is migrated
    db_path = os.environ.get("PMS_DATABASE_PATH")
    doc = BEJSONCore.bejson_core_load_file(db_path)
    if not doc:
        print(f"Database not found at {db_path}. Run 'init' first.")
        return
    
    fm = BEJSONCore.bejson_core_get_field_map(doc)
    projects = [r for r in doc["Values"] if r[fm["Record_Type_Parent"]] == "Project"]
    packages = [r for r in doc["Values"] if r[fm["Record_Type_Parent"]] == "Package"]
    
    print(f"\n{'Project Name':<25} | {'Type':<8} | {'Latest Version':<15} | {'Status'}")
    print("-" * 90)
    
    for p in projects:
        name = p[fm["project_name"]]
        p_type = p[fm.get("project_type", -1)] or "unknown"
        # Find latest package
        p_pkgs = sorted([pkg for pkg in packages if pkg[fm["project_name_fk"]] == name], 
                        key=lambda x: x[fm["last_updated"]], reverse=True)
        latest = p_pkgs[0][fm["version"]] if p_pkgs else "no releases"
        state = p_pkgs[0][fm["state"]] if p_pkgs else "n/a"
        
        print(f"{name:<25} | {p_type:<8} | {latest:<15} | {state}")

def main():
    parser = argparse.ArgumentParser(description=f"CLI_Package_Updater v{VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Initialize or migrate the relational registry")
    
    parser_add = subparsers.add_parser("add-project", help="Register a new project")
    parser_add.add_argument("name", help="Project name")
    parser_add.add_argument("--url", help="GitHub URL")
    parser_add.add_argument("--desc", help="Project description")
    parser_add.add_argument("--cat", default="tool", help="Category (tool, library, app, skill)")
    parser_add.add_argument("--type", help="Project type (python, web, bash, react, skill)")
    parser_add.add_argument("--dev", help="Path to development directory")

    parser_type = subparsers.add_parser("set-type", help="Set project type")
    parser_type.add_argument("name", help="Project name")
    parser_type.add_argument("type", help="Project type (python, web, bash, react, skill)")

    parser_move = subparsers.add_parser("relocate", help="Physically move project based on type")
    parser_move.add_argument("name", help="Project name")

    parser_rel = subparsers.add_parser("release", help="Release a project version")
    parser_rel.add_argument("name", help="Project name")
    parser_rel.add_argument("version", help="Version string (e.g. 1.2.3)")
    parser_rel.add_argument("source", help="Source directory to package")

    parser_bug = subparsers.add_parser("bug", help="Report a bug for a project")
    parser_bug.add_argument("name", help="Project name")
    parser_bug.add_argument("title", help="Short title")
    parser_bug.add_argument("sev", choices=["critical", "high", "medium", "low"], help="Severity level")
    parser_bug.add_argument("desc", help="Detailed description")

    subparsers.add_parser("list", help="List registered projects")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "add-project":
        cmd_add_project(args)
    elif args.command == "set-type":
        cmd_set_type(args)
    elif args.command == "relocate":
        cmd_relocate(args)
    elif args.command == "release":
        cmd_release(args)
    elif args.command == "bug":
        cmd_bug(args)
    elif args.command == "list":
        cmd_list()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
