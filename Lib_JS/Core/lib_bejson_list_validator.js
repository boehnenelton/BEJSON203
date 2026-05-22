/**
 * Library:      lib_bejson_list_validator.js
 * Family:       Core
 * Version:      1.0.0 OFFICIAL
 * Description:  JS implementation of the Hierarchical List Validator.
 */
'use strict';

const StandardValidator = (typeof require !== 'undefined') 
  ? require('./lib_bejson_validator.js') 
  : (window.BEJSON_VALIDATOR || {});

const ListValidator = {
    validate: function(jsonString) {
        if (!StandardValidator.bejson_validator_validate_string(jsonString)) {
            return { is_valid: false, errors: StandardValidator.bejson_validator_get_errors() };
        }
        const doc = JSON.parse(jsonString);
        if (doc.Format_Version !== '104a') return { is_valid: false, errors: ['Must be 104a'] };
        const idIdx = doc.Fields.findIndex(f => f.name === 'id');
        const pidIdx = doc.Fields.findIndex(f => f.name === 'parent_id');
        if (idIdx === -1 || pidIdx === -1) return { is_valid: false, errors: ['Missing core fields'] };
        const ids = new Set();
        const parentRefs = new Map();
        for (let row of doc.Values) {
            ids.add(row[idIdx]);
            if (row[pidIdx]) parentRefs.set(row[idIdx], row[pidIdx]);
        }
        for (let [uid, pid] of parentRefs) {
            if (!ids.has(pid)) return { is_valid: false, errors: ['Orphan detected'] };
        }
        return { is_valid: true, errors: [] };
    }
};

if (typeof module !== 'undefined') module.exports = ListValidator;
