import React, { useMemo, useState } from 'react';
import { humanizeCriterion } from '../utils.js';

const CRITERION_ORDER = ['technical_accuracy', 'methodology', 'critical_thinking', 'evidence_quality', 'structure', 'clarity', 'referencing', 'originality', 'professionalism'];

const CONFIDENCE_RANK = { high: 3, medium: 2, low: 1 };

const COLUMNS = [
  { key: 'name', label: 'Criterion', sortValue: (row) => humanizeCriterion(row.key).toLowerCase() },
  { key: 'level', label: 'Level', sortValue: (row) => row.level ?? -1 },
  { key: 'weight', label: 'Weight', sortValue: (row) => row.weight ?? -1 },
  { key: 'score', label: 'Score', sortValue: (row) => row.s_i ?? -1 },
  { key: 'confidence', label: 'Confidence', sortValue: (row) => CONFIDENCE_RANK[row.confidence] ?? 0 },
  { key: 'contribution', label: 'Contribution', sortValue: (row) => row.contribution ?? -1 },
  { key: 'uncertainty', label: 'Confidence risk (uᵢ)', sortValue: (row) => row.u_i ?? -1 },
];

function LevelBar({ level }) {
  return <div className="level-mini-bar">{Array.from({ length: 4 }, (_, index) => <span key={index} className={`level-mini-seg ${index < level ? 'filled' : ''}`} />)}</div>;
}

function ConfidenceCell({ value }) {
  const className = value === 'high' ? 'conf-high' : value === 'medium' ? 'conf-medium' : 'conf-low';
  return <span className={className} style={{ fontWeight: 500 }}>{value || '—'}</span>;
}

function ScoreMeter({ score }) {
  const percentage = Math.max(0, Math.min(100, (Number(score) || 0) * 100));
  return (
    <div className="criterion-score-meter" title={`Normalised score: ${percentage.toFixed(0)}%`}>
      <div className="criterion-score-meter-track">
        <span className="criterion-score-meter-fill" style={{ width: `${percentage}%` }} />
      </div>
      <span className="criterion-score-meter-label num">{percentage.toFixed(0)}%</span>
    </div>
  );
}

export default function CriterionTable({ scoring }) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const breakdown = scoring?.criterion_breakdown;
  const baseRows = useMemo(() => {
    if (!breakdown) return [];
    return CRITERION_ORDER.filter((key) => breakdown[key] != null).map((key) => ({ key, ...breakdown[key] }));
  }, [breakdown]);

  const rows = useMemo(() => {
    if (!sortKey) return baseRows;
    const column = COLUMNS.find((c) => c.key === sortKey);
    if (!column) return baseRows;
    const sorted = [...baseRows].sort((a, b) => {
      const av = column.sortValue(a);
      const bv = column.sortValue(b);
      if (av < bv) return -1;
      if (av > bv) return 1;
      return 0;
    });
    return sortDir === 'desc' ? sorted.reverse() : sorted;
  }, [baseRows, sortKey, sortDir]);

  if (!breakdown) return null;

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  return (
    <div className="criterion-table-wrap">
      <table className="criterion-table">
        <caption className="sr-only">
          Criterion breakdown: level, weight, normalised score, confidence, weighted contribution, and confidence risk for each of the nine assessment criteria. Columns are sortable.
        </caption>
        <thead>
          <tr>
            {COLUMNS.map((col) => {
              const active = sortKey === col.key;
              const ariaSort = active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none';
              return (
                <th key={col.key} aria-sort={ariaSort}>
                  <button
                    type="button"
                    onClick={() => handleSort(col.key)}
                    style={{
                      background: 'none', border: 'none', padding: 0, cursor: 'pointer',
                      font: 'inherit', color: active ? 'var(--accent)' : 'inherit',
                      display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                      textTransform: 'inherit', letterSpacing: 'inherit',
                    }}
                  >
                    {col.label}
                    {active && <span aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>}
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td className="criterion-name">{humanizeCriterion(row.key)}</td>
              <td><div className="criterion-level"><span className="level-pill">{row.level ?? '—'}</span>{row.level != null && <LevelBar level={row.level} />}</div></td>
              <td className="num">{row.weight != null ? `${(row.weight * 100).toFixed(0)}%` : '—'}</td>
              <td><ScoreMeter score={row.s_i} /></td>
              <td><ConfidenceCell value={row.confidence} /></td>
              <td className="num">{row.contribution?.toFixed(3) ?? '—'}</td>
              <td className="num">{row.u_i?.toFixed(2) ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
