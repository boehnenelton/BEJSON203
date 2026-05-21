# Library:      lib_bejson_core.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-05-18
# Description:  Low-level primitive operations for BEJSON document manipulation.

#===============================================================================

#-------------------------------------------------------------------------------
# SAFETY & ERROR HANDLING
#-------------------------------------------------------------------------------

set -o pipefail
set -o nounset

# Source the validator library (assumes same directory)
_CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$_CORE_DIR/lib_bejson_validator.sh" ]]; then
    # shellcheck source=./lib_bejson_validator.sh
    source "$_CORE_DIR/lib_bejson_validator.sh"
fi

# Error codes
[[ -v E_CORE_INVALID_VERSION ]] || readonly E_CORE_INVALID_VERSION=20
[[ -v E_CORE_INVALID_OPERATION ]] || readonly E_CORE_INVALID_OPERATION=21
[[ -v E_CORE_INDEX_OUT_OF_BOUNDS ]] || readonly E_CORE_INDEX_OUT_OF_BOUNDS=22
[[ -v E_CORE_FIELD_NOT_FOUND ]] || readonly E_CORE_FIELD_NOT_FOUND=23
[[ -v E_CORE_TYPE_CONVERSION_FAILED ]] || readonly E_CORE_TYPE_CONVERSION_FAILED=24
[[ -v E_CORE_BACKUP_FAILED ]] || readonly E_CORE_BACKUP_FAILED=25
[[ -v E_CORE_WRITE_FAILED ]] || readonly E_CORE_WRITE_FAILED=26
[[ -v E_CORE_QUERY_FAILED ]] || readonly E_CORE_QUERY_FAILED=27

#-------------------------------------------------------------------------------
# ATOMIC FILE OPERATIONS
#-------------------------------------------------------------------------------

__bejson_core_atomic_backup() {
    local file_path="$1"
    [[ ! -f "$file_path" ]] && return 0
    local backup_path="${file_path}.backup.$(date +%Y%m%d_%H%M%S).$$"
    cp -p "$file_path" "$backup_path" 2>/dev/null || return $E_CORE_BACKUP_FAILED
    echo "$backup_path"
    return 0
}

__bejson_core_restore_backup() {
    local file_path="$1"
    local backup_path="$2"
    [[ -f "$backup_path" ]] && mv "$backup_path" "$file_path" 2>/dev/null
}

bejson_core_atomic_write() {
    local file_path="$1"
    local content="$2"
    local create_backup="${3:-true}"
    local backup_path=""

    if [[ "$create_backup" == "true" ]]; then
        backup_path=$(__bejson_core_atomic_backup "$file_path") || return $?
    fi

    local target_dir=$(dirname "$file_path")
    mkdir -p "$target_dir"
    local temp_file="${target_dir}/.bejson_$$.tmp"

    printf '%s' "$content" > "$temp_file" 2>/dev/null || {
        [[ -n "$backup_path" ]] && __bejson_core_restore_backup "$file_path" "$backup_path"
        return $E_CORE_WRITE_FAILED
    }

    sync "$temp_file" 2>/dev/null || true
    mv "$temp_file" "$file_path" 2>/dev/null || {
        cp -p "$temp_file" "$file_path" 2>/dev/null && rm -f "$temp_file" || {
            [[ -n "$backup_path" ]] && __bejson_core_restore_backup "$file_path" "$backup_path"
            return $E_CORE_WRITE_FAILED
        }
    }
    sync "$(dirname "$file_path")" 2>/dev/null || true
    return 0
}

bejson_core_load_file() {
    local file_path="$1"
    if [[ ! -f "$file_path" ]]; then
        return $E_CORE_FIELD_NOT_FOUND
    fi
    cat "$file_path"
}

#-------------------------------------------------------------------------------
# FIELD & RECORD OPERATIONS
#-------------------------------------------------------------------------------

bejson_core_get_field_index() {
    local doc="$1"
    local field_name="$2"
    echo "$doc" | jq --arg fn "$field_name" '.Fields | map(.name) | index($fn) // -1'
}

bejson_core_get_record_count() {
    local doc="$1"
    echo "$doc" | jq '.Values | length'
}

bejson_core_add_record() {
    local doc="$1"
    local values_json="$2"
    echo "$doc" | jq --argjson row "$values_json" '.Values += [$row]'
}

bejson_core_remove_record() {
    local doc="$1"
    local index="$2"
    echo "$doc" | jq --argjson idx "$index" 'del(.Values[$idx])'
}

bejson_core_update_field() {
    local doc="$1"
    local rec_idx="$2"
    local field_name="$3"
    local new_val="$4"
    local f_idx=$(bejson_core_get_field_index "$doc" "$field_name")
    if [[ "$f_idx" == "-1" ]]; then return $E_CORE_FIELD_NOT_FOUND; fi
    echo "$doc" | jq --argjson ri "$rec_idx" --argjson fi "$f_idx" --arg nv "$new_val" '(.Values[$ri][$fi]) = $nv'
}

#-------------------------------------------------------------------------------
# QUERY & SORT
#-------------------------------------------------------------------------------

bejson_core_filter_rows() {
    local doc="$1"
    local field_name="$2"
    local value="$3"
    local f_idx=$(bejson_core_get_field_index "$doc" "$field_name")
    if [[ "$f_idx" == "-1" ]]; then return $E_CORE_FIELD_NOT_FOUND; fi
    echo "$doc" | jq --argjson fi "$f_idx" --arg val "$value" '.Values | map(select(.[$fi] == $val))'
}

bejson_core_sort_by_field() {
    local doc="$1"
    local field_name="$2"
    local ascending="${3:-true}"
    local f_idx=$(bejson_core_get_field_index "$doc" "$field_name")
    if [[ "$f_idx" == "-1" ]]; then return $E_CORE_FIELD_NOT_FOUND; fi
    if [[ "$ascending" == "true" ]]; then
        echo "$doc" | jq --argjson fi "$f_idx" '.Values |= sort_by(.[$fi])'
    else
        echo "$doc" | jq --argjson fi "$f_idx" '.Values |= (sort_by(.[$fi]) | reverse)'
    fi
}

# Export functions
export -f bejson_core_atomic_write
export -f bejson_core_load_file
export -f bejson_core_get_field_index
export -f bejson_core_get_record_count
export -f bejson_core_add_record
export -f bejson_core_remove_record
export -f bejson_core_update_field
export -f bejson_core_filter_rows
export -f bejson_core_sort_by_field