/**
 * Library:      lib_bejson_validator.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Structural integrity checker for positional values and mandatory keys.
 */

'use strict';

// ---------------------------------------------------------------------------
// Error codes (mirror bash readonly values / Python constants)
// ---------------------------------------------------------------------------
const BEJSON_ERRORS = (typeof require !== 'undefined') 
  ? require('./lib_bejson_errors.js') 
  : (window.BEJSON_ERRORS || {});

const {
  E_INVALID_JSON,
  E_MISSING_MANDATORY_KEY,
  E_INVALID_FORMAT,
  E_INVALID_VERSION,
  E_INVALID_RECORDS_TYPE,
  E_INVALID_FIELDS,
  E_INVALID_VALUES,
  E_TYPE_MISMATCH,
  E_RECORD_LENGTH_MISMATCH,
  E_RESERVED_KEY_COLLISION,
  E_INVALID_RECORD_TYPE_PARENT,
  E_NULL_VIOLATION,
  E_FILE_NOT_FOUND,
  E_PERMISSION_DENIED,
  E_ATOMIC_WRITE_FAILED
} = BEJSON_ERRORS;

const VALID_VERSIONS    = new Set(['104', '104a', '104db']);
const MANDATORY_KEYS    = ['Format', 'Format_Version', 'Format_Creator', 'Records_Type', 'Fields', 'Values'];
const VALID_FIELD_TYPES = new Set(['string', 'integer', 'number', 'boolean', 'array', 'object']);

// ---------------------------------------------------------------------------
// Validation exception
// ---------------------------------------------------------------------------

class BEJSONValidationError extends Error {
  
