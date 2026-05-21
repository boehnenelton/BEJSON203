/**
 * Library:      lib_bejson_schema.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-21
 * Description:  Schema management and enforcement for JavaScript.
 */

const BEJSONSchema = {
    /**
     * Extracts the schema (structure) from a BEJSON document.
     */
    extract: function(doc) {
        const schema = JSON.parse(JSON.stringify(doc));
        schema.Values = [];
        return schema;
    },

    /**
     * Validates a BEJSON document against a specific schema.
     */
    validateAgainst: function(doc, schema) {
        const result = { valid: true, errors: [] };

        // 1. Version Check
        if (doc.Format_Version !== schema.Format_Version) {
            result.valid = false;
            result.errors.push(`Version mismatch: Document is ${doc.Format_Version}, Schema is ${schema.Format_Version}`);
        }

        // 2. Records_Type Check
        if (JSON.stringify(doc.Records_Type) !== JSON.stringify(schema.Records_Type)) {
            result.valid = false;
            result.errors.push("Records_Type mismatch: Document types do not match schema types.");
        }

        // 3. Fields Check
        const docFields = doc.Fields || [];
        const schFields = schema.Fields || [];

        if (docFields.length !== schFields.length) {
            result.valid = false;
            result.errors.push(`Field count mismatch: Document has ${docFields.length}, Schema has ${schFields.length}`);
        } else {
            for (let i = 0; i < docFields.length; i++) {
                const df = docFields[i];
                const sf = schFields[i];

                if (df.name !== sf.name) {
                    result.valid = false;
                    result.errors.push(`Field name mismatch at index ${i}: expected '${sf.name}', found '${df.name}'`);
                }
                if (df.type !== sf.type) {
                    result.valid = false;
                    result.errors.push(`Field type mismatch for '${sf.name}': expected '${sf.type}', found '${df.type}'`);
                }
                if (df.Record_Type_Parent !== sf.Record_Type_Parent) {
                    result.valid = false;
                    result.errors.push(`Record_Type_Parent mismatch for '${sf.name}': expected '${sf.Record_Type_Parent}', found '${df.Record_Type_Parent}'`);
                }
            }
        }

        return result;
    },

    /**
     * Returns a mapping of field names to their definitions.
     */
    getFieldMap: function(schema) {
        const map = {};
        (schema.Fields || []).forEach(f => {
            map[f.name] = f;
        });
        return map;
    },

    /**
     * Utility to create a schema object from scratch.
     */
    inferFromData: function(recordsType, fields, version = "104a") {
        return {
            Format: "BEJSON",
            Format_Version: version,
            Format_Creator: "Elton Boehnen",
            Records_Type: Array.isArray(recordsType) ? recordsType : [recordsType],
            Fields: fields,
            Values: []
        };
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = BEJSONSchema;
}
