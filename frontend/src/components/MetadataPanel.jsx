import React, { useState } from 'react';
import { humanizeCriterion } from '../utils.js';

function ConfBadge({ value }) {
  const v = (value || '').toLowerCase();
  const cls = v === 'high' ? 'badge-green' : v === 'medium' ? 'badge-amber' : 'badge-red';
  return <span className={`badge ${cls}`} style={{ fontSize: '0.7rem' }}>{value}</span>;
}

export default function MetadataPanel({ metadata, consensus, fullResult }) {
  const [jsonOpen, setJsonOpen] = useState(false);

  const sections_found = metadata?.sections_found;
  const gate_triggered = metadata?.gate_triggered;
  const deferred = metadata?.deferred;
  const integrity = metadata?.integrity;
  const final_recommendation = metadata?.final_recommendation;
  const injection_found = metadata?.injection_found;

  const consensusScores = consensus?.scores || {};
  const hasConsensus = Object.keys(consensusScores).length > 0;

  return (
    <div>
      {/* Pipeline metadata tiles */}
      <div className="meta-grid">
        {sections_found != null && (
          <div className="meta-item">
            <div className="meta-item-label">Sections found</div>
            <div className="meta-item-value">{sections_found}</div>
          </div>
        )}
        {integrity != null && (
          <div className="meta-item">
            <div className="meta-item-label">Integrity</div>
            <div className="meta-item-value">{integrity}</div>
          </div>
        )}
        {final_recommendation != null && (
          <div className="meta-item">
            <div className="meta-item-label">Recommendation</div>
            <div className="meta-item-value">{final_recommendation}</div>
          </div>
        )}
        <div className="meta-item">
          <div className="meta-item-label">Gate triggered</div>
          <div className="meta-item-value">{gate_triggered ? 'Yes' : 'No'}</div>
        </div>
        <div className="meta-item">
          <div className="meta-item-label">Deferred</div>
          <div className="meta-item-value">{deferred ? 'Yes' : 'No'}</div>
        </div>
        <div className="meta-item">
          <div className="meta-item-label">Injection found</div>
          <div className="meta-item-value">{injection_found ? 'Yes' : 'No'}</div>
        </div>
      </div>

      {/* Consensus scores */}
      {hasConsensus && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            Consensus scores
          </div>
          <div className="consensus-grid">
            {Object.entries(consensusScores).map(([key, val]) => (
              <div key={key} className="consensus-item">
                <span className="consensus-name">{humanizeCriterion(key)}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="consensus-score">{val?.score ?? '—'}</span>
                  {val?.confidence && <ConfBadge value={val.confidence} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible raw JSON */}
      {fullResult && (
        <div>
          <div
            className="collapsible-header"
            role="button"
            tabIndex={0}
            onClick={() => setJsonOpen((v) => !v)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setJsonOpen((v) => !v); }}
            aria-expanded={jsonOpen}
          >
            <span className="collapsible-title">Raw JSON result</span>
            <span className={`collapsible-icon ${jsonOpen ? 'open' : ''}`}>▼</span>
          </div>
          {jsonOpen && (
            <pre className="raw-json-box">
              {JSON.stringify(fullResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
