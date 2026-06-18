import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Users, Briefcase, Award, TrendingUp, HelpCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

const STAGE_COLORS = {
  applied:      { color: '#60a5fa', bg: 'rgba(59,130,246,0.15)' },
  screened:     { color: '#34d399', bg: 'rgba(16,185,129,0.15)' },
  shortlisted:  { color: '#a78bfa', bg: 'rgba(139,92,246,0.15)' },
  interviewing: { color: '#fbbf24', bg: 'rgba(245,158,11,0.15)' },
  offered:      { color: '#f9a8d4', bg: 'rgba(236,72,153,0.15)' },
  rejected:     { color: '#f87171', bg: 'rgba(239,68,68,0.15)' },
};

function StatCard({ icon: Icon, label, value, unit, color, bgColor, delay = '0s' }) {
  return (
    <div className="dashboard-card" style={{ animationDelay: delay }}>
      <div className="stat-icon-wrap" style={{ background: bgColor }}>
        <Icon size={18} style={{ color }} />
      </div>
      <p className="card-label">{label}</p>
      <p className="card-value" style={{ animationDelay: delay }}>
        {value}
        {unit && <span className="card-value-unit">{unit}</span>}
      </p>
    </div>
  );
}

export default function Overview() {
  const [pipeline, setPipeline] = useState({ total_candidates: 0, stages: [] });
  const [funnel, setFunnel] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getPipeline(),
      api.getFunnel(),
      api.getJobs(),
      api.getEvaluations(),
    ]).then(([p, f, j, e]) => {
      setPipeline(p);
      setFunnel(Array.isArray(f) ? f : []);
      setJobs(j);
      setEvaluations(e);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const totalCandidates = pipeline.total_candidates || 0;
  const activeJobs = jobs.length;
  const scoredEvals = evaluations.filter(e => e.total_score != null);
  const avgScore = scoredEvals.length > 0
    ? (scoredEvals.reduce((s, e) => s + e.total_score, 0) / scoredEvals.length).toFixed(1)
    : '—';
  const shortlisted = pipeline.stages?.find(s => s.status === 'shortlisted')?.count || 0;
  const shortlistRate = totalCandidates > 0 ? Math.round((shortlisted / totalCandidates) * 100) : 0;

  const stageData = (pipeline.stages || []).filter(s => s.count > 0);
  const maxStageCount = Math.max(...stageData.map(s => s.count), 1);

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="skeleton" style={{ height: 28, width: 200, marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 16, width: 320 }} />
        </div>
        <div className="dashboard-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="dashboard-card">
              <div className="skeleton" style={{ height: 40, width: 40, borderRadius: '0.75rem', marginBottom: '1.25rem' }} />
              <div className="skeleton" style={{ height: 12, width: 80, marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 36, width: 60 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">HR Command Center</h1>
        <p className="page-subtitle">Overview of your multilingual hiring funnel and candidate pipeline.</p>
      </div>

      {/* Stat cards */}
      <div className="dashboard-grid">
        <StatCard icon={Briefcase} label="Active Roles" value={activeJobs}
          color="#818cf8" bgColor="rgba(99,102,241,0.12)" delay="0s" />
        <StatCard icon={Users} label="Total Candidates" value={totalCandidates}
          color="#60a5fa" bgColor="rgba(59,130,246,0.12)" delay="0.05s" />
        <StatCard icon={Award} label="Avg AI Score" value={avgScore} unit="/10"
          color="#34d399" bgColor="rgba(16,185,129,0.12)" delay="0.1s" />
        <StatCard icon={TrendingUp} label="Shortlist Rate" value={`${shortlistRate}%`}
          color="#a78bfa" bgColor="rgba(139,92,246,0.12)" delay="0.15s" />
      </div>

      {/* Two-panel grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 0.7fr', gap: '1.5rem', marginTop: '0.5rem' }}>

        {/* Pipeline funnel */}
        <div className="dashboard-card" style={{ animationDelay: '0.2s' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>Pipeline Stages</h3>
            <Link to="/candidates" style={{ fontSize: '0.75rem', color: 'var(--primary-light)', textDecoration: 'none', fontWeight: 600 }}>
              View all →
            </Link>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {stageData.map(({ status, count }) => {
              const pct = Math.round((count / maxStageCount) * 100);
              const c = STAGE_COLORS[status] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' };
              return (
                <div key={status}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{status}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{count}</span>
                  </div>
                  <div className="funnel-bar-bg">
                    <div className="funnel-bar-fill" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${c.color}99, ${c.color})` }}>
                      {pct > 15 && `${pct}%`}
                    </div>
                  </div>
                </div>
              );
            })}
            {stageData.length === 0 && (
              <div className="empty-state" style={{ padding: '2rem' }}>
                <p>No candidates yet. Share the candidate portal link to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Evaluation summary */}
          <div className="dashboard-card" style={{ animationDelay: '0.25s' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1rem' }}>Screening Activity</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              {[
                { label: 'Evaluations run', value: scoredEvals.length },
                { label: 'Shortlisted', value: shortlisted },
                { label: 'Open positions', value: activeJobs },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{label}</span>
                  <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tip */}
          <div className="dashboard-card" style={{ animationDelay: '0.3s', borderColor: 'rgba(99,102,241,0.2)', background: 'rgba(99,102,241,0.04)' }}>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <HelpCircle size={16} style={{ color: 'var(--primary-light)', flexShrink: 0, marginTop: '0.1rem' }} />
              <div>
                <p style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>Quick Tip</p>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Configure competency weights per job role in the <strong>Jobs</strong> tab to tune AI scoring for your team's priorities.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
