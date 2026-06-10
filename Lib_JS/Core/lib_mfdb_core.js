/**
 * Library:      lib_mfdb_core.js
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.3 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-09
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
     * @returns {Promise<{manifestDoc: Object, docMap: Object}>}
     */
    static async mount(zipFile, dirHandle) {
        if (!JSZip) throw new Error("JSZip library not found. Required for archive operations.");
        
        const zip = await JSZip.loadAsync(zipFile);
        const docMap = {};
        let manifestDoc = null;
        
        // REMEDIATED: Secure ZIP validation (Audit Finding 2).
        const utility = (typeof window !== 'undefined' && window.BEJSON_UTILITY) 
            ? window.BEJSON_UTILITY 
            : (typeof require !== 'undefined' ? require('./lib_bejson_secure_zip.js') : null);
        
        if (utility && utility.secure_zip_validate) {
            utility.secure_zip_validate({ getEntries: () => Object.keys(zip.files).map(k => ({ entryName: k })) }, dirHandle.name || "mount_root");
        }
        
        // Check for manifest
        if (!zip.file("104a.mfdb.bejson")) {
            throw new Error("Invalid MFDB Archive: 104a.mfdb.bejson missing at root.");
        }

        // Virtual "Extraction" to Directory Handle and Memory
        for (const [path, file] of Object.entries(zip.files)) {
            if (file.dir) continue;
            
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

            // Populate docMap for in-memory operations
            if (path.endsWith('.bejson')) {
                const text = await file.async("string");
                try {
                    const doc = JSON.parse(text);
                    docMap[path] = doc;
                    if (path === "104a.mfdb.bejson") manifestDoc = doc;
                } catch (e) {
                    console.warn(`[MFDB] Failed to parse ${path}:`, e);
                }
            }
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

        return { manifestDoc, docMap };
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
    version: "1.31",
    
    /**
     * load_manifest_from_doc (JS Mirror)
     * Returns manifest records as objects.
     */
    load_manifest_from_doc(doc) {
        return this.records_as_dicts(doc);
    },

    /**
     * records_as_dicts (JS Mirror)
     * Helper to convert BEJSON doc to array of objects using Field Map.
     */
    records_as_dicts(doc) {
        if (!doc || !doc.Fields || !doc.Values) return [];
        const fields = doc.Fields.map(f => f.name);
        return doc.Values.map(row => {
            const obj = {};
            fields.forEach((name, i) => { obj[name] = row[i]; });
            return obj;
        });
    },

    /**
     * mfdb_core_get_stats_from_map (JS Mirror)
     * Returns stats using in-memory docMap.
     */
    get_stats_from_map(manifestDoc, docMap) {
        const stats = { entity_count: 0, record_count: 0, total_bytes: 0 };
        const entries = this.load_manifest_from_doc(manifestDoc);
        
        entries.forEach(entry => {
            stats.entity_count++;
            const entDoc = docMap[entry.file_path];
            if (entDoc) {
                stats.record_count += (entDoc.Values ? entDoc.Values.length : 0);
            }
        });
        return stats;
    },

    /**
     * mfdb_core_load_entity_from_map (JS Mirror)
     * Returns entity records as objects using in-memory docMap.
     */
    load_entity_from_map(manifestDoc, docMap, entityName) {
        const entries = this.load_manifest_from_doc(manifestDoc);
        const entry = entries.find(e => e.entity_name === entityName);
        if (!entry) return null;
        
        const entDoc = docMap[entry.file_path];
        return entDoc ? this.records_as_dicts(entDoc) : null;
    },

    /**
     * mfdb_core_query_entity_from_map (JS Mirror)
     */
    query_entity_from_map(manifestDoc, docMap, entityName, predicate) {
        const records = this.load_entity_from_map(manifestDoc, docMap, entityName);
        return records ? records.filter(predicate) : [];
    },

    /**
     * mfdb_core_build_index_from_map (JS Mirror)
     */
    build_index_from_map(manifestDoc, docMap, entityName, fieldName) {
        const records = this.load_entity_from_map(manifestDoc, docMap, entityName);
        if (!records) return {};
        const index = {};
        records.forEach(r => {
            const val = r[fieldName];
            if (val !== undefined && val !== null) index[val] = r;
        });
        return index;
    },

    /**
     * mfdb_core_get_stats (JS Mirror)
     * Returns summary statistics for an MFDB directory handle.
     */
    async get_stats(dirHandle) {
        const stats = { entity_count: 0, record_count: 0, total_bytes: 0 };
        try {
            const manifestHandle = await dirHandle.getFileHandle('104a.mfdb.bejson');
            const file = await manifestHandle.getFile();
            const doc = JSON.parse(await file.text());
            
            const fpIdx = doc.Fields.findIndex(f => f.name === 'file_path');
            const enIdx = doc.Fields.findIndex(f => f.name === 'entity_name');
            
            for (const row of doc.Values) {
                stats.entity_count++;
                try {
                    const entPath = row[fpIdx];
                    const entHandle = await dirHandle.getFileHandle(entPath);
                    const entFile = await entHandle.getFile();
                    stats.total_bytes += entFile.size;
                    const entDoc = JSON.parse(await entFile.text());
                    stats.record_count += (entDoc.Values ? entDoc.Values.length : 0);
                } catch (e) {
                    console.warn(`[MFDB] Failed to stat entity: ${row[enIdx]}`);
                }
            }
        } catch (e) {
            console.error("[MFDB] Failed to get stats:", e);
        }
        return stats;
    },

    /**
     * mfdb_core_load_entity (JS Mirror)
     * Loads a specific entity from an MFDB directory handle as an array of objects.
     */
    async load_entity(dirHandle, entityName) {
        try {
            const manifestHandle = await dirHandle.getFileHandle('104a.mfdb.bejson');
            const file = await manifestHandle.getFile();
            const doc = JSON.parse(await file.text());
            
            const fpIdx = doc.Fields.findIndex(f => f.name === 'file_path');
            const enIdx = doc.Fields.findIndex(f => f.name === 'entity_name');
            
            const entry = doc.Values.find(row => row[enIdx] === entityName);
            if (!entry) throw new Error(`Entity not found: ${entityName}`);
            
            const entHandle = await dirHandle.getFileHandle(entry[fpIdx]);
            const entFile = await entHandle.getFile();
            const entDoc = JSON.parse(await entFile.text());
            
            const fields = entDoc.Fields.map(f => f.name);
            return entDoc.Values.map(row => {
                const obj = {};
                fields.forEach((name, i) => { obj[name] = row[i]; });
                return obj;
            });
        } catch (e) {
            console.error(`[MFDB] Failed to load entity ${entityName}:`, e);
            throw e;
        }
    }
};
