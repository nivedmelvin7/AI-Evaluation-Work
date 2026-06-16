import React, { useState, useEffect, useCallback } from 'react';
import { health } from '../api.js';

export default function HealthBadge() {
  const [state, setState] = useState('loading'); // loading | ok | err
  const [info, setInfo] = useState(null);

  const check = useCallback(async () => {
    setState('loading');
    try {
      const data = await health();
      setInfo(data);
      setState('ok');
    } catch (e) {
      setInfo(null);
      setState('err');
    }
  }, []);

  useEffect(() => { check(); }, [check]);

  return (
    <div className="health-badge-wrap">
      <div className={`health-dot ${state}`} title={state === 'ok' ? 'Backend online' : state === 'err' ? 'Backend unreachable' : 'Checking...'} />
      <div>
        {state === 'loading' && <div className="health-text">Checking backend…</div>}
        {state === 'err' && <div className="health-text" style={{ color: 'var(--danger)' }}>Backend offline</div>}
        {state === 'ok' && info && (
          <>
            <div className="health-text">
              {info.backend}{info.model ? ` · ${info.model}` : ''}
              {info.debug && <span className="badge badge-amber" style={{ marginLeft: '0.4rem', fontSize: '0.65rem' }}>DEBUG</span>}
            </div>
          </>
        )}
      </div>
      <button
        className="btn btn-ghost btn-sm"
        onClick={check}
        title="Re-check backend health"
        aria-label="Re-check backend health"
        style={{ padding: '0.25rem 0.5rem' }}
      >
        ↻
      </button>
    </div>
  );
}
