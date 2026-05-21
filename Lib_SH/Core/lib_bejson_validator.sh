# Library:      lib_bejson_validator.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-05-18
# Description:  Structural integrity checker for positional values and mandatory keys.

set -o pipefail
set -o nounset

# Error codes
[[ -v E_VAL_NOT_JSON ]] || readonly E_VAL_NOT_JSON=1
[[ -v E_VAL_MISSING_KEY ]] || readonly E_VAL_MISSING_KEY=2
[[ -v E_VAL_BAD_FORMAT ]] || readonly E_VAL_BAD_FORMAT=3
[[ -v E_VAL_BAD_VERSION ]] || readonly E_VAL_BAD_VERSION=4
[[ -v E_VAL_BAD_CREATOR ]] || readonly E_VAL_BAD_CREATOR=5
[[ -v E_VAL_SCHEMA_MISMATCH ]] || readonly E_VAL_SCHEMA_MISMATCH=6
[[ -v E_VAL_INVALID_TYPE ]] || readonly E_VAL_INVALID_TYPE=7

#-------------------------------------------------------------------------------
# CORE VALIDATION
#-------------------------------------------------------------------------------

bejson_validator_check_dependencies() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq is required for BEJSON validation" >&2
        return 1
    fi
    local jq_ver=$(jq --version | sed 's/jq-//')
    # Simple check for jq >= 1.6
    # Robust version check: compare major.minor as integers
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

    # 2. Mandatory Keys check
    local keys=$(jq -r 'keys | join(",")' "$file_path")
    for k in Format Format_Version Format_Creator Records_Type Fields Values; do
        if [[ ! "$keys" =~ "$k" ]]; then
            return $E_VAL_MISSING_KEY
        fi
    done

    # 3. Format & Creator check
    local fmt=$(jq -r '.Format' "$file_path")
    local creator=$(jq -r '.Format_Creator' "$file_path")
    [[ "$fmt" != "BEJSON" ]] && return $E_VAL_BAD_FORMAT
    [[ "$creator" != "Elton Boehnen" ]] && return $E_VAL_BAD_CREATOR

    # 4. Records Length check
    local field_count=$(jq '.Fields | length' "$file_path")
    local bad_records=$(jq --argjson fc "$field_count" '.Values | map(select(length != $fc)) | length' "$file_path")
    if [[ "$bad_records" -gt 0 ]]; then
        return $E_VAL_SCHEMA_MISMATCH
    fi

    return 0
}

# Export functions
export -f bejson_validator_check_dependencies
export -f bejson_validator_validate_file