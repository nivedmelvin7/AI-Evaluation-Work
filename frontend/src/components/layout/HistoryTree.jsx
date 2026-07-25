import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { listSessions, getSession, archiveSession } from '../../api.js';
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

function versionRoute(version) {
  if (!version) return null;
  return version.status === 'complete'
    ? `/evaluate/${version.job_id}/result`
    : `/evaluate/${version.job_id}/run`;
}

/**
 * Folder = Session (one uploaded document), files = EvaluationVersion (one
 * run against it, original + every re-evaluation). The list endpoint is
 * cheap and only carries the latest version per session; a folder's full
 * version list is fetched lazily on first expand via getSession().
 */
export default function HistoryTree({ onNavigate }) {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [versionsBySession, setVersionsBySession] = useState({});

  const refresh = useCallback(() => {
    setLoading(true);
    setLoadError(null);
    listSessions()
      .then((data) => setSessions(data?.sessions || []))
      .catch((err) => setLoadError(err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Catches a just-submitted evaluation landing back on the dashboard.
  useEffect(() => {
    if (location.pathname === '/') refresh();
  }, [location.pathname, refresh]);

  async function toggleExpand(session) {
    const id = session.session_id;
    const willOpen = !expanded[id];
    setExpanded((current) => ({ ...current, [id]: willOpen }));
    if (willOpen && !versionsBySession[id]) {
      setVersionsBySession((current) => ({ ...current, [id]: 'loading' }));
      try {
        const detail = await getSession(id);
        setVersionsBySession((current) => ({ ...current, [id]: detail.versions || [] }));
      } catch (err) {
        setVersionsBySession((current) => ({ ...current, [id]: 'error' }));
      }
    }
  }

  function openVersion(version) {
    const route = versionRoute(version);
    if (!route) return;
    onNavigate?.();
    navigate(route);
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
    <div className="sidebar-history">
      <div className="sidebar-history-label">Evaluation history</div>
      <div className="sidebar-history-body">
        {loading && sessions.length === 0 && (
          <div className="sidebar-history-empty">Loading…</div>
        )}

        {!loading && loadError && (
          <div className="sidebar-history-empty">Could not load history.</div>
        )}

        {!loading && !loadError && sessions.length === 0 && (
          <div className="sidebar-history-empty">
            No evaluations yet. Submitted reports appear here.
          </div>
        )}

        {sessions.map((session) => {
          const isOpen = !!expanded[session.session_id];
          const versions = versionsBySession[session.session_id];
          const sortedVersions = Array.isArray(versions)
            ? [...versions].sort((a, b) => b.version_number - a.version_number)
            : versions;

          return (
            <div key={session.session_id} className="history-folder">
              <button
                type="button"
                className="history-folder-row"
                onClick={() => toggleExpand(session)}
                aria-expanded={isOpen}
              >
                <span className={`history-chevron ${isOpen ? 'open' : ''}`} aria-hidden="true">›</span>
                <span className="history-folder-title" title={session.filename || 'Pasted text'}>
                  {session.filename || 'Pasted text'}
                </span>
                {session.version_count > 1 && (
                  <span className="badge badge-gray history-folder-count">{session.version_count}</span>
                )}
                <span
                  className="history-folder-archive"
                  role="button"
                  tabIndex={0}
                  aria-label="Archive evaluation"
                  onClick={(event) => handleArchive(event, session)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') handleArchive(event, session);
                  }}
                >
                  ×
                </span>
              </button>

              {isOpen && (
                <div className="history-files">
                  {sortedVersions === 'loading' && (
                    <div className="history-file-empty">Loading versions…</div>
                  )}
                  {sortedVersions === 'error' && (
                    <div className="history-file-empty">Could not load versions.</div>
                  )}
                  {Array.isArray(sortedVersions) && sortedVersions.map((version) => (
                    <button
                      key={version.job_id}
                      type="button"
                      className="history-file-row"
                      onClick={() => openVersion(version)}
                    >
                      <span className={`badge ${statusBadgeClass(version.status)} history-file-badge`}>
                        v{version.version_number}
                      </span>
                      <span className="history-file-meta">
                        {formatWhen(version.created_at)}
                        {version.final_score != null && ` · ${version.final_score}/100`}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
