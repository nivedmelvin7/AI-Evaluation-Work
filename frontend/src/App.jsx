import React, { useState, useEffect, useRef, useCallback } from 'react';
import HealthBadge from './components/HealthBadge.jsx';
import SubmitForm from './components/SubmitForm.jsx';
import ProgressTracker from './components/ProgressTracker.jsx';
import ResultView from './components/ResultView.jsx';
import { submitAsync, getStatus, getResult, evaluateSync } from './api.js';

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────
function extractDetail(err) {
  if (err && err.message) return err.message;
  return 'An unexpected error occurred.';
}

// ──────────────────────────────────────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────────────────────────────────────
function ErrorBanner({ message, onDismiss }) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-banner-icon">✗</span>
      <div className="error-banner-body">
        <div className="error-banner-title">Evaluation failed</div>
        <div className="error-banner-msg">{message}</div>
      </div>
      {onDismiss && (
        <button className="btn btn-ghost btn-sm" onClick={onDismiss} aria-label="Dismiss error">
          ×
        </button>
      )}
    </div>
  );
}

function SyncSpinner() {
  return (
    <div className="loading-center">
      <div className="spinner spinner-lg" />
      <div className="loading-label">Running full pipeline synchronously…<br />
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>This may take 30–120 seconds</span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// App
// ──────────────────────────────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 2000;

export default function App() {
  // view: idle | submitting | polling | sync_running | done | error
  const [view, setView]           = useState('idle');
  const [jobId, setJobId]         = useState(null);
  const [statusObj, setStatusObj] = useState(null); // { status, stage, progress, error }
  const [result, setResult]       = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const pollIntervalRef = useRef(null);
  const unmountedRef    = useRef(false);

  // ── Cleanup ────────────────────────────────────────────────────────────────
  useEffect(() => {
    unmountedRef.current = false;
    return () => {
      unmountedRef.current = true;
      clearPolling();
    };
  }, []);

  function clearPolling() {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }

  // ── Reset ──────────────────────────────────────────────────────────────────
  function handleReset() {
    clearPolling();
    setView('idle');
    setJobId(null);
    setStatusObj(null);
    setResult(null);
    setErrorMessage('');
  }

  // ── Poll loop ──────────────────────────────────────────────────────────────
  const startPolling = useCallback((id) => {
    async function tick() {
      if (unmountedRef.current) return;
      try {
        const data = await getStatus(id);
        if (unmountedRef.current) return;
        setStatusObj(data);

        if (data.status === 'complete') {
          clearPolling();
          // Fetch full result
          const res = await getResult(id);
          if (unmountedRef.current) return;
          if (res && res.__status === 202) {
            // Not ready yet — shouldn't happen but continue polling
            return;
          }
          setResult(res);
          setView('done');
        } else if (data.status === 'failed') {
          clearPolling();
          setErrorMessage(data.error || 'Pipeline failed. Check backend logs.');
          setView('error');
        }
      } catch (err) {
        if (unmountedRef.current) return;
        clearPolling();
        setErrorMessage(extractDetail(err));
        setView('error');
      }
    }

    // Run immediately, then on interval
    tick();
    pollIntervalRef.current = setInterval(tick, POLL_INTERVAL_MS);
  }, []);

  // ── Async submit ───────────────────────────────────────────────────────────
  async function handleSubmitAsync(payload) {
    setView('submitting');
    setErrorMessage('');
    try {
      const data = await submitAsync(payload);
      if (unmountedRef.current) return;
      if (!data?.job_id) throw new Error('No job_id returned from server.');
      setJobId(data.job_id);
      setStatusObj({ status: 'queued', stage: 'pending', progress: 0 });
      setView('polling');
      startPolling(data.job_id);
    } catch (err) {
      if (unmountedRef.current) return;
      setErrorMessage(extractDetail(err));
      setView('error');
    }
  }

  // ── Sync submit ────────────────────────────────────────────────────────────
  async function handleSubmitSync(payload) {
    setView('sync_running');
    setErrorMessage('');
    try {
      const data = await evaluateSync(payload);
      if (unmountedRef.current) return;
      setResult(data);
      setView('done');
    } catch (err) {
      if (unmountedRef.current) return;
      let msg = extractDetail(err);
      if (err.status === 403) {
        msg = 'Access denied: missing or incorrect secret key.';
      }
      setErrorMessage(msg);
      setView('error');
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  const isSubmitting = view === 'submitting' || view === 'sync_running';

  return (
    <div className="app-wrapper">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-title">
            <span className="app-title-icon">⚙</span>
            Engineering Report Evaluation
          </div>
          <HealthBadge />
        </div>
      </header>

      {/* ── Main ── */}
      <main className="app-main">
        <div className="container">

          {/* ── IDLE / SUBMIT view ── */}
          {(view === 'idle' || view === 'submitting' || view === 'error') && (
            <div>
              {/* Hero blurb on idle */}
              {view === 'idle' && (
                <div style={{ marginBottom: '2rem' }}>
                  <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.4rem' }}>
                    Evaluate an engineering report
                  </h1>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    Upload a PDF, DOCX, or TXT file — or paste report text — and the AI multi-agent pipeline will assess it across nine criteria and return structured feedback.
                  </p>
                </div>
              )}

              {/* Error banner */}
              {view === 'error' && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <ErrorBanner message={errorMessage} onDismiss={handleReset} />
                </div>
              )}

              {/* Submit form card */}
              <div className="card" style={{ maxWidth: '680px' }}>
                <div className="card-header">
                  <span className="card-title">Submit report</span>
                </div>
                <div className="card-body">
                  <SubmitForm
                    onSubmitAsync={handleSubmitAsync}
                    onSubmitSync={handleSubmitSync}
                    isSubmitting={isSubmitting}
                  />
                </div>
              </div>
            </div>
          )}

          {/* ── SYNC RUNNING ── */}
          {view === 'sync_running' && (
            <div className="card" style={{ maxWidth: '480px', margin: '0 auto' }}>
              <div className="card-body">
                <SyncSpinner />
              </div>
            </div>
          )}

          {/* ── POLLING ── */}
          {view === 'polling' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', alignItems: 'start' }}>
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Pipeline progress</span>
                  {jobId && (
                    <span
                      className="badge badge-accent"
                      style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: 0 }}
                    >
                      {jobId.slice(0, 8)}…
                    </span>
                  )}
                </div>
                <div className="card-body">
                  <ProgressTracker
                    stage={statusObj?.stage || 'pending'}
                    progress={statusObj?.progress || 0}
                    status={statusObj?.status || 'queued'}
                  />
                </div>
              </div>

              {/* Side panel */}
              <div className="card">
                <div className="card-body">
                  <div className="loading-center" style={{ padding: '1rem 0' }}>
                    <div className="spinner" />
                    <div className="loading-label">
                      {statusObj?.stage
                        ? `Stage: ${statusObj.stage}`
                        : 'Waiting…'}
                    </div>
                  </div>
                  <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
                    <div className="text-sm text-muted" style={{ marginBottom: '0.25rem' }}>Job ID</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{jobId}</div>
                  </div>
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ marginTop: '1rem', width: '100%' }}
                    onClick={handleReset}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── DONE ── */}
          {view === 'done' && result && (
            <ResultView result={result} onReset={handleReset} />
          )}

        </div>
      </main>
    </div>
  );
}
