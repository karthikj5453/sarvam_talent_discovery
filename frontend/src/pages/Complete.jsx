import React from 'react';
import { CheckCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function Complete() {
  const candidateName = sessionStorage.getItem('candidate_name') || 'Candidate';

  const handleClose = () => {
    // Clear storage
    sessionStorage.clear();
    // Redirect back to apply page
    window.location.href = '/';
  };

  return (
    <div className="app-container">
      <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', color: 'var(--success)', marginBottom: '2rem' }}>
          <CheckCircle size={40} />
        </div>

        <h1 className="title-gradient" style={{ fontSize: '2.25rem', marginBottom: '1rem' }}>
          All Done, {candidateName}!
        </h1>
        
        <p style={{ color: 'var(--text-light)', fontSize: '1.1rem', fontWeight: 500, marginBottom: '1rem' }}>
          Your screening session was submitted successfully.
        </p>
        
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6, maxWidth: '480px', margin: '0 auto 3rem auto' }}>
          Our AI recruiter is currently translating and transcribing your audio responses to evaluate key job competencies. The hiring team will be notified shortly.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button className="btn btn-primary" onClick={handleClose}>
            Back to Application Portal <ArrowRight size={18} />
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '1rem' }}>
            <ShieldCheck size={14} style={{ color: 'var(--success)' }} />
            <span>Securely processed via Sarvam AI & AWS S3</span>
          </div>
        </div>
      </div>
    </div>
  );
}
