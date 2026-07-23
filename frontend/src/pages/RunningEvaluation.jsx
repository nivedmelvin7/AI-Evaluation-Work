import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ProgressTracker from '../components/ProgressTracker.jsx';
import FailureScreen from '../components/ui/FailureScreen.jsx';
import { useTopBarConfig } from '../context/TopBarContext.jsx';
import { getStatus } from '../api.js';

const POLL_INTERVAL_MS = 2000;
const MAX_TRANSIENT_RETRIES = 5;

export default function RunningEvaluation() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  useTopBarConfig({ title: 'Running evaluation' });

  const [statusObj, setStatusObj] = useState({ status: 'queued', stage: 'pending', progress: 0 });
  const [connectionState, setConnectionState] = useState('ok'); // ok | retrying | lost
  const [notFound, setNotFound] = useState(false);
  const [pollAttempt, setPollAttempt] = useState(0); // bump to restart polling after "Retry connection"

  const intervalRef = useRef(null);
  const retriesRef = useRef(0);
  const unmountedRef = useRef(false);

  const clearPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    unmountedRef.current = false;
    return () => {
      unmountedRef.current = true;
      clearPolling();
    };
  }, [clearPolling]);

  useEffect(() => {
    if (!jobId) return undefined;
    setNotFound(false);
    setConnectionState('ok');
    retriesRef.current = 0;

    async function tick() {
      if (unmountedRef.current) return;
      try {
        const data = await getStatus(jobId);
        if (unmountedRef.current) return;
        retriesRef.current = 0;
        setConnectionState('ok');
        setStatusObj(data);

        if (data.status === 'complete') {
          clearPolling();
          navigate(`/evaluate/${jobId}/result`);
          return;
        }
        if (data.status === 'failed') {
          clearPolling();
          return;
        }
        intervalRef.current = window.setTimeout(tick, POLL_INTERVAL_MS);
      } catch (err) {
        if (unmountedRef.current) return;
        if (err.status === 404) {
          clearPolling();
          setNotFound(true);
          return;
        }
        retriesRef.current += 1;
        if (retriesRef.current > MAX_TRANSIENT_RETRIES) {
          clearPolling();
          setConnectionState('lost');
          return;
        }
        setConnectionState('retrying');
        const backoff = Math.min(POLL_INTERVAL_MS * 2 ** retriesRef.current, 20000);
        intervalRef.current = window.setTimeout(tick, backoff);
      }
    }

    tick();
    return () => clearPolling();
  }, [jobId, pollAttempt, navigate, clearPolling]);

  function handleRetryConnection() {
    setConnectionState('ok');
    setPollAttempt((n) => n + 1);
  }

  function handleStartOver() {
    navigate('/evaluate/new');
  }

  if (notFound) {
    return (
      <FailureScreen
        title="Evaluation not found"
        message={`No evaluation with ID ${jobId} exists on this server. It may have been submitted before the server last restarted.`}
        onStartOver={handleStartOver}
      />
    );
  }

  if (connectionState === 'lost') {
    return (
      <FailureScreen
        title="Lost connection to the server"
        message="We couldn't reach the backend after several attempts. Your evaluation may still be running — try reconnecting."
        onRetry={handleRetryConnection}
        retryLabel="Retry connection"
        onStartOver={handleStartOver}
        startOverLabel="Start over"
      />
    );
  }

  if (statusObj.status === 'failed') {
    return (
      <FailureScreen
        title="Evaluation failed"
        message={statusObj.error || 'The pipeline encountered an error. Check backend logs for details.'}
        onStartOver={handleStartOver}
        startOverLabel="Start over"
      />
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 'var(--space-5)', alignItems: 'start' }}>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Pipeline progress</span>
          {jobId && (
            <span className="badge badge-accent" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: 0 }}>
              {jobId.slice(0, 8)}…
            </span>
          )}
        </div>
        <div className="card-body">
          <ProgressTracker
            stage={statusObj.stage || 'pending'}
            progress={statusObj.progress || 0}
            status={statusObj.status || 'queued'}
          />
          {connectionState === 'retrying' && (
            <div className="reconnect-banner" role="status">
              <span className="spinner" style={{ width: 14, height: 14 }} />
              Reconnecting to server…
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="loading-center" style={{ padding: '1rem 0' }}>
            <div className="spinner" />
            <div className="loading-label">
              {statusObj.stage ? `Stage: ${statusObj.stage}` : 'Waiting…'}
            </div>
          </div>
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
            <div className="text-sm text-muted" style={{ marginBottom: '0.25rem' }}>Job ID</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{jobId}</div>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: '1rem', width: '100%' }} onClick={handleStartOver}>
            Cancel and start over
          </button>
        </div>
      </div>
    </div>
  );
}
