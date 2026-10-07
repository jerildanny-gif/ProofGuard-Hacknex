const API_BASE = '/api';

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

export async function getSampleDatasets() {
  const res = await fetch(`${API_BASE}/datasets/samples`);
  if (!res.ok) throw new Error('Failed to fetch sample datasets');
  return await res.json();
}

export async function getAllDatasets() {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets list');
  return await res.json();
}

export async function uploadDatasetFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to upload dataset');
  }

  return await res.json();
}

export async function getDatasetDetails(datasetId) {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch dataset details');
  }
  return await res.json();
}

export async function getDatasetPreview(datasetId, page = 1, pageSize = 25) {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}/preview?page=${page}&page_size=${pageSize}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch preview data');
  }
  return await res.json();
}

export async function analyzeQuestion(question, datasetId = null) {
  const payload = { question };
  if (datasetId) {
    payload.dataset_id = datasetId;
  }
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to analyze question');
  }
  return await res.json();
}

export async function getAnalysisSuggestions(datasetId = null) {
  const url = datasetId 
    ? `${API_BASE}/analyze/suggestions?dataset_id=${encodeURIComponent(datasetId)}`
    : `${API_BASE}/analyze/suggestions`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch suggestions');
  return await res.json();
}

export async function getDatasetForensics(datasetId) {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}/forensics`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch dataset forensics');
  }
  return await res.json();
}

export async function assessQuestionForensics(question, datasetId = null) {
  const payload = { question };
  if (datasetId) {
    payload.dataset_id = datasetId;
  }
  const res = await fetch(`${API_BASE}/analyze/forensics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to assess question forensics');
  }
  return await res.json();
}

// ─── STAGE 4: PROOFGUARD TRUST LAYER ─────────────────────────────────────────

/**
 * Submit an analyst's answer to the Answer Guardian for independent trust evaluation.
 * @param {Object} guardianRequest - GuardianRequest payload (question, answer details, forensic findings)
 * @returns {Promise<Object>} GuardianResponse with trust score, challenges, verdict, proof lineage
 */
export async function evaluateWithGuardian(guardianRequest) {
  const res = await fetch(`${API_BASE}/guardian/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(guardianRequest),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Guardian evaluation failed');
  }
  return await res.json();
}

/**
 * Submit a user counter-challenge against the Guardian's verdict.
 * @param {Object} challengeRequest - ChallengeRequest payload (question, challenge_text, dataset_id)
 * @returns {Promise<Object>} ChallengeResponse with upheld/overturned verdict
 */
export async function submitUserChallenge(challengeRequest) {
  const res = await fetch(`${API_BASE}/guardian/challenge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(challengeRequest),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Challenge submission failed');
  }
  return await res.json();
}

