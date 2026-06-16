const BASE_URL = 'http://localhost:8000';

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
    try {
      const data = await response.json();
      errorDetail = data.detail || errorDetail;
    } catch (_) {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Login
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

  // Logout
  logout() {
    localStorage.removeItem('hr_token');
    window.location.href = '/login';
  },

  // Get current HR user profile
  async getMe() {
    return request('/auth/me');
  },

  // Register a new HR account (optional utility)
  async register({ email, password, full_name, role = 'hr' }) {
    return request('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, full_name, role }),
    });
  },

  // Job Operations
  async getJobs() {
    return request('/jobs/');
  },

  async createJob(jobData) {
    return request('/jobs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jobData),
    });
  },

  // Candidate Operations
  async getCandidates(jobId = null) {
    const endpoint = jobId ? `/candidates/?job_id=${jobId}` : '/candidates/';
    return request(endpoint);
  },

  async updateCandidateStatus(candidateId, status) {
    return request(`/candidates/${candidateId}/status?status=${status}`, {
      method: 'PATCH',
    });
  },

  // Competency Evaluations
  async getEvaluations() {
    return request('/evaluations/');
  },

  async getCandidateEvaluation(candidateId) {
    return request(`/evaluations/candidate/${candidateId}`);
  },

  // Dashboard Aggregates & Analytics
  async getStats() {
    return request('/dashboard/stats');
  },

  async getLanguages() {
    return request('/dashboard/languages');
  },

  async getFunnel() {
    return request('/dashboard/funnel');
  },
};
