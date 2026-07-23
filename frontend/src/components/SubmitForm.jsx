import React, { useState, useRef } from 'react';

const MAX_CHARS = 80000;

export default function SubmitForm({ onSubmitAsync, onSubmitSync, isSubmitting }) {
  const [inputMode, setInputMode] = useState('file'); // 'file' | 'text'
  const [evalMode, setEvalMode] = useState('async'); // 'async' | 'sync'
  const [file, setFile] = useState(null);
  const [rawText, setRawText] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const fileRef = useRef(null);

  const charCount = rawText.length;
  const overLimit = charCount > MAX_CHARS;
  const nearLimit = charCount > MAX_CHARS * 0.85;

  const hasInput = inputMode === 'file' ? !!file : rawText.trim().length > 0;
  const canSubmit = hasInput && !overLimit && !isSubmitting;

  function handleFileChange(e) {
    const f = e.target.files?.[0] || null;
    setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    const payload = inputMode === 'file' ? { file } : { rawText };
    if (evalMode === 'async') {
      onSubmitAsync(payload);
    } else {
      onSubmitSync({ ...payload, secretKey: secretKey || undefined });
    }
  }

  function handleClearFile() {
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
  }

  const charClass = overLimit ? 'over' : nearLimit ? 'warn' : '';

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-section">
        {/* Input mode toggle */}
        <div>
          <div className="form-label" style={{ marginBottom: '0.5rem' }}>Input</div>
          <div className="toggle-group">
            <button
              type="button"
              className={`toggle-btn ${inputMode === 'file' ? 'active' : ''}`}
              onClick={() => setInputMode('file')}
            >
              Upload file
            </button>
            <button
              type="button"
              className={`toggle-btn ${inputMode === 'text' ? 'active' : ''}`}
              onClick={() => setInputMode('text')}
            >
              Paste text
            </button>
          </div>
        </div>

        {/* File upload */}
        {inputMode === 'file' && (
          <div className="form-group">
            <div
              className={`file-drop ${dragOver ? 'drag-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => !file && fileRef.current?.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <div className="file-drop-icon">📄</div>
              {file ? (
                <div>
                  <div className="file-selected">✓ {file.name}</div>
                  <div className="file-drop-hint" style={{ marginTop: '0.4rem' }}>
                    {(file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ) : (
                <>
                  <div className="file-drop-text">
                    <strong>Click to browse</strong> or drag &amp; drop
                  </div>
                  <div className="file-drop-hint">PDF, DOCX, or TXT — max ~80 000 chars</div>
                </>
              )}
            </div>
            {file && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleClearFile}
                style={{ alignSelf: 'flex-start' }}
              >
                × Remove file
              </button>
            )}
          </div>
        )}

        {/* Text paste */}
        {inputMode === 'text' && (
          <div className="form-group">
            <textarea
              className="form-textarea"
              placeholder="Paste your engineering report text here…"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={10}
              aria-label="Report text"
            />
            <div className={`char-count ${charClass}`}>
              {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
              {overLimit && ' — exceeds server limit'}
            </div>
            {nearLimit && !overLimit && (
              <div className="form-hint warn">Approaching the 80 000-character limit.</div>
            )}
          </div>
        )}

        <div className="section-divider" />

        {/* Advanced / developer options — synchronous mode is a debug path,
            not part of the ordinary submission flow, so it stays tucked away. */}
        <div className="advanced-section">
          <button
            type="button"
            className="advanced-toggle"
            onClick={() => setAdvancedOpen((v) => !v)}
            aria-expanded={advancedOpen}
          >
            <span>⚙ Advanced / developer options</span>
            <span className={`collapsible-icon ${advancedOpen ? 'open' : ''}`} aria-hidden="true">▼</span>
          </button>
          {advancedOpen && (
            <div className="advanced-body">
              <div>
                <div className="form-label" style={{ marginBottom: '0.5rem' }}>Evaluation mode</div>
                <div className="toggle-group">
                  <button
                    type="button"
                    className={`toggle-btn ${evalMode === 'async' ? 'active' : ''}`}
                    onClick={() => setEvalMode('async')}
                  >
                    Async <span style={{ opacity: 0.7, fontSize: '0.75em' }}>(recommended)</span>
                  </button>
                  <button
                    type="button"
                    className={`toggle-btn ${evalMode === 'sync' ? 'active' : ''}`}
                    onClick={() => setEvalMode('sync')}
                  >
                    Sync
                  </button>
                </div>
                <div className="form-hint mt-1">
                  {evalMode === 'async'
                    ? 'Submits in the background; you can track progress stage by stage.'
                    : 'Waits for the full pipeline to finish in one request (may take 30–120 s) — useful for scripting or debugging, not recommended for normal use.'}
                </div>
              </div>

              {evalMode === 'sync' && (
                <div className="form-group">
                  <label className="form-label" htmlFor="secret-key">
                    Secret key <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span>
                  </label>
                  <input
                    id="secret-key"
                    type="password"
                    className="form-input"
                    placeholder="x_secret_key"
                    value={secretKey}
                    onChange={(e) => setSecretKey(e.target.value)}
                    autoComplete="off"
                  />
                  <div className="form-hint">Leave blank if your backend does not require a key.</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Submit button */}
        <button
          type="submit"
          className="btn btn-primary btn-lg w-full"
          disabled={!canSubmit}
          aria-label="Evaluate report"
        >
          {isSubmitting ? (
            <><span className="spinner" />Submitting…</>
          ) : (
            <>{evalMode === 'async' ? '⚡ Evaluate (async)' : '▶ Evaluate (sync)'}</>
          )}
        </button>
      </div>
    </form>
  );
}
