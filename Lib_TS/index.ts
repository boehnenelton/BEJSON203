/**
 * Library:      index.ts
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.2 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-06-02
 * Description:  Main entry point for TypeScript library family.
 */

// Types & error classes
export * from "./Core/lib_bejson_types";

// Core operations (parse, serialize, record CRUD)
export * from "./Core/lib_bejson_core";

// BEJSON validators (104, 104a, 104db)
export {
  validateDocument,
  validate104,
  validate104a,
  validate104db,
  assertValid,
  isValid,
} from "./Core/lib_bejson_validators";

// MFDB validators
export {
  discoverRole,
  validateManifest,
  validateEntityFile,
  validateDatabase,
  decodeManifestRecords,
  decodeDatabaseMeta,
} from "./Core/lib_mfdb_validators";

// MFDB core
export {
  createManifest,
  registerEntity,
  unregisterEntity,
  syncRecordCount,
} from "./Core/lib_mfdb_core";

export type { EntityValidationOptions, DatabaseValidationOptions } from "./Core/lib_mfdb_validators";
export type { CreateManifestOptions as MFDBCreateManifestOptions } from "./Core/lib_mfdb_core";

export * from "./Gaming/bejson_assets";
export * from "./Gaming/bejson_engine";
export * from "./Gaming/bejson_events";
export * from "./Gaming/bejson_grid";
export * from "./Gaming/bejson_input";
export * from "./Gaming/bejson_physics";
export * from "./Gaming/bejson_renderer";

// Schema management
export * from "./Core/lib_bejson_schema";
