export function faultMatches(fault, urlPath, bodyText) {
  if (fault.path_contains && !urlPath.includes(fault.path_contains)) return false;
  if (fault.body_contains && !bodyText.includes(fault.body_contains)) return false;
  if (fault.body_contains_all && !fault.body_contains_all.every((marker) => bodyText.includes(marker))) return false;
  return true;
}
