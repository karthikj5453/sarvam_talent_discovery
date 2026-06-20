import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Search, Filter, User, Calendar, Award, Globe, ArrowRight, ChevronLeft, ChevronRight, Clock, CheckCircle2, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

const PAGE_SIZE = 15;

export default function Candidates() {
  const [candidatesWithScores, setCandidatesWithScores] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [page, setPage] = useState(1);

  const [sortBy, setSortBy] = useState('date_desc');
  const [statusFilter, setStatusFilter] = useState('all');
  const [hrUser, setHrUser] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const skip = (page - 1) * PAGE_SIZE;
      const statusParam = statusFilter !== 'all' ? statusFilter : null;
      const [candResult, jobList, user] = await Promise.all([
        api.getDashboardCandidates(selectedJobId || null, statusParam, searchTerm || null, skip, PAGE_SIZE),
        jobs.length ? Promise.resolve(jobs) : api.getJobs(),
        api.getMe().catch(() => null),
      ]);
      if (Array.isArray(candResult)) {
        setCandidatesWithScores(candResult);
        setTotalCount(candResult.length);
      } else {
        setCandidatesWithScores(candResult?.items || []);
        setTotalCount(candResult?.total || 0);
      }
      if (!jobs.length) setJobs(jobList);
      setHrUser(user);
    } catch (err) {
      setLoadError(err.message || 'Failed to load candidates.');
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
  }, [page, selectedJobId, statusFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      loadData();
    }, 400);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const getJobTitle = (jobId) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.title : 'Software Engineer';
  };

  const filteredAndSorted = React.useMemo(() => {
    let result = [...candidatesWithScores];
    result.sort((a, b) => {
      if (sortBy === 'date_desc') return new Date(b.candidate.created_at) - new Date(a.candidate.created_at);
      if (sortBy === 'date_asc') return new Date(a.candidate.created_at) - new Date(b.candidate.created_at);
      if (sortBy === 'score_desc') return (b.score?.total_score || -1) - (a.score?.total_score || -1);
      if (sortBy === 'score_asc') return (a.score?.total_score || -1) - (b.score?.total_score || -1);
      return 0;
    });
    return result;
  }, [candidatesWithScores, sortBy]);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paginated = filteredAndSorted;

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

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '150px' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select
            className="form-input"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          >
            <option value="all">All Status</option>
            <option value="applied">Applied</option>
            <option value="screened">Screened</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="interviewing">Interviewing</option>
            <option value="offered">Offered</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '200px' }}>
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '160px' }}>
          <select
            className="form-input"
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
          >
            <option value="date_desc">Sort: Newest First</option>
            <option value="date_asc">Sort: Oldest First</option>
            <option value="score_desc">Sort: Highest Score</option>
            <option value="score_asc">Sort: Lowest Score</option>
          </select>
        </div>

        {/* Total count */}
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {totalCount} candidate{totalCount !== 1 ? 's' : ''}
        </span>
      </div>

      {loadError && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{loadError}</div>
      )}

      {/* Desktop table */}
      <div className="table-container candidates-table-desktop">
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
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
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
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <Link to={`/candidates/${cand.id}`} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', width: 'auto' }}>
                        Details <ArrowRight size={12} />
                      </Link>
                      {hrUser && hrUser.role !== 'interviewer' && (
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.4rem', color: 'var(--error)', borderColor: 'rgba(239, 71, 111, 0.2)', width: 'auto', display: 'inline-flex' }}
                          onClick={() => handleDeleteCandidate(cand.id)}
                          title="Delete Candidate Profile"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {paginated.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No candidates matching the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="candidates-cards-mobile">
        {paginated.map(({ candidate: cand, score }) => {
          const totalScore = score?.total_score;
          return (
            <div key={cand.id} className="candidate-card-mobile dashboard-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>{cand.name}</strong>
                <span className={`badge badge-${cand.status === 'shortlisted' ? 'success' : 'primary'}`}>{cand.status}</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>{cand.email}</p>
              <p style={{ fontSize: '0.85rem', marginBottom: '0.75rem' }}>{getJobTitle(cand.job_id)}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: totalScore >= 6 ? '#34d399' : '#a5b4fc' }}>
                  {totalScore != null ? `${totalScore.toFixed(1)}/10` : '—'}
                </span>
                <Link to={`/candidates/${cand.id}`} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', width: 'auto' }}>
                  Details <ArrowRight size={12} />
                </Link>
              </div>
            </div>
          );
        })}
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

          {(() => {
            const pages = [];
            const maxButtons = 7;
            let start = Math.max(1, currentPage - Math.floor(maxButtons / 2));
            let end = Math.min(totalPages, start + maxButtons - 1);
            start = Math.max(1, end - maxButtons + 1);
            for (let p = start; p <= end; p++) pages.push(p);
            return pages.map(p => (
              <button
                key={p}
                className={`btn ${p === currentPage ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.5rem 0.85rem', minWidth: 38 }}
                onClick={() => setPage(p)}
              >
                {p}
              </button>
            ));
          })()}

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
