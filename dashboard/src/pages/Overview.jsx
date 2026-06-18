import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Users, Briefcase, Award, Percent, HelpCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Overview() {
  const [pipeline, setPipeline] = useState({ total_candidates: 0, stages: [] });
  const [funnel, setFunnel] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [pipelineData, funnelData, jobList, evalList] = await Promise.all([
          api.getPipeline(),
          api.getFunnel(),
          api.getJobs(),
          api.getEvaluations(),
        ]);
        setPipeline(pipelineData);
        setFunnel(funnelData);
        setJobs(jobList);
        setEvaluations(evalList);
      } catch (err) {
        console.error('Failed to load dashboard overview data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <p style={{ color: 'var(--text-secondary)' }}>Loading overview metrics...</p>;
  }

  const totalCandidates = pipeline.total_candidates || 0;
  const activeJobs = jobs.length;

  // Average score from evaluations
  const scoredEvals = evaluations.filter(e => e.total_score != null);
  const avgScore = scoredEvals.length > 0
    ? scoredEvals.reduce((acc, e) => acc + e.total_score, 0) / scoredEvals.length
    : 0;

  // Shortlisted count from pipeline stages
  const shortlistedStage = pipeline.stages?.find(s => s.status === 'shortlisted');
  const shortlistedCount = shortlistedStage?.count || 0;
  const shortlistRate = totalCandidates > 0
    ? Math.round((shortlistedCount / totalCandidates) * 100)
    : 0;

  // Funnel data: backend returns [{stage, count}]
  const funnelItems = Array.isArray(funnel) ? funnel : [];
  const maxFunnelCount = Math.max(...funnelItems.map(f => f.count), 1);

  // Language distribution: derive from pipeline stages (no dedicated endpoint)
  const stageData = pipeline.stages || [];

  return (
    <div>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>HR Command Center</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2.5rem' }}>Overview of multilingual hiring funnel and candidate rankings.</p>

      {/* Stats Cards Grid */}
      <div className="dashboard-grid">
        <div className="dashboard-card" style={{ borderLeft: '4px solid var(--primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p className="card-title">Active Job Roles</p>
              <h2 className="card-value">{activeJobs}</h2>
            </div>
            <div style={{ background: 'var(--primary-glow)', padding: '0.75rem', borderRadius: '0.5rem', color: 'var(--primary-light)' }}>
              <Briefcase size={22} />
            </div>
          </div>
        </div>

        <div className="dashboard-card" style={{ borderLeft: '4px solid #3b82f6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p className="card-title">Total Candidates</p>
              <h2 className="card-value">{totalCandidates}</h2>
            </div>
            <div style={{ background: 'rgba(59, 130, 246, 0.12)', padding: '0.75rem', borderRadius: '0.5rem', color: '#60a5fa' }}>
              <Users size={22} />
            </div>
          </div>
        </div>

        <div className="dashboard-card" style={{ borderLeft: '4px solid var(--success)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p className="card-title">Avg Competency Score</p>
              <h2 className="card-value">{avgScore.toFixed(1)}<span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/10</span></h2>
            </div>
            <div style={{ background: 'rgba(16, 185, 129, 0.12)', padding: '0.75rem', borderRadius: '0.5rem', color: '#34d399' }}>
              <Award size={22} />
            </div>
          </div>
        </div>

        <div className="dashboard-card" style={{ borderLeft: '4px solid var(--accent)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p className="card-title">Shortlist Rate</p>
              <h2 className="card-value">{shortlistRate}%</h2>
            </div>
            <div style={{ background: 'rgba(139, 92, 246, 0.12)', padding: '0.75rem', borderRadius: '0.5rem', color: '#a78bfa' }}>
              <Percent size={22} />
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', marginTop: '2rem' }}>

        {/* Hiring Pipeline Funnel */}
        <div className="dashboard-card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.5rem' }}>Hiring Pipeline Funnel</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {funnelItems.map(({ stage, count }) => {
              const percentage = Math.round((count / maxFunnelCount) * 100);
              return (
                <div key={stage} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ textTransform: 'capitalize', fontWeight: 600, color: 'var(--text-primary)' }}>{stage}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{count} candidates ({percentage}%)</span>
                  </div>
                  <div style={{ height: '24px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${percentage}%`, background: `linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%)`, borderRadius: '4px', transition: 'width 0.6s' }}></div>
                  </div>
                </div>
              );
            })}
            {funnelItems.length === 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No candidates in pipeline yet.</p>
            )}
          </div>
        </div>

        {/* Pipeline Stage Distribution */}
        <div className="dashboard-card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.5rem' }}>Pipeline Stage Breakdown</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {stageData.filter(s => s.count > 0).map(({ status, count }) => {
              const pct = totalCandidates > 0 ? Math.round((count / totalCandidates) * 100) : 0;
              const color = status === 'shortlisted' ? '#10b981'
                : status === 'screened' ? '#818cf8'
                : status === 'offered' ? '#f59e0b'
                : status === 'rejected' ? '#ef4444'
                : 'var(--primary-light)';
              return (
                <div key={status} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{status}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{count} ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '4px', transition: 'width 0.6s' }}></div>
                  </div>
                </div>
              );
            })}
            {stageData.every(s => s.count === 0) && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No candidates yet.</p>
            )}
          </div>
        </div>

      </div>

      {/* Prompt Guide / Alert Callout */}
      <div className="dashboard-card" style={{ marginTop: '2.5rem', background: 'rgba(99,102,241,0.03)', border: '1px dashed rgba(99,102,241,0.25)', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div style={{ background: 'var(--primary-glow)', padding: '0.5rem', borderRadius: '50%', color: 'var(--primary-light)' }}>
          <HelpCircle size={18} />
        </div>
        <div>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>HR Tip: Customize Competency Weights</h4>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
            Go to the <strong>Jobs</strong> tab to create active role profiles and configure the exact weights for your 6 competency metrics. Our Sarvam evaluator pipeline automatically calculates total candidate scores based on these preferences!
          </p>
        </div>
      </div>
    </div>
  );
}
