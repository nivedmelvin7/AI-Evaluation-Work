import React, { useCallback, useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfjsWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { getDocumentBlob, getDocumentHtml, getDocumentMeta } from '../api.js';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl;

const PDF_SCALE = 1.4;

function findItemsForQuote(items, quote) {
  if (!quote || !items.length) return [];
  // Build concatenated text with char→item mapping. Whitespace is stripped
  // entirely (not just collapsed) because pdf.js often omits the space
  // between adjacent text items (e.g. kerned/justified text), which would
  // otherwise merge words together and break substring matching.
  let fullText = '';
  const offsets = [];
  for (const item of items) {
    const piece = item.str.replace(/\s+/g, '');
    if (!piece) continue;
    offsets.push({ start: fullText.length, end: fullText.length + piece.length, item });
    fullText += piece;
  }
  const qNorm = quote.toLowerCase().replace(/\s+/g, '');
  const tNorm = fullText.toLowerCase();
  // Try full quote first, then progressively shorter prefixes
  const candidates = [qNorm, qNorm.slice(0, 80), qNorm.slice(0, 40)];
  for (const q of candidates) {
    if (q.length < 8) continue;
    const idx = tNorm.indexOf(q);
    if (idx === -1) continue;
    const end = idx + q.length;
    return offsets.filter(o => o.start < end && o.end > idx).map(o => o.item);
  }
  return [];
}

function drawHighlights(canvas, items, viewport) {
  const overlay = canvas.nextSibling;
  if (!overlay || overlay.tagName !== 'CANVAS') return;
  const ctx = overlay.getContext('2d');
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!items.length) return;
  const scale = viewport.scale;
  ctx.fillStyle = 'rgba(255, 237, 0, 0.42)';
  ctx.strokeStyle = 'rgba(180, 150, 0, 0.55)';
  ctx.lineWidth = 1;
  for (const item of items) {
    const [x, y] = viewport.convertToViewportPoint(item.transform[4], item.transform[5]);
    const w = item.width * scale;
    const h = (Math.abs(item.transform[3]) * scale) || 14;
    ctx.fillRect(x, y - h, w, h);
    ctx.strokeRect(x, y - h, w, h);
  }
}

// Scrolls only within the preview's own scroll container, never the page —
// el.scrollIntoView() would otherwise walk up and scroll ancestor containers
// (including the window) to bring the target fully into view.
function scrollIntoContainer(el, block = 'start') {
  if (!el) return;
  const container = el.closest('.doc-preview-body');
  if (!container) return;
  const elRect = el.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  const delta = block === 'center'
    ? (elRect.top + elRect.height / 2) - (containerRect.top + containerRect.height / 2)
    : elRect.top - containerRect.top;
  container.scrollBy({ top: delta, behavior: 'smooth' });
}

function clearAllHighlights(containerRef) {
  if (!containerRef.current) return;
  containerRef.current.querySelectorAll('canvas.pdf-highlight').forEach(c => {
    c.getContext('2d').clearRect(0, 0, c.width, c.height);
  });
}

