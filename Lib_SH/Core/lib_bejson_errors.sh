# Library:      lib_bejson_errors.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      1.1.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-06-09
# Description:  Centralized error code registry for all Bash BEJSON libraries.
#               Mirrors lib_bejson_errors.js and lib_bejson_errors.py.
#
# CHANGELOG v1.1.1:
#   - Added standardized codes 60-65 (Audit Finding TS1 Parity).
#
# CHANGELOG v1.1.0:
#   - Added E_CORE_ENCRYPTION_FAILED (28) and E_CORE_DECRYPTION_FAILED (29).
#   - Added MFDB Core codes 54-56, 70-71.
#   - Reassigned E_VAL_BAD_CREATOR to code 16 to resolve collision with E_INVALID_RECORDS_TYPE (5).

# ===========================================================================
# BEJSON VALIDATOR ERRORS (1–19)  — mirrors E_* in lib_bejson_errors.js / .py
# ===========================================================================
[[ -v E_INVALID_JSON                ]] || readonly E_INVALID_JSON=1
[[ -v E_MISSING_MANDATORY_KEY       ]] || readonly E_MISSING_MANDATORY_KEY=2
[[ -v E_INVALID_FORMAT              ]] || readonly E_INVALID_FORMAT=3
[[ -v E_INVALID_VERSION             ]] || readonly E_INVALID_VERSION=4
[[ -v E_INVALID_RECORDS_TYPE        ]] || readonly E_INVALID_RECORDS_TYPE=5
[[ -v E_INVALID_FIELDS              ]] || readonly E_INVALID_FIELDS=6
[[ -v E_INVALID_VALUES              ]] || readonly E_INVALID_VALUES=7
[[ -v E_TYPE_MISMATCH               ]] || readonly E_TYPE_MISMATCH=8
[[ -v E_RECORD_LENGTH_MISMATCH      ]] || readonly E_RECORD_LENGTH_MISMATCH=9
[[ -v E_RESERVED_KEY_COLLISION      ]] || readonly E_RESERVED_KEY_COLLISION=10
[[ -v E_INVALID_RECORD_TYPE_PARENT  ]] || readonly E_INVALID_RECORD_TYPE_PARENT=11
[[ -v E_NULL_VIOLATION              ]] || readonly E_NULL_VIOLATION=12
[[ -v E_FILE_NOT_FOUND              ]] || readonly E_FILE_NOT_FOUND=13
[[ -v E_PERMISSION_DENIED           ]] || readonly E_PERMISSION_DENIED=14
[[ -v E_ATOMIC_WRITE_FAILED         ]] || readonly E_ATOMIC_WRITE_FAILED=15
[[ -v E_INVALID_FORMAT_CREATOR      ]] || readonly E_INVALID_FORMAT_CREATOR=16

# ===========================================================================
# BEJSON CORE ERRORS (20–29, 60-69)
# ===========================================================================
[[ -v E_CORE_INVALID_VERSION        ]] || readonly E_CORE_INVALID_VERSION=20
[[ -v E_CORE_INVALID_OPERATION      ]] || readonly E_CORE_INVALID_OPERATION=21
[[ -v E_CORE_INDEX_OUT_OF_BOUNDS    ]] || readonly E_CORE_INDEX_OUT_OF_BOUNDS=22
[[ -v E_CORE_FIELD_NOT_FOUND        ]] || readonly E_CORE_FIELD_NOT_FOUND=23
[[ -v E_CORE_TYPE_CONVERSION_FAILED ]] || readonly E_CORE_TYPE_CONVERSION_FAILED=24
[[ -v E_CORE_BACKUP_FAILED          ]] || readonly E_CORE_BACKUP_FAILED=25
[[ -v E_CORE_WRITE_FAILED           ]] || readonly E_CORE_WRITE_FAILED=26
[[ -v E_CORE_QUERY_FAILED           ]] || readonly E_CORE_QUERY_FAILED=27
[[ -v E_CORE_ENCRYPTION_FAILED      ]] || readonly E_CORE_ENCRYPTION_FAILED=28
[[ -v E_CORE_DECRYPTION_FAILED      ]] || readonly E_CORE_DECRYPTION_FAILED=29

# Standardized codes 60-65 (Audit Finding TS1 Parity)
[[ -v E_CORE_PARSE_ERROR            ]] || readonly E_CORE_PARSE_ERROR=60
[[ -v E_CORE_NULL_DOCUMENT          ]] || readonly E_CORE_NULL_DOCUMENT=61
[[ -v E_CORE_SERIALIZATION_ERROR    ]] || readonly E_CORE_SERIALIZATION_ERROR=62
[[ -v E_CORE_UNSUPPORTED_OPERATION  ]] || readonly E_CORE_UNSUPPORTED_OPERATION=63
[[ -v E_CORE_WRITE_LENGTH_MISMATCH  ]] || readonly E_CORE_WRITE_LENGTH_MISMATCH=64
[[ -v E_CORE_WRITE_TYPE_MISMATCH    ]] || readonly E_CORE_WRITE_TYPE_MISMATCH=65

