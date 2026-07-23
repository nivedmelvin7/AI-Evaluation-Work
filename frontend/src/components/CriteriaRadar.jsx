import React from 'react';
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts';
import { humanizeCriterion } from '../utils.js';

const ORDER = ['technical_accuracy', 'methodology', 'critical_thinking', 'evidence_quality', 'structure', 'clarity', 'referencing', 'originality', 'professionalism'];

export default function CriteriaRadar({ scoring }) {
  const breakdown = scoring?.criterion_breakdown;
  if (!breakdown) return null;
  const data = ORDER.filter((key) => breakdown[key]).map((key) => ({
    criterion: humanizeCriterion(key),
    score: Math.round(((Number(breakdown[key].s_i) || 0) * 100)),
    weight: Math.round((Number(breakdown[key].weight) || 0) * 100),
  }));
  if (!data.length) return null;

  return (
    <div className="criteria-radar">
      <div className="chart-heading">
        <span>Criteria profile</span>
        <small>Normalised score</small>
      </div>
      <div className="criteria-radar-chart">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="66%">
            <PolarGrid stroke="var(--chart-grid)" />
            <PolarAngleAxis dataKey="criterion" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
            <Tooltip formatter={(value, _name, props) => [`${value}%`, `Score · ${props.payload.weight}% weight`]} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Radar name="Score" dataKey="score" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.23} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
