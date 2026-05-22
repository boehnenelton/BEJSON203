/**
 * Library:      lib_bejson_utility.js
 * Family:       Utility
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.2.1 OFFICIAL (DEP81)
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-21
 * Description:  Cross-compatible chunking utilities for CLI_CHUNKER and MFDB_V5.
 *               Strictly non-regex, standard string-based implementation.
 */

'use strict';

(function() {
    const Utility = {
        DEFAULT_EXTENSIONS: [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".sh", ".txt", ".bejson", ".tsx", ".jsx"],
        DEFAULT_EXCLUDES: [".git", "__pycache__", "node_modules", "lib", "output", ".mfdb_lock", "dist", "build"],

        SCHEMA_CLI_CHUNKER: [
            {"name": "Record_Type_Parent", "type": "string"},
            {"name": "project_name", "type": "string", "Record_Type_Parent": "ProjectMeta"},
            {"name": "version", "type": "string", "Record_Type_Parent": "ProjectMeta"},
            {"name": "root_path", "type": "string", "Record_Type_Parent": "ProjectMeta"},
            {"name": "file_path", "type": "string", "Record_Type_Parent": "FileContent"},
            {"name": "file_name", "type": "string", "Record_Type_Parent": "FileContent"},
            {"name": "content", "type": "string", "Record_Type_Parent": "FileContent"},
            {"name": "is_binary", "type": "boolean", "Record_Type_Parent": "FileContent"}
        ],

        SCHEMA_MFDB_ENTITY: [
            {"name": "version",   "type": "string"},
            {"name": "file_path", "type": "string"},
            {"name": "file_name", "type": "string"},
            {"name": "content",   "type": "string"},
            {"name": "is_binary", "type": "boolean"},
            {"name": "is_base64", "type": "boolean"},
        ],

        sanitizeName: function(name) {
            const invalid = '<>:"/\\|?*';
            let res = name;
            for (let i = 0; i < invalid.length; i++) {
                res = res.split(invalid[i]).join('_');
            }
            return res;
        },

        getTimestamp: function() {
            const iso = new Date().toISOString();
            // String manipulation instead of regex
            return iso.split('.')[0].split(':').join('').split('-').join('').replace('T', '_');
        },

        downloadBase64: function(base64, fileName) {
            const link = document.createElement('a');
            link.href = 'data:application/octet-stream;base64,' + base64;
            link.download = fileName;
            link.click();
        }
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Utility;
    }
    if (typeof window !== 'undefined') {
        window.BEJSON = window.BEJSON || {};
        window.BEJSON.Utility = Utility;
    }
})();
