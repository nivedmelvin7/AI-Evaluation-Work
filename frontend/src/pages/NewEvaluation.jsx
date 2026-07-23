import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SubmitForm from '../components/SubmitForm.jsx';
import { useToast } from '../components/Toast.jsx';
import { useTopBarConfig } from '../context/TopBarContext.jsx';
import { submitAsync, evaluateSync } from '../api.js';

function extractDetail(err) {
  if (err && err.message) return err.message;
  return 'An unexpected error occurred.';
}

export default function NewEvaluation() {
  useTopBarConfig({ title: 'New evaluation' });
  const navigate = useNavigate();
  const toast = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmitAsync(payload) {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      const data = await submitAsync(payload);
      if (!data?.job_id) throw new Error('No job_id returned from server.');
      navigate(`/evaluate/${data.job_id}/run`);
    } catch (err) {
      toast.error(extractDetail(err));
      setIsSubmitting(false);
    }
  }

  async function handleSubmitSync(payload) {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      const data = await evaluateSync(payload);
      if (!data?.job_id) throw new Error('No job_id returned from server.');
      toast.success('Evaluation complete — your report is ready.');
      navigate(`/evaluate/${data.job_id}/result`);
    } catch (err) {
      let msg = extractDetail(err);
      if (err.status === 403) msg = 'Access denied: missing or incorrect secret key.';
      toast.error(msg);
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem', maxWidth: '680px' }}>
        <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, marginBottom: '0.4rem' }}>
          Evaluate an engineering report
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-base)' }}>
          Upload a PDF, DOCX, or TXT file — or paste report text — and the AI multi-agent
          pipeline will assess it across nine weighted criteria: technical accuracy,
          methodology, critical thinking, evidence quality, structure, clarity,
          referencing, originality, and professionalism. You'll get a scored breakdown,
          structured feedback with document citations, and an integrity check.
        </p>
      </div>

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
  );
}
