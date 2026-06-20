import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Users, Briefcase, Award, TrendingUp, HelpCircle, CheckCircle2, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend, CartesianGrid 
} from 'recharts';

const STAGE_COLORS = {
  applied:      '#60a5fa',
  screened:     '#34d399',
  shortlisted:  '#a78bfa',
  interviewing: '#fbbf24',
  offered:      '#f9a8d4',
  rejected:     '#f87171',
};

const CHART_COLORS = ['#4361ee', '#7209b7', '#06d6a0', '#4cc9f0', '#f9a8d4', '#fbbf24', '#f87171'];

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
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getPipeline(),
      api.getFunnel(),
      api.getJobs(),
      api.getEvaluations(),
      api.getDashboardCandidates(),
    ]).then(([p, f, j, e, c]) => {
      setPipeline(p);
      setFunnel(Array.isArray(f) ? f : []);
      setJobs(j);
      setEvaluations(e);
      const candidatesList = Array.isArray(c) ? c : (c?.items || []);
      setCandidates(candidatesList);
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

  // Prepare pipeline chart data
  const pipelineChartData = (pipeline.stages || []).map(s => ({
    name: s.status.charAt(0).toUpperCase() + s.status.slice(1),
    count: s.count,
    fill: STAGE_COLORS[s.status] || '#94a3b8'
  }));

  // Prepare job distribution chart data
  const jobDistributionData = jobs.map(job => {
    const count = candidates.filter(({ candidate }) => candidate.job_id === job.id).length;
    return { name: job.title, value: count };
  }).filter(item => item.value > 0);

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

      {/* Visual Analytics Row */}
      <div className="analytics-grid">
        
        {/* Pipeline Chart */}
        <div className="dashboard-card" style={{ animationDelay: '0.2s', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Recruitment Pipeline Volume</h3>
            <Link to="/candidates" style={{ fontSize: '0.78rem', color: 'var(--primary-light)', textDecoration: 'none', fontWeight: 600 }}>
              Candidates Directory →
            </Link>
          </div>
          <div style={{ flexGrow: 1, minHeight: '260px' }}>
            {totalCandidates > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={pipelineChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-card)', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff', fontWeight: 600 }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {pipelineChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', height: '260px', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No candidate data available yet.
              </div>
            )}
          </div>
        </div>

        {/* Job Distribution Donut Chart */}
        <div className="dashboard-card" style={{ animationDelay: '0.25s', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1.5rem' }}>Candidate Volume by Role</h3>
          <div style={{ flexGrow: 1, minHeight: '260px' }}>
            {jobDistributionData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={jobDistributionData}
                    cx="50%"
                    cy="48%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {jobDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-card)', borderRadius: '8px' }}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    iconType="circle"
                    formatter={(value) => <span style={{ color: 'var(--text-body)', fontSize: '0.75rem', fontWeight: 500 }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', height: '260px', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No active candidate applications.
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Two-panel Grid for Activity and Info */}
      <div className="bottom-grid">

        {/* Screening Activity Table */}
        <div className="dashboard-card" style={{ animationDelay: '0.3s' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1.25rem' }}>Screening Activity & Status</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { label: 'Completed AI Evaluations', value: scoredEvals.length, desc: 'Candidate interviews scored and ranked' },
              { label: 'Shortlisted Candidates', value: shortlisted, desc: 'Selected for final human interviews' },
              { label: 'Active Job Openings', value: activeJobs, desc: 'Job postings currently accepting applications' },
            ].map(({ label, value, desc }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-glass)', border: '1px solid var(--border-card)', padding: '1rem', borderRadius: '0.75rem' }}>
                <div>
                  <p style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>{label}</p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{desc}</p>
                </div>
                <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary-light)' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tip & Guide */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="dashboard-card" style={{ animationDelay: '0.35s', borderColor: 'rgba(99,102,241,0.2)', background: 'rgba(99,102,241,0.04)' }}>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <HelpCircle size={18} style={{ color: 'var(--primary-light)', flexShrink: 0, marginTop: '0.1rem' }} />
              <div>
                <p style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '0.35rem' }}>Hiring Command Tips</p>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-body)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
                  Assign weights (e.g. Technical Depth vs. Communication signals) to match your team's role requirements.
                </p>
                <Link to="/jobs" style={{ fontSize: '0.78rem', color: 'var(--primary-light)', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  Configure weights in Jobs →
                </Link>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
