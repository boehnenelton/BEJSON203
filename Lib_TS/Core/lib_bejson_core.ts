/**
 * Library:      bejson_core.ts
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.4 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-09
 * Description:  Low-level primitive operations for BEJSON document manipulation.
 * REMEDIATED:   Removed regex parser crutch and optimized cryptographic bottlenecks.
 * ALIGNED:      v2.0.3 parity with JS core families; internal metadata stripping (Audit Finding 13).
 */

import {
  BEJSONDocument,
  BEJSONField,
  BEJSONValue,
  BEJSONCoreError,
  BEJSON_CORE_CODES,
} from "./bejson_types";

// ---------------------------------------------------------------------------
// Parse & Serialize
// ---------------------------------------------------------------------------


/**
 * Optimal BEJSON Parsing Standard (TS)
 * Enforces native JSON.parse() immediately wrapped in structural validation.
 * REMEDIATED: Removed regex pre-processor to eliminate fragility.
 */
export function parse(text: string): BEJSONDocument {
  if (typeof text !== 'string') {
    throw new BEJSONCoreError(BEJSON_CORE_CODES.PARSE_ERROR, 'Input must be a string.');
  }

  let raw: unknown;
  try {
    // 1. Parse Object Tree using native engine directly
    raw = JSON.parse(text);
  } catch (e) {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.PARSE_ERROR,
      "Invalid JSON: " + String(e)
    );
  }

  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.PARSE_ERROR,
      "Parsed JSON root must be an object."
    );
  }

  return raw as BEJSONDocument;
}


export function serialize(doc: BEJSONDocument, indent: number = 2): string {
  if (doc === null || doc === undefined) {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.NULL_DOCUMENT,
      "Cannot serialize null or undefined document."
    );
  }
  try {
    // RE-ALIGNED: Strip internal metadata keys (starting with _) before serialization
    const cleanDoc: Record<string, any> = {};
    for (const key in doc) {
      if (Object.prototype.hasOwnProperty.call(doc, key) && !key.startsWith("_")) {
        cleanDoc[key] = doc[key];
      }
    }
    return JSON.stringify(cleanDoc, null, indent || undefined);
  } catch (e) {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.SERIALIZATION_ERROR,
      "Serialization failed: " + String(e)
    );
  }
}

// ---------------------------------------------------------------------------
// Field index helpers
// ---------------------------------------------------------------------------


export function getFieldIndex(doc: BEJSONDocument, name: string): number {
  _assertDoc(doc);
  const idx = doc.Fields.findIndex((f) => f.name === name);
  if (idx === -1) {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.FIELD_NOT_FOUND,
      "Field not found: " + name
    );
  }
  return idx;
}


export function getFieldNames(doc: BEJSONDocument): string[] {
  _assertDoc(doc);
  return doc.Fields.map((f) => f.name);
}


export function getFields(doc: BEJSONDocument): BEJSONField[] {
  _assertDoc(doc);
  return doc.Fields.map((f) => Object.assign({}, f));
}

// ---------------------------------------------------------------------------
// Record accessors
// ---------------------------------------------------------------------------


export function getRecord(
  doc: BEJSONDocument,
  index: number
): Record<string, BEJSONValue> {
  _assertDoc(doc);
  _assertIndex(doc, index);
  return _rowToObject(doc.Fields, doc.Values[index]);
}


export function getAllRecords(
  doc: BEJSONDocument
): Record<string, BEJSONValue>[] {
  _assertDoc(doc);
  return doc.Values.map((row) => _rowToObject(doc.Fields, row));
}


export function getFieldValue(
  doc: BEJSONDocument,
  index: number,
  fieldName: string
): BEJSONValue {
  _assertDoc(doc);
  _assertIndex(doc, index);
  const fi = getFieldIndex(doc, fieldName);
  return doc.Values[index][fi];
}


export function getRecordCount(doc: BEJSONDocument): number {
  _assertDoc(doc);
  return doc.Values.length;
}

// ---------------------------------------------------------------------------
// 104db — entity-scoped record access
// ---------------------------------------------------------------------------


