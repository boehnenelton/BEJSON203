# Library:      lib_bejson_list_validator.sh
# Family:       Core
# Version:      1.0.0 OFFICIAL

source "$(dirname "$BASH_SOURCE")/lib_bejson_validator.sh"

bejson_list_validator_validate() {
    local file="$1"
    bejson_validator_validate_file "$file" || return $?
    local ver=$(jq -r ".Format_Version" "$file")
    [[ "$ver" != "104a" ]] && return 4
    return 0
}
