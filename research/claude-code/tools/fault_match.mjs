export function faultMatches(fault, urlPath, bodyText) {
  if (fault.path_contains !== undefined) {
    if (typeof fault.path_contains !== "string" || !urlPath.includes(fault.path_contains)) return false;
  }
  if (fault.body_contains !== undefined) {
    if (typeof fault.body_contains !== "string" || !bodyText.includes(fault.body_contains)) return false;
  }
  if (fault.body_contains_all !== undefined) {
    if (!Array.isArray(fault.body_contains_all) ||
        !fault.body_contains_all.every((marker) => typeof marker === "string" && bodyText.includes(marker))) {
      return false;
    }
  }
  if (fault.body_not_contains !== undefined) {
    if (!Array.isArray(fault.body_not_contains) ||
        !fault.body_not_contains.every((marker) => typeof marker === "string" && !bodyText.includes(marker))) {
      return false;
    }
  }
  return true;
}
