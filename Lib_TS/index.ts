/**
 * Library:      index.ts
 * Family:       Core
 * Jurisdiction: ["BEJSON_LIBRARIES", "TS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Main entry point for TypeScript library family.
 */

// Types & error classes
export * from "./bejson_types";

// Core operations (parse, serialize, record CRUD)
export * from "./bejson_core";

// BEJSON validators (104, 104a, 104db)
export {
  validateDocument,
  validate104,
  validate104a,
  validate104db,
  assertValid,
  isValid,
} from "./bejson_validators";

// MFDB validators
export {
  discoverRole,
  validateManifest,
  validateEntityFile,
  validateDatabase,
  decodeManifestRecords,
  decodeDatabaseMeta,
} from "./mfdb_validators";

// MFDB core
export {
  createManifest,
  registerEntity,
  unregisterEntity,
  syncRecordCount,
} from "./mfdb_core";

export type { EntityValidationOptions, DatabaseValidationOptions } from "./mfdb_validators";
export type { CreateManifestOptions as MFDBCreateManifestOptions } from "./mfdb_core";

export * from "./bejson_assets";
export * from "./bejson_engine";
export * from "./bejson_events";
export * from "./bejson_grid";
export * from "./bejson_input";
export * from "./bejson_physics";
export * from "./bejson_renderer";

// Schema management
export * from "./bejson_schema";
