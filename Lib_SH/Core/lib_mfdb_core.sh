# Library:      lib_mfdb_core.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.2 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-06-02
# Description:  Multi-file database orchestrator managing manifests and entity synchronization.
#
# CHANGELOG v2.0.2:
#   [SH3] Fixed: removed top-level `set -o nounset` to prevent polluting host script options.

# NOTE: set -o nounset intentionally omitted — library files must not modify
# global shell options; doing so breaks host scripts that source this file. (SH3)
set -o pipefail

# Source dependencies if not already loaded.
_MFDB_CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! declare -f bejson_core_atomic_write > /dev/null 2>&1; then
    # shellcheck source=./lib_bejson_core.sh
    source "${_MFDB_CORE_DIR}/lib_bejson_core.sh"
fi

if ! declare -f mfdb_validator_validate_manifest > /dev/null 2>&1; then
    # shellcheck source=./lib_mfdb_validator.sh
    source "${_MFDB_CORE_DIR}/lib_mfdb_validator.sh"
fi

#-------------------------------------------------------------------------------
# Error codes (50–79)
#-------------------------------------------------------------------------------

[[ -v E_MFDB_CORE_MANIFEST_NOT_FOUND ]] || readonly E_MFDB_CORE_MANIFEST_NOT_FOUND=50
[[ -v E_MFDB_CORE_ENTITY_NOT_FOUND ]] || readonly E_MFDB_CORE_ENTITY_NOT_FOUND=51
[[ -v E_MFDB_CORE_WRITE_FAILED ]] || readonly E_MFDB_CORE_WRITE_FAILED=52
[[ -v E_MFDB_CORE_CREATE_FAILED ]] || readonly E_MFDB_CORE_CREATE_FAILED=53
[[ -v E_MFDB_CORE_INVALID_OPERATION ]] || readonly E_MFDB_CORE_INVALID_OPERATION=54
[[ -v E_MFDB_CORE_INDEX_OUT_OF_BOUNDS ]] || readonly E_MFDB_CORE_INDEX_OUT_OF_BOUNDS=55
[[ -v E_MFDB_CORE_ARCHIVE_ERROR ]] || readonly E_MFDB_CORE_ARCHIVE_ERROR=70
[[ -v E_MFDB_CORE_MOUNT_CONFLICT ]] || readonly E_MFDB_CORE_MOUNT_CONFLICT=71

#-------------------------------------------------------------------------------
# MFDBArchive (v1.2 Feature)
#-------------------------------------------------------------------------------

