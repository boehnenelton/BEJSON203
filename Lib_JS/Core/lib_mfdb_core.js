/**
 * Library:      lib_mfdb_core.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Multi-file database orchestrator managing manifests and entity synchronization.
 */

'use strict';

const JSZip = window.JSZip || (typeof require !== 'undefined' ? require('jszip') : null);

/**
 * MFDBArchive Class - Vanilla Implementation
 * Leverages the Browser's File System Access API and JSZip.
 */
class MFDBArchive {
    /**
     * mount (Browser version)
     * @param {File|Blob} zipFile - The .mfdb.zip file.
     * @param {FileSystemDirectoryHandle} dirHandle - The target directory handle.
     */
    static async mount(zipFile, dirHandle) {
        if (!JSZip) throw new Error("JSZip library not found. Required for archive operations.");
        
        const zip = await JSZip.loadAsync(zipFile);
        
        // Check for manifest
        if (!zip.file("104a.mfdb.bejson")) {
            throw new Error("Invalid MFDB Archive: 104a.mfdb.bejson missing at root.");
        }

        // Virtual "Extraction" to Directory Handle
        for (const [path, file] of Object.entries(zip.files)) {
            if (file.dir) continue; // Skip directories (created as needed by getFileHandle)
            
            const pathParts = path.split('/');
            const fileName = pathParts.pop();
            let currentDir = dirHandle;

            // Navigate/Create subdirectories
            for (const part of pathParts) {
                if (part === "") continue;
                currentDir = await currentDir.getDirectoryHandle(part, { create: true });
            }

            const data = await file.async("uint8array");
            const fileHandle = await currentDir.getFileHandle(fileName, { create: true });
            const writable = await fileHandle.createWritable();
            await writable.write(data);
            await writable.close();
        }

        // Create session lock file
        const lockHandle = await dirHandle.getFileHandle('.mfdb_lock', { create: true });
        const lockWritable = await lockHandle.createWritable();
        const lockData = {
            mounted_at: new Date().toISOString(),
            original_name: zipFile.name || "archive.mfdb.zip"
        };
        await lockWritable.write(JSON.stringify(lockData));
        await lockWritable.close();

        return "Mounted successfully to FileSystemHandle";
    }

    /**
     * commit (Browser version)
     * Repacks the directory handle back into a JSZip Blob.
     */
    static async commit(dirHandle) {
        if (!JSZip) throw new Error("JSZip library not found.");
        
        const zip = new JSZip();
        
        async function readDir(handle, currentPath = "") {
            for await (const entry of handle.values()) {
                if (entry.name === '.mfdb_lock') continue;
                
                if (entry.kind === 'file') {
                    const file = await entry.getFile();
                    const data = await file.arrayBuffer();
                    zip.file(currentPath + entry.name, data);
                } else if (entry.kind === 'directory') {
                    await readDir(entry, currentPath + entry.name + "/");
                }
            }
        }

        await readDir(dirHandle);
        return await zip.generateAsync({ type: "blob", compression: "DEFLATE" });
    }
}

// Attach to global scope
window.MFDB_CORE = {
    ...window.MFDB_CORE,
    MFDBArchive,
    version: "1.21"
};
