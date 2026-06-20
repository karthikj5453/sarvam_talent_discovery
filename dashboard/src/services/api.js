const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('hr_token');
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    localStorage.removeItem('hr_token');
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Please login again.');
  }

  if (!response.ok) {
    let errorDetail = 'API error';
    const text = await response.text();
    try {
      const data = JSON.parse(text);
      errorDetail = data.detail || text;
    } catch (_) {
      errorDetail = text || errorDetail;
    }
    throw new Error(errorDetail);
  }

  // Some endpoints return 204 No Content
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  // ─── Auth ──────────────────────────────────────────────────
  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 password flow uses 'username'
    formData.append('password', password);

    const data = await request('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (data.access_token) {
      localStorage.setItem('hr_token', data.access_token);
    }
    return data;
  },

  logout() {
    localStorage.removeItem('hr_token');
    window.location.href = '/login';
  },

  async getMe() {
    return request('/auth/me');
  },

  async register({ email, password, full_name, role = 'hr' }) {
    return request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name, role }),
    });
  },

  // ─── Jobs ──────────────────────────────────────────────────
  async getJobs(activeOnly = true) {
    return request(`/jobs/?active_only=${activeOnly}`);
  },

  async createJob(jobData) {
    return request('/jobs/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData),
    });
  },

  async updateJob(jobId, jobData) {
    return request(`/jobs/${jobId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData),
    });
  },

  async deleteJob(jobId) {
    return request(`/jobs/${jobId}`, { method: 'DELETE' });
  },

  // ─── Candidates ────────────────────────────────────────────
  async getCandidates(jobId = null, status = null) {
    const params = new URLSearchParams();
    if (jobId) params.append('job_id', jobId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/candidates/${query}`);
  },

  async getCandidate(candidateId) {
    return request(`/candidates/${candidateId}`);
  },

  async updateCandidateStatus(candidateId, newStatus) {
    // Status goes in request body as JSON
    return request(`/candidates/${candidateId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
  },

  async deleteCandidate(candidateId) {
    return request(`/candidates/${candidateId}`, { method: 'DELETE' });
  },

  // ─── Evaluations ───────────────────────────────────────────
  async getEvaluations(jobId = null, minScore = null) {
    const params = new URLSearchParams();
    if (jobId) params.append('job_id', jobId);
    if (minScore !== null) params.append('min_score', minScore);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/evaluations/${query}`);
  },

  async getCandidateEvaluation(candidateId) {
    // Backend route is GET /evaluations/{candidate_id}
    return request(`/evaluations/${candidateId}`);
  },

  // ─── Dashboard Pipeline ────────────────────────────────────
  async getPipeline(jobId = null) {
    const query = jobId ? `?job_id=${jobId}` : '';
    return request(`/dashboard/pipeline${query}`);
  },

  async getDashboardCandidates(jobId = null, status = null) {
    const params = new URLSearchParams();
    if (jobId) params.append('job_id', jobId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/dashboard/candidates${query}`);
  },

  async getTopCandidates(jobId, limit = 10) {
    return request(`/dashboard/jobs/${jobId}/top-candidates?limit=${limit}`);
  },

  // ─── Analytics ─────────────────────────────────────────────
  async getFunnel() {
    return request('/analytics/funnel');
  },

  async getDropOff() {
    return request('/analytics/drop-off');
  },

  async trackEvent(eventType, candidateId = null, jobId = null, metadata = {}) {
    return request('/analytics/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        candidate_id: candidateId,
        job_id: jobId,
        event_metadata: metadata,
      }),
    });
  },

  // ─── Screening Session (read-only for HR) ─────────────────
  async getScreeningSession(sessionId) {
    return request(`/screening/${sessionId}`);
  },
};
