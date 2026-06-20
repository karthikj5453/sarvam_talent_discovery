import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Briefcase, User, Mail, Phone, UploadCloud, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react';

const STEPS = ['Apply', 'Intro', 'Interview', 'Done'];

export default function Apply() {
  const [jobs, setJobs] = useState([]);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', github_url: '', jobId: '', consent_given: false });
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadJobs() {
      try {
        const activeJobs = await api.getJobs();
        setJobs(activeJobs);
        const params = new URLSearchParams(window.location.search);
        const jobParam = params.get('job_id');
        if (jobParam && activeJobs.some(j => j.id === jobParam)) {
          setFormData(prev => ({ ...prev, jobId: jobParam }));
        } else if (activeJobs.length > 0) {
          setFormData(prev => ({ ...prev, jobId: activeJobs[0].id }));
        }
      } catch {
        setError('Failed to load open positions. Make sure the backend is running.');
      } finally {
        setJobsLoading(false);
      }
    }
    loadJobs();
  }, []);

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!formData.jobId) { setError('Please select a position.'); return; }
    if (!formData.consent_given) {
      setError('Consent for data processing is required to start screening.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const candidate = await api.applyJob(formData);

      const session = await api.startScreening(candidate.id);

      if (resumeFile) {
        try {
          await api.uploadResume(candidate.id, resumeFile);
        } catch (resumeErr) {
          console.warn('Resume upload failed (non-blocking):', resumeErr.message);
        }
      }

      sessionStorage.setItem('screening_session_id', session.id);
      sessionStorage.setItem('candidate_id', candidate.id);
      sessionStorage.setItem('candidate_name', candidate.name);
      if (session.screening_token) {
        sessionStorage.setItem('screening_token', session.screening_token);
      }

      api.trackEvent('application_submitted', candidate.id, formData.jobId);
      navigate('/intro');
    } catch (err) {
      const msg = err.status === 409
        ? 'You have already applied for this position. Contact HR if you need to continue your screening.'
        : (err.message || 'Something went wrong. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const selectedJob = jobs.find(j => j.id === formData.jobId);

  return (
    <div className="app-container">
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.375rem 1rem',
          background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: '9999px', fontSize: '0.78rem', fontWeight: 700,
          color: 'var(--primary-light)', letterSpacing: '0.05em', marginBottom: '1.25rem'
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
          AI SCREENING PORTAL
        </div>
        <h1 className="title-gradient">Start Your Journey</h1>
        <p className="subtitle">Fill in your details and begin an AI-powered multilingual screening in seconds.</p>
      </div>

      {/* Steps */}
      <div className="progress-steps" style={{ marginBottom: '2rem' }}>
        {STEPS.map((s, i) => (
          <div key={s} className="step-item">
            <div className={`step-dot ${i === 0 ? 'active' : ''}`}>{i + 1}</div>
            {i < STEPS.length - 1 && <div className="step-line" />}
          </div>
        ))}
      </div>

      <div className="glass-card">
        {error && (
          <div className="alert alert-error">
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Name + Email row */}
          <div className="form-grid-2">
            <div className="form-group">
              <label className="form-label"><User size={12} /> Full Name</label>
              <div className="form-input-wrap">
                <input
                  type="text" name="name" required
                  placeholder="Aarav Sharma"
                  value={formData.name} onChange={handleChange}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label"><Mail size={12} /> Email</label>
              <div className="form-input-wrap">
                <input
                  type="email" name="email" required
                  placeholder="aarav@company.com"
                  value={formData.email} onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label"><Phone size={12} /> Phone Number</label>
            <input
              type="tel" name="phone" required
              placeholder="+91 98765 43210"
              value={formData.phone} onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label className="form-label"><UploadCloud size={12} /> GitHub Profile (Optional)</label>
            <input
              type="url" name="github_url"
              placeholder="https://github.com/aarav"
              value={formData.github_url} onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label className="form-label"><Briefcase size={12} /> Position</label>
            {jobsLoading ? (
              <div style={{ padding: '0.875rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading positions...</div>
            ) : (
              <select name="jobId" value={formData.jobId} onChange={handleChange} required>
                {jobs.map(job => (
                  <option key={job.id} value={job.id}>
                    {job.title} · {job.department || 'General'} · {job.location || 'Remote'}
                  </option>
                ))}
                {jobs.length === 0 && <option value="">No open positions</option>}
              </select>
            )}
          </div>

          {/* Job description preview */}
          {selectedJob?.description && (
            <div style={{
              background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: '0.875rem', padding: '1rem', marginBottom: '1.25rem',
              fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.55
            }}>
              {selectedJob.description.slice(0, 140)}{selectedJob.description.length > 140 ? '…' : ''}
            </div>
          )}

          <div className="form-group">
            <label className="form-label"><UploadCloud size={12} /> Resume (PDF, optional)</label>
            <div
              className={`file-upload-zone ${resumeFile ? 'has-file' : ''}`}
              onClick={() => document.getElementById('resume-input').click()}
              role="button" tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && document.getElementById('resume-input').click()}
            >
              {resumeFile ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <CheckCircle size={18} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--success)', fontSize: '0.9rem' }}>{resumeFile.name}</span>
                </div>
              ) : (
                <>
                  <UploadCloud size={28} style={{ color: 'var(--primary)', marginBottom: '0.5rem' }} />
                  <p style={{ fontWeight: 600, color: 'var(--text-light)', fontSize: '0.9rem' }}>Click to upload PDF</p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Max 10MB · PDF only</p>
                </>
              )}
              <input
                id="resume-input" type="file" accept=".pdf"
                style={{ display: 'none' }}
                onChange={e => {
                  const f = e.target.files[0];
                  if (f && f.size > 10 * 1024 * 1024) {
                    setError('Resume must be under 10 MB.');
                    return;
                  }
                  if (f && f.type !== 'application/pdf') {
                    setError('Only PDF files are accepted.');
                    return;
                  }
                  setResumeFile(f);
                  setError(null);
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginTop: '1.25rem', marginBottom: '1.25rem' }}>
            <input
              id="consent_given"
              type="checkbox"
              name="consent_given"
              checked={formData.consent_given}
              onChange={handleChange}
              required
              style={{
                width: '18px',
                height: '18px',
                accentColor: 'var(--primary)',
                cursor: 'pointer',
                marginTop: '2px'
              }}
            />
            <label htmlFor="consent_given" style={{ fontSize: '0.825rem', color: 'var(--text-light)', lineHeight: 1.4, cursor: 'pointer', userSelect: 'none' }}>
              I consent to the recording, processing, and translation of my voice and resume data for evaluation purposes (DPDP Act 2023 / GDPR compliance).
            </label>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading || jobs.length === 0}>
            {loading ? <><span className="spinner" /> Submitting...</> : <>Apply & Start Screening <ChevronRight size={16} /></>}
          </button>
        </form>

        {/* Language info */}
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-card)' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '0.5rem' }}>
            🌐 Speak in any Indian language during the screening
          </p>
          <div className="lang-tags" style={{ justifyContent: 'center' }}>
            {['English', 'Hindi', 'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Marathi', 'Bengali', 'Gujarati', 'Punjabi'].map(l => (
              <span key={l} className="lang-tag">{l}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
