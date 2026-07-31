import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import html2pdf from 'html2pdf.js';
import * as XLSX from 'xlsx';
import { Document, HeadingLevel, Packer, Paragraph, Table, TableCell, TableRow, TextRun, WidthType } from 'docx';
import Tabs, { TabPanel } from '../components/ui/Tabs.jsx';
import FailureScreen from '../components/ui/FailureScreen.jsx';
import OverviewSummary from '../components/OverviewSummary.jsx';
import CriterionTable from '../components/CriterionTable.jsx';
import FeedbackPanel from '../components/FeedbackPanel.jsx';
import VerificationPanel from '../components/VerificationPanel.jsx';
import MetadataPanel from '../components/MetadataPanel.jsx';
import DocumentPreview from '../components/DocumentPreview.jsx';
import ReportDocument from '../components/ReportDocument.jsx';
import { useToast } from '../components/Toast.jsx';
import { useTopBarConfig } from '../context/TopBarContext.jsx';
import { getResult, getDocumentMeta, getStatus, reevaluateSession } from '../api.js';
import { humanizeCriterion } from '../utils.js';

const CRITERION_ORDER = ['technical_accuracy', 'methodology', 'critical_thinking', 'evidence_quality', 'structure', 'clarity', 'referencing', 'originality', 'professionalism'];

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'criteria', label: 'Criteria' },
  { id: 'feedback', label: 'Feedback & Evidence' },
  { id: 'integrity', label: 'Integrity' },
  { id: 'technical', label: 'Technical details' },
];

function downloadBlob(content, filename, type) {
  const blob = content instanceof Blob ? content : new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 500);
}

function downloadJson(data, filename) {
  downloadBlob(JSON.stringify(data, null, 2), filename, 'application/json');
}

function criterionRows(scoring) {
  const breakdown = scoring?.criterion_breakdown || {};
  return CRITERION_ORDER.filter((key) => breakdown[key]).map((key) => ({ key, ...breakdown[key] }));
}

function textOf(value) {
  if (Array.isArray(value)) return value.join('; ');
  if (value && typeof value === 'object') return JSON.stringify(value);
  return value == null ? '—' : String(value);
}

function buildDocx(result) {
  const scoring = result.scoring || {};
  const feedback = result.feedback || {};
  const rows = criterionRows(scoring);
  const scoreLine = `${scoring.final_score ?? '—'} / 100 · ${scoring.grade_band || 'Unbanded'}`;
  const tableRows = [
    ['Criterion', 'Level', 'Weight', 'Score', 'Confidence'],
    ...rows.map((row) => [humanizeCriterion(row.key), row.level ?? '—', row.weight != null ? `${Math.round(row.weight * 100)}%` : '—', row.s_i != null ? `${Math.round(row.s_i * 100)}%` : '—', row.confidence || '—']),
  ].map((cells, index) => new TableRow({
    children: cells.map((value) => new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: String(value), bold: index === 0 })] })] })),
  }));

  const feedbackParagraphs = [
    ['Overall assessment', feedback.overall_assessment],
    ['Strengths', feedback.strengths],
    ['Areas for improvement', (feedback.areas_for_improvement || []).map((item) => `${item.priority ? `${item.priority}: ` : ''}${item.text || item}`)],
    ['Recommended actions', feedback.recommended_actions],
    ['Closing', feedback.closing],
  ].filter(([, value]) => value).flatMap(([heading, value]) => [
    new Paragraph({ text: heading, heading: HeadingLevel.HEADING_2 }),
    new Paragraph(textOf(value)),
  ]);

  return new Document({
    sections: [{
      properties: {},
      children: [
        new Paragraph({ text: 'Engineering Report Evaluation', heading: HeadingLevel.TITLE }),
        new Paragraph({ children: [new TextRun({ text: scoreLine, bold: true })] }),
        new Paragraph({ text: 'Score breakdown', heading: HeadingLevel.HEADING_1 }),
        new Table({ rows: tableRows, width: { size: 100, type: WidthType.PERCENTAGE } }),
        new Paragraph({ text: 'Feedback', heading: HeadingLevel.HEADING_1 }),
        ...feedbackParagraphs,
      ],
    }],
  });
}

