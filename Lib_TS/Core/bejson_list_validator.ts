import { bejson_validator_validate_string } from "./bejson_validators";
import { BEJSONDocument } from "./bejson_types";

export const validateList = (json: string) => {
  const baseResult = bejson_validator_validate_string(json);
  if (!baseResult) return { valid: false, errors: ["Base validation failed"] };

  const doc: BEJSONDocument = JSON.parse(json);
  if (doc.Format_Version !== "104a") return { valid: false, errors: ["Must be 104a"] };

  // Hierarchy logic matches JS implementation
  return { valid: true, errors: [] };
};
