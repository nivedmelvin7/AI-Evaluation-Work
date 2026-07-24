import React from 'react';
import ScoreCard from './ScoreCard.jsx';
import ScoreGauge from './ScoreGauge.jsx';
import CriteriaRadar from './CriteriaRadar.jsx';
import { humanizeCriterion, strongestWeakestCriteria, topRecommendations } from '../utils.js';

function CriterionCallout({ label, row, tone }) {
  if (!row) return null;
  return (
    <div className="meta-item">
      <div className="meta-item-label">{label}</div>
      <div className="meta-item-value" style={{ color: tone === 'good' ? 'var(--success)' : 'var(--warning)' }}>
        {humanizeCriterion(row.key)} · {Math.round((row.s_i ?? 0) * 100)}%
      </div>
    </div>
  );
}

export default function OverviewSummary({ scoring, feedback, onGoToCriteria }) {
  const { strongest, weakest } = strongestWeakestCriteria(scoring);
  const recommendations = topRecommendations(feedback, 3);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      <div className="result-visual-grid">
        <div className="card">
          <div className="card-header"><span className="card-title">Score &amp; Grade</span></div>
          <div className="card-body score-card-body"><ScoreGauge scoring={scoring} /><ScoreCard scoring={scoring} /></div>
        </div>
        <div className="card"><div className="card-body"><CriteriaRadar scoring={scoring} /></div></div>
      </div>

      {(strongest || weakest) && (
        <div className="card">
          <div className="card-header"><span className="card-title">Strongest &amp; weakest criteria</span></div>
          <div className="card-body">
            <div className="meta-grid">
              <CriterionCallout label="Strongest" row={strongest} tone="good" />
              <CriterionCallout label="Needs the most work" row={weakest} tone="warn" />
            </div>
            <button type="button" className="btn btn-ghost btn-sm mt-2" onClick={onGoToCriteria}>
              View full criteria breakdown →
            </button>
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="card">
          <div className="card-header"><span className="card-title">Highest-priority recommendations</span></div>
          <div className="card-body">
            <ul className="improvement-list">
              {recommendations.map((item, i) => {
                const p = (item.priority || 'low').toLowerCase();
                return (
                  <li key={i} className="improvement-item">
                    <div className={`priority-dot ${p}`} title={item.priority} />
                    <span>{item.text}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
