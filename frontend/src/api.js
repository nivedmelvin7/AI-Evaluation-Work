const BASE = import.meta.env.VITE_API_BASE || '';

function apiFetch(url, options = {}) {
  return fetch(url, { credentials: 'include', ...options });
}

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
  const res = await apiFetch(`${BASE}/api/v1/health`);
  return handleResponse(res);
}

export async function submitAsync({ file, rawText }) {
  const form = new FormData();
  if (file) {
    form.append('file', file);
  } else if (rawText != null) {
    form.append('raw_text', rawText);
  }
  const res = await apiFetch(`${BASE}/api/v1/evaluate`, {
    method: 'POST',
    body: form,
  });
  return handleResponse(res);
}

export async function getStatus(jobId) {
  const res = await apiFetch(`${BASE}/api/v1/status/${jobId}`);
  return handleResponse(res);
}

export async function getResult(jobId) {
  const res = await apiFetch(`${BASE}/api/v1/result/${jobId}`);
  return handleResponse(res);
}

export async function getDocumentMeta(jobId) {
  const res = await apiFetch(`${BASE}/api/v1/document/${jobId}/meta`);
  return handleResponse(res);
}

export async function getDocumentBlob(jobId) {
  const res = await apiFetch(`${BASE}/api/v1/document/${jobId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function getDocumentHtml(jobId) {
  const res = await apiFetch(`${BASE}/api/v1/document/${jobId}/html`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

export async function listSessions({ includeArchived = false } = {}) {
  const res = await apiFetch(`${BASE}/api/v1/sessions?include_archived=${includeArchived}`);
  return handleResponse(res);
}

export async function getSession(sessionId) {
  const res = await apiFetch(`${BASE}/api/v1/sessions/${sessionId}`);
  return handleResponse(res);
}

export async function reevaluateSession(sessionId) {
  const res = await apiFetch(`${BASE}/api/v1/sessions/${sessionId}/reevaluate`, { method: 'POST' });
  return handleResponse(res);
}

export async function archiveSession(sessionId) {
  const res = await apiFetch(`${BASE}/api/v1/sessions/${sessionId}`, { method: 'DELETE' });
  return handleResponse(res);
}

export async function unarchiveSession(sessionId) {
  const res = await apiFetch(`${BASE}/api/v1/sessions/${sessionId}/unarchive`, { method: 'POST' });
  return handleResponse(res);
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
  const res = await apiFetch(`${BASE}/api/v1/evaluate/sync`, {
    method: 'POST',
    body: form,
  });
  return handleResponse(res);
}

export async function getCurrentUser() {
  const res = await apiFetch(`${BASE}/api/v1/auth/me`);
  return handleResponse(res);
}

export async function signUp(payload) {
  const res = await apiFetch(`${BASE}/api/v1/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function signIn({ email, password }) {
  const res = await apiFetch(`${BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function signOut() {
  const res = await apiFetch(`${BASE}/api/v1/auth/logout`, { method: 'POST' });
  return handleResponse(res);
}

export function googleSignInUrl() {
  return `${BASE}/api/v1/auth/google/start`;
}
