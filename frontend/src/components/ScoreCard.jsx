import React from 'react';

export default function ScoreCard({ scoring }) {
  if (!scoring) return null;

  const {
    achievement_score,
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
          <div className="score-meta-label">Weighted score</div>
          <div className="score-meta-value num">{achievement_score?.toFixed(1) ?? '-'}</div>
        </div>
        <div className="score-meta-item">
          <div className="score-meta-label">Uncertainty band</div>
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
      </div>

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
