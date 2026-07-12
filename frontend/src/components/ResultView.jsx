import React, { useState } from 'react';
import ScoreCard from './ScoreCard.jsx';
import CriterionTable from './CriterionTable.jsx';
import FeedbackPanel from './FeedbackPanel.jsx';
import VerificationPanel from './VerificationPanel.jsx';
import MetadataPanel from './MetadataPanel.jsx';
import DocumentPreview from './DocumentPreview.jsx';

function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResultView({ result, onReset }) {
  if (!result) return null;

  const { job_id, scoring, feedback, verification, consensus, pipeline_metadata } = result;
  const filename = `evaluation-${job_id ? job_id.slice(0, 8) : 'result'}.json`;

  const [previewOpen, setPreviewOpen] = useState(false);
  const [activeQuote, setActiveQuote] = useState(null);
  const [activePage, setActivePage] = useState(null);

  function handleCitationHover(citation) {
    setActiveQuote(citation.quote || null);
    setActivePage(citation.page || null);
    if (!previewOpen) setPreviewOpen(true);
  }

  function handleCitationLeave() {
    // Keep quote visible while hovering tooltip — clear on actual leave
    // (cleared when next citation hovered or preview closed)
  }

  function handleTogglePreview() {
    setPreviewOpen(v => !v);
    if (previewOpen) {
      setActiveQuote(null);
      setActivePage(null);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="result-header">
        <div>
          <div className="result-title">Evaluation Report</div>
          {job_id && <div className="result-job-id">Job: {job_id}</div>}
        </div>
        <div className="result-actions">
          <button
            className={`btn ${previewOpen ? 'btn-primary' : 'btn-secondary'}`}
            onClick={handleTogglePreview}
            title={previewOpen ? 'Hide document preview' : 'Show document preview'}
          >
            {previewOpen ? '◧ Hide preview' : '◨ Document preview'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => downloadJson(result, filename)}
          >
            ↓ Download JSON
          </button>
          <button className="btn btn-primary" onClick={onReset}>
            + New evaluation
          </button>
        </div>
      </div>

      {/* Split layout */}
      <div className={previewOpen ? 'result-split-layout' : undefined}>
        {/* Left: result sections */}
        <div className="result-sections">
          {/* Score */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Score &amp; Grade</span>
            </div>
            <div className="card-body">
              <ScoreCard scoring={scoring} />
            </div>
          </div>

          {/* Criterion breakdown */}
          {scoring?.criterion_breakdown && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Criterion Breakdown</span>
                <span className="badge badge-gray">
                  {Object.keys(scoring.criterion_breakdown).length} criteria
                </span>
              </div>
              <div className="card-body" style={{ padding: '0' }}>
                <CriterionTable scoring={scoring} />
              </div>
            </div>
          )}

          {/* Feedback */}
          {feedback && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Feedback</span>
                {previewOpen && (
                  <span className="badge badge-accent" style={{ fontSize: '0.7rem' }}>
                    Hover citations to highlight
                  </span>
                )}
              </div>
              <div className="card-body">
                <FeedbackPanel
                  feedback={feedback}
                  onCitationHover={handleCitationHover}
                  onCitationLeave={handleCitationLeave}
                />
              </div>
            </div>
          )}

          {/* Verification */}
          {verification && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Verification &amp; Integrity</span>
                {verification.overall_integrity && (
                  <span className={`badge ${
                    verification.overall_integrity === 'PASS' ? 'badge-green' :
                    verification.overall_integrity === 'FLAG' ? 'badge-amber' : 'badge-red'
                  }`}>{verification.overall_integrity}</span>
                )}
              </div>
              <div className="card-body">
                <VerificationPanel verification={verification} />
              </div>
            </div>
          )}

          {/* Metadata */}
          {(pipeline_metadata || consensus) && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Pipeline Metadata</span>
              </div>
              <div className="card-body">
                <MetadataPanel
                  metadata={pipeline_metadata}
                  consensus={consensus}
                  fullResult={result}
                />
              </div>
            </div>
          )}
        </div>

        {/* Right: document preview */}
        {previewOpen && (
          <div className="result-preview-col">
            <DocumentPreview
              jobId={job_id}
              isOpen={previewOpen}
              onToggle={handleTogglePreview}
              activeQuote={activeQuote}
              activePage={activePage}
            />
          </div>
        )}
      </div>
    </div>
  );
}
