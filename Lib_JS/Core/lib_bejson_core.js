/**
 * Library:      lib_bejson_core.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Low-level primitive operations for BEJSON document manipulation.
 */
'use strict';

const BEJSON_ERRORS = (typeof require !== 'undefined') 
  ? require('./lib_bejson_errors.js') 
  : (window.BEJSON_ERRORS || {});

 const {
     E_CORE_INVALID_VERSION,
     E_CORE_INVALID_OPERATION,
     E_CORE_INDEX_OUT_OF_BOUNDS,
     E_CORE_FIELD_NOT_FOUND,
     E_CORE_TYPE_CONVERSION_FAILED,
     E_CORE_BACKUP_FAILED,
     E_CORE_WRITE_FAILED,
     E_CORE_QUERY_FAILED,
     E_CORE_ENCRYPTION_FAILED,
     E_CORE_DECRYPTION_FAILED
 } = BEJSON_ERRORS;

 // --- Environment Detection ---
let crypto = (typeof window !== 'undefined' && window.crypto) ? window.crypto : null;
if (!crypto && typeof require !== 'undefined') {
    try {
        crypto = require('crypto').webcrypto;
    } catch (e) {
        // Fallback for older Node.js or other environments
    }
}

class BEJSONCoreError extends Error {
    constructor(message, code) {
        super(message);
        this.code = code;
        this.name = "BEJSONCoreError";
    }
}

class BEJSONEngine {
    constructor() {
        this.systems = new Map();
        this.state = 'BOOT';
    }
    registerSystem(name, system) { this.systems.set(name, system); }
    getSystem(name) { return this.systems.get(name); }
    loop(dt) {
        this.systems.forEach(s => {
            if (s.step) s.step(dt);
            if (s.update) s.update(dt);
        });
    }
}

const CryptoUtils = {
    async deriveKey(password, salt) {
        const enc = new TextEncoder();
        const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveKey"]);
        return await crypto.subtle.deriveKey(
            { name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" },
            keyMaterial,
            { name: "AES-GCM", length: 256 },
            false,
            ["encrypt", "decrypt"]
        );
    },

    ab2base64(buf) { const b = new Uint8Array(buf); let s = ''; for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]); return btoa(s); },
    base642ab(base64) { const b = atob(base64); return new Uint8Array(b.length).map((_, i) => b.charCodeAt(i)); },

    async encryptRecord(doc, recordIndex, password) {
        if (recordIndex < 0 || recordIndex >= doc.Values.length) throw new BEJSONCoreError("Index out of bounds", E_CORE_INDEX_OUT_OF_BOUNDS);
        
        const record = doc.Values[recordIndex];
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const key = await this.deriveKey(password, salt);
        const saltB64 = this.ab2base64(salt);
        
        const newRecord = [...record];
        for (let i = 0; i < newRecord.length; i++) {
            const field = doc.Fields[i];
            if (field.name === "Record_Type_Parent" || field.name === "is_encrypted") continue;
            
            const val = newRecord[i];
            if (val === null) continue;
            if (typeof val === "object" && val._enc === "AES-GCM") continue;

            const dataEnc = new TextEncoder().encode(JSON.stringify(val));
            const iv = crypto.getRandomValues(new Uint8Array(12));
            const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: iv }, key, dataEnc);
            
            const ivB64 = this.ab2base64(iv);
            const ctB64 = this.ab2base64(ciphertext);
            
            newRecord[i] = {
                _enc: "AES-GCM",
                salt: saltB64,
                iv: ivB64,
                ct: ctB64
            };
        }

        const ieIdx = doc.Fields.findIndex(f => f.name === "is_encrypted");
        if (ieIdx !== -1) newRecord[ieIdx] = true;

        doc.Values[recordIndex] = newRecord;
        return doc;
    },

    async decryptRecord(doc, recordIndex, password) {
        if (recordIndex < 0 || recordIndex >= doc.Values.length) throw new BEJSONCoreError("Index out of bounds", E_CORE_INDEX_OUT_OF_BOUNDS);
        
        const record = doc.Values[recordIndex];
        const newRecord = [...record];
        
        for (let i = 0; i < newRecord.length; i++) {
            const val = newRecord[i];
            
            // Handle both legacy string format and new object format for transition
            let saltB64, ivB64, ctB64;
            
            if (typeof val === "string" && val.startsWith("ENC:AES-GCM:")) {
                const parts = val.split(":");
                if (parts.length === 5) {
                    saltB64 = parts[2];
                    ivB64 = parts[3];
                    ctB64 = parts[4];
                }
            } else if (val && typeof val === "object" && val._enc === "AES-GCM") {
                saltB64 = val.salt;
                ivB64 = val.iv;
                ctB64 = val.ct;
            }
            
            if (!saltB64 || !ivB64 || !ctB64) continue;
            
            try {
                const salt = this.base642ab(saltB64);
                const iv = this.base642ab(ivB64);
                const ct = this.base642ab(ctB64);
                const key = await this.deriveKey(password, salt);
                
                const decrypted = await crypto.subtle.decrypt({ name: "AES-GCM", iv: iv }, key, ct);
                newRecord[i] = JSON.parse(new TextDecoder().decode(decrypted));
            } catch (e) {
                throw new BEJSONCoreError("Decryption failed at field " + i + ": " + e.message, E_CORE_DECRYPTION_FAILED);
            }
        }

        const ieIdx = doc.Fields.findIndex(f => f.name === "is_encrypted");
        if (ieIdx !== -1) {
            newRecord[ieIdx] = newRecord.some((v, idx) => {
                if (doc.Fields[idx].name === "is_encrypted") return false;
                return (typeof v === "string" && v.startsWith("ENC:AES-GCM:")) || (v && v._enc === "AES-GCM");
            });
        }

        doc.Values[recordIndex] = newRecord;
        return doc;
    }
};

// Stubs for parser compatibility (Audit 2 Finding)
function bejson_core_is_valid(doc) { return !!(doc && doc.Format === "BEJSON"); }
function bejson_core_get_version(doc) { return doc ? (doc.Format_Version || doc.Version) : null; }
function bejson_core_get_stats(doc) {
    if (!doc || !doc.Values) return { records: 0, fields: 0 };
    return { records: doc.Values.length, fields: doc.Fields ? doc.Fields.length : 0 };
}

const CoreExports = {
    BEJSONCoreError,
    BEJSONEngine,
    Crypto: CryptoUtils,
    bejson_core_is_valid,
    bejson_core_get_version,
    bejson_core_get_stats,
    // Error codes
    E_CORE_INVALID_VERSION, E_CORE_INVALID_OPERATION, E_CORE_INDEX_OUT_OF_BOUNDS,
    E_CORE_FIELD_NOT_FOUND, E_CORE_TYPE_CONVERSION_FAILED, E_CORE_BACKUP_FAILED,
    E_CORE_WRITE_FAILED, E_CORE_QUERY_FAILED, E_CORE_ENCRYPTION_FAILED, E_CORE_DECRYPTION_FAILED
};

// UMD-like export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoreExports;
}
if (typeof window !== 'undefined') {
    window.BEJSON = window.BEJSON || {};
    Object.assign(window.BEJSON, CoreExports);
}
