/**
 * Library:      lib_bejson_utility.js
 * Family:       Utility
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  General-purpose helper functions for the BEJSON ecosystem.
 */

const fs = require('fs');
const path = require('path');

const DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".sh", ".txt", ".bejson"];
const DEFAULT_EXCLUDES = [".git", "__pycache__", "node_modules", "lib", "output", ".mfdb_lock"];

const CHUNK_SCHEMA = [
    { name: "Record_Type_Parent", type: "string" },
    { name: "id", type: "string" },
    { name: "timestamp", type: "string" },
    { name: "project_name", type: "string", Record_Type_Parent: "Project" },
    { name: "current_version", type: "string", Record_Type_Parent: "Project" },
    { name: "version_label", type: "string", Record_Type_Parent: "Snapshot" },
    { name: "version_notes", type: "string", Record_Type_Parent: "Snapshot" },
    { name: "changes", type: "string", Record_Type_Parent: "Snapshot" },
    { name: "file_path", type: "string", Record_Type_Parent: "File" },
    { name: "content", type: "string", Record_Type_Parent: "File" },
    { name: "snapshot_id_fk", type: "string", Record_Type_Parent: "File" }
];

function walk(dir, results = []) {
    const list = fs.readdirSync(dir);
    list.forEach((file) => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat && stat.isDirectory()) {
            if (!DEFAULT_EXCLUDES.includes(file)) {
                walk(filePath, results);
            }
        } else {
            results.push(filePath);
        }
    });
    return results;
}

function bejson_utility_init_project_db(projectName) {
    const now = new Date().toISOString();
    return {
        Format: "BEJSON",
        Format_Version: "104db",
        Format_Creator: "Elton Boehnen",
        Records_Type: ["Project", "Snapshot", "File"],
        Fields: CHUNK_SCHEMA,
        Values: [
            ["Project", `PROJ-${projectName}`, now, projectName, "0.0.0", null, null, null, null, null, null]
        ]
    };
}

function bejson_utility_snapshot_project(dbDoc, targetDir, versionLabel, notes = "", changes = "") {
    const targetPath = path.resolve(targetDir);
    const now = new Date().toISOString();
    const snapshotId = `SNAP-${Date.now()}`;
    
    // Update current version
    dbDoc.Values.forEach(row => {
        if (row[0] === "Project") row[4] = versionLabel;
    });

    // Add Snapshot (11 fields)
    dbDoc.Values.push(["Snapshot", snapshotId, now, null, null, versionLabel, notes, changes, null, null, null]);

    const files = walk(targetPath);
    files.forEach(fPath => {
        const ext = path.extname(fPath).toLowerCase();
        if (DEFAULT_EXTENSIONS.includes(ext)) {
            const relPath = path.relative(targetPath, fPath);
            const content = fs.readFileSync(fPath, 'utf8');
            // File row (11 fields)
            dbDoc.Values.push(["File", `FILE-${relPath}`, now, null, null, null, null, null, relPath, content, snapshotId]);
        }
    });

    return dbDoc;
}

function bejson_utility_restore_version(dbDoc, versionLabel, outputDir) {
    const fields = dbDoc.Fields.map(f => f.name);
    const snapIdIdx = fields.indexOf("id");
    const vlabelIdx = fields.indexOf("version_label");
    const fpathIdx = fields.indexOf("file_path");
    const contIdx = fields.indexOf("content");
    const fkIdx = fields.indexOf("snapshot_id_fk");

    let snapshotId = null;
    dbDoc.Values.forEach(row => {
        if (row[0] === "Snapshot" && row[vlabelIdx] === versionLabel) snapshotId = row[snapIdIdx];
    });

    if (!snapshotId) throw new Error(`Version '${versionLabel}' not found.`);

    const outRoot = path.resolve(outputDir);
    let count = 0;

    dbDoc.Values.forEach(row => {
        if (row[0] === "File" && row[fkIdx] === snapshotId) {
            const relPath = row[fpathIdx];
            const content = row[contIdx];
            if (relPath) {
                const targetFile = path.join(outRoot, relPath);
                const targetDir = path.dirname(targetFile);
                if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });
                fs.writeFileSync(targetFile, content, 'utf8');
                count++;
            }
        }
    });

    return count;
}

module.exports = {
    bejson_utility_init_project_db,
    bejson_utility_snapshot_project,
    bejson_utility_restore_version
};
