const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function parseErrorDetail(detail) {
  if (!detail) return 'API error';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ');
  }
  return String(detail);
}

async function request(endpoint, options = {}, isRetry = false) {
  const token = localStorage.getItem('hr_token');
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
    // Include cookies for the refresh endpoint (HTTP-only cookie is sent automatically)
    credentials: 'include',
  });

  if (response.status === 401) {
    if (!isRetry) {
      // Attempt silent token refresh using the HTTP-only cookie
      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',  // Sends the HTTP-only hr_refresh_token cookie
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem('hr_token', data.access_token);
          return request(endpoint, options, true);
        }
      } catch (err) {
        console.error('Token refresh failed', err);
      }
    }
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
      errorDetail = parseErrorDetail(data.detail) || text;
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

    const data = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
      credentials: 'include',  // Ensures the Set-Cookie for refresh token is accepted
    });

    if (!data.ok) {
      const err = await data.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail ? parseErrorDetail(err.detail) : 'Login failed');
    }

    const json = await data.json();
    if (json.access_token) {
      localStorage.setItem('hr_token', json.access_token);
      // Note: refresh_token is now stored as HTTP-only cookie by the backend
      // No need to save it in localStorage
    }
    return json;
  },

  async logout() {
    try {
      // Ask backend to clear the HTTP-only refresh cookie
      await fetch(`${BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (_) {
      // Silently fail — we always clear local state
    }
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

  async getDashboardCandidates(jobId = null, status = null, search = null, skip = 0, limit = 50) {
    const params = new URLSearchParams();
    if (jobId) params.append('job_id', jobId);
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('skip', skip);
    params.append('limit', limit);
    return request(`/dashboard/candidates?${params.toString()}`);
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

  async getCandidateSessions(candidateId) {
    return request(`/candidates/${candidateId}/sessions`);
  },

  async getNotes(candidateId) {
    return request(`/notes/candidates/${candidateId}/notes`);
  },

  async addNote(candidateId, content, isPinned = false) {
    return request(`/notes/candidates/${candidateId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, is_pinned: isPinned }),
    });
  },

  async getTimeline(candidateId) {
    return request(`/notes/candidates/${candidateId}/timeline`);
  },
};
