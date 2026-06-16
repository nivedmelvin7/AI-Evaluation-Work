import React from 'react';

function gradeMeta(grade) {
  const g = (grade || '').toUpperCase();
  if (g === 'DISTINCTION') return { cls: 'distinction', badgeCls: 'grade-distinction' };
  if (g === 'MERIT')       return { cls: 'merit',       badgeCls: 'grade-merit' };
  if (g === 'PASS')        return { cls: 'pass',        badgeCls: 'grade-pass' };
  if (g === 'DEFERRED')    return { cls: 'deferred',    badgeCls: 'grade-deferred' };
  return { cls: 'fail', badgeCls: 'grade-fail' };
}

export default function ScoreCard({ scoring }) {
  if (!scoring) return null;

  const {
    final_score,
    grade_band,
    penalised_score,
    baseline_score,
    aggregate_uncertainty_U,
    confidence_interval,
    gate_triggered,
    gate_reason,
    deferred,
    deferral_reason,
  } = scoring;

  const { cls, badgeCls } = gradeMeta(grade_band);

  const ciStr = Array.isArray(confidence_interval) && confidence_interval.length === 2
    ? `${confidence_interval[0].toFixed(1)} – ${confidence_interval[1].toFixed(1)}`
    : '—';

  return (
    <div>
      <div className="score-hero">
        {/* Big score */}
        <div className="score-big">
          <div className={`score-number ${cls}`}>{final_score ?? '—'}</div>
          <span className={`grade-badge ${badgeCls}`}>{grade_band || 'Unknown'}</span>
        </div>

        {/* Meta tiles */}
        <div className="score-meta-grid">
          <div className="score-meta-item">
            <div className="score-meta-label">Penalised score</div>
            <div className="score-meta-value num">{penalised_score?.toFixed(1) ?? '—'}</div>
          </div>
          <div className="score-meta-item">
            <div className="score-meta-label">Baseline score</div>
            <div className="score-meta-value num">{baseline_score?.toFixed(1) ?? '—'}</div>
          </div>
          <div className="score-meta-item">
            <div className="score-meta-label">Confidence interval</div>
            <div className="score-meta-value num">{ciStr}</div>
          </div>
          <div className="score-meta-item">
            <div className="score-meta-label">Uncertainty (U)</div>
            <div className="score-meta-value num">{aggregate_uncertainty_U?.toFixed(3) ?? '—'}</div>
          </div>
        </div>
      </div>

      {/* Flag chips */}
      {(gate_triggered || deferred) && (
        <div className="flag-chips">
          {gate_triggered && (
            <span className="badge badge-amber">
              ⚠ Gate triggered{gate_reason ? `: ${gate_reason}` : ''}
            </span>
          )}
          {deferred && (
            <span className="badge badge-purple">
              ⏸ Deferred{deferral_reason ? `: ${deferral_reason}` : ''}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