# ===========================================================================
# MFDB VALIDATOR ERRORS (30–49)
# ===========================================================================
[[ -v E_MFDB_NOT_MANIFEST           ]] || readonly E_MFDB_NOT_MANIFEST=30
[[ -v E_MFDB_NOT_ENTITY_FILE        ]] || readonly E_MFDB_NOT_ENTITY_FILE=31
[[ -v E_MFDB_MANIFEST_RECORDS_TYPE  ]] || readonly E_MFDB_MANIFEST_RECORDS_TYPE=32
[[ -v E_MFDB_ENTITY_NOT_FOUND       ]] || readonly E_MFDB_ENTITY_NOT_FOUND=33
[[ -v E_MFDB_ENTITY_NAME_MISMATCH   ]] || readonly E_MFDB_ENTITY_NAME_MISMATCH=34
[[ -v E_MFDB_DUPLICATE_ENTRY        ]] || readonly E_MFDB_DUPLICATE_ENTRY=35
[[ -v E_MFDB_NO_PARENT_HIERARCHY    ]] || readonly E_MFDB_NO_PARENT_HIERARCHY=36
[[ -v E_MFDB_MANIFEST_NOT_FOUND     ]] || readonly E_MFDB_MANIFEST_NOT_FOUND=37
[[ -v E_MFDB_BIDIRECTIONAL_FAIL     ]] || readonly E_MFDB_BIDIRECTIONAL_FAIL=38
[[ -v E_MFDB_FK_UNRESOLVED          ]] || readonly E_MFDB_FK_UNRESOLVED=39
[[ -v E_MFDB_MISSING_REQUIRED_FIELD ]] || readonly E_MFDB_MISSING_REQUIRED_FIELD=40
[[ -v E_MFDB_NULL_REQUIRED          ]] || readonly E_MFDB_NULL_REQUIRED=41

# ===========================================================================
# MFDB CORE ERRORS (50–79)
# ===========================================================================
[[ -v E_MFDB_CORE_LOAD_FAILED       ]] || readonly E_MFDB_CORE_LOAD_FAILED=50
[[ -v E_MFDB_CORE_WRITE_FAILED      ]] || readonly E_MFDB_CORE_WRITE_FAILED=51
[[ -v E_MFDB_CORE_ENTITY_MISSING    ]] || readonly E_MFDB_CORE_ENTITY_MISSING=52
[[ -v E_MFDB_CORE_LOCK_FAILED       ]] || readonly E_MFDB_CORE_LOCK_FAILED=53
[[ -v E_MFDB_CORE_INVALID_OPERATION ]] || readonly E_MFDB_CORE_INVALID_OPERATION=54
[[ -v E_MFDB_CORE_INDEX_OUT_OF_BOUNDS ]] || readonly E_MFDB_CORE_INDEX_OUT_OF_BOUNDS=55
[[ -v E_MFDB_CORE_JOIN_FAILED       ]] || readonly E_MFDB_CORE_JOIN_FAILED=56
[[ -v E_MFDB_CORE_ARCHIVE_ERROR     ]] || readonly E_MFDB_CORE_ARCHIVE_ERROR=70
[[ -v E_MFDB_CORE_MOUNT_CONFLICT    ]] || readonly E_MFDB_CORE_MOUNT_CONFLICT=71

# ===========================================================================
# LEGACY ALIASES — lib_bejson_validator.sh used different names pre-v2.0.2.
# These aliases keep existing scripts working while pointing to unified codes.
# ===========================================================================
[[ -v E_VAL_NOT_JSON        ]] || readonly E_VAL_NOT_JSON=$E_INVALID_JSON
[[ -v E_VAL_MISSING_KEY     ]] || readonly E_VAL_MISSING_KEY=$E_MISSING_MANDATORY_KEY
[[ -v E_VAL_BAD_FORMAT      ]] || readonly E_VAL_BAD_FORMAT=$E_INVALID_FORMAT
[[ -v E_VAL_BAD_VERSION     ]] || readonly E_VAL_BAD_VERSION=$E_INVALID_VERSION
[[ -v E_VAL_BAD_CREATOR     ]] || readonly E_VAL_BAD_CREATOR=$E_INVALID_FORMAT_CREATOR
[[ -v E_VAL_SCHEMA_MISMATCH ]] || readonly E_VAL_SCHEMA_MISMATCH=$E_RECORD_LENGTH_MISMATCH
[[ -v E_VAL_INVALID_TYPE    ]] || readonly E_VAL_INVALID_TYPE=$E_TYPE_MISMATCH