export function getRecordsByType(
  doc: BEJSONDocument,
  type: string
): Record<string, BEJSONValue>[] {
  _assertDoc(doc);
  if (doc.Format_Version !== "104db") {
    throw new BEJSONCoreError(
      BEJSON_CORE_CODES.UNSUPPORTED_OPERATION,
      "getRecordsByType is only valid on BEJSON 104db documents."
    );
  }
  return doc.Values.filter((row) => row[0] === type).map((row) =>
    _rowToObject(doc.Fields, row)
  );
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------


export function appendRecord(
  doc: BEJSONDocument,
  values: BEJSONValue[]
): BEJSONDocument {
  _assertDoc(doc);
  _assertRowLength(doc, values);
  const coerced = values.map((v, i) => _coerceValue(v, doc.Fields[i].type));
  return _cloneWith(doc, { Values: [...doc.Values, coerced] });
}


export function updateRecord(
  doc: BEJSONDocument,
  index: number,
  values: BEJSONValue[]
): BEJSONDocument {
  _assertDoc(doc);
  _assertIndex(doc, index);
  _assertRowLength(doc, values);
  const coerced = values.map((v, i) => _coerceValue(v, doc.Fields[i].type));
  const newValues = doc.Values.map((row, i) =>
    i === index ? coerced : row
  );
  return _cloneWith(doc, { Values: newValues });
}

// ---------------------------------------------------------------------------
// Encryption Utilities (REMEDIATED: Optimized)
// ---------------------------------------------------------------------------

/**
 * Derives a CryptoKey from a password and salt.
 * Caller should cache this key to avoid PBKDF2 bottlenecks.
 */
export async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  return await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

// Internal Key Cache for current session/document operation
let _keyCache: { password: string; salt: string; key: CryptoKey } | null = null;

async function _getOrDeriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const saltHex = _ab2hex(salt);
  if (_keyCache && _keyCache.password === password && _keyCache.salt === saltHex) {
    return _keyCache.key;
  }
  const key = await deriveKey(password, salt);
  _keyCache = { password, salt: saltHex, key };
  return key;
}

function _ab2hex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function _ab2base64(buf: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

function _base642ab(base64: string): Uint8Array {
  const b = atob(base64);
  return new Uint8Array(b.length).map((_, i) => b.charCodeAt(i));
}

export async function encryptRecord(
  doc: BEJSONDocument,
  recordIndex: number,
  password: string,
  providedSalt?: Uint8Array
): Promise<BEJSONDocument> {
  _assertDoc(doc);
  _assertIndex(doc, recordIndex);

  // Reuse salt if provided, otherwise generate. Reusing salt allows key caching.
  const salt = providedSalt || crypto.getRandomValues(new Uint8Array(16));
  const key = await _getOrDeriveKey(password, salt);
  const saltB64 = _ab2base64(salt);

  const row = doc.Values[recordIndex];
  const newRow = [...row];

  for (let j = 0; j < newRow.length; j++) {
    const field = doc.Fields[j];
    if (field.name === "Record_Type_Parent" || field.name === "is_encrypted") continue;
    
    const val = newRow[j];
    if (val === null) continue;
    
    // Check if already encrypted (handle both legacy string and new object format)
    if (typeof val === "string" && val.startsWith("ENC:AES-GCM:")) continue;
    if (val && typeof val === "object" && (val as any)._enc === "AES-GCM") continue;

    const dataEnc = new TextEncoder().encode(JSON.stringify(val));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: iv }, key, dataEnc);

    newRow[j] = {
      _enc: "AES-GCM",
      salt: saltB64,
      iv: _ab2base64(iv),
      ct: _ab2base64(ciphertext)
    };
  }

  const ieIdx = doc.Fields.findIndex((f) => f.name === "is_encrypted");
  if (ieIdx !== -1) newRow[ieIdx] = true;

  const newValues = doc.Values.map((r, i) => (i === recordIndex ? newRow : r));
  return _cloneWith(doc, { Values: newValues });
}

