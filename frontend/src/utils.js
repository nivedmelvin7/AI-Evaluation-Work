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

const GRADE_BADGE_CLASSES = {
  DISTINCTION: 'grade-distinction',
  MERIT: 'grade-merit',
  PASS: 'grade-pass',
  DEFERRED: 'grade-deferred',
};

/**
 * Returns the CSS class for a grade-band badge, defaulting to the "fail" styling
 * for any unrecognised or missing grade.
 */
export function gradeBadgeClass(grade) {
  return GRADE_BADGE_CLASSES[(grade || '').toUpperCase()] || 'grade-fail';
}

const CRITERION_ORDER = ['technical_accuracy', 'methodology', 'critical_thinking', 'evidence_quality', 'structure', 'clarity', 'referencing', 'originality', 'professionalism'];

/**
 * Returns { strongest, weakest } criterion rows (by normalised score s_i),
 * or nulls when there isn't enough data to compare.
 */
export function strongestWeakestCriteria(scoring) {
  const breakdown = scoring?.criterion_breakdown;
  if (!breakdown) return { strongest: null, weakest: null };
  const rows = CRITERION_ORDER
    .filter((key) => breakdown[key] != null)
    .map((key) => ({ key, ...breakdown[key] }));
  if (rows.length === 0) return { strongest: null, weakest: null };
  const sorted = [...rows].sort((a, b) => (b.s_i ?? 0) - (a.s_i ?? 0));
  return { strongest: sorted[0], weakest: sorted[sorted.length - 1] };
}

const PRIORITY_RANK = { high: 3, medium: 2, low: 1 };

/**
 * Returns up to `limit` improvement items sorted by priority (high first),
 * normalising both the legacy string format and the {text, priority} format.
 */
export function topRecommendations(feedback, limit = 3) {
  const items = feedback?.areas_for_improvement || [];
  return [...items]
    .map((item) => (typeof item === 'string' ? { text: item, priority: undefined } : item))
    .sort((a, b) => (PRIORITY_RANK[(b.priority || '').toLowerCase()] || 0) - (PRIORITY_RANK[(a.priority || '').toLowerCase()] || 0))
    .slice(0, limit);
}