export default function ResultWorkspace() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [result, setResult] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [docFilename, setDocFilename] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [activeQuote, setActiveQuote] = useState(null);
  const [activePage, setActivePage] = useState(null);
  const [sessionMeta, setSessionMeta] = useState(null);
  const [reevaluating, setReevaluating] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    getResult(jobId).then((data) => {
      if (cancelled) return;
      if (data?.__status === 202) {
        navigate(`/evaluate/${jobId}/run`, { replace: true });
        return;
      }
      setResult(data);
      setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setLoadError(err);
      setLoading(false);
    });

    getDocumentMeta(jobId).then((meta) => {
      if (!cancelled) setDocFilename(meta?.filename || null);
    }).catch(() => {});

    getStatus(jobId).then((status) => {
      if (!cancelled) setSessionMeta({ sessionId: status.session_id, versionNumber: status.version_number });
    }).catch(() => {});

    return () => { cancelled = true; };
  }, [jobId, navigate]);

  async function handleReevaluate() {
    if (!sessionMeta?.sessionId || reevaluating) return;
    setReevaluating(true);
    try {
      const data = await reevaluateSession(sessionMeta.sessionId);
      toast.success('Re-evaluation started — the previous result stays available in Evaluation history.');
      navigate(`/evaluate/${data.job_id}/run`);
    } catch (err) {
      toast.error(err.message || 'Could not start re-evaluation.');
      setReevaluating(false);
    }
  }

  const topBarAction = useMemo(() => (
    <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('/evaluate/new')}>
      + New evaluation
    </button>
  ), [navigate]);

  useTopBarConfig({
    title: docFilename ? `Result — ${docFilename}` : 'Evaluation result',
    action: topBarAction,
  });

  function handleCitationHover(citation) {
    setActiveQuote(citation.quote || null);
    setActivePage(citation.page || null);
  }

  async function exportPdf() {
    if (!reportRef.current) return;
    try {
      await html2pdf().set({
        margin: [12, 12, 14, 12],
        filename: `${baseName}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['css', 'legacy'] },
      }).from(reportRef.current).save();
      toast.success('PDF report exported.');
    } catch (error) {
      toast.error(`Could not export PDF: ${error.message || 'unknown error'}`);
    }
  }

  function exportXlsx() {
    try {
      const rows = criterionRows(result.scoring).map((row) => ({
        Criterion: humanizeCriterion(row.key),
        Level: row.level ?? '',
        'Normalised score': row.s_i ?? '',
        Weight: row.weight ?? '',
        Contribution: row.contribution ?? '',
        Confidence: row.confidence ?? '',
        'Uncertainty contribution': row.uncertainty_contribution ?? '',
      }));
      const summary = [{
        'Final score': result.scoring?.final_score ?? '',
        'Grade band': result.scoring?.grade_band ?? '',
        'Uncertainty low': result.scoring?.uncertainty_band?.[0] ?? '',
        'Uncertainty high': result.scoring?.uncertainty_band?.[1] ?? '',
      }];
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(summary), 'Summary');
      XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(rows), 'Criteria');
      XLSX.writeFile(workbook, `${baseName}.xlsx`);
      toast.success('XLSX score breakdown exported.');
    } catch (error) {
      toast.error(`Could not export XLSX: ${error.message || 'unknown error'}`);
    }
  }

  async function exportDocx() {
    try {
      const blob = await Packer.toBlob(buildDocx(result));
      downloadBlob(blob, `${baseName}.docx`, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      toast.success('DOCX report exported.');
    } catch (error) {
      toast.error(`Could not export DOCX: ${error.message || 'unknown error'}`);
    }
  }

  if (loading) {
    return (
      <div className="loading-center" style={{ padding: '4rem 0' }}>
        <div className="spinner spinner-lg" />
        <div className="loading-label">Loading evaluation result…</div>
      </div>
    );
  }

  if (loadError) {
    const is404 = loadError.status === 404;
    return (
      <FailureScreen
        title={is404 ? 'Result not found' : 'Could not load result'}
        message={is404
          ? `No evaluation with ID ${jobId} exists on this server.`
          : (loadError.message || 'An unexpected error occurred while loading this result.')}
        onRetry={() => window.location.reload()}
        onStartOver={() => navigate('/evaluate/new')}
      />
    );
  }

  if (!result) return null;

  const baseName = `evaluation-${jobId ? jobId.slice(0, 8) : 'result'}`;
  const { scoring, feedback, verification, consensus, pipeline_metadata } = result;

  return (
    <div>
      <div className="result-header">
        <div>
          <div className="result-title">
            {scoring?.final_score ?? '—'} / 100
            {scoring?.grade_band && <span className={`grade-badge grade-${scoring.grade_band.toLowerCase()}`} style={{ marginLeft: '0.75rem', verticalAlign: 'middle' }}>{scoring.grade_band}</span>}
          </div>
          <div className="result-job-id">
            {docFilename ? `${docFilename} · ` : ''}Job: {jobId}
            {sessionMeta?.versionNumber ? ` · Version ${sessionMeta.versionNumber}` : ''}
          </div>
        </div>
        <div className="result-actions">
          <div className="export-menu" aria-label="Export report">
            <button
              className="btn btn-secondary"
              onClick={handleReevaluate}
              disabled={!sessionMeta?.sessionId || reevaluating}
              title="Re-run the pipeline. This result stays saved in Evaluation history."
            >
              {reevaluating ? 'Starting…' : '↻ Re-evaluate'}
            </button>
            <button className="btn btn-secondary" onClick={exportPdf}>Export PDF</button>
            <button className="btn btn-secondary" onClick={exportDocx}>DOCX</button>
            <button className="btn btn-secondary" onClick={exportXlsx}>XLSX</button>
            <button className="btn btn-ghost" onClick={() => downloadJson(result, `${baseName}.json`)}>JSON</button>
          </div>
        </div>
      </div>

      <Tabs tabs={TABS} activeId={activeTab} onChange={setActiveTab} idPrefix="result" />

      <TabPanel id="overview" activeId={activeTab} idPrefix="result">
        <OverviewSummary scoring={scoring} feedback={feedback} onGoToCriteria={() => setActiveTab('criteria')} />
      </TabPanel>

      <TabPanel id="criteria" activeId={activeTab} idPrefix="result">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Criterion breakdown</span>
            {scoring?.criterion_breakdown && <span className="badge badge-gray">{Object.keys(scoring.criterion_breakdown).length} criteria</span>}
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <CriterionTable scoring={scoring} />
          </div>
        </div>
      </TabPanel>

      <TabPanel id="feedback" activeId={activeTab} idPrefix="result">
        <div className="result-split-layout">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Feedback</span>
              <span className="badge badge-accent" style={{ fontSize: '0.7rem' }}>Hover a citation to highlight it in the document</span>
            </div>
            <div className="card-body">
              <FeedbackPanel feedback={feedback} onCitationHover={handleCitationHover} onCitationLeave={() => {}} />
            </div>
          </div>

          <div className="result-preview-col">
            <DocumentPreview jobId={jobId} activeQuote={activeQuote} activePage={activePage} />
          </div>
        </div>
      </TabPanel>

      <TabPanel id="integrity" activeId={activeTab} idPrefix="result">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Verification &amp; Integrity</span>
            {verification?.overall_integrity && (
              <span className={`badge ${verification.overall_integrity === 'PASS' ? 'badge-green' : verification.overall_integrity === 'FLAG' ? 'badge-amber' : 'badge-red'}`}>
                {verification.overall_integrity}
              </span>
            )}
          </div>
          <div className="card-body"><VerificationPanel verification={verification} /></div>
        </div>
      </TabPanel>

      <TabPanel id="technical" activeId={activeTab} idPrefix="result">
        <div className="card">
          <div className="card-header"><span className="card-title">Pipeline metadata</span></div>
          <div className="card-body">
            <MetadataPanel metadata={pipeline_metadata} consensus={consensus} fullResult={result} />
          </div>
        </div>
      </TabPanel>

      {/* Off-screen report layout used only as the html2pdf export source */}
      <div className="report-document-wrap">
        <ReportDocument result={result} ref={reportRef} />
      </div>
    </div>
  );
}
