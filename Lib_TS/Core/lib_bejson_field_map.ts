/**
 * Library:      bejson_field_map.ts
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.1.0 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-02
 * Description:  TypeScript implementation of the Field Map Cache.
 */

import { BEJSONDocument } from './bejson_types';

/**
 * Field Map type: mapping of field name to its positional index.
 */
export type FieldMap = { [key: string]: number };

/**
 * Internal global cache for FieldMaps.
 */
const _FIELD_MAP_CACHE: Map<string, FieldMap> = new Map();

/**
 * Generates a mapping of field names to their indices for a BEJSON document.
 * Utilizes a global cache to speed up repeated access to similar structures.
 */
export function bejson_core_get_field_map(doc: BEJSONDocument): FieldMap {
    if (!doc || !doc.Fields) return {};

    // High-performance in-document cache check
    if ((doc as any)._bejson_field_map) return (doc as any)._bejson_field_map;
    
    const fieldNames = doc.Fields.map(f => f.name);
    const cacheKey = (doc.Format_Version || '104') + ':' + fieldNames.join(',');
    
    let fieldMap = _FIELD_MAP_CACHE.get(cacheKey);
    
    if (!fieldMap) {
        fieldMap = {};
        doc.Fields.forEach((f, i) => {
            fieldMap![f.name] = i;
        });
        _FIELD_MAP_CACHE.set(cacheKey, fieldMap);
    }

    // Inject into document for subsequent O(1) lookups
    try { (doc as any)._bejson_field_map = fieldMap; } catch(e) {}
    
    return fieldMap;
}

/**
 * Returns the index of a specific field by name, using the cache.
 */
export function bejson_core_get_field_index(doc: BEJSONDocument, fieldName: string): number {
    const fieldMap = bejson_core_get_field_map(doc);
    const idx = fieldMap[fieldName];
    return (idx !== undefined) ? idx : -1;
}

/**
 * Clears the internal field map cache.
 */
export function bejson_core_clear_field_map_cache(): void {
    _FIELD_MAP_CACHE.clear();
}
