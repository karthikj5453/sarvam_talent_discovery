import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Search, Filter, User, Calendar, Award, Globe, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Candidates() {
  const [candidatesWithScores, setCandidatesWithScores] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [candList, jobList] = await Promise.all([
        api.getDashboardCandidates(),   // returns [{candidate, score}]
        api.getJobs()
      ]);
      setCandidatesWithScores(candList);
      setJobs(jobList);
    } catch (err) {
      console.error('Failed to load candidate metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getJobTitle = (jobId) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.title : 'Software Engineer';
  };

  // Filter candidates
  const filtered = candidatesWithScores.filter(({ candidate }) => {
    const matchesJob = selectedJobId ? candidate.job_id === selectedJobId : true;
    const matchesSearch = searchTerm
      ? (candidate.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        candidate.email.toLowerCase().includes(searchTerm.toLowerCase())
      : true;
    return matchesJob && matchesSearch;
  });

  if (loading) {
    return <p style={{ color: 'var(--text-secondary)' }}>Loading candidate ledger...</p>;
  }

  return (
    <div>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>Candidates Directory</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2.5rem' }}>Review applicants, track screening progress, and inspect evaluation metrics.</p>

      {/* Filter and Search Bar Layout */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
        <div style={{ position: 'relative', flexGrow: 1, minWidth: '240px' }}>
          <Search size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search candidates by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '220px' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select 
            className="form-input"
            value={selectedJobId} 
            onChange={(e) => setSelectedJobId(e.target.value)}
          >
            <option value="">All Job Profiles</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} ({job.department})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Candidates List */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Applicant Name</th>
              <th>Applied Role</th>
              <th>Overall Score</th>
              <th>Primary Language</th>
              <th>Applied Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(({ candidate: cand, score }) => {
              const totalScore = score?.total_score;
              return (
                <tr key={cand.id}>
                  <td style={{ fontWeight: 600, color: '#fff' }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span>{cand.name}</span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-secondary)' }}>{cand.email}</span>
                    </div>
                  </td>
                  <td>{getJobTitle(cand.job_id)}</td>
                  <td style={{ fontWeight: 700 }}>
                    {totalScore != null ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: totalScore >= 6.0 ? '#34d399' : '#a5b4fc' }}>
                        <Award size={14} /> {totalScore.toFixed(1)}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Unscreened</span>
                    )}
                  </td>
                  <td>
                    {cand.detected_language ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}>
                        <Globe size={14} style={{ color: 'var(--text-secondary)' }} />
                        {cand.detected_language}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>-</span>
                    )}
                  </td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      <Calendar size={14} />
                      {new Date(cand.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${cand.status === 'shortlisted' ? 'success' : cand.status === 'screened' ? 'primary' : 'warning'}`}>
                      {cand.status}
                    </span>
                  </td>
                  <td>
                    <Link to={`/candidates/${cand.id}`} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                      Details <ArrowRight size={12} />
                    </Link>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No candidates matching the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
