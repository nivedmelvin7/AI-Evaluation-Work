const BASE = import.meta.env.VITE_API_BASE || '';

async function handleResponse(res) {
  if (res.ok) {
    // 202 means "not ready yet" — caller should handle
    if (res.status === 202) return { __status: 202 };
    return res.json();
  }
  let detail = `HTTP ${res.status}`;
  try {
    const body = await res.json();
    if (body && body.detail) detail = body.detail;
    else if (body && body.message) detail = body.message;
  } catch (_) {
    // ignore parse error
  }
  const err = new Error(detail);
  err.status = res.status;
  throw err;
}

export async function health() {
  const res = await fetch(`${BASE}/api/v1/health`);
  return handleResponse(res);
}

export async function submitAsync({ file, rawText }) {
  const form = new FormData();
  if (file) {
    form.append('file', file);
  } else if (rawText != null) {
    form.append('raw_text', rawText);
  }
  const res = await fetch(`${BASE}/api/v1/evaluate`, {
    method: 'POST',
    body: form,
  });
  return handleResponse(res);
}

export async function getStatus(jobId) {
  const res = await fetch(`${BASE}/api/v1/status/${jobId}`);
  return handleResponse(res);
}

export async function getResult(jobId) {
  const res = await fetch(`${BASE}/api/v1/result/${jobId}`);
  return handleResponse(res);
}

export async function getDocumentMeta(jobId) {
  const res = await fetch(`${BASE}/api/v1/document/${jobId}/meta`);
  return handleResponse(res);
}

export async function getDocumentBlob(jobId) {
  const res = await fetch(`${BASE}/api/v1/document/${jobId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function getDocumentHtml(jobId) {
  const res = await fetch(`${BASE}/api/v1/document/${jobId}/html`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

export async function evaluateSync({ file, rawText, secretKey }) {
  const form = new FormData();
  if (file) {
    form.append('file', file);
  } else if (rawText != null) {
    form.append('raw_text', rawText);
  }
  if (secretKey) {
    form.append('x_secret_key', secretKey);
  }
  const res = await fetch(`${BASE}/api/v1/evaluate/sync`, {
    method: 'POST',
    body: form,
  });
  return handleResponse(res);
}
