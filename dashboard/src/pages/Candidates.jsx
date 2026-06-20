import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Search, Filter, User, Calendar, Award, Globe, ArrowRight, ChevronLeft, ChevronRight, Clock, CheckCircle2, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

const PAGE_SIZE = 15;

export default function Candidates() {
  const [candidatesWithScores, setCandidatesWithScores] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

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

  const handleDeleteCandidate = async (candId) => {
    if (!window.confirm("Are you sure you want to permanently delete this candidate and all their data? This cannot be undone.")) return;
    try {
      await api.deleteCandidate(candId);
      loadData();
    } catch (err) {
      alert(err.message || 'Failed to delete candidate.');
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

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paginated = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  // Reset to page 1 on filter change
  const handleSearch = (val) => { setSearchTerm(val); setPage(1); };
  const handleJobFilter = (val) => { setSelectedJobId(val); setPage(1); };

  // Evaluation status helper
  const evalStatus = (candidate, score) => {
    if (score?.total_score != null) return 'evaluated';
    if (candidate.status === 'screened') return 'pending';
    return 'unscreened';
  };

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="skeleton" style={{ height: 28, width: 220, marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 16, width: 380 }} />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Candidates Directory</h1>
        <p className="page-subtitle">Review applicants, track screening progress, and inspect AI evaluation scores.</p>
      </div>

      {/* Filter and Search Bar Layout */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flexGrow: 1, minWidth: '240px' }}>
          <Search size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search candidates by name or email..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '220px' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select
            className="form-input"
            value={selectedJobId}
            onChange={(e) => handleJobFilter(e.target.value)}
          >
            <option value="">All Job Profiles</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} ({job.department})
              </option>
            ))}
          </select>
        </div>

        {/* Total count */}
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {filtered.length} candidate{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Candidates Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Applicant Name</th>
              <th>Applied Role</th>
              <th>Overall Score</th>
              <th>Eval Status</th>
              <th>Primary Language</th>
              <th>Applied Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map(({ candidate: cand, score }) => {
              const totalScore = score?.total_score;
              const ev = evalStatus(cand, score);
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
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                  {/* Feature 4: Evaluation Status Indicator */}
                  <td>
                    {ev === 'evaluated' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.78rem', color: '#34d399', fontWeight: 600 }}>
                        <CheckCircle2 size={13} /> Scored
                      </span>
                    )}
                    {ev === 'pending' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.78rem', color: '#fbbf24', fontWeight: 600 }}>
                        <Clock size={13} /> Evaluating…
                      </span>
                    )}
                    {ev === 'unscreened' && (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Not screened</span>
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
                  <td style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <Link to={`/candidates/${cand.id}`} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', width: 'auto' }}>
                      Details <ArrowRight size={12} />
                    </Link>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.4rem', color: 'var(--error)', borderColor: 'rgba(239, 71, 111, 0.2)', width: 'auto', display: 'inline-flex' }}
                      onClick={() => handleDeleteCandidate(cand.id)}
                      title="Delete Candidate Profile"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No candidates matching the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Feature 3: Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button
            className="btn btn-ghost"
            style={{ padding: '0.5rem 0.9rem' }}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft size={16} />
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              className={`btn ${p === currentPage ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '0.5rem 0.85rem', minWidth: 38 }}
              onClick={() => setPage(p)}
            >
              {p}
            </button>
          ))}

          <button
            className="btn btn-ghost"
            style={{ padding: '0.5rem 0.9rem' }}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            <ChevronRight size={16} />
          </button>

          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Page {currentPage} of {totalPages}
          </span>
        </div>
      )}
    </div>
  );
}
