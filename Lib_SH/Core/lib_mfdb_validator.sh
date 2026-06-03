# Library:      lib_mfdb_validator.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.2 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-06-02
# Description:  Bidirectional path and manifest-entity relationship validator.
#
# CHANGELOG v2.0.2:
#   [SH3] Fixed: removed top-level `set -o nounset` to prevent polluting host script options.

# NOTE: set -o nounset intentionally omitted — library files must not modify
# global shell options; doing so breaks host scripts that source this file. (SH3)
set -o pipefail

# Source base validator if not already loaded
_MFDB_VAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! declare -f bejson_validator_validate_file > /dev/null 2>&1; then
    # shellcheck source=./lib_bejson_validator.sh
    source "${_MFDB_VAL_DIR}/lib_bejson_validator.sh"
fi

#-------------------------------------------------------------------------------
# Error codes (30–49)
#-------------------------------------------------------------------------------

[[ -v E_MFDB_NOT_MANIFEST ]] || readonly E_MFDB_NOT_MANIFEST=30
[[ -v E_MFDB_NOT_ENTITY_FILE ]] || readonly E_MFDB_NOT_ENTITY_FILE=31
[[ -v E_MFDB_MANIFEST_RECORDS_TYPE ]] || readonly E_MFDB_MANIFEST_RECORDS_TYPE=32
[[ -v E_MFDB_ENTITY_NOT_FOUND ]] || readonly E_MFDB_ENTITY_NOT_FOUND=33
[[ -v E_MFDB_ENTITY_NAME_MISMATCH ]] || readonly E_MFDB_ENTITY_NAME_MISMATCH=34
[[ -v E_MFDB_DUPLICATE_ENTRY ]] || readonly E_MFDB_DUPLICATE_ENTRY=35
[[ -v E_MFDB_NO_PARENT_HIERARCHY ]] || readonly E_MFDB_NO_PARENT_HIERARCHY=36
[[ -v E_MFDB_MANIFEST_NOT_FOUND ]] || readonly E_MFDB_MANIFEST_NOT_FOUND=37
[[ -v E_MFDB_BIDIRECTIONAL_FAIL ]] || readonly E_MFDB_BIDIRECTIONAL_FAIL=38
[[ -v E_MFDB_FK_UNRESOLVED ]] || readonly E_MFDB_FK_UNRESOLVED=39
[[ -v E_MFDB_MISSING_REQUIRED_FIELD ]] || readonly E_MFDB_MISSING_REQUIRED_FIELD=40
[[ -v E_MFDB_NULL_REQUIRED ]] || readonly E_MFDB_NULL_REQUIRED=41
[[ -v E_MFDB_INVALID_ARCHIVE ]] || readonly E_MFDB_INVALID_ARCHIVE=42

#-------------------------------------------------------------------------------
# Validation state
#-------------------------------------------------------------------------------

__MFDB_VALIDATION_ERRORS=()
__MFDB_VALIDATION_WARNINGS=()

mfdb_validator_reset_state() {
    __MFDB_VALIDATION_ERRORS=()
    __MFDB_VALIDATION_WARNINGS=()
}

__mfdb_add_error() {
    local message="$1"
    local location="${2:-}"
    __MFDB_VALIDATION_ERRORS+=("ERROR | Location: $location | Message: $message")
}

mfdb_validator_has_errors()   { [[ ${#__MFDB_VALIDATION_ERRORS[@]}   -gt 0 ]]; }
mfdb_validator_get_errors()    { printf '%s\n' "${__MFDB_VALIDATION_ERRORS[@]+"${__MFDB_VALIDATION_ERRORS[@]}"}"; }

#-------------------------------------------------------------------------------
# Archive Validation
#-------------------------------------------------------------------------------

# mfdb_validator_validate_archive <archive_path>
mfdb_validator_validate_archive() {
    local archive_path="$1"
    mfdb_validator_reset_state
    if [[ ! -f "$archive_path" ]]; then
        __mfdb_add_error "Archive not found: $archive_path" "File System"
        return $E_MFDB_MANIFEST_NOT_FOUND
    fi

    if ! unzip -l "$archive_path" | grep -q "104a.mfdb.bejson"; then
        __mfdb_add_error "Missing 104a.mfdb.bejson manifest inside archive" "Zip Structure"
        return $E_MFDB_INVALID_ARCHIVE
    fi
    return 0
}

#-------------------------------------------------------------------------------
# Main validation
#-------------------------------------------------------------------------------

mfdb_validator_validate_manifest() {
    local manifest_path="$1"
    mfdb_validator_reset_state
    [[ ! -f "$manifest_path" ]] && return $E_MFDB_MANIFEST_NOT_FOUND
    bejson_validator_validate_file "$manifest_path" || return $E_MFDB_NOT_MANIFEST
    
    local rt=$(jq -r '.Records_Type | @json' "$manifest_path" 2>/dev/null)
    [[ "$rt" != '["mfdb"]' ]] && return $E_MFDB_MANIFEST_RECORDS_TYPE
    return 0
}

#-------------------------------------------------------------------------------
# Dependency check
#-------------------------------------------------------------------------------

mfdb_validator_check_dependencies() {
    if ! command -v unzip >/dev/null 2>&1; then
        echo "ERROR: Required command 'unzip' not found" >&2
        return 1
    fi
    # Strictly enforce jq >= 1.6 via base validator
    if ! bejson_validator_check_dependencies; then
        return 1
    fi
    return 0
}

# Export functions
export -f mfdb_validator_validate_archive
export -f mfdb_validator_validate_manifest
export -f mfdb_validator_reset_state
export -f mfdb_validator_has_errors
export -f mfdb_validator_get_errors
export -f mfdb_validator_check_dependencies