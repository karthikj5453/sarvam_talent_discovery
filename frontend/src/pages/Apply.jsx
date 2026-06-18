import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Briefcase, User, Mail, Phone, UploadCloud, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react';

const STEPS = ['Apply', 'Intro', 'Interview', 'Done'];

export default function Apply() {
  const [jobs, setJobs] = useState([]);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', github_url: '', jobId: '' });
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
        if (activeJobs.length > 0) {
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
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!formData.jobId) { setError('Please select a position.'); return; }
    setLoading(true);
    setError(null);

    try {
      const candidate = await api.applyJob(formData);
      const session = await api.startScreening(candidate.id);
      if (resumeFile) await api.uploadResume(candidate.id, resumeFile);

      sessionStorage.setItem('screening_session_id', session.id);
      sessionStorage.setItem('candidate_id', candidate.id);
      sessionStorage.setItem('candidate_name', candidate.name);
      navigate('/intro');
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
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
                onChange={e => setResumeFile(e.target.files[0])}
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '0.75rem' }}>
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
