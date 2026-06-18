const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, options);
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
  return response.json();
}

export const api = {
  // Public list of active jobs
  async getJobs() {
    return request('/jobs/public');
  },

  // Candidate application
  async applyJob({ name, email, phone, github_url, jobId }) {
    return request('/candidates/public/apply', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, email, phone, github_url, job_id: jobId }),
    });
  },

  // Start screening session
  async startScreening(candidateId) {
    return request('/screening/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ candidate_id: candidateId }),
    });
  },

  // Get screening session details
  async getScreeningSession(sessionId) {
    return request(`/screening/${sessionId}`);
  },

  // Upload resume PDF
  async uploadResume(candidateId, file) {
    const formData = new FormData();
    formData.append('candidate_id', candidateId);
    formData.append('file', file);

    return request('/screening/upload-resume', {
      method: 'POST',
      body: formData,
    });
  },

  // Upload voice introduction
  async uploadIntro(sessionId, audioBlob, transcript = null, language = null) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    
    if (audioBlob) {
      formData.append('file', audioBlob, 'intro.wav');
    }
    if (transcript) {
      formData.append('transcript', transcript);
    }
    if (language) {
      formData.append('detected_language', language);
    }

    return request('/screening/upload-intro', {
      method: 'POST',
      body: formData,
    });
  },

  // Upload voice answer
  async uploadAnswer(sessionId, questionIndex, audioBlob, transcript = null) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('question_index', questionIndex.toString());
    
    if (audioBlob) {
      formData.append('file', audioBlob, `answer_${questionIndex}.wav`);
    }
    if (transcript) {
      formData.append('transcript', transcript);
    }

    return request('/screening/upload-answer', {
      method: 'POST',
      body: formData,
    });
  },

  // Complete screening session
  async completeScreening(sessionId, proctoringFlags = {}) {
    return request(`/screening/complete?session_id=${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(proctoringFlags),
    });
  },
};
