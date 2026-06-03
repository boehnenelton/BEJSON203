# Library:      lib_bejson_core.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.3 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-06-02
# Description:  Low-level primitive operations for BEJSON document manipulation.
#
# CHANGELOG v2.0.3:
#   [SH2] Fixed: bejson_core_update_field always wrote strings via --arg jq flag.
#         Now inspects field type and uses --argjson for integer/number/boolean fields.
#   [SH3] Fixed: removed top-level set -o nounset to avoid polluting host script options.
#   [SH6] Documented: sync || true pattern on SD card exFAT paths on Android.
#   [SH7] Added: resilient_lock_acquire/release (PID-verified locks, Policy Sec. 47).

#===============================================================================

#-------------------------------------------------------------------------------
# SAFETY & ERROR HANDLING
#-------------------------------------------------------------------------------

# NOTE: set -o nounset intentionally omitted — library files must not modify
# global shell options; doing so breaks host scripts that source this file. (SH3)
set -o pipefail

# Source the validator library and error registry (assumes same directory)
_CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$_CORE_DIR/lib_bejson_errors.sh" ]]; then
    # shellcheck source=./lib_bejson_errors.sh
    source "$_CORE_DIR/lib_bejson_errors.sh"
fi

if [[ -f "$_CORE_DIR/lib_bejson_validator.sh" ]]; then
    # shellcheck source=./lib_bejson_validator.sh
    source "$_CORE_DIR/lib_bejson_validator.sh"
fi

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

    # NOTE SH6: On Android exFAT SD card paths (/storage/<UUID>/...), sync(1) may be a
    # no-op or unavailable. The || true swallow is intentional — writes to SD have
    # weaker durability guarantees than internal storage on Android.
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

#-------------------------------------------------------------------------------
# MUTEX LOCKING (Policy Sec. 47)
#-------------------------------------------------------------------------------

resilient_lock_acquire() {
    local target="$1"
    local lock_dir="${target}.lockdir"
    local meta="${lock_dir}/lock_meta.json"
    local timeout="${2:-10}"
    local start
    start=$(date +%s)
    
    while true; do
        if mkdir "$lock_dir" 2>/dev/null; then
            # Lock acquired — write PID metadata
            printf '{"pid": %d, "timestamp": %d}\n' "$$" "$(date +%s)" > "$meta"
            return 0
        fi
        
        # Check for dead-process orphan
        if [[ -f "$meta" ]]; then
            local pid
            pid=$(jq -r '.pid // empty' "$meta" 2>/dev/null)
            if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
                # Safe reclamation: owner process is dead
                rm -rf "$lock_dir" 2>/dev/null
                continue
            fi
        fi
        
        if [[ $(($(date +%s) - start)) -ge $timeout ]]; then
            return 53  # E_MFDB_CORE_LOCK_FAILED
        fi
        sleep 0.2
    done
}

resilient_lock_release() {
    local target="$1"
    local lock_dir="${target}.lockdir"
    [[ -d "$lock_dir" ]] && rm -rf "$lock_dir" 2>/dev/null
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
    # FIX SH2: --arg always writes a JSON string. Inspect declared field type and use
    # --argjson when the field is not a string so integers/booleans/numbers round-trip
    # correctly. Falls back to --arg only for string-typed fields.
    local doc="$1"
    local rec_idx="$2"
    local field_name="$3"
    local new_val="$4"
    local f_idx
    f_idx=$(bejson_core_get_field_index "$doc" "$field_name")
    if [[ "$f_idx" == "-1" ]]; then return $E_CORE_FIELD_NOT_FOUND; fi

    local field_type
    field_type=$(echo "$doc" | jq -r --argjson fi "$f_idx" '.Fields[$fi].type // "string"')

    if [[ "$field_type" == "string" ]]; then
        echo "$doc" | jq --argjson ri "$rec_idx" --argjson fi "$f_idx" --arg nv "$new_val" '(.Values[$ri][$fi]) = $nv'
    else
        # Use --argjson so the value is written as the correct JSON type (number, boolean, etc.)
        echo "$doc" | jq --argjson ri "$rec_idx" --argjson fi "$f_idx" --argjson nv "$new_val" '(.Values[$ri][$fi]) = $nv'
    fi
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
export -f resilient_lock_acquire
export -f resilient_lock_release