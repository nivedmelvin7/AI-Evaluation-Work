import React from 'react';
import { RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

const GRADE_COLORS = {
  distinction: '#3ecf8e',
  merit: '#5b6af0',
  pass: '#f5a623',
  deferred: '#9b5de5',
  fail: '#e84040',
};

function gradeColor(grade) {
  return GRADE_COLORS[(grade || '').toLowerCase()] || GRADE_COLORS.fail;
}

export default function ScoreGauge({ scoring }) {
  if (!scoring) return null;
  const score = Math.max(0, Math.min(100, Number(scoring.final_score) || 0));
  const interval = Array.isArray(scoring.uncertainty_band) ? scoring.uncertainty_band : [];
  const low = Math.max(0, Math.min(100, Number(interval[0])));
  const high = Math.max(low, Math.min(100, Number(interval[1])));
  const color = gradeColor(scoring.grade_band);

  return (
    <div className="score-gauge" aria-label={`Final score: ${score} out of 100`}>
      <div className="score-gauge-chart">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="50%" innerRadius="72%" outerRadius="100%" startAngle={90} endAngle={-270} barSize={14} data={[{ value: score, fill: color }]}>
            <RadialBar background={{ fill: 'var(--gauge-track)' }} dataKey="value" cornerRadius={8} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="score-gauge-value">
          <strong>{score}</strong>
          <span>out of 100</span>
        </div>
      </div>
      {interval.length === 2 && Number.isFinite(low) && Number.isFinite(high) && (
        <div className="confidence-band-wrap">
          <div className="confidence-band-label">Uncertainty band <span>{low.toFixed(1)}–{high.toFixed(1)}</span></div>
          <div className="confidence-band-track" aria-label={`Uncertainty band ${low.toFixed(1)} to ${high.toFixed(1)}`}>
            <span className="confidence-band" style={{ left: `${low}%`, width: `${Math.max(high - low, 1)}%`, backgroundColor: color }} />
            <span className="confidence-marker" style={{ left: `${score}%`, borderColor: color }} />
          </div>
        </div>
      )}
    </div>
  );
}
