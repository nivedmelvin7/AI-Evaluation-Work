import React from 'react';

function PriorityBadge({ priority }) {
  const p = (priority || '').toLowerCase();
  if (p === 'high') return <span className="badge badge-red">High</span>;
  if (p === 'medium') return <span className="badge badge-amber">Medium</span>;
  return <span className="badge badge-gray">Low</span>;
}

export default function FeedbackPanel({ feedback }) {
  if (!feedback) return null;

  const {
    overall_assessment,
    strengths = [],
    areas_for_improvement = [],
    recommended_actions,
    closing,
  } = feedback;

  return (
    <div>
      {overall_assessment && (
        <div className="feedback-section">
          <div className="feedback-section-label">Overall assessment</div>
          <p className="feedback-prose">{overall_assessment}</p>
        </div>
      )}

      {strengths.length > 0 && (
        <div className="feedback-section">
          <div className="feedback-section-label">Strengths</div>
          <ul className="strengths-list">
            {strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {areas_for_improvement.length > 0 && (
        <div className="feedback-section">
          <div className="feedback-section-label">Areas for improvement</div>
          <ul className="improvement-list">
            {areas_for_improvement.map((item, i) => {
              const text = typeof item === 'string' ? item : item.text;
              const priority = typeof item === 'object' ? item.priority : undefined;
              const p = (priority || 'low').toLowerCase();
              return (
                <li key={i} className="improvement-item">
                  <div className={`priority-dot ${p}`} title={priority} />
                  <div style={{ flex: 1 }}>
                    {priority && (
                      <PriorityBadge priority={priority} />
                    )}
                    <span style={{ marginLeft: priority ? '0.5rem' : 0 }}>{text}</span>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {recommended_actions && (
        <div className="feedback-section">
          <div className="feedback-section-label">Recommended actions</div>
          <p className="feedback-prose">{recommended_actions}</p>
        </div>
      )}

      {closing && (
        <div className="feedback-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <p className="feedback-prose" style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>{closing}</p>
        </div>
      )}
    </div>
  );
}