export default function DocumentPreview({ jobId, isOpen, onToggle, activeQuote, activePage }) {
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [numPages, setNumPages] = useState(0);
  const [docHtml, setDocHtml] = useState(null);
  const containerRef = useRef(null);
  const textLayerRef = useRef({}); // pageNum → { items, viewport }
  const blobUrlRef = useRef(null);

  // Load document when panel opens
  useEffect(() => {
    if (!isOpen || !jobId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const m = await getDocumentMeta(jobId);
        if (cancelled) return;
        setMeta(m);

        if (m.type === 'pdf') {
          const blob = await getDocumentBlob(jobId);
          if (cancelled) return;
          const arrayBuf = await blob.arrayBuffer();
          if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
          blobUrlRef.current = URL.createObjectURL(new Blob([arrayBuf], { type: 'application/pdf' }));
          const pdf = await pdfjsLib.getDocument({ data: arrayBuf }).promise;
          if (cancelled) return;
          setPdfDoc(pdf);
          setNumPages(pdf.numPages);
        } else {
          const html = await getDocumentHtml(jobId);
          if (cancelled) return;
          setDocHtml(html);
        }
      } catch (e) {
        if (!cancelled) {
          if (e.message?.includes('404') || e.status === 404) {
            setError('no-document');
          } else {
            setError(e.message || 'Failed to load document');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [isOpen, jobId]);

  // Render PDF pages after pdfDoc is set
  useEffect(() => {
    if (!pdfDoc || !containerRef.current) return;
    textLayerRef.current = {};

    async function renderPages() {
      for (let p = 1; p <= pdfDoc.numPages; p++) {
        const wrapper = containerRef.current?.querySelector(`[data-page="${p}"]`);
        const canvas = wrapper?.querySelector('canvas.pdf-page');
        if (!canvas) continue;

        const page = await pdfDoc.getPage(p);
        const viewport = page.getViewport({ scale: PDF_SCALE });
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        // Size the overlay canvas too
        const overlay = wrapper.querySelector('canvas.pdf-highlight');
        if (overlay) { overlay.width = viewport.width; overlay.height = viewport.height; }

        await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;

        const tc = await page.getTextContent();
        textLayerRef.current[p] = { items: tc.items, viewport };
      }
    }

    renderPages();
  }, [pdfDoc]);

  // Highlight active quote in PDF
  useEffect(() => {
    if (!pdfDoc || !containerRef.current) return;
    clearAllHighlights(containerRef);
    if (!activeQuote) return;

    // If we know the page, highlight there; otherwise search all pages
    const targetPages = activePage
      ? [activePage]
      : Array.from({ length: numPages }, (_, i) => i + 1);

    for (const p of targetPages) {
      const layer = textLayerRef.current[p];
      if (!layer) continue;
      const matching = findItemsForQuote(layer.items, activeQuote);
      if (!matching.length) continue;

      const wrapper = containerRef.current?.querySelector(`[data-page="${p}"]`);
      const canvas = wrapper?.querySelector('canvas.pdf-page');
      if (canvas) {
        drawHighlights(canvas, matching, layer.viewport);
        scrollIntoContainer(wrapper, 'start');
      }
      break;
    }
  }, [activeQuote, activePage, pdfDoc, numPages]);

  // Highlight in HTML iframe (DOCX/TXT)
  const iframeRef = useRef(null);
  const highlightInIframe = useCallback((quote) => {
    const iframe = iframeRef.current;
    if (!iframe?.contentDocument || !quote) return;
    const doc = iframe.contentDocument;

    // Remove previous marks
    doc.querySelectorAll('mark.cit-highlight').forEach(m => {
      m.outerHTML = m.innerHTML;
    });

    if (!quote) return;

    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const qLower = quote.toLowerCase().slice(0, 80);
    let node;
    while ((node = walker.nextNode())) {
      const idx = node.textContent.toLowerCase().indexOf(qLower);
      if (idx === -1) continue;
      const range = doc.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + qLower.length);
      const mark = doc.createElement('mark');
      mark.className = 'cit-highlight';
      range.surroundContents(mark);
      mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
      break;
    }
  }, []);

  useEffect(() => {
    if (meta?.type !== 'pdf' && docHtml) {
      // Small delay to ensure iframe is rendered
      setTimeout(() => highlightInIframe(activeQuote), 100);
    }
  }, [activeQuote, docHtml, meta, highlightInIframe]);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
    };
  }, []);

  if (!isOpen) return null;

  return (
    <div className="doc-preview-panel">
      {/* Header */}
      <div className="doc-preview-header">
        <div className="doc-preview-header-left">
          <span className="doc-preview-title">Document Preview</span>
          {meta && (
            <span className="badge badge-gray" style={{ fontSize: '0.7rem', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {meta.filename}
            </span>
          )}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onToggle} title="Close preview">
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="doc-preview-body">
        {loading && (
          <div className="loading-center" style={{ padding: '4rem 0' }}>
            <div className="spinner spinner-lg" />
            <div className="loading-label">Loading document…</div>
          </div>
        )}

        {!loading && error === 'no-document' && (
          <div className="doc-preview-empty">
            <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📄</div>
            <div style={{ fontWeight: 600, marginBottom: '0.4rem' }}>No document to preview</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              This evaluation used pasted text — preview is only available when a PDF, DOCX, or TXT file is uploaded.
            </div>
          </div>
        )}

        {!loading && error && error !== 'no-document' && (
          <div className="doc-preview-empty">
            <div style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>Failed to load preview</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{error}</div>
          </div>
        )}

        {/* PDF rendering — canvas per page */}
        {!loading && !error && meta?.type === 'pdf' && pdfDoc && (
          <div ref={containerRef} className="pdf-pages-container">
            {Array.from({ length: numPages }, (_, i) => i + 1).map(p => (
              <div key={p} data-page={p} className="pdf-page-wrapper">
                <div className="pdf-page-num">Page {p}</div>
                <div className="pdf-canvas-wrap">
                  <canvas className="pdf-page" />
                  <canvas className="pdf-highlight" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* DOCX / TXT rendering */}
        {!loading && !error && meta?.type !== 'pdf' && docHtml && (
          <iframe
            ref={iframeRef}
            className="doc-html-iframe"
            srcDoc={docHtml}
            title="Document Preview"
            sandbox="allow-same-origin"
          />
        )}
      </div>

      {/* Citation spotlight — shown when quote is active */}
      {activeQuote && !loading && !error && (
        <div className="citation-spotlight">
          <div className="citation-spotlight-label">
            Cited passage{activePage ? ` · Page ${activePage}` : ''}
          </div>
          <div className="citation-spotlight-quote">"{activeQuote}"</div>
        </div>
      )}
    </div>
  );
}
