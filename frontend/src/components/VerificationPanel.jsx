import React from 'react';

function IntegrityBadge({ value }) {
  const v = (value || '').toUpperCase();
  if (v === 'PASS') return <span className="badge badge-green" style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>✓ PASS</span>;
  if (v === 'FLAG') return <span className="badge badge-amber" style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>⚑ FLAG</span>;
  if (v === 'FAIL') return <span className="badge badge-red" style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>✗ FAIL</span>;
  return <span className="badge badge-gray">{value || '—'}</span>;
}

function RecommendationBadge({ value }) {
  const v = (value || '').toUpperCase();
  if (v === 'RELEASE') return <span className="badge badge-green" style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>▶ RELEASE</span>;
  if (v === 'HOLD')    return <span className="badge badge-amber" style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>⏸ HOLD</span>;
  if (v === 'REJECT')  return <span className="badge badge-red"   style={{ fontSize: '0.85rem', padding: '0.3em 0.8em' }}>✗ REJECT</span>;
  return <span className="badge badge-gray">{value || '—'}</span>;
}

export default function VerificationPanel({ verification }) {
  if (!verification) return null;

  const {
    overall_integrity,
    final_recommendation,
    injection_found,
    detected_patterns = [],
    factual_summary,
    release_note,
    rejection_warning,
  } = verification;

  return (
    <div>
      {/* Hero row */}
      <div className="verification-hero">
        <div className="integrity-badge">
          <div className="integrity-label">Integrity</div>
          <IntegrityBadge value={overall_integrity} />
        </div>
        <div className="integrity-badge">
          <div className="integrity-label">Recommendation</div>
          <RecommendationBadge value={final_recommendation} />
        </div>
      </div>

      {/* Injection warning */}
      {injection_found && (
        <div className="warning-banner danger">
          <span className="warning-banner-icon">⚠</span>
          <div>
            <strong>Prompt injection detected.</strong> One or more patterns were found that may attempt to influence the evaluation AI. Results should be reviewed carefully.
          </div>
        </div>
      )}

      {/* Rejection warning */}
      {rejection_warning && (
        <div className="warning-banner danger">
          <span className="warning-banner-icon">✗</span>
          <div>
            <strong>Rejection warning: </strong>{rejection_warning}
          </div>
        </div>
      )}

      {/* Detected patterns */}
      {detected_patterns.length > 0 && (
        <div style={{ marginBottom: '1.25rem' }}>
          <div className="feedback-section-label" style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
            Detected patterns ({detected_patterns.length})
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="patterns-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Content</th>
                  <th>Intent</th>
                </tr>
              </thead>
              <tbody>
                {detected_patterns.map((p, i) => (
                  <tr key={i}>
                    <td><span className="badge badge-amber">{p.type || '—'}</span></td>
                    <td style={{ color: 'var(--text-secondary)' }}>{p.location || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.77rem', color: 'var(--text-secondary)' }}>
                      {p.content || '—'}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{p.intent || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Factual summary */}
      {factual_summary && (
        <div style={{ marginBottom: '1rem' }}>
          <div className="feedback-section-label" style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Factual summary
          </div>
          <p className="feedback-prose">{factual_summary}</p>
        </div>
      )}

      {/* Release note */}
      {release_note && (
        <div className="warning-banner warning">
          <span className="warning-banner-icon">ℹ</span>
          <div>{release_note}</div>
        </div>
      )}
    </div>
  );
}