# mfdb_archive_mount <archive_path> <target_dir> [force]
# Extracts archive to workspace and creates session lock.
mfdb_archive_mount() {
    local archive_path="$1"
    local target_dir="$2"
    local force="${3:-false}"

    if [[ ! -f "$archive_path" ]]; then
        echo "ERROR: Archive not found: $archive_path" >&2
        return $E_MFDB_CORE_ARCHIVE_ERROR
    fi

    local lock_file="$target_dir/.mfdb_lock"
    if [[ -f "$lock_file" && "$force" != "true" ]]; then
        local old_pid
        old_pid=$(jq -r '.pid' "$lock_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "ERROR: Workspace $target_dir is locked by active PID $old_pid" >&2
            return $E_MFDB_CORE_MOUNT_CONFLICT
        fi
    fi

    mkdir -p "$target_dir"
    unzip -q -o "$archive_path" -d "$target_dir" || {
        echo "ERROR: Extraction failed for $archive_path" >&2
        return $E_MFDB_CORE_ARCHIVE_ERROR
    }

    if [[ ! -f "$target_dir/104a.mfdb.bejson" ]]; then
        echo "ERROR: Invalid MFDB Archive: manifest missing" >&2
        rm -rf "$target_dir"
        return $E_MFDB_CORE_ARCHIVE_ERROR
    fi

    local hash
    hash=$(sha256sum "$archive_path" | awk '{print $1}')
    
    jq -n \
        --arg pid "$$" \
        --arg path "$(realpath "$archive_path")" \
        --arg hash "$hash" \
        --arg time "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{pid: $pid|tonumber, archive_path: $path, original_hash: $hash, mounted_at: $time}' \
        > "$lock_file"

    echo "$(realpath "$target_dir/104a.mfdb.bejson")"
}

# mfdb_archive_commit <mount_dir> [archive_path]
# Repacks workspace into .mfdb.zip atomically.
mfdb_archive_commit() {
    local mount_dir="$1"
    local archive_path="${2:-}"
    local lock_file="$mount_dir/.mfdb_lock"

    if [[ ! -f "$lock_file" ]]; then
        echo "ERROR: No active mount session in $mount_dir" >&2
        return $E_MFDB_CORE_INVALID_OPERATION
    fi

    local dest
    if [[ -n "$archive_path" ]]; then
        dest="$archive_path"
    else
        dest=$(jq -r '.archive_path' "$lock_file")
    fi

    local tmp_zip
    tmp_zip="${TMPDIR:-/tmp}/mfdb_commit_$$.zip"
    rm -f "$tmp_zip"

    (cd "$mount_dir" && zip -r -q "$tmp_zip" . -x ".mfdb_lock") || {
        rm -f "$tmp_zip"
        echo "ERROR: Repack failed for $mount_dir" >&2
        return $E_MFDB_CORE_WRITE_FAILED
    }

    mv "$tmp_zip" "$dest" || {
        rm -f "$tmp_zip"
        echo "ERROR: Atomic swap failed for $dest" >&2
        return $E_MFDB_CORE_WRITE_FAILED
    }

    local new_hash
    new_hash=$(sha256sum "$dest" | awk '{print $1}')
    local tmp_lock
    tmp_lock=$(mktemp)
    jq --arg h "$new_hash" '.original_hash = $h' "$lock_file" > "$tmp_lock" && mv "$tmp_lock" "$lock_file"

    echo "$(realpath "$dest")"
}

# mfdb_archive_unmount <mount_dir> [cleanup]
mfdb_archive_unmount() {
    local mount_dir="$1"
    local cleanup="${2:-true}"
    local lock_file="$mount_dir/.mfdb_lock"

    [[ -f "$lock_file" ]] && rm -f "$lock_file"
    [[ "$cleanup" == "true" && -d "$mount_dir" ]] && rm -rf "$mount_dir"
}

#-------------------------------------------------------------------------------
# Discovery
#-------------------------------------------------------------------------------

# mfdb_core_discover <file_path>
# Prints: 'manifest', 'entity', 'archive', or 'standalone'
mfdb_core_discover() {
    local file_path="$1"

    if [[ ! -f "$file_path" ]]; then
        echo "ERROR: File not found: $file_path" >&2
        return $E_MFDB_CORE_MANIFEST_NOT_FOUND
    fi

    if [[ "$file_path" == *".mfdb.zip" ]]; then
        echo "archive"
        return 0
    fi

    local version filename
    version="$(jq -r '.Format_Version // empty' "$file_path" 2>/dev/null)"
    filename="$(basename "$file_path")"

    if [[ "$version" == "104a" && "$filename" == *".mfdb.bejson" ]]; then
        echo "manifest"
    elif [[ "$version" == "104" ]]; then
        local ph
        ph="$(jq -r '.Parent_Hierarchy // empty' "$file_path" 2>/dev/null)"
        if [[ -n "$ph" ]]; then
            echo "entity"
        else
            echo "standalone"
        fi
    else
        echo "standalone"
    fi
}

#-------------------------------------------------------------------------------
# Internal helpers
#-------------------------------------------------------------------------------

__mfdb_core_resolve() {
    local manifest_path="$1"
    local file_path_rel="$2"
    local manifest_dir
    manifest_dir="$(cd "$(dirname "$manifest_path")" && pwd)"
    realpath -m "$manifest_dir/$file_path_rel" 2>/dev/null || echo "$manifest_dir/$file_path_rel"
}

__mfdb_field_index() {
    local file_path="$1"
    local field_name="$2"
    local doc
    doc=$(cat "$file_path")
    bejson_core_get_field_index "$doc" "$field_name"
}

__mfdb_core_en_idx() {
    __mfdb_field_index "$1" "entity_name"
}

__mfdb_core_fp_idx() {
    __mfdb_field_index "$1" "file_path"
}

__mfdb_core_get_file_path() {
    local manifest_path="$1"
    local entity_name="$2"
    local en_idx fp_idx
    en_idx="$(__mfdb_core_en_idx "$manifest_path")"
    fp_idx="$(__mfdb_core_fp_idx "$manifest_path")"
    jq -r --argjson ei "$en_idx" --argjson fi "$fp_idx" --arg en "$entity_name" \
        '.Values[] | select(.[$ei] == $en) | .[$fi] // empty' \
        "$manifest_path" 2>/dev/null | head -n1
}

#-------------------------------------------------------------------------------
# Dependency check
#-------------------------------------------------------------------------------

mfdb_core_check_dependencies() {
    mfdb_validator_check_dependencies || return $?
    if ! declare -f bejson_core_atomic_write > /dev/null 2>&1; then
        echo "ERROR: lib_bejson_core.sh must be sourced before lib_mfdb_core.sh" >&2
        return 1
    fi
    for cmd in unzip zip sha256sum; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "ERROR: Required command '$cmd' not found" >&2
            return 1
        fi
    done
    return 0
}

#-------------------------------------------------------------------------------
# Read operations
#-------------------------------------------------------------------------------

mfdb_core_load_manifest() {
    local manifest_path="$1"
    if ! mfdb_validator_validate_manifest "$manifest_path"; then
        echo "ERROR: Manifest validation failed: $manifest_path" >&2
        return $E_MFDB_CORE_MANIFEST_NOT_FOUND
    fi
    jq -r '.Values[] | @tsv' "$manifest_path" 2>/dev/null
}

mfdb_core_list_entities() {
    local manifest_path="$1"
    local en_idx
    en_idx="$(__mfdb_core_en_idx "$manifest_path")"
    jq -r --argjson ei "$en_idx" '.Values[] | .[$ei] // empty' "$manifest_path" 2>/dev/null
}

mfdb_core_load_entity() {
    local manifest_path="$1"
    local entity_name="$2"
    local file_path_rel
    file_path_rel="$(__mfdb_core_get_file_path "$manifest_path" "$entity_name")"
    if [[ -z "$file_path_rel" ]]; then
        echo "ERROR: Entity '$entity_name' not found in manifest" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    local resolved
    resolved="$(__mfdb_core_resolve "$manifest_path" "$file_path_rel")"
    if [[ ! -f "$resolved" ]]; then
        echo "ERROR: Entity file not found: $resolved" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    jq -r '[.Fields[].name] | @tsv' "$resolved" 2>/dev/null
    jq -r '.Values[] | @tsv' "$resolved" 2>/dev/null
}

mfdb_core_get_entity_path() {
    local manifest_path="$1"
    local entity_name="$2"
    local file_path_rel
    file_path_rel="$(__mfdb_core_get_file_path "$manifest_path" "$entity_name")"
    if [[ -z "$file_path_rel" ]]; then
        echo "ERROR: Entity '$entity_name' not found in manifest" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    __mfdb_core_resolve "$manifest_path" "$file_path_rel"
}

mfdb_core_get_stats() {
    local manifest_path="$1"
    local db_name schema_version
    db_name="$(jq -r '.DB_Name // "N/A"' "$manifest_path" 2>/dev/null)"
    schema_version="$(jq -r '.Schema_Version // "N/A"' "$manifest_path" 2>/dev/null)"
    echo "=== MFDB Stats ==="
    echo "DB Name        : $db_name"
    echo "Schema Version : $schema_version"
    echo "Manifest       : $manifest_path"
    echo ""
    local en_idx fp_idx
    en_idx="$(__mfdb_core_en_idx "$manifest_path")"
    fp_idx="$(__mfdb_core_fp_idx "$manifest_path")"
    local entity_count=0
    while IFS=$'\t' read -r entity_name file_path_rel; do
        entity_count=$((entity_count + 1))
        local resolved
        resolved="$(__mfdb_core_resolve "$manifest_path" "$file_path_rel")"
        local rec_count="?"
        if [[ -f "$resolved" ]]; then
            rec_count="$(jq -r '.Values | length' "$resolved" 2>/dev/null)"
        fi
        printf "  %-24s  %-36s  records: %s\n" "$entity_name" "$file_path_rel" "$rec_count"
    done < <(jq -r --argjson ei "$en_idx" --argjson fi "$fp_idx" \
        '.Values[] | [.[$ei] // "null", .[$fi] // "null"] | @tsv' \
        "$manifest_path" 2>/dev/null)
    echo ""
    echo "Total entities : $entity_count"
}

#-------------------------------------------------------------------------------
# Write operations
#-------------------------------------------------------------------------------

mfdb_core_add_entity_record() {
    local manifest_path="$1"
    local entity_name="$2"
    local json_values_array="$3"
    local file_path_rel
    file_path_rel="$(__mfdb_core_get_file_path "$manifest_path" "$entity_name")"
    if [[ -z "$file_path_rel" ]]; then
        echo "ERROR: Entity '$entity_name' not found in manifest" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    local resolved
    resolved="$(__mfdb_core_resolve "$manifest_path" "$file_path_rel")"
    if [[ ! -f "$resolved" ]]; then
        echo "ERROR: Entity file not found: $resolved" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    if ! echo "$json_values_array" | jq -e 'if type == "array" then true else error end' > /dev/null 2>&1; then
        echo "ERROR: json_values_array must be a JSON array string" >&2
        return $E_MFDB_CORE_INVALID_OPERATION
    fi
    local tmp_file
    tmp_file="$(mktemp "${resolved}.tmp.XXXXXX")"
    if ! jq --argjson row "$json_values_array" '.Values += [$row]' "$resolved" > "$tmp_file" 2>/dev/null; then
        rm -f "$tmp_file"
        echo "ERROR: Failed to append record to $resolved" >&2
        return $E_MFDB_CORE_WRITE_FAILED
    fi
    mv "$tmp_file" "$resolved"
    mfdb_core_sync_manifest_count "$manifest_path" "$entity_name"
}

mfdb_core_remove_entity_record() {
    local manifest_path="$1"
    local entity_name="$2"
    local record_index="$3"
    local file_path_rel
    file_path_rel="$(__mfdb_core_get_file_path "$manifest_path" "$entity_name")"
    if [[ -z "$file_path_rel" ]]; then
        echo "ERROR: Entity '$entity_name' not found in manifest" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    local resolved
    resolved="$(__mfdb_core_resolve "$manifest_path" "$file_path_rel")"
    if [[ ! -f "$resolved" ]]; then
        echo "ERROR: Entity file not found: $resolved" >&2
        return $E_MFDB_CORE_ENTITY_NOT_FOUND
    fi
    local rec_count
    rec_count="$(jq -r '.Values | length' "$resolved" 2>/dev/null)"
    if [[ "$record_index" -lt 0 || "$record_index" -ge "$rec_count" ]]; then
        echo "ERROR: Record index $record_index is out of bounds (count: $rec_count)" >&2
        return $E_MFDB_CORE_INDEX_OUT_OF_BOUNDS
    fi
    local tmp_file
    tmp_file="$(mktemp "${resolved}.tmp.XXXXXX")"
    if ! jq --argjson ri "$record_index" 'del(.Values[$ri])' "$resolved" > "$tmp_file" 2>/dev/null; then
        rm -f "$tmp_file"
        echo "ERROR: Failed to remove record $record_index from $resolved" >&2
        return $E_MFDB_CORE_WRITE_FAILED
    fi
    mv "$tmp_file" "$resolved"
    mfdb_core_sync_manifest_count "$manifest_path" "$entity_name"
}

#-------------------------------------------------------------------------------
# Manifest sync
#-------------------------------------------------------------------------------

mfdb_core_sync_manifest_count() {
    local manifest_path="$1"
    local entity_name="$2"
    local file_path_rel
    file_path_rel="$(__mfdb_core_get_file_path "$manifest_path" "$entity_name")"
    [[ -z "$file_path_rel" ]] && return $E_MFDB_CORE_ENTITY_NOT_FOUND
    local resolved
    resolved="$(__mfdb_core_resolve "$manifest_path" "$file_path_rel")"
    [[ ! -f "$resolved" ]] && return $E_MFDB_CORE_ENTITY_NOT_FOUND
    local actual_count
    actual_count="$(jq -r '.Values | length' "$resolved" 2>/dev/null)"
    local en_idx rc_idx
    en_idx="$(__mfdb_core_en_idx "$manifest_path")"
    rc_idx="$(__mfdb_field_index "$manifest_path" "record_count")"
    [[ "$rc_idx" == "-1" ]] && return 0
    local tmp_file
    tmp_file="$(mktemp "${manifest_path}.tmp.XXXXXX")"
    if ! jq --argjson ei "$en_idx" --argjson ri "$rc_idx" \
            --arg en "$entity_name" --argjson count "$actual_count" \
            '(.Values[] | select(.[$ei] == $en) | .[$ri]) = $count' \
            "$manifest_path" > "$tmp_file" 2>/dev/null; then
        rm -f "$tmp_file"
        return $E_MFDB_CORE_WRITE_FAILED
    fi
    mv "$tmp_file" "$manifest_path"
    echo "$actual_count"
}

mfdb_core_sync_all_counts() {
    local manifest_path="$1"
    while IFS= read -r entity_name; do
        local count
        count="$(mfdb_core_sync_manifest_count "$manifest_path" "$entity_name")"
        printf "%-24s  %s records\n" "$entity_name" "$count"
    done < <(mfdb_core_list_entities "$manifest_path")
}

#-------------------------------------------------------------------------------
# Database creation
#-------------------------------------------------------------------------------

mfdb_core_create_entity_file() {
    local manifest_path="$1"
    local entity_name="$2"
    local fields_json="$3"
    local description="${4:-}"
    local primary_key="${5:-}"
    local schema_version="${6:-1.0}"
    local file_path_rel="${7:-}"
    if [[ -z "$file_path_rel" ]]; then
        file_path_rel="data/$(echo "$entity_name" | tr '[:upper:]' '[:lower:]').bejson"
    fi
    local manifest_dir resolved entity_dir rel_to_manifest
    manifest_dir="$(cd "$(dirname "$manifest_path")" && pwd)"
    resolved="$(realpath -m "$manifest_dir/$file_path_rel" 2>/dev/null || echo "$manifest_dir/$file_path_rel")"
    entity_dir="$(dirname "$resolved")"
    mkdir -p "$entity_dir"
    rel_to_manifest="$(realpath --relative-to="$entity_dir" "$manifest_path" 2>/dev/null || echo "../$(basename "$manifest_path")")"
    local tmp_entity
    tmp_entity="$(mktemp "${resolved}.tmp.XXXXXX")"
    jq -n \
        --arg en "$entity_name" \
        --arg ph "$rel_to_manifest" \
        --argjson fields "$fields_json" \
        '{
            "Format":           "BEJSON",
            "Format_Version":   "104",
            "Format_Creator":   "Elton Boehnen",
            "Parent_Hierarchy": $ph,
            "Records_Type":     [$en],
            "Fields":           $fields,
            "Values":           []
        }' > "$tmp_entity" 2>/dev/null && mv "$tmp_entity" "$resolved"
    local en_idx fp_idx
    en_idx="$(__mfdb_core_en_idx "$manifest_path")"
    fp_idx="$(__mfdb_core_fp_idx "$manifest_path")"
    local new_row_json
    new_row_json="$(jq -r \
        --arg en "$entity_name" \
        --arg fp "$file_path_rel" \
        --arg desc "${description:-null}" \
        --arg pk "${primary_key:-null}" \
        --arg sv "$schema_version" \
        '[.Fields[].name] | map(
            if . == "entity_name"    then $en
            elif . == "file_path"    then $fp
            elif . == "description"  then (if $desc == "null" then null else $desc end)
            elif . == "record_count" then 0
            elif . == "schema_version" then $sv
            elif . == "primary_key"  then (if $pk == "null" then null else $pk end)
            else null
            end
        )' "$manifest_path" 2>/dev/null)"
    local tmp_manifest
    tmp_manifest="$(mktemp "${manifest_path}.tmp.XXXXXX")"
    jq --argjson row "$new_row_json" '.Values += [$row]' "$manifest_path" > "$tmp_manifest" && mv "$tmp_manifest" "$manifest_path"
    echo "$resolved"
}

