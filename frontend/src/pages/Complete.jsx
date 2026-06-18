import React, { useEffect } from 'react';
import { CheckCircle, Sparkles, ShieldCheck, Clock, Brain } from 'lucide-react';

const STEPS = ['Apply', 'Intro', 'Interview', 'Done'];

export default function Complete() {
  const candidateName = sessionStorage.getItem('candidate_name') || 'there';

  useEffect(() => {
    sessionStorage.clear();
  }, []);

  return (
    <div className="app-container">
      {/* Steps — all done */}
      <div className="progress-steps" style={{ marginBottom: '2rem' }}>
        {STEPS.map((s, i) => (
          <div key={s} className="step-item">
            <div className={`step-dot done`}>✓</div>
            {i < STEPS.length - 1 && <div className="step-line done" />}
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 2.5rem' }}>

        {/* Success icon */}
        <div className="success-ring">
          <CheckCircle size={42} style={{ color: 'var(--success)' }} />
        </div>

        <h1 className="title-gradient" style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>
          You're All Done, {candidateName}!
        </h1>

        <p style={{ color: 'var(--text-body)', fontSize: '0.95rem', lineHeight: 1.6, maxWidth: '420px', margin: '0 auto 2rem' }}>
          Your screening responses have been securely submitted. Our AI system is now evaluating your competencies across 6 dimensions.
        </p>

        {/* What happens next chips */}
        <div className="info-chips">
          <div className="info-chip">
            <Brain size={14} style={{ color: 'var(--primary-light)' }} />
            AI evaluation in progress
          </div>
          <div className="info-chip">
            <Clock size={14} style={{ color: '#fbbf24' }} />
            Results in 2–5 minutes
          </div>
          <div className="info-chip">
            <ShieldCheck size={14} style={{ color: 'var(--success)' }} />
            Sarvam AI · Encrypted
          </div>
        </div>

        {/* CTA */}
        <button
          className="btn btn-primary"
          style={{ marginTop: '2rem', maxWidth: '300px', margin: '2rem auto 0' }}
          onClick={() => { window.location.href = '/'; }}
        >
          <Sparkles size={16} /> Apply for Another Role
        </button>

        <p style={{ marginTop: '1.25rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          The hiring team will be in touch if you are shortlisted.
        </p>
      </div>
    </div>
  );
}
