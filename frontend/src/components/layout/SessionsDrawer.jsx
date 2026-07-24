import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listSessions, archiveSession } from '../../api.js';
import { useToast } from '../Toast.jsx';

function formatWhen(iso) {
  if (!iso) return '';
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

function statusBadgeClass(status) {
  if (status === 'complete') return 'badge-green';
  if (status === 'failed') return 'badge-red';
  return 'badge-blue';
}

export default function SessionsDrawer({ open, onClose }) {
  const navigate = useNavigate();
  const toast = useToast();
  const panelRef = useRef(null);

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setLoadError(null);
    listSessions()
      .then((data) => setSessions(data?.sessions || []))
      .catch((err) => setLoadError(err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    refresh();

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleKeyDown);
    const previouslyFocused = document.activeElement;
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus?.();
    };
  }, [open, onClose, refresh]);

  if (!open) return null;

  function openSession(session) {
    const latest = session.latest;
    if (!latest) return;
    onClose();
    if (latest.status === 'complete') {
      navigate(`/evaluate/${latest.job_id}/result`);
    } else if (latest.status === 'failed') {
      navigate(`/evaluate/${latest.job_id}/run`);
    } else {
      navigate(`/evaluate/${latest.job_id}/run`);
    }
  }

  async function handleArchive(event, session) {
    event.stopPropagation();
    try {
      await archiveSession(session.session_id);
      toast.success('Evaluation archived. It stays in the database and can be restored later.');
      setSessions((current) => current.filter((s) => s.session_id !== session.session_id));
    } catch (err) {
      toast.error(err.message || 'Could not archive this evaluation.');
    }
  }

  return (
    <>
      <div className="mobile-drawer-backdrop" onClick={onClose} />
      <div
        className="sessions-drawer"
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Evaluation history"
      >
        <div className="sessions-drawer-header">
          <span className="card-title">Evaluation history</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close history">
            ×
          </button>
        </div>

        <div className="sessions-drawer-body">
          {loading && (
            <div className="loading-center" style={{ padding: '2rem 0' }}>
              <div className="spinner" />
              <div className="loading-label">Loading history…</div>
            </div>
          )}

          {!loading && loadError && (
            <div className="empty-state-sub" style={{ padding: '1rem' }}>
              Could not load evaluation history: {loadError.message || 'unknown error'}
            </div>
          )}

          {!loading && !loadError && sessions.length === 0 && (
            <div className="empty-state-sub" style={{ padding: '1rem' }}>
              No evaluations yet. Submitted reports will appear here so you can reopen or
              re-evaluate them later — nothing is ever lost.
            </div>
          )}

          {!loading && !loadError && sessions.map((session) => (
            <button
              key={session.session_id}
              type="button"
              className="sessions-drawer-item"
              onClick={() => openSession(session)}
            >
              <div className="sessions-drawer-item-top">
                <span className="sessions-drawer-item-title">
                  {session.filename || 'Pasted text'}
                </span>
                {session.latest && (
                  <span className={`badge ${statusBadgeClass(session.latest.status)}`}>
                    {session.latest.status}
                  </span>
                )}
              </div>
              <div className="sessions-drawer-item-meta">
                <span>{formatWhen(session.updated_at)}</span>
                {session.version_count > 1 && (
                  <span className="badge badge-gray">{session.version_count} versions</span>
                )}
                {session.latest?.final_score != null && (
                  <span>{session.latest.final_score}/100 · {session.latest.grade_band}</span>
                )}
              </div>
              <span
                className="sessions-drawer-item-archive"
                role="button"
                tabIndex={0}
                aria-label="Archive evaluation"
                onClick={(event) => handleArchive(event, session)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') handleArchive(event, session);
                }}
              >
                Archive
              </span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
