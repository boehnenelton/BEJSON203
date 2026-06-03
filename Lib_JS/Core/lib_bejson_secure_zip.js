/**
 * Library:      lib_bejson_secure_zip.js
 * Family:       Utility
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      1.0.0 OFFICIAL
 * Date:         2026-06-02
 * Description:  Secure ZIP extraction logic to mitigate Zip Slip vulnerabilities.
 * REMEDIATED:   Implemented Phase 2 Boundary Safety.
 */

'use strict';

const path = (typeof require !== 'undefined') ? require('path') : null;

/**
 * Validates entries in a ZIP archive to ensure they do not escape the target directory.
 * @param {object} zip - adm-zip or compatible object
 * @param {string} targetDir - The base directory for extraction
 * @throws {Error} if Zip Slip is detected
 */
function secure_zip_validate(zip, targetDir) {
    if (!path) return true; // Cannot validate without path module (browser context)
    
    const targetPath = path.resolve(targetDir);
    zip.getEntries().forEach(entry => {
        const entryName = entry.entryName;
        const entryPath = path.resolve(targetPath, entryName);
        if (!entryPath.startsWith(targetPath)) {
            throw new Error(`Zip Slip detected: "${entryName}" attempts to escape target directory`);
        }
    });
    return true;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { secure_zip_validate };
}
if (typeof window !== 'undefined') {
    window.BEJSON_UTILITY = window.BEJSON_UTILITY || {};
    window.BEJSON_UTILITY.secure_zip_validate = secure_zip_validate;
}
