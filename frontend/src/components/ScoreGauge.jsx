import React from 'react';
import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';
import { gradeBadgeClass } from '../utils.js';

const GRADE_COLORS = {
  distinction: '#3ecf8e', merit: '#5b6af0', pass: '#f5a623', deferred: '#9b5de5', fail: '#e84040',
};

function gradeColor(grade) {
  return GRADE_COLORS[(grade || '').toLowerCase()] || GRADE_COLORS.fail;
}

export default function ScoreGauge({ scoring }) {
  if (!scoring) return null;
  const hasFinal = scoring.final_score != null && Number.isFinite(Number(scoring.final_score));
  const hasProvisional = !hasFinal && scoring.provisional_score != null && Number.isFinite(Number(scoring.provisional_score));
  const displayScore = hasFinal ? Number(scoring.final_score) : hasProvisional ? Number(scoring.provisional_score) : null;
  const chartScore = displayScore == null ? 0 : Math.max(0, Math.min(100, displayScore));
  const achievement = Number.isFinite(Number(scoring.achievement_score)) ? Number(scoring.achievement_score) : null;
  const interval = Array.isArray(scoring.achievement_uncertainty_band)
    ? scoring.achievement_uncertainty_band
    : (Array.isArray(scoring.uncertainty_band) ? scoring.uncertainty_band : []);
  const low = Math.max(0, Math.min(100, Number(interval[0])));
  const high = Math.max(low, Math.min(100, Number(interval[1])));
  const color = gradeColor(scoring.grade_band);
  const label = displayScore == null ? 'Not scored' : hasProvisional ? `Provisional ${displayScore.toFixed(2)}` : displayScore.toFixed(2);

  return (
    <div className="score-gauge" aria-label={`${hasProvisional ? 'Provisional' : 'Final'} score: ${label}, grade ${scoring.grade_band || 'unknown'}`}>
      <div className="score-gauge-chart">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="50%" innerRadius="72%" outerRadius="100%" startAngle={90} endAngle={-270} barSize={14} data={[{ value: chartScore, fill: color }]}>
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} axisLine={false} />
            <RadialBar background={{ fill: 'var(--gauge-track)' }} dataKey="value" cornerRadius={8} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="score-gauge-value">
          <strong>{label}</strong>
          <span>{hasProvisional ? 'provisional / 100' : displayScore == null ? 'assessment incomplete' : 'out of 100'}</span>
        </div>
      </div>
      <span className={`grade-badge score-gauge-badge ${gradeBadgeClass(scoring.grade_band)}`}>{scoring.grade_band || 'Unknown'}</span>
      {interval.length === 2 && achievement != null && Number.isFinite(low) && Number.isFinite(high) && (
        <div className="confidence-band-wrap">
          <div className="confidence-band-label">Achievement uncertainty band (F6) <span>{low.toFixed(2)}–{high.toFixed(2)}</span></div>
          <div className="confidence-band-track" aria-label={`Achievement uncertainty band ${low.toFixed(2)} to ${high.toFixed(2)}`}>
            <span className="confidence-band" style={{ left: `${low}%`, width: `${Math.max(high - low, 1)}%`, backgroundColor: color }} />
            <span className="confidence-marker" title={`Achievement score ${achievement.toFixed(2)}`} style={{ left: `${achievement}%`, borderColor: color }} />
          </div>
        </div>
      )}
    </div>
  );
}
