import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useLocation } from 'react-router-dom';

// Each section covers one screen (or cross-cutting concern) of the app.
// `match` decides which section opens by default for the page Help was
// clicked from, so a new user always lands on something relevant. Sections
// are paged through with the left/right arrows rather than a tab strip —
// the modal is too narrow to fit six tab labels without its own scrollbar.
const SECTIONS = [
  {
    id: 'basics',
    label: 'Getting started',
    match: (path) => path === '/',
    content: (
      <>
        <h3>What this is</h3>
        <p>
          The Assessment Workspace scores an engineering report using a multi-agent AI
          pipeline. Submit a document and you get a weighted score, a letter grade band,
          written feedback with citations back into your document, and an integrity check
          — all reviewed across nine criteria:
        </p>
        <ul>
          <li>Technical accuracy</li>
          <li>Methodology</li>
          <li>Critical thinking</li>
          <li>Evidence quality</li>
          <li>Structure</li>
          <li>Clarity</li>
          <li>Referencing</li>
          <li>Originality</li>
          <li>Professionalism</li>
        </ul>

        <h3>The basic workflow</h3>
        <ul>
          <li><strong>New evaluation</strong> — upload or paste a report and submit it.</li>
          <li><strong>Running evaluation</strong> — watch the pipeline work through its stages live.</li>
          <li><strong>Result workspace</strong> — review the score, feedback, and integrity check once it finishes.</li>
        </ul>
        <p>
          Every submission is saved automatically — find it again any time under
          <strong> Evaluation history</strong> in the sidebar. Use the arrows above to page
          through help for every other screen.
        </p>
      </>
    ),
  },
  {
    id: 'navigation',
    label: 'Sidebar & history',
    match: () => false,
    content: (
      <>
        <h3>Sidebar</h3>
        <ul>
          <li><strong>⌂ Dashboard</strong> — the landing page; empty until you have an evaluation open.</li>
          <li><strong>✎ New evaluation</strong> — where you submit a report to be scored.</li>
        </ul>

        <h3>Evaluation history</h3>
        <p>
          Below the main navigation, every document you've submitted appears as a folder.
          Expand one to see its versions — the original run plus any re-evaluations — each
          tagged with a status badge and score. Click a version to jump back to its running
          progress or finished result. The × on a folder archives it (it stays in the
          database and isn't deleted, just hidden from this list).
        </p>

        <h3>Collapsing & mobile</h3>
        <p>
          The « button at the bottom of the sidebar collapses it to icons only, to save
          space — your choice is remembered. On narrow screens the sidebar becomes a
          slide-over drawer, opened with the ☰ button in the top bar.
        </p>
      </>
    ),
  },
  {
    id: 'new-evaluation',
    label: 'New evaluation',
    match: (path) => path.startsWith('/evaluate/new'),
    content: (
      <>
        <h3>Providing the report</h3>
        <ul>
          <li><strong>Upload file</strong> — drag &amp; drop or click to browse. PDF, DOCX, or TXT.</li>
          <li><strong>Paste text</strong> — paste the report directly, up to 80,000 characters (a live counter warns as you approach the limit).</li>
        </ul>

        <h3>Advanced / developer options</h3>
        <p>Collapsed by default — most people never need to open this.</p>
        <ul>
          <li><strong>Async (recommended)</strong> — submits in the background and takes you to a live progress tracker. Use this normally.</li>
          <li><strong>Sync</strong> — waits for the entire pipeline to finish in one request (roughly 30–120 seconds). Mainly useful for scripting or debugging, and can optionally take a secret key if your backend requires one.</li>
        </ul>
        <p>Once you're ready, hit <strong>Evaluate</strong> to start.</p>
      </>
    ),
  },
  {
    id: 'running',
    label: 'Running evaluation',
    match: (path) => /^\/evaluate\/[^/]+\/run/.test(path),
    content: (
      <>
        <h3>What you're looking at</h3>
        <p>
          After an async submission you land here, and the page checks the server every
          couple of seconds for progress. The bar at the top shows overall percent complete;
          the stepper below shows exactly which stage the AI pipeline is on:
        </p>
        <ul>
          <li>Queued → Segmentation → Domain Review → Methodology Audit</li>
          <li>Self-Critique → Consensus → Scoring → Feedback → Verification → Complete</li>
        </ul>

        <h3>If something goes wrong</h3>
        <p>
          A dropped connection shows a reconnecting banner and retries automatically with
          backoff; after repeated failures you'll see a <strong>Retry connection</strong> option
          instead. <strong>Cancel and start over</strong> abandons this run and takes you back to
          New evaluation — the evaluation is still saved in history if you want to check on
          it later. Once the pipeline finishes, you're taken to the result automatically.
        </p>
      </>
    ),
  },
  {
    id: 'results',
    label: 'Result workspace',
    match: (path) => /^\/evaluate\/[^/]+\/result/.test(path),
    content: (
      <>
        <h3>Header</h3>
        <p>
          Shows the overall score and grade band, the document name, job ID, and version
          number. <strong>↻ Re-evaluate</strong> reruns the full pipeline on the same document as
          a new version — the current result stays saved in history. The export buttons
          (PDF, DOCX, XLSX, JSON) download the result in that format.
        </p>

        <h3>The five tabs</h3>
        <ul>
          <li><strong>Overview</strong> — score gauge and grade, a radar chart across all nine criteria, your strongest and weakest criteria, and the top priority recommendations.</li>
          <li><strong>Criteria</strong> — the full breakdown table: level, weight, normalised score, and confidence for every criterion.</li>
          <li><strong>Feedback &amp; Evidence</strong> — written feedback (strengths, areas to improve, recommended actions). Hover a citation to highlight the matching passage in the document preview alongside it.</li>
          <li><strong>Integrity</strong> — the automated integrity check: overall integrity (PASS / FLAG / FAIL), a final recommendation (RELEASE / HOLD / REJECT), any detected prompt-injection attempts, and a factual summary.</li>
          <li><strong>Technical details</strong> — raw pipeline metadata and consensus data, useful for auditing or debugging.</li>
        </ul>
      </>
    ),
  },
  {
    id: 'account',
    label: 'Top bar & account',
    match: () => false,
    content: (
      <>
        <h3>Top bar controls</h3>
        <ul>
          <li><strong>Health badge</strong> — live backend connection status; click ↻ to re-check it.</li>
          <li><strong>Theme selector</strong> — switch between Dark and Paper (light) colour themes; your choice is remembered.</li>
          <li><strong>User chip</strong> — shows your signed-in account (hover for your email).</li>
          <li><strong>Sign out</strong> — ends your session and returns you to the login screen.</li>
        </ul>

        <h3>Signing in</h3>
        <p>
          Sign in with Google, or with an email and password. New here? Use "Create an
          account" on the login screen — your evaluations are private to your account and
          available whenever you sign back in.
        </p>
      </>
    ),
  },
];

function indexForPath(pathname) {
  const index = SECTIONS.findIndex((section) => section.match(pathname));
  return index === -1 ? 0 : index;
}

export default function HelpGuide() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const activeIndexRef = useRef(activeIndex);
  activeIndexRef.current = activeIndex;
  const panelRef = useRef(null);

  function handleOpen() {
    setActiveIndex(indexForPath(location.pathname));
    setOpen(true);
  }

  function step(delta) {
    setActiveIndex((SECTIONS.length + activeIndexRef.current + delta) % SECTIONS.length);
  }

  useEffect(() => {
    if (!open) return undefined;

    function handleKeyDown(event) {
      if (event.key === 'Escape') setOpen(false);
      else if (event.key === 'ArrowRight') step(1);
      else if (event.key === 'ArrowLeft') step(-1);
    }
    document.addEventListener('keydown', handleKeyDown);

    const previouslyFocused = document.activeElement;
    panelRef.current?.querySelector('button')?.focus();

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const active = SECTIONS[activeIndex];
  const prevLabel = SECTIONS[(activeIndex - 1 + SECTIONS.length) % SECTIONS.length].label;
  const nextLabel = SECTIONS[(activeIndex + 1) % SECTIONS.length].label;

  return (
    <>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={handleOpen}
        aria-haspopup="dialog"
        title="Help & guide"
      >
        <span aria-hidden="true">?</span> Help
      </button>

      {open && createPortal(
        <>
          <div className="help-modal-backdrop" onClick={() => setOpen(false)} />
          <div
            className="help-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-modal-title"
            ref={panelRef}
          >
            <div className="help-modal-header">
              <div>
                <div id="help-modal-title" className="help-modal-title">Help &amp; guide</div>
                <div className="help-modal-subtitle">A walkthrough of every screen in the Assessment Workspace.</div>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setOpen(false)}
                aria-label="Close help"
              >
                ×
              </button>
            </div>

            <div className="help-modal-subheader">
              <span className="help-modal-section-label">{active.label}</span>
              <span className="help-modal-section-count">{activeIndex + 1} / {SECTIONS.length}</span>
            </div>

            <div className="help-modal-body-wrap">
              <button
                type="button"
                className="help-modal-arrow help-modal-arrow-prev"
                onClick={() => step(-1)}
                aria-label={`Previous section: ${prevLabel}`}
              >
                ‹
              </button>
              <button
                type="button"
                className="help-modal-arrow help-modal-arrow-next"
                onClick={() => step(1)}
                aria-label={`Next section: ${nextLabel}`}
              >
                ›
              </button>

              <div className="help-modal-body">
                <div className="help-section">
                  {active.content}
                </div>
              </div>
            </div>
          </div>
        </>,
        document.body,
      )}
    </>
  );
}
