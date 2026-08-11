import React from 'react';

export default function ScoreCard({ scoring }) {
  if (!scoring) return null;

  const {
    achievement_score,
    final_policy_score,
    provisional_score,
    provisional_grade_band,
    scoring_complete,
    content_based_estimate,
    missing_criteria,
    aggregate_uncertainty_U,
    uncertainty_band,
    gate_triggered,
    gate_reason,
    deferred,
    deferral_reason,
    holistic_validation,
  } = scoring;
  const uncertaintyText = Array.isArray(uncertainty_band) && uncertainty_band.length === 2
    ? `${uncertainty_band[0].toFixed(1)} - ${uncertainty_band[1].toFixed(1)}`
    : '-';
  const holisticText = !holistic_validation?.available
    ? 'Unavailable'
    : holistic_validation.requires_moderation ? 'Review needed' : 'Aligned';

  return (
    <div>
      <div className="score-meta-grid">
        <div className="score-meta-item">
          <div className="score-meta-label">Achievement score (F3)</div>
          <div className="score-meta-value num">{achievement_score?.toFixed(2) ?? 'Not scored'}</div>
        </div>
        <div className="score-meta-item">
          <div className="score-meta-label">Policy score (F7)</div>
          <div className="score-meta-value num">{final_policy_score?.toFixed(2) ?? 'Not scored'}</div>
        </div>
        <div className="score-meta-item">
          <div className="score-meta-label">Achievement uncertainty band (F6)</div>
          <div className="score-meta-value num">{uncertaintyText}</div>
        </div>
        <div className="score-meta-item">
          <div className="score-meta-label">Uncertainty index (U)</div>
          <div className="score-meta-value num">{aggregate_uncertainty_U?.toFixed(3) ?? '-'}</div>
        </div>
        <div className="score-meta-item">
          <div className="score-meta-label">Holistic check</div>
          <div className="score-meta-value">{holisticText}</div>
        </div>
        {provisional_score != null && (
          <div className="score-meta-item">
            <div className="score-meta-label">Provisional result</div>
            <div className="score-meta-value num">{provisional_score.toFixed(2)} · {provisional_grade_band}</div>
          </div>
        )}
      </div>

      {content_based_estimate && (
        <div className="flag-chips">
          <span className="badge badge-amber">
            Content-based score{missing_criteria?.length ? `: ${missing_criteria.length} non-core criterion${missing_criteria.length === 1 ? '' : 's'} could not be checked.` : '.'}
          </span>
        </div>
      )}
      {!scoring_complete && !content_based_estimate && !deferred && (
        <div className="flag-chips"><span className="badge badge-amber">Some assessment checks were unavailable.</span></div>
      )}

      {(gate_triggered || deferred || holistic_validation?.requires_moderation) && (
        <div className="flag-chips">
          {gate_triggered && <span className="badge badge-amber">Gate triggered{gate_reason ? `: ${gate_reason}` : ''}</span>}
          {deferred && <span className="badge badge-purple">Deferred{deferral_reason ? `: ${deferral_reason}` : ''}</span>}
          {holistic_validation?.requires_moderation && (
            <span className="badge badge-amber">Moderation needed: holistic grade is {holistic_validation.expected_grade_band}</span>
          )}
        </div>
      )}
    </div>
  );
}
