const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getScreeningToken() {
  return sessionStorage.getItem('screening_token') || '';
}

function parseErrorDetail(detail) {
  if (!detail) return 'Something went wrong. Please try again.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ');
  }
  return String(detail);
}

async function request(endpoint, options = {}) {
  const headers = { ...options.headers };
  const screeningToken = getScreeningToken();
  if (screeningToken && !headers['X-Screening-Token']) {
    headers['X-Screening-Token'] = screeningToken;
  }

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = 'API error';
    const text = await response.text();
    try {
      const data = JSON.parse(text);
      errorDetail = parseErrorDetail(data.detail) || text;
    } catch (_) {
      errorDetail = text || errorDetail;
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  async getJobs() {
    return request('/jobs/public');
  },

  async applyJob({ name, email, phone, github_url, jobId, consent_given }) {
    return request('/candidates/public/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, github_url, job_id: jobId, consent_given }),
    });
  },

  async startScreening(candidateId) {
    const session = await request('/screening/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_id: candidateId }),
    });
    if (session.screening_token) {
      sessionStorage.setItem('screening_token', session.screening_token);
    }
    return session;
  },

  async getScreeningSession(sessionId) {
    return request(`/screening/${sessionId}`);
  },

  async getSessionJob(sessionId) {
    return request(`/screening/${sessionId}/job`);
  },

  async uploadResume(candidateId, file) {
    const formData = new FormData();
    formData.append('candidate_id', candidateId);
    formData.append('file', file);
    return request('/screening/upload-resume', { method: 'POST', body: formData });
  },

  async uploadIntro(sessionId, audioBlob, mimeType = 'audio/webm') {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    if (audioBlob) {
      const ext = mimeType.includes('ogg') ? 'ogg' : 'webm';
      formData.append('file', audioBlob, `intro.${ext}`);
    }
    return request('/screening/upload-intro', { method: 'POST', body: formData });
  },

  async uploadAnswer(sessionId, questionIndex, audioBlob, code = null, mimeType = 'audio/webm') {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('question_index', questionIndex.toString());
    if (audioBlob) {
      const ext = mimeType.includes('ogg') ? 'ogg' : 'webm';
      formData.append('file', audioBlob, `answer_${questionIndex}.${ext}`);
    }
    if (code) formData.append('code', code);
    return request('/screening/upload-answer', { method: 'POST', body: formData });
  },

  async completeScreening(sessionId, proctoringFlags = {}) {
    return request(`/screening/complete/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(proctoringFlags),
    });
  },

  async trackEvent(eventType, candidateId = null, jobId = null, metadata = {}) {
    try {
      await request('/analytics/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: eventType,
          candidate_id: candidateId,
          job_id: jobId,
          event_metadata: metadata,
        }),
      });
    } catch (_) { /* non-blocking */ }
  },
};
