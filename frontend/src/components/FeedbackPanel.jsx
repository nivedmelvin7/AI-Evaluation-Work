import React, { useState } from 'react';

function PriorityBadge({ priority }) {
  const p = (priority || '').toLowerCase();
  if (p === 'high') return <span className="badge badge-red">High</span>;
  if (p === 'medium') return <span className="badge badge-amber">Medium</span>;
  return <span className="badge badge-gray">Low</span>;
}

function CitationChip({ citation, index, onHover, onLeave }) {
  const [tipVisible, setTipVisible] = useState(false);
  if (!citation?.quote) return null;

  function handleEnter() {
    setTipVisible(true);
    onHover?.(citation);
  }
  function handleLeave() {
    setTipVisible(false);
    onLeave?.();
  }

  const label = citation.section
    ? `§${citation.section.replace(/_/g, ' ')}`
    : '§source';

  return (
    <span className="citation-chip-wrap">
      <span
        className="citation-chip"
        onMouseEnter={handleEnter}
        onMouseLeave={handleLeave}
        role="button"
        tabIndex={0}
        aria-label={`Citation from ${label}: ${citation.quote}`}
      >
        [{index + 1}] {label}
        {citation.page && <span className="citation-page"> p.{citation.page}</span>}
      </span>
      {tipVisible && (
        <span className="citation-tooltip">
          <span className="citation-tooltip-section">{label}</span>
          <span className="citation-tooltip-quote">"{citation.quote}"</span>
          {citation.page && (
            <span className="citation-tooltip-page">Page {citation.page}</span>
          )}
        </span>
      )}
    </span>
  );
}

function FeedbackText({ item, onHover, onLeave }) {
  // item can be a string (old format) or {text, citations} (new format)
  if (typeof item === 'string') {
    return <span>{item}</span>;
  }
  const { text, citations = [] } = item;
  return (
    <span>
      {text}
      {citations.length > 0 && (
        <span className="citation-chips-row">
          {citations.map((cit, i) => (
            <CitationChip
              key={i}
              citation={cit}
              index={i}
              onHover={onHover}
              onLeave={onLeave}
            />
          ))}
        </span>
      )}
    </span>
  );
}

export default function FeedbackPanel({ feedback, onCitationHover, onCitationLeave }) {
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
              <li key={i}>
                <FeedbackText
                  item={s}
                  onHover={onCitationHover}
                  onLeave={onCitationLeave}
                />
              </li>
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
                    {priority && <PriorityBadge priority={priority} />}
                    <span style={{ marginLeft: priority ? '0.5rem' : 0 }}>
                      <FeedbackText
                        item={item}
                        onHover={onCitationHover}
                        onLeave={onCitationLeave}
                      />
                    </span>
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
          <p className="feedback-prose" style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
            {closing}
          </p>
        </div>
      )}
    </div>
  );
}
