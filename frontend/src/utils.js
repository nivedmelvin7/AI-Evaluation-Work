/**
 * Converts a snake_case criterion key to a humanized display name.
 * e.g. "technical_accuracy" → "Technical Accuracy"
 */
export function humanizeCriterion(key) {
  if (!key) return '';
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