export async function decryptRecord(
  doc: BEJSONDocument,
  recordIndex: number,
  password: string
): Promise<BEJSONDocument> {
  _assertDoc(doc);
  _assertIndex(doc, recordIndex);

  const row = doc.Values[recordIndex];
  const newRow = [...row];

  for (let j = 0; j < newRow.length; j++) {
    const val = newRow[j];
    
    let saltB64: string | undefined;
    let ivB64: string | undefined;
    let ctB64: string | undefined;

    if (typeof val === "string" && val.startsWith("ENC:AES-GCM:")) {
      const parts = val.split(":");
      if (parts.length === 5) {
        saltB64 = parts[2];
        ivB64 = parts[3];
        ctB64 = parts[4];
      }
    } else if (val && typeof val === "object" && (val as any)._enc === "AES-GCM") {
      saltB64 = (val as any).salt;
      ivB64 = (val as any).iv;
      ctB64 = (val as any).ct;
    }

    if (!saltB64 || !ivB64 || !ctB64) continue;

    try {
      const salt = _base642ab(saltB64);
      const iv = _base642ab(ivB64);
      const ct = _base642ab(ctB64);

      const key = await _getOrDeriveKey(password, salt);
      const decrypted = await crypto.subtle.decrypt({ name: "AES-GCM", iv: iv }, key, ct);
      newRow[j] = JSON.parse(new TextDecoder().decode(decrypted));
    } catch (e) {
      throw new BEJSONCoreError(BEJSON_CORE_CODES.DECRYPTION_FAILED, "Decryption failed at field " + j + ": " + String(e));
    }
  }

  const ieIdx = doc.Fields.findIndex((f) => f.name === "is_encrypted");
  if (ieIdx !== -1) {
    newRow[ieIdx] = newRow.some((v, idx) => {
      if (doc.Fields[idx].name === "is_encrypted") return false;
      return (typeof v === "string" && v.startsWith("ENC:AES-GCM:")) || (v && typeof v === "object" && (v as any)._enc === "AES-GCM");
    });
  }

  const newValues = doc.Values.map((r, i) => (i === recordIndex ? newRow : r));
  return _cloneWith(doc, { Values: newValues });
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _assertDoc(doc: BEJSONDocument): void {
  if (doc === null || doc === undefined) throw new BEJSONCoreError(BEJSON_CORE_CODES.NULL_DOCUMENT, "Document is null.");
}

function _assertIndex(doc: BEJSONDocument, index: number): void {
  if (index < 0 || index >= doc.Values.length) throw new BEJSONCoreError(BEJSON_CORE_CODES.INDEX_OUT_OF_BOUNDS, "Index out of bounds.");
}

function _assertRowLength(doc: BEJSONDocument, values: BEJSONValue[]): void {
  if (values.length !== doc.Fields.length) throw new BEJSONCoreError(BEJSON_CORE_CODES.WRITE_LENGTH_MISMATCH, "Length mismatch.");
}

function _rowToObject(fields: BEJSONField[], row: BEJSONValue[]): Record<string, BEJSONValue> {
  const obj: Record<string, BEJSONValue> = {};
  for (let i = 0; i < fields.length; i++) obj[fields[i].name] = row[i];
  return obj;
}

function _cloneWith(doc: BEJSONDocument, overrides: Partial<BEJSONDocument>): BEJSONDocument {
  return Object.assign({}, doc, overrides);
}

function _coerceValue(value: any, fieldType: string): BEJSONValue {
  if (fieldType === "string") return String(value);
  if (fieldType === "integer" || fieldType === "number") {
    const num = fieldType === "integer" ? parseInt(value, 10) : parseFloat(value);
    if (isNaN(num)) throw new BEJSONCoreError(BEJSON_CORE_CODES.WRITE_TYPE_MISMATCH, "Coercion failed.");
    return num;
  }
  if (fieldType === "boolean") {
    if (typeof value === "boolean") return value;
    if (String(value).toLowerCase() === "true") return true;
    if (String(value).toLowerCase() === "false") return false;
    throw new BEJSONCoreError(BEJSON_CORE_CODES.WRITE_TYPE_MISMATCH, "Coercion failed.");
  }
  return value as BEJSONValue;
}
