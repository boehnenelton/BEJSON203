#!/bin/bash
# Library:      lib_bejson_schema.sh
# Family:       Core
# Jurisdiction: ["BEJSON_LIBRARIES", "SH"]
# Status:       OFFICIAL
# Author:       Elton Boehnen
# Version:      2.0.1 OFFICIAL
# MFDB Version: 1.31
# Format_Creator: Elton Boehnen
# Date:         2026-05-21
# Description:  Schema management for Shell using jq.

# Depends on lib_bejson_core.sh for jq wrappers

function bejson_schema_extract() {
    local input_file="$1"
    # Extract all except Values, set Values to []
    jq 'del(.Values) | .Values = []' "$input_file"
}

function bejson_schema_validate_against() {
    local doc_file="$1"
    local schema_file="$2"
    
    # 1. Check Format_Version
    local doc_ver=$(jq -r '.Format_Version' "$doc_file")
    local sch_ver=$(jq -r '.Format_Version' "$schema_file")
    if [ "$doc_ver" != "$sch_ver" ]; then
        echo "FAIL: Version mismatch (Doc: $doc_ver, Schema: $sch_ver)"
        return 1
    fi
    
    # 2. Check Fields count
    local doc_f_count=$(jq '.Fields | length' "$doc_file")
    local sch_f_count=$(jq '.Fields | length' "$schema_file")
    if [ "$doc_f_count" -ne "$sch_f_count" ]; then
        echo "FAIL: Field count mismatch (Doc: $doc_f_count, Schema: $sch_f_count)"
        return 1
    fi
    
    # 3. Deep check fields structure (names and types)
    local doc_f_sig=$(jq -c '.Fields | map({name, type, Record_Type_Parent})' "$doc_file")
    local sch_f_sig=$(jq -c '.Fields | map({name, type, Record_Type_Parent})' "$schema_file")
    if [ "$doc_f_sig" != "$sch_f_sig" ]; then
        echo "FAIL: Field signature mismatch."
        return 1
    fi
    
    echo "SUCCESS: Document matches schema."
    return 0
}

function bejson_schema_infer() {
    local record_type="$1"
    local fields_json="$2" # Expected as JSON array string
    local version="${3:-104a}"
    
    jq -n \
        --arg rt "$record_type" \
        --arg ver "$version" \
        --arg creator "Elton Boehnen" \
        --argjson fields "$fields_json" \
        '{
            Format: "BEJSON",
            Format_Version: $ver,
            Format_Creator: $creator,
            Records_Type: [$rt],
            Fields: $fields,
            Values: []
        }'
}
