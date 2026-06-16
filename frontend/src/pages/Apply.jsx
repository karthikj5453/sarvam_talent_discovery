import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Briefcase, User, Mail, Phone, FileText, UploadCloud, AlertCircle } from 'lucide-react';

export default function Apply() {
  const [jobs, setJobs] = useState([]);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', jobId: '' });
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadJobs() {
      try {
        const activeJobs = await api.getJobs();
        setJobs(activeJobs);
        if (activeJobs.length > 0) {
          setFormData((prev) => ({ ...prev, jobId: activeJobs[0].id }));
        }
      } catch (err) {
        setError('Failed to load active jobs. Please check if backend is running.');
      }
    }
    loadJobs();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.jobId) {
      setError('Please select a job position.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      // 1. Submit application
      const candidate = await api.applyJob(formData);
      
      // 2. Start screening session
      const session = await api.startScreening(candidate.id);

      // 3. Upload resume if provided
      if (resumeFile) {
        await api.uploadResume(candidate.id, resumeFile);
      }

      // Store in session storage to pass to the next screens
      sessionStorage.setItem('screening_session_id', session.id);
      sessionStorage.setItem('candidate_name', candidate.name);

      // Navigate to intro recording screen
      navigate('/intro');
    } catch (err) {
      setError(err.message || 'Something went wrong during application.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <h1 className="title-gradient">Join Our Team</h1>
        <p className="subtitle">Submit details and start your multilingual AI screening session instantly.</p>

        {error && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', padding: '1rem', borderRadius: '0.75rem', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.9rem' }}>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User size={16} /> Full Name
            </label>
            <input
              type="text"
              name="name"
              placeholder="e.g. Aarav Sharma"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Mail size={16} /> Email Address
            </label>
            <input
              type="email"
              name="email"
              placeholder="e.g. aarav@company.com"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Phone size={16} /> Phone Number
            </label>
            <input
              type="tel"
              name="phone"
              placeholder="e.g. +91 9876543210"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Briefcase size={16} /> Select Job Position
            </label>
            <select name="jobId" value={formData.jobId} onChange={handleChange} required>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} - {job.department || 'General'} ({job.location || 'Remote'})
                </option>
              ))}
              {jobs.length === 0 && <option value="">No active positions available</option>}
            </select>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={16} /> Upload Resume (PDF)
            </label>
            <div 
              className="file-upload-zone"
              onClick={() => document.getElementById('resume-input').click()}
            >
              <UploadCloud size={32} style={{ color: 'var(--primary)', marginBottom: '0.5rem' }} />
              {resumeFile ? (
                <p style={{ color: 'var(--text-light)', fontWeight: 500 }}>{resumeFile.name}</p>
              ) : (
                <>
                  <p style={{ color: 'var(--text-light)', fontWeight: 500 }}>Click to browse resume</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.25rem' }}>Only PDF format supported</p>
                </>
              )}
              <input
                id="resume-input"
                type="file"
                accept=".pdf"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
            style={{ marginTop: '1rem' }}
          >
            {loading ? 'Submitting...' : 'Apply & Start Interview'}
          </button>
        </form>
      </div>
    </div>
  );
}
