import React from 'react';

const STAGES = [
  { key: 'pending',      label: 'Queued',           sub: 'Waiting to start' },
  { key: 'segmentation', label: 'Segmentation',     sub: 'Splitting document into sections' },
  { key: 'reviewing',    label: 'Domain Review',    sub: 'Expert agents reviewing content' },
  { key: 'auditing',     label: 'Methodology Audit',sub: 'Methodologist & communication check' },
  { key: 'reflecting',   label: 'Self-Critique',    sub: 'Self-critique & reflection passes' },
  { key: 'consensus',    label: 'Consensus',        sub: 'Agents reaching consensus' },
  { key: 'scoring',      label: 'Scoring',          sub: 'Computing criterion scores' },
  { key: 'feedback',     label: 'Feedback',         sub: 'Generating structured feedback' },
  { key: 'verification', label: 'Verification',     sub: 'Integrity & injection check' },
  { key: 'complete',     label: 'Complete',         sub: 'Evaluation finished' },
];

function getStepState(stageKey, currentStage, status) {
  const currentIdx = STAGES.findIndex((s) => s.key === currentStage);
  const thisIdx = STAGES.findIndex((s) => s.key === stageKey);
  if (status === 'complete' || thisIdx < currentIdx) return 'done';
  if (thisIdx === currentIdx) return 'active';
  return 'pending';
}

export default function ProgressTracker({ stage, progress, status }) {
  const progressPct = typeof progress === 'number' ? progress : 0;

  return (
    <div>
      {/* Progress bar */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
          <span className="text-sm text-muted">Overall progress</span>
          <span className="text-sm num" style={{ color: 'var(--text-secondary)' }}>{progressPct}%</span>
        </div>
        <div className="progress-bar-wrap">
          <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      {/* Stepper */}
      <div className="pipeline-stepper">
        {STAGES.map((s, idx) => {
          const state = getStepState(s.key, stage, status);
          const isLast = idx === STAGES.length - 1;
          return (
            <div key={s.key} className="step-row">
              <div className="step-indicator-col">
                <div className={`step-dot ${state}`}>
                  {state === 'done' ? '✓' : idx + 1}
                </div>
                {!isLast && (
                  <div
                    className={`step-connector ${
                      state === 'done' ? 'done' : state === 'active' ? 'active' : ''
                    }`}
                  />
                )}
              </div>
              <div className="step-content">
                <div className={`step-label ${state}`}>{s.label}</div>
                {state === 'active' && (
                  <div className="step-sub">{s.sub}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
