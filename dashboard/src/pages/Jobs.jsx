import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Briefcase, MapPin, Layers, ListChecks, Plus, X, AlertCircle } from 'lucide-react';

const DEFAULT_WEIGHTS = {
  technical_depth: 0.25,
  first_principles: 0.20,
  shipping_velocity: 0.20,
  ownership_signals: 0.15,
  curiosity_depth: 0.10,
  multilingual_fluency: 0.10,
};

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form State
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [location, setLocation] = useState('Remote');
  const [description, setDescription] = useState('');
  const [skillsStr, setSkillsStr] = useState('');
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);

  const loadJobs = async () => {
    try {
      const activeJobs = await api.getJobs();
      setJobs(activeJobs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleWeightChange = (key, val) => {
    setWeights((prev) => ({
      ...prev,
      [key]: parseFloat(val) || 0,
    }));
  };

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate weights sum to 1.0 (with a small margin for floats)
    if (Math.abs(totalWeight - 1.0) > 0.01) {
      setError(`Competency weights must sum up to exactly 1.0. Current sum: ${totalWeight.toFixed(2)}`);
      return;
    }

    const skills = skillsStr.split(',').map(s => s.trim()).filter(Boolean);

    try {
      await api.createJob({
        title,
        department,
        location,
        description,
        required_skills: skills,
        competency_weights: weights,
      });

      // Reset Form
      setTitle('');
      setDepartment('');
      setLocation('Remote');
      setDescription('');
      setSkillsStr('');
      setWeights(DEFAULT_WEIGHTS);
      setShowModal(false);
      loadJobs();
    } catch (err) {
      setError(err.message || 'Failed to create job posting.');
    }
  };

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="skeleton" style={{ height: 28, width: 160, marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 16, width: 280 }} />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h1 className="page-title">Job Profiles</h1>
          <p className="page-subtitle">Manage role configurations and competency weightings for AI evaluations.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New Job Profile
        </button>
      </div>

      {/* Jobs Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Role / Title</th>
              <th>Department</th>
              <th>Location</th>
              <th>Required Skills</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td style={{ fontWeight: 600, color: '#fff' }}>{job.title}</td>
                <td>{job.department || 'N/A'}</td>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <MapPin size={14} style={{ color: 'var(--text-muted)' }} />
                    {job.location}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                    {job.required_skills?.map((s) => (
                      <span key={s} className="badge badge-primary" style={{ fontSize: '0.7rem' }}>
                        {s}
                      </span>
                    ))}
                    {(!job.required_skills || job.required_skills.length === 0) && '-'}
                  </div>
                </td>
                <td>
                  <span className={`badge ${job.is_active ? 'badge-success' : 'badge-danger'}`}>
                    {job.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td colSpan="5">
                  <div className="empty-state">
                    <div className="empty-state-icon"><Briefcase size={22} /></div>
                    <p style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No job profiles yet</p>
                    <p style={{ fontSize: '0.82rem' }}>Click "New Job Profile" to create the first one.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Dialog */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">New Job Profile</h2>
              <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <X size={18} />
              </button>
            </div>

            {error && (
              <div className="alert alert-error">
                <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <label>JOB TITLE</label>
                  <input type="text" className="form-input" placeholder="e.g. AI Product Engineer" value={title} onChange={(e) => setTitle(e.target.value)} required />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <label>DEPARTMENT</label>
                  <input type="text" className="form-input" placeholder="e.g. Engineering" value={department} onChange={(e) => setDepartment(e.target.value)} required />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <label>LOCATION</label>
                  <input type="text" className="form-input" placeholder="e.g. Bangalore, IN" value={location} onChange={(e) => setLocation(e.target.value)} required />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <label>REQUIRED SKILLS (COMMA-SEPARATED)</label>
                  <input type="text" className="form-input" placeholder="e.g. Python, RAG, FastAPI" value={skillsStr} onChange={(e) => setSkillsStr(e.target.value)} required />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <label>JOB DESCRIPTION</label>
                <textarea rows="3" className="form-input" style={{ resize: 'none' }} placeholder="Detail target responsibilities..." value={description} onChange={(e) => setDescription(e.target.value)} required></textarea>
              </div>

              <div style={{ borderTop: '1px solid var(--border-muted)', paddingTop: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <ListChecks size={16} /> Competency Weightings
                  </label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: Math.abs(totalWeight - 1.0) < 0.01 ? 'var(--success)' : 'var(--danger)' }}>
                    Total: {totalWeight.toFixed(2)} / 1.00
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxHeight: '180px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                  {Object.entries(weights).map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <label style={{ fontSize: '0.75rem', textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {key.replace('_', ' ')}
                      </label>
                      <input 
                        type="number" 
                        step="0.05" 
                        min="0" 
                        max="1" 
                        className="form-input"
                        value={value} 
                        onChange={(e) => handleWeightChange(key, e.target.value)} 
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ width: '50%' }} onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ width: '50%' }}>
                  Create Role
                </button>
              </div>
            </form>
            </div>
        </div>
      )}
    </div>
  );
}
