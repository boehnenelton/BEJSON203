# Library:      lib_be_core.sh
# Family:       System
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-05-18
# Description:  BE-specific core system abstractions and utility wrappers.

# Get the root path of BECore dynamically
bec_core_get_root() {
    if [[ -n "${BEC_ROOT:-}" ]]; then
        echo "$BEC_ROOT"
        return 0
    fi
    # REMEDIATED: Use BEJSON_STORAGE_ROOT to avoid hardcoded absolute paths (Phase 1)
    local default_storage="${BEJSON_STORAGE_ROOT:-/storage/emulated/0}"
    local root_file="${SC_ROOT:-$default_storage/Brain-Container/BEJSON_Core}/Data/state/BEC_ROOT.txt"
    if [[ -f "$root_file" ]]; then
        cat "$root_file"
    else
        # Fallback if state not yet initialized
        echo "${SC_ROOT:-$default_storage/Brain-Container/BEJSON_Core}"
    fi
}

# Export BEC_ROOT if not set
bec_core_source_env() {
    if [[ -z "$BEC_ROOT" ]]; then
        export BEC_ROOT=$(bec_core_get_root)
    fi
}

# State Management - Save a key-value pair to a manager state file
bec_core_save_state() {
    local manager="$1" # "bash" or "python"
    local key="$2"
    local value="$3"
    local state_file="$(bec_core_get_root)/Data/state/${manager}_manager_state.txt"
    
    mkdir -p "$(dirname "$state_file")"
    touch "$state_file"
    
    if grep -q "^${key}=" "$state_file"; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$state_file"
    else
        echo "${key}=${value}" >> "$state_file"
    fi
}

# State Management - Load a value by key from a manager state file
bec_core_load_state() {
    local manager="$1"
    local key="$2"
    local state_file="$(bec_core_get_root)/Data/state/${manager}_manager_state.txt"
    
    if [[ -f "$state_file" ]]; then
        grep "^${key}=" "$state_file" | cut -d'=' -f2
    fi
}

export -f bec_core_get_root
export -f bec_core_source_env
export -f bec_core_save_state
export -f bec_core_load_state