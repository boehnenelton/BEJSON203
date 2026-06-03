# Library:      lib_bejson_validator.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.3 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-06-02
# Description:  Structural integrity checker for positional values and mandatory keys.
#
# CHANGELOG v2.0.3:
#   [SH1] Fixed: mandatory-key check used substring match (=~) on a joined key string.
#         "Format" matched inside "Format_Creator", so a document missing the bare
#         "Format" key was incorrectly declared valid. Now uses exact jq per-key check.
#   [SH3] Fixed: removed top-level `set -o nounset`. When sourced into a host script,
#         this option was applied to the caller, causing fatal errors on any pre-existing
#         unset variable in that script. Library files must not modify global shell options.
#   [SH4] Standardized: Updated error codes to align with lib_bejson_errors.sh (v1.1.0).

set -o pipefail

# Source the error registry (assumes same directory)
_VAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$_VAL_DIR/lib_bejson_errors.sh" ]]; then
    # shellcheck source=./lib_bejson_errors.sh
    source "$_VAL_DIR/lib_bejson_errors.sh"
fi

# Legacy aliases for backward compatibility with older scripts
[[ -v E_VAL_NOT_JSON        ]] || readonly E_VAL_NOT_JSON=$E_INVALID_JSON
[[ -v E_VAL_MISSING_KEY     ]] || readonly E_VAL_MISSING_KEY=$E_MISSING_MANDATORY_KEY
[[ -v E_VAL_BAD_FORMAT      ]] || readonly E_VAL_BAD_FORMAT=$E_INVALID_FORMAT
[[ -v E_VAL_BAD_VERSION     ]] || readonly E_VAL_BAD_VERSION=$E_INVALID_VERSION
[[ -v E_VAL_BAD_CREATOR     ]] || readonly E_VAL_BAD_CREATOR=$E_INVALID_FORMAT_CREATOR
[[ -v E_VAL_SCHEMA_MISMATCH ]] || readonly E_VAL_SCHEMA_MISMATCH=$E_RECORD_LENGTH_MISMATCH
[[ -v E_VAL_INVALID_TYPE    ]] || readonly E_VAL_INVALID_TYPE=$E_TYPE_MISMATCH

#-------------------------------------------------------------------------------
# CORE VALIDATION
#-------------------------------------------------------------------------------

bejson_validator_check_dependencies() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq is required for BEJSON validation" >&2
        return 1
    fi
    local jq_ver
    jq_ver=$(jq --version | sed 's/jq-//')
    local jq_major jq_minor
    jq_major="${jq_ver%%.*}"
    jq_minor="${jq_ver#*.}"; jq_minor="${jq_minor%%.*}"
    if [[ "$jq_major" -lt 1 ]] || { [[ "$jq_major" -eq 1 ]] && [[ "$jq_minor" -lt 6 ]]; }; then
        echo "ERROR: jq >= 1.6 is required. Found: $jq_ver" >&2
        return 1
    fi
    return 0
}

bejson_validator_validate_file() {
    local file_path="$1"
    if [[ ! -f "$file_path" ]]; then
        echo "ERROR: File not found: $file_path" >&2
        return 1
    fi

    # 1. Basic JSON check
    if ! jq . "$file_path" >/dev/null 2>&1; then
        return $E_VAL_NOT_JSON
    fi

    # 2. Mandatory Keys — exact presence check via jq (FIX SH1)
    #    Using =~ on a joined key string caused substring collisions:
    #    "Format" matched inside "Format_Creator", making missing bare "Format" go undetected.
    for k in Format Format_Version Format_Creator Records_Type Fields Values; do
        if ! jq -e --arg key "$k" 'has($key)' "$file_path" >/dev/null 2>&1; then
            return $E_VAL_MISSING_KEY
        fi
    done

    # 3. Format & Creator check
    local fmt creator
    fmt=$(jq -r '.Format' "$file_path")
    creator=$(jq -r '.Format_Creator' "$file_path")
    [[ "$fmt"     != "BEJSON"        ]] && return $E_VAL_BAD_FORMAT
    [[ "$creator" != "Elton Boehnen" ]] && return $E_VAL_BAD_CREATOR

    # 4. Records Length check
    local field_count bad_records
    field_count=$(jq '.Fields | length' "$file_path")
    bad_records=$(jq --argjson fc "$field_count" '.Values | map(select(length != $fc)) | length' "$file_path")
    if [[ "$bad_records" -gt 0 ]]; then
        return $E_VAL_SCHEMA_MISMATCH
    fi

    return 0
}

# Export functions for subshell use
export -f bejson_validator_check_dependencies
export -f bejson_validator_validate_file