  constructor(message, code) {
    super(message);
    this.name = 'BEJSONValidationError';
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// Validation state — mirrors bash globals / Python ValidationState
// ---------------------------------------------------------------------------

class ValidationState {
  constructor() {
    this.errors      = [];
    this.warnings    = [];
    this.currentFile = '';
  }

  
  reset() {
    this.errors      = [];
    this.warnings    = [];
    this.currentFile = '';
  }

  
  addError(message, location = '', context = '') {
    let entry = 'ERROR';
    if (location) entry += ` | Location: ${location}`;
    entry += ` | Message: ${message}`;
    if (context) entry += ` | Context: ${context}`;
    this.errors.push(entry);
  }

  
  addWarning(message, location = '') {
    let entry = 'WARNING';
    if (location) entry += ` | Location: ${location}`;
    entry += ` | Message: ${message}`;
    this.warnings.push(entry);
  }

  
  getErrors() { return [...this.errors]; }

  
  getWarnings() { return [...this.warnings]; }

  
  hasErrors() { return this.errors.length > 0; }

  
  hasWarnings() { return this.warnings.length > 0; }

  
  errorCount() { return this.errors.length; }

  
  warningCount() { return this.warnings.length; }
}

// Module-level default state (mirrors bash global arrays / Python _state)
const _state = new ValidationState();

// ---------------------------------------------------------------------------
// Convenience accessors that operate on the module-level state
// (mirror the exported bash / Python functions)
// ---------------------------------------------------------------------------

function bejson_validator_reset_state() {
  _state.reset();
}

function bejson_validator_get_errors() {
  return _state.getErrors();
}

function bejson_validator_get_warnings() {
  return _state.getWarnings();
}

function bejson_validator_has_errors() {
  return _state.hasErrors();
}

function bejson_validator_has_warnings() {
  return _state.hasWarnings();
}

function bejson_validator_error_count() {
  return _state.errorCount();
}

function bejson_validator_warning_count() {
  return _state.warningCount();
}

// ---------------------------------------------------------------------------
// Dependency check (no-op in JS — JSON is built-in)
// mirrors bejson_validator_check_dependencies
// ---------------------------------------------------------------------------


function bejson_validator_check_dependencies() {
  return true;
}

// ---------------------------------------------------------------------------
// JSON syntax validation
// mirrors bejson_validator_check_json_syntax
// ---------------------------------------------------------------------------


// ---------------------------------------------------------------------------
// Environment Abstraction Layer
// ---------------------------------------------------------------------------

const IO_PROVIDER = {
  readFile: (path) => {
    if (typeof require !== 'undefined') {
      try {
        const fs = require('fs');
        return fs.readFileSync(path, 'utf8');
      } catch (e) {
        throw new Error(`Node.js fs failed: ${e.message}`);
      }
    }
    throw new Error('File I/O not available in this environment');
  },
  exists: (path) => {
    if (typeof require !== 'undefined') {
      try {
        const fs = require('fs');
        return fs.existsSync(path);
      } catch (e) {
        return false;
      }
    }
    return false;
  }
};


function bejson_validator_check_json_syntax(input, isFile = false) {
  let text;

  if (isFile) {
    if (!IO_PROVIDER.exists(input)) {
      _state.addError(`File not found: ${input}`, 'File System');
      throw new BEJSONValidationError(`File not found: ${input}`, E_FILE_NOT_FOUND);
    }
    try {
      text = IO_PROVIDER.readFile(input);
      _state.currentFile = input;
    } catch (err) {
      _state.addError(`IO Error: ${err.message}`, 'File System');
      throw new BEJSONValidationError(`IO Error: ${err.message}`, E_FILE_NOT_FOUND);
    }
  } else {
    text = input;
  }

  if (typeof text === 'object' && text !== null) {
    return text; // already parsed
  }

  try {
    return JSON.parse(text);
  } catch (err) {
    _state.addError(`Invalid JSON syntax: ${err.message}`, 'JSON Parse');
    throw new BEJSONValidationError(`Invalid JSON syntax: ${err.message}`, E_INVALID_JSON);
  }
}

// ---------------------------------------------------------------------------
// Mandatory key validation
// mirrors bejson_validator_check_mandatory_keys
// ---------------------------------------------------------------------------


function bejson_validator_check_mandatory_keys(doc) {
  for (const key of MANDATORY_KEYS) {
    if (!(key in doc)) {
      _state.addError(`Missing mandatory top-level key: '${key}'`, 'Top-Level Keys');
      throw new BEJSONValidationError(`Missing mandatory key: ${key}`, E_MISSING_MANDATORY_KEY);
    }
  }

  if (doc['Format'] !== 'BEJSON') {
    _state.addError(
      `Invalid 'Format' value: Expected 'BEJSON', got '${doc['Format']}'`,
      'Top-Level Keys/Format',
    );
    throw new BEJSONValidationError('Invalid Format', E_INVALID_FORMAT);
  }

  const version = doc['Format_Version'] ?? '';

  if (!VALID_VERSIONS.has(version)) {
    _state.addError(
      `Invalid 'Format_Version': Expected '104', '104a', or '104db', got '${version}'`,
      'Top-Level Keys/Format_Version',
    );
    throw new BEJSONValidationError(`Invalid version: ${version}`, E_INVALID_VERSION);
  }

  if (typeof doc['Format_Creator'] !== 'string') {
    _state.addError("Invalid 'Format_Creator': Must be a string", 'Top-Level Keys/Format_Creator');
    throw new BEJSONValidationError('Invalid Format_Creator', E_INVALID_FORMAT);
  }

  const checks = [
    ['Records_Type', E_INVALID_RECORDS_TYPE, 'Top-Level Keys/Records_Type'],
    ['Fields',       E_INVALID_FIELDS,       'Top-Level Keys/Fields'],
    ['Values',       E_INVALID_VALUES,       'Top-Level Keys/Values'],
  ];
  for (const [key, code, section] of checks) {
    if (!Array.isArray(doc[key])) {
      _state.addError(`Invalid '${key}': Must be an array`, section);
      throw new BEJSONValidationError(`Invalid ${key}`, code);
    }
  }

  return version;
}

// ---------------------------------------------------------------------------
// Records_Type validation
// mirrors bejson_validator_check_records_type
// ---------------------------------------------------------------------------


function bejson_validator_check_records_type(doc, version) {
  const rt    = doc['Records_Type'];
  const count = rt.length;

  if (version === '104' || version === '104a') {
    if (count !== 1 || typeof rt[0] !== 'string') {
      _state.addError(
        `For BEJSON ${version}, 'Records_Type' must contain exactly one string. Found ${count} entries.`,
        'Records_Type',
      );
      throw new BEJSONValidationError('Bad Records_Type', E_INVALID_RECORDS_TYPE);
    }
  } else if (version === '104db') {
    if (count < 2) {
      _state.addError(
        `For BEJSON 104db, 'Records_Type' must contain two or more unique strings. Found ${count} entries.`,
        'Records_Type',
      );
      throw new BEJSONValidationError('Bad Records_Type', E_INVALID_RECORDS_TYPE);
    }
    const seen = new Set();
    for (let i = 0; i < rt.length; i++) {
      if (typeof rt[i] !== 'string') {
        _state.addError(`Records_Type[${i}] must be a string`, `Records_Type[${i}]`);
        throw new BEJSONValidationError('Bad Records_Type entry', E_INVALID_RECORDS_TYPE);
      }
      if (seen.has(rt[i])) {
        _state.addError(`Duplicate type '${rt[i]}' found in 'Records_Type'`, 'Records_Type');
        throw new BEJSONValidationError(`Duplicate Records_Type: ${rt[i]}`, E_INVALID_RECORDS_TYPE);
      }
      seen.add(rt[i]);
    }
  }
}

// ---------------------------------------------------------------------------
// Fields structure validation
// mirrors bejson_validator_check_fields_structure
// ---------------------------------------------------------------------------


function bejson_validator_check_fields_structure(doc, version) {
  const fields = doc['Fields'];
  if (!fields || fields.length === 0) {
    _state.addError("'Fields' array cannot be empty", 'Fields Array');
    throw new BEJSONValidationError('Empty Fields', E_INVALID_FIELDS);
  }

  const seenNames = new Set();
  for (let i = 0; i < fields.length; i++) {
    const fieldDef = fields[i];
    if (typeof fieldDef !== 'object' || fieldDef === null || Array.isArray(fieldDef)) {
      _state.addError(`Field at index ${i} must be an object`, `Fields[${i}]`);
      throw new BEJSONValidationError(`Field ${i} not an object`, E_INVALID_FIELDS);
    }

    const name = fieldDef['name'];
    if (typeof name !== 'string') {
      _state.addError(
        `Field at index ${i}: Missing or invalid 'name' (must be string)`,
        `Fields[${i}]`,
      );
      throw new BEJSONValidationError(`Field ${i} bad name`, E_INVALID_FIELDS);
    }

    if (seenNames.has(name)) {
      _state.addError(`Duplicate field name '${name}' found in 'Fields' array`, `Fields[${i}]`);
      throw new BEJSONValidationError(`Duplicate field: ${name}`, E_INVALID_FIELDS);
    }
    seenNames.add(name);

    const ftype = fieldDef['type'];
    if (typeof ftype !== 'string' || !VALID_FIELD_TYPES.has(ftype)) {
      _state.addError(
        `Field '${name}' (index ${i}): Invalid type '${ftype}'. Valid: ${[...VALID_FIELD_TYPES].join(', ')}`,
        `Fields[${i}]`,
      );
      throw new BEJSONValidationError(`Field ${name} invalid type`, E_INVALID_FIELDS);
    }

    if (version === '104a' && (ftype === 'array' || ftype === 'object')) {
      _state.addError(
        `Field '${name}' (index ${i}): Type '${ftype}' not allowed in 104a.`,
        `Fields[${i}]`,
      );
      throw new BEJSONValidationError(`Field ${name} disallowed type for 104a`, E_INVALID_FIELDS);
    }
  }

  return fields.length;
}

// ---------------------------------------------------------------------------
// 104db Record_Type_Parent validation
// mirrors bejson_validator_check_record_type_parent
// ---------------------------------------------------------------------------


function bejson_validator_check_record_type_parent(doc) {
  const fields = doc['Fields'];
  const first  = fields[0] ?? {};
  if (!fields.length || first['name'] !== 'Record_Type_Parent' || first['type'] !== 'string') {
    _state.addError(
      `For BEJSON 104db, the first field must be {"name": "Record_Type_Parent", "type": "string"}. ` +
      `Found: ${JSON.stringify(first)}`,
      'Fields[0]',
    );
    throw new BEJSONValidationError('Bad Record_Type_Parent field', E_INVALID_RECORD_TYPE_PARENT);
  }

  const validTypes = new Set(doc['Records_Type']);
  for (let i = 0; i < doc['Values'].length; i++) {
    const record = doc['Values'][i];
    if (!Array.isArray(record)) {
      _state.addError(`Values[${i}] must be an array (record)`, `Values[${i}]`);
      throw new BEJSONValidationError(`Bad record at ${i}`, E_INVALID_VALUES);
    }
    const rtp = record[0] ?? null;
    if (!rtp) {
      _state.addError(
        `Record at 'Values' index ${i}: 'Record_Type_Parent' is missing or null`,
        `Values[${i}][0]`,
      );
      throw new BEJSONValidationError(`Missing RTP at ${i}`, E_INVALID_RECORD_TYPE_PARENT);
    }
    if (!validTypes.has(rtp)) {
      _state.addError(
        `Record at 'Values' index ${i}: 'Record_Type_Parent' value '${rtp}' ` +
        `does not match any declared type in 'Records_Type'`,
        `Values[${i}][0]`,
      );
      throw new BEJSONValidationError(`Invalid RTP '${rtp}' at ${i}`, E_INVALID_RECORD_TYPE_PARENT);
    }
  }
}

// ---------------------------------------------------------------------------
// Values validation
// mirrors bejson_validator_check_values
// ---------------------------------------------------------------------------


function _jsonType(value) {
  if (value === null)             return 'null';
  if (typeof value === 'boolean') return 'boolean';
  if (Number.isInteger(value))    return 'integer';
  if (typeof value === 'number')  return 'number';
  if (typeof value === 'string')  return 'string';
  if (Array.isArray(value))       return 'array';
  if (typeof value === 'object')  return 'object';
  return 'unknown';
}


function bejson_validator_check_values(doc, version, fieldsCount) {
  const values = doc['Values'];
  const fields = doc['Fields'];

  for (let i = 0; i < values.length; i++) {
    const record = values[i];
    if (!Array.isArray(record)) {
      _state.addError(`Values[${i}] must be an array (record)`, `Values[${i}]`);
      throw new BEJSONValidationError(`Bad record at ${i}`, E_INVALID_VALUES);
    }

    if (record.length !== fieldsCount) {
      _state.addError(
        `Record at 'Values' index ${i} has ${record.length} elements, ` +
        `but 'Fields' defines ${fieldsCount} fields.`,
        `Values[${i}]`,
      );
      throw new BEJSONValidationError(`Length mismatch at ${i}`, E_RECORD_LENGTH_MISMATCH);
    }

    const recordType = (version === '104db' && record.length > 0) ? record[0] : null;

    for (let j = 0; j < record.length; j++) {
      const value     = record[j];
      const fieldDef  = fields[j];
      const fieldName = fieldDef['name'];
      const fieldType = fieldDef['type'];
      const fieldParent = fieldDef['Record_Type_Parent'] ?? '';

      // 104db applicability: field not for this record type → must be null
      if (version === '104db' && fieldParent && j > 0) {
        if (fieldParent !== recordType) {
          if (value !== null) {
            _state.addError(
              `Record at 'Values' index ${i} (type '${recordType}'), ` +
              `field '${fieldName}' (index ${j}): not applicable to this type; must be null.`,
              `Values[${i}][${j}]`,
            );
            throw new BEJSONValidationError('Null violation', E_NULL_VIOLATION);
          }
          continue;
        }
      }

      if (value === null) continue;

      const vtype = _jsonType(value);
      let typeValid = false;

      switch (fieldType) {
        case 'string':
          typeValid = typeof value === 'string';
          break;
        case 'integer':
          typeValid = Number.isInteger(value) && typeof value !== 'boolean';
          break;
        case 'number':
          typeValid = typeof value === 'number' && typeof value !== 'boolean';
          break;
        case 'boolean':
          typeValid = typeof value === 'boolean';
          break;
        case 'array':
          typeValid = Array.isArray(value);
          break;
        case 'object':
          typeValid = typeof value === 'object' && !Array.isArray(value);
          break;
      }

      if (!typeValid) {
        _state.addError(
          `Record at 'Values' index ${i}, field '${fieldName}' (index ${j}): ` +
          `Value '${value}' is of type '${vtype}', but 'Fields' defines type '${fieldType}'.`,
          `Values[${i}][${j}]`,
        );
        throw new BEJSONValidationError(`Type mismatch at [${i}][${j}]`, E_TYPE_MISMATCH);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Custom headers validation (104a)
// mirrors bejson_validator_check_custom_headers
// ---------------------------------------------------------------------------

const _PASCAL_CASE = /^[A-Z][a-zA-Z0-9_]*$/;


function bejson_validator_check_custom_headers(doc, version) {
  const mandatorySet = new Set(MANDATORY_KEYS);
  for (const key of Object.keys(doc)) {
    if (mandatorySet.has(key) || key === 'Parent_Hierarchy') continue;
    if (version === '104' || version === '104db') {
      _state.addError(
        `For BEJSON ${version}, custom top-level key '${key}' is not permitted.`,
        `Top-Level Keys/${key}`,
      );
      throw new BEJSONValidationError(`Unexpected key: ${key}`, E_RESERVED_KEY_COLLISION);
    }
    // 104a: Custom headers allowed, no strict naming enforcement
    // Audit 2 Finding: Removed PascalCase warning to avoid conflict with 104db rigidity.
  }
}

// ---------------------------------------------------------------------------
// Main validation entry points
// mirrors bejson_validator_validate_string / bejson_validator_validate_file
// ---------------------------------------------------------------------------


function bejson_validator_validate_string(jsonString) {
  bejson_validator_reset_state();
  const doc          = bejson_validator_check_json_syntax(jsonString, false);
  const version      = bejson_validator_check_mandatory_keys(doc);
  bejson_validator_check_custom_headers(doc, version);
  bejson_validator_check_records_type(doc, version);
  const fieldsCount  = bejson_validator_check_fields_structure(doc, version);
  if (version === '104db') bejson_validator_check_record_type_parent(doc);
  bejson_validator_check_values(doc, version, fieldsCount);
  return true;
}

function bejson_validator_validate_file(filePath) {
  bejson_validator_reset_state();
  try {
    const text = IO_PROVIDER.readFile(filePath);
    _state.currentFile = filePath;
    return bejson_validator_validate_string(text);
  } catch (err) {
    _state.addError(`IO Error: ${err.message}`, 'File System');
    throw new BEJSONValidationError(`IO Error: ${err.message}`, E_FILE_NOT_FOUND);
  }
}

// ---------------------------------------------------------------------------
// Validation report
// mirrors bejson_validator_get_report
// ---------------------------------------------------------------------------


function bejson_validator_get_report(input, isFile = false) {
  let valid = false;
  try {
    if (isFile) {
      valid = bejson_validator_validate_file(input);
    } else {
      valid = bejson_validator_validate_string(input);
    }
  } catch (_) {
    // errors captured in _state
  }

  const lines = [
    '=== BEJSON Validation Report ===',
    `Status: ${valid ? 'VALID' : 'INVALID'}`,
    '',
    `Errors: ${bejson_validator_error_count()}`,
  ];
  if (bejson_validator_has_errors()) {
    lines.push('---');
    lines.push(...bejson_validator_get_errors());
  }
  lines.push('', `Warnings: ${bejson_validator_warning_count()}`);
  if (bejson_validator_has_warnings()) {
    lines.push('---');
    lines.push(...bejson_validator_get_warnings());
  }

  return lines.join('\n');
}

// ===========================================================================
// MFDB VALIDATOR — appended from lib_mfdb_validator.js v1.0.0
// ===========================================================================

// ---------------------------------------------------------------------------
// Error codes (30–49)
// ---------------------------------------------------------------------------

const E_MFDB_NOT_MANIFEST           = 30;
const E_MFDB_NOT_ENTITY_FILE        = 31;
const E_MFDB_MANIFEST_RECORDS_TYPE  = 32;
const E_MFDB_ENTITY_NOT_FOUND       = 33;
const E_MFDB_ENTITY_NAME_MISMATCH   = 34;
const E_MFDB_DUPLICATE_ENTRY        = 35;
const E_MFDB_NO_PARENT_HIERARCHY    = 36;
const E_MFDB_MANIFEST_NOT_FOUND     = 37;
const E_MFDB_BIDIRECTIONAL_FAIL     = 38;
const E_MFDB_FK_UNRESOLVED          = 39;
const E_MFDB_MISSING_REQUIRED_FIELD = 40;
const E_MFDB_NULL_REQUIRED          = 41;

class MFDBValidationError extends Error {
  
  constructor(message, code) {
    super(message);
    this.name = 'MFDBValidationError';
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// Validation state
// ---------------------------------------------------------------------------

let _mErrors   = [];
let _mWarnings = [];

function _mReset()                  { _mErrors = []; _mWarnings = []; }
function _mAddError(msg, loc)       { _mErrors.push(   'ERROR'   + (loc ? ` | Location: ${loc}` : '') + ` | Message: ${msg}`); }
function _mAddWarning(msg, loc)     { _mWarnings.push( 'WARNING' + (loc ? ` | Location: ${loc}` : '') + ` | Message: ${msg}`); }
function _mHasErrors()              { return _mErrors.length   > 0; }
function _mHasWarnings()            { return _mWarnings.length > 0; }


// ---------------------------------------------------------------------------
// Internal helpers (also exported for lib_mfdb_core.js)
// ---------------------------------------------------------------------------


function _loadJson(filePath) {
  const fs = require('fs');
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}


function _rowsAsDicts(doc) {
  const names = doc.Fields.map(f => f.name);
  return doc.Values.map(row => Object.fromEntries(names.map((n, i) => [n, row[i]])));
}


function _resolveEntityPath(manifestPath, filePathRel) {
  const path = require('path');
  return path.resolve(path.dirname(manifestPath), filePathRel);
}


function _fileExists(filePath) {
  const fs = require('fs');
  return fs.existsSync(filePath);
}


// ---------------------------------------------------------------------------
// Manifest Validation  (Spec §8.1)
// ---------------------------------------------------------------------------


function mfdb_validator_validate_manifest(manifestPath) {
  _mReset();

  if (!_fileExists(manifestPath)) {
    _mAddError(`Manifest file not found: ${manifestPath}`, 'File System');
    throw new MFDBValidationError(`File not found: ${manifestPath}`, E_MFDB_MANIFEST_NOT_FOUND);
  }

  try {
    bejson_validator_validate_file(manifestPath);
  } catch (exc) {
    _mAddError(`BEJSON 104a validation failed: ${exc.message}`, 'BEJSON Validation');
    throw new MFDBValidationError(exc.message, E_MFDB_NOT_MANIFEST);
  }

  const doc = _loadJson(manifestPath);

  if (doc.Format_Version !== '104a') {
    _mAddError("Manifest must be Format_Version '104a'", 'Format_Version');
    throw new MFDBValidationError('Manifest must be 104a', E_MFDB_NOT_MANIFEST);
  }

  const rt = doc.Records_Type || [];
  if (!(rt.length === 1 && rt[0] === 'mfdb')) {
    _mAddError(`Records_Type must be ["mfdb"]. Found: ${JSON.stringify(rt)}`, 'Records_Type');
    throw new MFDBValidationError('Bad manifest Records_Type', E_MFDB_MANIFEST_RECORDS_TYPE);
  }

  const fieldNames = (doc.Fields || []).map(f => f.name);
  for (const required of ['entity_name', 'file_path']) {
    if (!fieldNames.includes(required)) {
      _mAddError(`Manifest Fields must include '${required}'`, 'Fields');
      throw new MFDBValidationError(`Missing required field '${required}'`, E_MFDB_MISSING_REQUIRED_FIELD);
    }
  }

  const entries    = _rowsAsDicts(doc);
  const seenNames  = new Set();
  const seenPaths  = new Set();

  for (let i = 0; i < entries.length; i++) {
    const entry      = entries[i];
    const entityName = entry.entity_name;
    const filePath   = entry.file_path;

    if (!entityName) {
      _mAddError(`Record ${i}: entity_name is null or missing`, `Values[${i}]`);
      throw new MFDBValidationError('Null entity_name', E_MFDB_NULL_REQUIRED);
    }
    if (!filePath) {
      _mAddError(`Record ${i}: file_path is null or missing`, `Values[${i}]`);
      throw new MFDBValidationError('Null file_path', E_MFDB_NULL_REQUIRED);
    }
    if (seenNames.has(entityName)) {
      _mAddError(`Duplicate entity_name: '${entityName}'`, `Values[${i}]`);
      throw new MFDBValidationError(`Duplicate entity_name: ${entityName}`, E_MFDB_DUPLICATE_ENTRY);
    }
    seenNames.add(entityName);

    if (seenPaths.has(filePath)) {
      _mAddError(`Duplicate file_path: '${filePath}'`, `Values[${i}]`);
      throw new MFDBValidationError(`Duplicate file_path: ${filePath}`, E_MFDB_DUPLICATE_ENTRY);
    }
    seenPaths.add(filePath);

    const resolved = _resolveEntityPath(manifestPath, filePath);
    if (!_fileExists(resolved)) {
      _mAddError(`Entity file '${filePath}' not found (resolved: ${resolved})`, `Values[${i}]/file_path`);
      throw new MFDBValidationError(`Entity file not found: ${resolved}`, E_MFDB_ENTITY_NOT_FOUND);
    }
  }

  return true;
}


// ---------------------------------------------------------------------------
// Entity File Validation  (Spec §8.2)
// ---------------------------------------------------------------------------


function mfdb_validator_validate_entity_file(entityPath, checkBidirectional = true) {
  const path = require('path');
  _mReset();

  if (!_fileExists(entityPath)) {
    _mAddError(`Entity file not found: ${entityPath}`, 'File System');
    throw new MFDBValidationError(`File not found: ${entityPath}`, E_MFDB_ENTITY_NOT_FOUND);
  }

  try {
    bejson_validator_validate_file(entityPath);
  } catch (exc) {
    _mAddError(`BEJSON 104 validation failed: ${exc.message}`, 'BEJSON Validation');
    throw new MFDBValidationError(exc.message, E_MFDB_NOT_ENTITY_FILE);
  }

  const doc = _loadJson(entityPath);

  if (doc.Format_Version !== '104') {
    _mAddError("Entity file must be Format_Version '104'", 'Format_Version');
    throw new MFDBValidationError('Entity file must be 104', E_MFDB_NOT_ENTITY_FILE);
  }

  const parentHierarchy = doc.Parent_Hierarchy;
  if (!parentHierarchy) {
    _mAddError('Entity file must contain Parent_Hierarchy pointing to the manifest', 'Parent_Hierarchy');
    throw new MFDBValidationError('Missing Parent_Hierarchy', E_MFDB_NO_PARENT_HIERARCHY);
  }

  const entityDir    = path.dirname(path.resolve(entityPath));
  const manifestPath = path.resolve(entityDir, parentHierarchy);

  if (!_fileExists(manifestPath)) {
    _mAddError(
      `Parent_Hierarchy '${parentHierarchy}' resolves to '${manifestPath}' which does not exist`,
      'Parent_Hierarchy',
    );
    throw new MFDBValidationError(`Manifest not found: ${manifestPath}`, E_MFDB_MANIFEST_NOT_FOUND);
  }

  if (!path.basename(manifestPath).endsWith('.mfdb.bejson')) {
    _mAddWarning(
      `Parent_Hierarchy target '${manifestPath}' does not end in '.mfdb.bejson'. Expected: 104a.mfdb.bejson`,
      'Parent_Hierarchy',
    );
  }

  const rt = doc.Records_Type || [];
  if (rt.length !== 1) {
    _mAddError(`Entity file Records_Type must have exactly one entry. Found: ${JSON.stringify(rt)}`, 'Records_Type');
    throw new MFDBValidationError('Entity Records_Type must be single-entry', E_MFDB_NOT_ENTITY_FILE);
  }

  const entityName = rt[0];

  let manifestDoc, entries, manifestEntityNames;
  try {
    manifestDoc        = _loadJson(manifestPath);
    entries            = _rowsAsDicts(manifestDoc);
    manifestEntityNames = entries.map(e => e.entity_name);
  } catch (exc) {
    _mAddError(`Could not read manifest: ${exc.message}`, 'Manifest');
    throw new MFDBValidationError(`Cannot read manifest: ${exc.message}`, E_MFDB_MANIFEST_NOT_FOUND);
  }

  if (!manifestEntityNames.includes(entityName)) {
    _mAddError(
      `Records_Type '${entityName}' does not appear as entity_name in the manifest`,
      'Records_Type vs Manifest',
    );
    throw new MFDBValidationError(
      `Entity '${entityName}' not registered in manifest`, E_MFDB_ENTITY_NAME_MISMATCH,
    );
  }

  if (checkBidirectional) {
    const match = entries.find(e => e.entity_name === entityName);
    if (match) {
      const manifestDir    = path.dirname(path.resolve(manifestPath));
      const fromManifest   = path.resolve(manifestDir, match.file_path || '');
      const thisFile       = path.resolve(entityPath);
      if (fromManifest !== thisFile) {
        _mAddError(
          `Bidirectional check failed for entity '${entityName}': ` +
          `manifest points to '${fromManifest}', but this file is '${thisFile}'`,
          'Bidirectional Path Check',
        );
        throw new MFDBValidationError('Bidirectional path check failed', E_MFDB_BIDIRECTIONAL_FAIL);
      }
    }
  }

  return true;
}


// ---------------------------------------------------------------------------
// Database-Level Validation  (Spec §8.3)
// ---------------------------------------------------------------------------


function mfdb_validator_validate_database(manifestPath, strictFk = false) {
  _mReset();

  try {
    mfdb_validator_validate_manifest(manifestPath);
  } catch (exc) {
    throw exc;
  }

  const manifestDoc = _loadJson(manifestPath);
  const entries     = _rowsAsDicts(manifestDoc);

  const pkMap = {};
  for (const e of entries) {
    if (e.primary_key) pkMap[e.entity_name] = e.primary_key;
  }

  for (const entry of entries) {
    const entityName    = entry.entity_name;
    const filePathRel   = entry.file_path;
    const declaredCount = entry.record_count;

    const resolved = _resolveEntityPath(manifestPath, filePathRel);

    try {
      mfdb_validator_validate_entity_file(resolved, true);
    } catch (exc) {
      _mAddError(`Entity '${entityName}' failed validation: ${exc.message}`, `Entity/${entityName}`);
      throw exc;
    }

    if (declaredCount !== null && declaredCount !== undefined) {
      const edoc        = _loadJson(resolved);
      const actualCount = (edoc.Values || []).length;
      if (actualCount !== declaredCount) {
        _mAddWarning(
          `Entity '${entityName}': manifest declares record_count=${declaredCount}, ` +
          `actual=${actualCount}. Call mfdb_core_sync_all_counts() to correct.`,
          `Entity/${entityName}/record_count`,
        );
      }
    }

    if (strictFk) {
      const edoc    = _loadJson(resolved);
      const fkFields = (edoc.Fields || []).filter(f => f.name.endsWith('_fk')).map(f => f.name);
      for (const fkField of fkFields) {
        const targetFound = Object.entries(pkMap).some(
          ([en, pk]) => pk && (fkField.includes(pk) || fkField.toLowerCase().includes(en.toLowerCase()))
        );
        if (!targetFound) {
          _mAddWarning(
            `Entity '${entityName}': FK field '${fkField}' has no matching primary_key ` +
            `declaration in the manifest. Consider adding a Relationships header (MFDB v1.1).`,
            `Entity/${entityName}/${fkField}`,
          );
        }
      }
    }
  }

  return true;
}


// ---------------------------------------------------------------------------
// Validation report
// ---------------------------------------------------------------------------


function mfdb_validator_get_report(manifestPath, strictFk = false) {
  let valid = false;
  try {
    valid = mfdb_validator_validate_database(manifestPath, strictFk);
  } catch (_) {}

  const lines = [
    '=== MFDB Validation Report ===',
    `Manifest : ${manifestPath}`,
    `Status   : ${valid ? 'VALID' : 'INVALID'}`,
    '',
    `Errors   : ${_mErrors.length}`,
  ];
  if (_mHasErrors()) {
    lines.push('---');
    lines.push(..._mErrors);
  }
  lines.push('', `Warnings : ${_mWarnings.length}`);
  if (_mHasWarnings()) {
    lines.push('---');
    lines.push(..._mWarnings);
  }
  return lines.join('\n');
}


// ---------------------------------------------------------------------------
// State accessors
// ---------------------------------------------------------------------------

function mfdb_validator_reset_state()      { _mReset(); }
function mfdb_validator_has_errors()       { return _mHasErrors(); }
function mfdb_validator_has_warnings()     { return _mHasWarnings(); }
function mfdb_validator_get_errors()       { return [..._mErrors]; }
function mfdb_validator_get_warnings()     { return [..._mWarnings]; }
function mfdb_validator_error_count()      { return _mErrors.length; }
function mfdb_validator_warning_count()    { return _mWarnings.length; }


// ---------------------------------------------------------------------------
// Exports (CommonJS + browser global)
// ---------------------------------------------------------------------------

const exports_ = {
  // ── BEJSON VALIDATOR ──
  // Error codes
  E_INVALID_JSON,
  E_MISSING_MANDATORY_KEY,
  E_INVALID_FORMAT,
  E_INVALID_VERSION,
  E_INVALID_RECORDS_TYPE,
  E_INVALID_FIELDS,
  E_INVALID_VALUES,
  E_TYPE_MISMATCH,
  E_RECORD_LENGTH_MISMATCH,
  E_RESERVED_KEY_COLLISION,
  E_INVALID_RECORD_TYPE_PARENT,
  E_NULL_VIOLATION,
  E_FILE_NOT_FOUND,
  E_PERMISSION_DENIED,
  E_ATOMIC_WRITE_FAILED,
  // Constants
  VALID_VERSIONS,
  MANDATORY_KEYS,
  VALID_FIELD_TYPES,
  // Classes
  BEJSONValidationError,
  ValidationState,
  // State accessors
  bejson_validator_reset_state,
  bejson_validator_get_errors,
  bejson_validator_get_warnings,
  bejson_validator_has_errors,
  bejson_validator_has_warnings,
  bejson_validator_error_count,
  bejson_validator_warning_count,
  // Validation steps
  bejson_validator_check_dependencies,
  bejson_validator_check_json_syntax,
  bejson_validator_check_mandatory_keys,
  bejson_validator_check_records_type,
  bejson_validator_check_fields_structure,
  bejson_validator_check_record_type_parent,
  bejson_validator_check_values,
  bejson_validator_check_custom_headers,
  // Entry points
  bejson_validator_validate_string,
  bejson_validator_validate_file,
  bejson_validator_get_report,

  // ── MFDB VALIDATOR ──
  // Error codes
  E_MFDB_NOT_MANIFEST,
  E_MFDB_NOT_ENTITY_FILE,
  E_MFDB_MANIFEST_RECORDS_TYPE,
  E_MFDB_ENTITY_NOT_FOUND,
  E_MFDB_ENTITY_NAME_MISMATCH,
  E_MFDB_DUPLICATE_ENTRY,
  E_MFDB_NO_PARENT_HIERARCHY,
  E_MFDB_MANIFEST_NOT_FOUND,
  E_MFDB_BIDIRECTIONAL_FAIL,
  E_MFDB_FK_UNRESOLVED,
  E_MFDB_MISSING_REQUIRED_FIELD,
  E_MFDB_NULL_REQUIRED,
  // Class
  MFDBValidationError,
  // Internal helpers (needed by lib_bejson_core.js MFDB section)
  _loadJson,
  _rowsAsDicts,
  _resolveEntityPath,
  _fileExists,
  // Validation functions
  mfdb_validator_validate_manifest,
  mfdb_validator_validate_entity_file,
  mfdb_validator_validate_database,
  mfdb_validator_get_report,
  // State accessors
  mfdb_validator_reset_state,
  mfdb_validator_has_errors,
  mfdb_validator_has_warnings,
  mfdb_validator_get_errors,
  mfdb_validator_get_warnings,
  mfdb_validator_error_count,
  mfdb_validator_warning_count,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = exports_;
}
if (typeof window !== 'undefined') {
  window.BEJSON_VALIDATOR = exports_;
}
