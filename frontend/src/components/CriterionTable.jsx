import React from 'react';
import { humanizeCriterion } from '../utils.js';

// Ordered by weight descending
const CRITERION_ORDER = [
  'technical_accuracy',
  'methodology',
  'critical_thinking',
  'evidence_quality',
  'structure',
  'clarity',
  'referencing',
  'originality',
  'professionalism',
];

function LevelBar({ level }) {
  const max = 4;
  return (
    <div className="level-bar-wrap">
      <div className="level-mini-bar">
        {Array.from({ length: max + 1 }, (_, i) => (
          <div key={i} className={`level-mini-seg ${i <= level ? 'filled' : ''}`} />
        ))}
      </div>
    </div>
  );
}

function ConfidenceCell({ value }) {
  const cls = value === 'high' ? 'conf-high' : value === 'medium' ? 'conf-medium' : 'conf-low';
  return <span className={cls} style={{ fontWeight: 500 }}>{value || '—'}</span>;
}

export default function CriterionTable({ scoring }) {
  if (!scoring?.criterion_breakdown) return null;

  const breakdown = scoring.criterion_breakdown;

  const rows = CRITERION_ORDER
    .filter((key) => breakdown[key] != null)
    .map((key) => ({ key, ...breakdown[key] }));

  return (
    <div className="criterion-table-wrap">
      <table className="criterion-table">
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Level</th>
            <th>Weight</th>
            <th>Score (sᵢ)</th>
            <th>Confidence</th>
            <th>Contribution</th>
            <th>Uncertainty contrib.</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                {humanizeCriterion(row.key)}
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="level-pill">{row.level ?? '—'}</span>
                  {row.level != null && <LevelBar level={row.level} />}
                </div>
              </td>
              <td className="num">{row.weight != null ? `${(row.weight * 100).toFixed(0)}%` : '—'}</td>
              <td className="num">{row.s_i?.toFixed(2) ?? '—'}</td>
              <td><ConfidenceCell value={row.confidence} /></td>
              <td className="num">{row.contribution?.toFixed(3) ?? '—'}</td>
              <td className="num">{row.uncertainty_contribution?.toFixed(3) ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