mfdb_core_create_database() {
    local root_dir="$1"
    local db_name="$2"
    local db_description="${3:-}"
    local entities_json="$4"
    local schema_version="${5:-1.0.0}"
    local author="${6:-Elton Boehnen}"
    mkdir -p "$root_dir"
    local manifest_path="$root_dir/104a.mfdb.bejson"
    local created_at
    created_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")"
    # Build manifest Values from entities_json.
    local manifest_values_json
    manifest_values_json="$(echo "$entities_json" | jq -c \
        '[.[] | [
            .name,
            (.file_path // ("data/" + (.name | ascii_downcase) + ".bejson")),
            (.description // null),
            0,
            (.schema_version // "1.0"),
            (.primary_key // null)
        ]]')"

    local tmp_manifest
    tmp_manifest="$(mktemp "${manifest_path}.tmp.XXXXXX")"

    if ! jq -n \
        --arg db_name "$db_name" \
        --arg db_desc "$db_description" \
        --arg sv "$schema_version" \
        --arg author "$author" \
        --arg created_at "$created_at" \
        --argjson values "$manifest_values_json" \
        '{
            "Format":          "BEJSON",
            "Format_Version":  "104a",
            "Format_Creator":  "Elton Boehnen",
            "MFDB_Version":    "1.31",
            "DB_Name":         $db_name,
            "DB_Description":  $db_desc,
            "Schema_Version":  $sv,
            "Author":          $author,
            "Created_At":      $created_at,
            "Records_Type":    ["mfdb"],
            "Fields": [
                {"name":"entity_name",    "type":"string"},
                {"name":"file_path",      "type":"string"},
                {"name":"description",    "type":"string"},
                {"name":"record_count",   "type":"integer"},
                {"name":"schema_version", "type":"string"},
                {"name":"primary_key",    "type":"string"}
            ],
            "Values": $values
        }' > "$tmp_manifest"; then
        rm -f "$tmp_manifest"
        echo "ERROR: Failed to generate manifest JSON" >&2
        return $E_MFDB_CORE_CREATE_FAILED
    fi

    mv "$tmp_manifest" "$manifest_path"

    local entity_count
    entity_count="$(echo "$entities_json" | jq -r 'length')"
    for (( i=0; i<entity_count; i++ )); do
        local ename fp_rel efields
        ename="$(echo "$entities_json" | jq -r ".[$i].name" 2>/dev/null)"
        fp_rel="$(echo "$entities_json" | jq -r ".[$i].file_path // (\"data/\" + (.[$i].name | ascii_downcase) + \".bejson\")" 2>/dev/null)"
        efields="$(echo "$entities_json" | jq -c ".[$i].fields" 2>/dev/null)"
        local resolved entity_dir rel_to_manifest
        resolved="$(realpath -m "$root_dir/$fp_rel" 2>/dev/null || echo "$root_dir/$fp_rel")"
        entity_dir="$(dirname "$resolved")"
        mkdir -p "$entity_dir"
        rel_to_manifest="$(realpath --relative-to="$entity_dir" "$manifest_path" 2>/dev/null || echo "../$(basename "$manifest_path")")"
        local tmp_entity
        tmp_entity="$(mktemp "${resolved}.tmp.XXXXXX")"
        jq -n \
            --arg en "$ename" \
            --arg ph "$rel_to_manifest" \
            --argjson fields "$efields" \
            '{
                "Format":           "BEJSON",
                "Format_Version":   "104",
                "Format_Creator":   "Elton Boehnen",
                "Parent_Hierarchy": $ph,
                "Records_Type":     [$en],
                "Fields":           $fields,
                "Values":           []
            }' > "$tmp_entity" 2>/dev/null && mv "$tmp_entity" "$resolved"
    done
    echo "$manifest_path"
}

# Export functions
export -f mfdb_archive_mount
export -f mfdb_archive_commit
export -f mfdb_archive_unmount
export -f mfdb_core_check_dependencies
export -f mfdb_core_discover
export -f mfdb_core_load_manifest
export -f mfdb_core_list_entities
export -f mfdb_core_load_entity
export -f mfdb_core_get_entity_path
export -f mfdb_core_get_stats
export -f mfdb_core_add_entity_record
export -f mfdb_core_remove_entity_record
export -f mfdb_core_sync_manifest_count
export -f mfdb_core_sync_all_counts
export -f mfdb_core_create_entity_file
export -f mfdb_core_create_database