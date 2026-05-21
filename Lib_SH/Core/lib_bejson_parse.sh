# Library:      lib_bejson_parse.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-05-18
# Description:  Rapid indexing and retrieval engine for dense tabular data.

# 104db schemas. Sources lib_bejson_core.sh and lib_bejson_validator.sh.
# Author:      Elton Boehnen
# Version:     "2.0.1 OFFICIAL",
# Compatibility: Bash 4.0+, Termux/Android
# Dependencies:  lib_bejson_core.sh, lib_bejson_validator.sh, jq, zip

set -o pipefail
set -o nounset

# ------------------------------------------------------------------
# Source BEJSON ecosystem — core + validator
# ------------------------------------------------------------------
BEJSON_PARSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$BEJSON_PARSE_DIR/lib_bejson_core.sh" ]]; then
    source "$BEJSON_PARSE_DIR/lib_bejson_core.sh"
fi

if [[ -f "$BEJSON_PARSE_DIR/lib_bejson_validator.sh" ]]; then
    source "$BEJSON_PARSE_DIR/lib_bejson_validator.sh"
fi

# Default output directory
BEJSON_PARSE_DEFAULT_OUT="${BEJSON_PARSE_DIR}/output"

# Globals populated by bejson_extract_data
BEJSON_PROJECT_NAME="My_Project"
BEJSON_FILES_NAMES=()
BEJSON_FILES_CONTENTS=()

# ------------------------------------------------------------------
# PARSER CORE
# ------------------------------------------------------------------

bejson_parse_json() {
    local text="$1"

    # 1. Enforce optimal parser (jq >= 1.6)
    if declare -f bejson_validator_check_dependencies >/dev/null 2>&1; then
        bejson_validator_check_dependencies || return 1
    elif ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq is required for bejson_parse_json" >&2
        return 1
    fi

    # 2. Extract JSON using awk/sed to safely strip wrappers
    # First priority: Markdown blocks
    local clean
    clean=$(echo "$text" | awk '
        BEGIN { found=0 }
        /```json/ { found=1; next }
        /```/ && found { exit }
        found { print }
    ')

    # Second priority: Balanced braces heuristic (tr/sed)
    if [[ -z "$clean" ]] || ! echo "$clean" | jq '.' >/dev/null 2>&1; then
        clean=$(echo "$text" | tr '\n' '\f' | sed 's/^[^{]*//; s/}[^}]*$/}/' | tr '\f' '\n')
    fi

    # 3. Pipe to jq '.' for standard validation and extraction
    if echo "$clean" | jq '.' > /dev/null 2>&1; then
        echo "$clean" | jq '.'
        return 0
    fi

    # Final fallback for raw JSON
    if echo "$text" | jq '.' > /dev/null 2>&1; then
        echo "$text" | jq '.'
        return 0
    fi

    echo "ERROR: bejson_parse_json — could not parse JSON from input" >&2
    return 1
}

bejson_extract_data() {
    local json="$1"
    BEJSON_PROJECT_NAME="My_Project"
    BEJSON_FILES_NAMES=()
    BEJSON_FILES_CONTENTS=()

    _bejson_parse_get_project_name() {
        local j="$1"
        local result="My_Project"
        local cands=("zipfilename" "projectname" "containername")
        for cand in "${cands[@]}"; do
            local idx
            idx=$(echo "$j" | jq --arg c "$cand" '
                .Fields | to_entries[] |
                select((.value.name | ascii_downcase | gsub("[^a-z0-9]";"")) == $c) |
                .key
            ' 2>/dev/null | head -1)
            if [[ -n "$idx" ]]; then
                local val
                val=$(echo "$j" | jq -r --argjson i "$idx" '
                    .Values[] |
                    if (. | length) > $i then .[$i] else null end |
                    select(. != null and . != "") |
                    tostring
                ' 2>/dev/null | head -1)
                if [[ -n "$val" && "$val" != "null" ]]; then
                    result="$val"
                    break
                fi
            fi
        done
        echo "$result"
    }

    BEJSON_PROJECT_NAME=$( _bejson_parse_get_project_name "$json" )
    BEJSON_PROJECT_NAME=$(echo "$BEJSON_PROJECT_NAME" | sed 's/[<>:"\/\\|?*]/_/g')

    for i in $(seq 1 50); do
        local name_key="file${i}name"
        local cont_key="file${i}content"
        local name_idx cont_idx
        name_idx=$(echo "$json" | jq --arg k "$name_key" '
            .Fields | to_entries[] |
            select((.value.name | ascii_downcase | gsub("[^a-z0-9]";"")) == $k) |
            .key
        ' 2>/dev/null | head -1)
        cont_idx=$(echo "$json" | jq --arg k "$cont_key" '
            .Fields | to_entries[] |
            select((.value.name | ascii_downcase | gsub("[^a-z0-9]";"")) == $k) |
            .key
        ' 2>/dev/null | head -1)
        [[ -z "$name_idx" || -z "$cont_idx" ]] && continue
        local row_count=$(echo "$json" | jq '.Values | length')
        for r in $(seq 0 $(( row_count - 1 ))); do
            local fname fcont
            fname=$(echo "$json" | jq -r --argjson r "$r" --argjson ni "$name_idx" '.Values[$r][$ni] // empty | select(. != null and . != "")' 2>/dev/null)
            fcont=$(echo "$json" | jq -r --argjson r "$r" --argjson ci "$cont_idx" '.Values[$r][$ci] // empty | select(. != null and . != "")' 2>/dev/null)
            if [[ -n "$fname" && -n "$fcont" ]]; then
                BEJSON_FILES_NAMES+=("$fname")
                BEJSON_FILES_CONTENTS+=("$fcont")
            fi
        done
    done
    [[ ${#BEJSON_FILES_NAMES[@]} -eq 0 ]] && return 1
    return 0
}

bejson_save_files() {
    local proj="${1:-My_Project}"
    local base_dir="${2:-$BEJSON_PARSE_DEFAULT_OUT}"
    local overwrite="${3:-false}"
    mkdir -p "$base_dir" 2>/dev/null
    local target
    if [[ "$overwrite" == "true" ]]; then
        target="${base_dir}/${proj}"
    else
        target="${base_dir}/$(date +"%Y%m%d_%H%M%S")_${proj}"
    fi
    mkdir -p "$target" 2>/dev/null
    for i in $(seq 0 $(( ${#BEJSON_FILES_NAMES[@]} - 1 ))); do
        local fpath="${target}/${BEJSON_FILES_NAMES[$i]}"
        mkdir -p "$(dirname "$fpath")"
        printf '%s' "${BEJSON_FILES_CONTENTS[$i]}" > "$fpath"
    done
    sync "$target" 2>/dev/null || sync 2>/dev/null || true
    echo "{\"success\":true,\"path\":\"$target\",\"file_count\":${#BEJSON_FILES_NAMES[@]}}"
}

export -f bejson_parse_json
export -f bejson_extract_data
export -f bejson_save_files
