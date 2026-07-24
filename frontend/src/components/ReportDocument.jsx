import React, { forwardRef } from 'react';
import { humanizeCriterion } from '../utils.js';

const CRITERION_ORDER = ['technical_accuracy', 'methodology', 'critical_thinking', 'evidence_quality', 'structure', 'clarity', 'referencing', 'originality', 'professionalism'];

function text(value) {
  if (Array.isArray(value)) return value.map((v) => (typeof v === 'string' ? v : v.text)).join('\n');
  if (value && typeof value === 'object') return value.text || JSON.stringify(value);
  return value == null ? '' : String(value);
}

/**
 * A print-oriented, purely semantic layout used only as the source for PDF
 * export (via html2pdf). Kept separate from the interactive tabbed UI so the
 * exported PDF reads as an assessment report rather than a screenshot of the
 * app shell, sidebar, and tab chrome.
 */
const ReportDocument = forwardRef(function ReportDocument({ result }, ref) {
  if (!result) return null;
  const { job_id, scoring = {}, feedback = {}, verification = {} } = result;
  const rows = CRITERION_ORDER
    .filter((key) => scoring.criterion_breakdown?.[key])
    .map((key) => ({ key, ...scoring.criterion_breakdown[key] }));

  const uncertaintyStr = Array.isArray(scoring.uncertainty_band) && scoring.uncertainty_band.length === 2
    ? `${scoring.uncertainty_band[0].toFixed(1)} – ${scoring.uncertainty_band[1].toFixed(1)}`
    : '—';

  return (
    <div className="report-document" ref={ref}>
      <div className="report-doc-title">Engineering Report Evaluation</div>
      <div className="report-doc-sub">
        Job {job_id} · Generated {new Date().toLocaleString()}
      </div>

      <div className="report-doc-section">
        <h2>Score &amp; grade</h2>
        <div className="report-doc-score-row">
          <span className="report-doc-score">{scoring.final_score ?? '—'}<span style={{ fontSize: '1rem', fontWeight: 500 }}> / 100</span></span>
          <span className="report-doc-grade">{scoring.grade_band || 'Unbanded'}</span>
        </div>
        <table className="report-doc-table">
          <tbody>
            <tr><th>Weighted score</th><td>{scoring.achievement_score?.toFixed(1) ?? '—'}</td></tr>
            <tr><th>Uncertainty band</th><td>{uncertaintyStr}</td></tr>
            <tr><th>Aggregate uncertainty (U)</th><td>{scoring.aggregate_uncertainty_U?.toFixed(3) ?? '—'}</td></tr>
            <tr><th>Gate triggered</th><td>{scoring.gate_triggered ? `Yes — ${scoring.gate_reason || ''}` : 'No'}</td></tr>
            <tr><th>Deferred</th><td>{scoring.deferred ? `Yes — ${scoring.deferral_reason || ''}` : 'No'}</td></tr>
            <tr><th>Holistic validation</th><td>{scoring.holistic_validation?.available ? (scoring.holistic_validation.requires_moderation ? `Moderation needed — expected ${scoring.holistic_validation.expected_grade_band}` : 'Aligned') : 'Unavailable'}</td></tr>
          </tbody>
        </table>
      </div>

      {rows.length > 0 && (
        <div className="report-doc-section">
          <h2>Criterion breakdown</h2>
          <table className="report-doc-table">
            <thead>
              <tr><th>Criterion</th><th>Level</th><th>Weight</th><th>Score</th><th>Confidence</th><th>Contribution</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key}>
                  <td>{humanizeCriterion(row.key)}</td>
                  <td>{row.level ?? '—'}</td>
                  <td>{row.weight != null ? `${Math.round(row.weight * 100)}%` : '—'}</td>
                  <td>{row.s_i != null ? `${Math.round(row.s_i * 100)}%` : '—'}</td>
                  <td>{row.confidence || '—'}</td>
                  <td>{row.contribution?.toFixed(3) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {feedback.overall_assessment && (
        <div className="report-doc-section">
          <h2>Overall assessment</h2>
          <p className="report-doc-prose">{feedback.overall_assessment}</p>
        </div>
      )}

      {feedback.strengths?.length > 0 && (
        <div className="report-doc-section">
          <h2>Strengths</h2>
          <ul className="report-doc-list">
            {feedback.strengths.map((s, i) => <li key={i}>{text(s)}</li>)}
          </ul>
        </div>
      )}

      {feedback.areas_for_improvement?.length > 0 && (
        <div className="report-doc-section">
          <h2>Areas for improvement</h2>
          <ul className="report-doc-list">
            {feedback.areas_for_improvement.map((item, i) => {
              const priority = typeof item === 'object' ? item.priority : undefined;
              return <li key={i}>{priority ? `[${priority}] ` : ''}{text(item)}</li>;
            })}
          </ul>
        </div>
      )}

      {feedback.recommended_actions && (
        <div className="report-doc-section">
          <h2>Recommended actions</h2>
          <p className="report-doc-prose">{text(feedback.recommended_actions)}</p>
        </div>
      )}

      {feedback.closing && (
        <div className="report-doc-section">
          <h2>Closing remarks</h2>
          <p className="report-doc-prose">{feedback.closing}</p>
        </div>
      )}

      {verification && Object.keys(verification).length > 0 && (
        <div className="report-doc-section">
          <h2>Integrity &amp; verification</h2>
          <table className="report-doc-table">
            <tbody>
              <tr><th>Overall integrity</th><td>{verification.overall_integrity || '—'}</td></tr>
              <tr><th>Recommendation</th><td>{verification.final_recommendation || '—'}</td></tr>
              <tr><th>Injection detected</th><td>{verification.injection_found ? 'Yes' : 'No'}</td></tr>
            </tbody>
          </table>
          {verification.factual_summary && (
            <p className="report-doc-prose" style={{ marginTop: '0.6rem' }}>{verification.factual_summary}</p>
          )}
        </div>
      )}

      <div className="report-doc-footer">
        AI-assisted evaluation. Intended to support, not replace, marker judgement. Job ID: {job_id}
      </div>
    </div>
  );
});

export default ReportDocument;
