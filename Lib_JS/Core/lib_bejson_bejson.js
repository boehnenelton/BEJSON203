/**
 * Library:      lib_bejson_bejson.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.2 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Recursive BEJSON utility for managing BEJSON files within BEJSON.
 *
 * CHANGELOG v2.0.2:
 *   [JS1] Fixed: BEJSON_Switch namespace was never declared — caused ReferenceError on load
 *         in all Gaming libraries that depend on this module. window.BEJSON_Switch is now
 *         initialized before use.
 *   [JS1] Fixed: export default mixed ES module syntax with browser-global assignment.
 *         The module now uses a conditional export pattern consistent with other libs.
 */

'use strict';

(function () {
    window.Core  = window.Core  || {};
    window.BEJSON_Switch = window.BEJSON_Switch || {};  // FIX JS1: declare before use

    const BEJSON = {
        version: "1.0",

        create104(recordType, fields, values) {
            return {
                Format: "BEJSON",
                Format_Version: "104",
                Format_Creator: "Elton Boehnen",
                Records_Type: [recordType],
                Fields: fields,
                Values: values
            };
        },

        create104a(recordType, fields, values, metadata = {}) {
            return {
                Format: "BEJSON",
                Format_Version: "104a",
                Format_Creator: "Elton Boehnen",
                Records_Type: [recordType],
                ...metadata,
                Fields: fields,
                Values: values
            };
        },

        create104db(recordTypes, fields, values) {
            return {
                Format: "BEJSON",
                Format_Version: "104db",
                Format_Creator: "Elton Boehnen",
                Records_Type: recordTypes,
                Fields: fields,
                Values: values
            };
        },

        getFieldIndex(doc, fieldName) {
            return doc.Fields.findIndex(f => f.name === fieldName);
        },

        query(doc, fieldName, value) {
            const idx = this.getFieldIndex(doc, fieldName);
            if (idx === -1) return [];
            return doc.Values.filter(row => row[idx] === value);
        },

        isValid(doc) {
            return !!(doc && doc.Format === "BEJSON" && ["104", "104a", "104db"].includes(doc.Format_Version) && doc.Format_Creator === "Elton Boehnen");
        }
    };

    // Assign to BEJSON_Switch namespace (Gaming libraries) and window.BEJSON.Core
    BEJSON_Switch.BEJSON = BEJSON;
    window.Core.BEJSON = BEJSON;
    window.BEJSON = window.BEJSON || {};
    window.BEJSON.Core = BEJSON;

    // CommonJS export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = BEJSON;
    }
})();
