import React from 'react';
import ScoreCard from './ScoreCard.jsx';
import CriterionTable from './CriterionTable.jsx';
import FeedbackPanel from './FeedbackPanel.jsx';
import VerificationPanel from './VerificationPanel.jsx';
import MetadataPanel from './MetadataPanel.jsx';

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

      {/* Sections */}
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
              <span className="badge badge-gray">{Object.keys(scoring.criterion_breakdown).length} criteria</span>
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
            </div>
            <div className="card-body">
              <FeedbackPanel feedback={feedback} />
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
    </div>
  );
}
