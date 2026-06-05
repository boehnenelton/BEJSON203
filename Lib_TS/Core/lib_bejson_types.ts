/**
 * Library:      bejson_types.ts
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.3 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-05
 * Description:  Type definitions and interface contracts for TypeScript libraries.
 * 
 * NOTE: Error codes are mirrored across SH, JS, PY, and TS registries.
 * Reference canonical codes in lib_bejson_errors.js / lib_bejson_errors.sh.
 */

// ---------------------------------------------------------------------------
// Primitive and union types
// ---------------------------------------------------------------------------

export type BEJSONVersion = "104" | "104a" | "104db";


export type BEJSONFieldType =
  | "string"
  | "integer"
  | "number"
  | "boolean"
  | "array"
  | "object";


export type BEJSONPrimitiveType = "string" | "integer" | "number" | "boolean";


export type BEJSONValue =
  | string
  | number
  | boolean
  | null
  | unknown[]
  | Record<string, unknown>;

// ---------------------------------------------------------------------------
// Field and Document interfaces
// ---------------------------------------------------------------------------

export interface BEJSONField {
  name: string;
  type: BEJSONFieldType;
  
  Record_Type_Parent?: string;
}


export interface BEJSONDocument {
  Format: "BEJSON";
  Format_Version: "104" | "104a" | "104db";
  Format_Creator: "Elton Boehnen";
  Records_Type: string[];
  Fields: BEJSONField[];
  Values: BEJSONValue[][];
  
  Parent_Hierarchy?: string;
  [key: string]: unknown; // custom 104a headers + index access
}

// ---------------------------------------------------------------------------
// Validation result types
// ---------------------------------------------------------------------------

export interface ValidationError {
  code: number;
  message: string;
  field?: string;
  recordIndex?: number;
}

export interface ValidationWarning {
  code: number;
  message: string;
  field?: string;
  recordIndex?: number;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

// ---------------------------------------------------------------------------
// MFDB-specific interfaces
// ---------------------------------------------------------------------------


export interface MFDBManifestRecord {
  entity_name: string;
  file_path: string;
  description?: string | null;
  record_count?: number | null;
  schema_version?: string | null;
  primary_key?: string | null;
}


export interface MFDBDatabaseMeta {
  mfdb_version: string;
  db_name: string;
  db_description?: string;
  schema_version?: string;
  author?: string;
  created_at?: string;
}


export type MFDBFileRole = "manifest" | "entity" | "standalone";

// ---------------------------------------------------------------------------
// Error classes
// ---------------------------------------------------------------------------


export class BEJSONValidationError extends Error {
  public readonly code: number;
  constructor(code: number, message: string) {
    super(message);
    this.name = "BEJSONValidationError";
    this.code = code;
  }
}


export class BEJSONCoreError extends Error {
  public readonly code: number;
  constructor(code: number, message: string) {
    super(message);
    this.name = "BEJSONCoreError";
    this.code = code;
  }
}


export class MFDBValidationError extends Error {
  public readonly code: number;
  constructor(code: number, message: string) {
    super(message);
    this.name = "MFDBValidationError";
    this.code = code;
  }
}


export class MFDBCoreError extends Error {
  public readonly code: number;
  constructor(code: number, message: string) {
    super(message);
    this.name = "MFDBCoreError";
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// Validation error code catalogue
// ---------------------------------------------------------------------------

export const BEJSON_VALIDATION_CODES = {
  
  INVALID_JSON: 1,
  
  MISSING_MANDATORY_KEY: 2,
  
  INVALID_FORMAT_VALUE: 3,
  
  INVALID_FORMAT_VERSION: 4,
  
  INVALID_RECORDS_TYPE: 5,
  
  INVALID_FIELDS: 6,
  
  INVALID_VALUES: 7,
  
  VALUE_TYPE_MISMATCH: 8,
  
  RECORD_LENGTH_MISMATCH: 9,
  
  RESERVED_KEY_COLLISION: 10,
  
  INVALID_RECORD_TYPE_PARENT: 11,
  
  NULL_VIOLATION: 12,
  
  FILE_NOT_FOUND: 13,
  
  PERMISSION_DENIED: 14,
  
  ATOMIC_WRITE_FAILED: 15,
  
  INVALID_FORMAT_CREATOR: 16,
} as const;

export const BEJSON_CORE_CODES = {
  
  INVALID_VERSION: 20,
  
  INVALID_OPERATION: 21,
  
  INDEX_OUT_OF_BOUNDS: 22,
  
  FIELD_NOT_FOUND: 23,
  
  TYPE_CONVERSION_FAILED: 24,
  
  BACKUP_FAILED: 25,
  
  WRITE_FAILED: 26,
  
  QUERY_FAILED: 27,
  
  ENCRYPTION_FAILED: 28,
  
  DECRYPTION_FAILED: 29,
} as const;

export const MFDB_VALIDATION_CODES = {
  
  NOT_A_MANIFEST: 30,
  
  NOT_AN_ENTITY: 31,
  
  MANIFEST_RECORDS_TYPE_INVALID: 32,
  
  ENTITY_FILE_NOT_FOUND: 33,
  
  ENTITY_NAME_MISMATCH: 34,
  
  DUPLICATE_ENTRY: 35,
  
  MISSING_PARENT_HIERARCHY: 36,
  
  MANIFEST_FILE_NOT_FOUND: 37,
  
  BIDIRECTIONAL_PATH_FAILED: 38,
  
  FK_UNRESOLVED: 39,
  
  MISSING_REQUIRED_MANIFEST_FIELD: 40,
  
  NULL_IN_REQUIRED_MANIFEST_FIELD: 41,
  
  INVALID_ARCHIVE: 42,
} as const;

export const MFDB_CORE_CODES = {
  
  MANIFEST_NOT_FOUND: 50,
  
  ENTITY_NOT_FOUND: 51,
  
  WRITE_FAILED: 52,
  
  LOCK_FAILED: 53,
  
  INVALID_OPERATION: 54,
  
  INDEX_OUT_OF_BOUNDS: 55,
  
  JOIN_FAILED: 56,
  
  ARCHIVE_ERROR: 70,
  
  MOUNT_CONFLICT: 71,
} as const;
