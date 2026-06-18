import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowLeft, User, Mail, Phone, Calendar, Globe, FileText, CheckCircle, XCircle, Play, AlertTriangle } from 'lucide-react';

export default function CandidateDetails() {
  const { candidateId } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      // getCandidate returns {candidate, score} (CandidateWithScore)
      const candWithScore = await api.getCandidate(candidateId);
      setCandidate(candWithScore.candidate);
      setEvaluation(candWithScore.score || null);

      // Try to load the screening session if we have an evaluation
      if (candWithScore.score?.session_id) {
        try {
          const sessData = await api.getScreeningSession(candWithScore.score.session_id);
          setSession(sessData);
        } catch (_) {
          // Session may not exist yet
        }
      }
    } catch (err) {
      setError('Failed to load candidate profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [candidateId]);

  const handleStatusChange = async (newStatus) => {
    setStatusLoading(true);
    try {
      await api.updateCandidateStatus(candidateId, newStatus);
      // Reload candidate state
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setStatusLoading(false);
    }
  };

  if (loading) {
    return <p style={{ color: 'var(--text-secondary)' }}>Loading candidate profile details...</p>;
  }

  if (error || !candidate) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error || 'Candidate profile not found.'}</p>
        <Link to="/candidates" className="btn btn-secondary"><ArrowLeft size={16} /> Back to Directory</Link>
      </div>
    );
  }

  const scoresList = evaluation ? [
    { name: 'technical_depth', value: evaluation.technical_depth },
    { name: 'first_principles', value: evaluation.first_principles },
    { name: 'shipping_velocity', value: evaluation.shipping_velocity },
    { name: 'ownership_signals', value: evaluation.ownership_signals },
    { name: 'curiosity_depth', value: evaluation.curiosity_depth },
    { name: 'multilingual_fluency', value: evaluation.multilingual_fluency },
  ] : [];

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <Link to="/candidates" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--primary-light)', textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem', marginBottom: '1rem' }}>
          <ArrowLeft size={16} /> Back to Candidates Directory
        </Link>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#fff', marginBottom: '0.25rem' }}>{candidate.name}</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Applicant Profile Review</p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              className="btn btn-secondary" 
              style={{ color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.2)' }}
              onClick={() => handleStatusChange('rejected')}
              disabled={statusLoading || candidate.status === 'rejected'}
            >
              <XCircle size={16} /> Reject
            </button>
            <button 
              className="btn btn-primary" 
              onClick={() => handleStatusChange('shortlisted')}
              disabled={statusLoading || candidate.status === 'shortlisted'}
            >
              <CheckCircle size={16} /> Shortlist
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 0.6fr', gap: '2rem' }}>
        
        {/* Left column - Assessment metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Overall evaluation */}
          {evaluation ? (
            <div className="dashboard-card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                AI Recruiter Assessment Report
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '2rem', marginBottom: '2rem', alignItems: 'center' }}>
                <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-muted)', padding: '1.5rem', borderRadius: '0.75rem' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>OVERALL SCORE</p>
                  <h3 style={{ fontSize: '3rem', fontWeight: 800, color: evaluation.total_score >= 6.0 ? '#10b981' : 'var(--primary-light)' }}>
                    {evaluation.total_score.toFixed(1)}
                  </h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>out of 10.0</p>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>Executive HR Summary</h4>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {evaluation.hr_summary}
                  </p>
                  
                  {evaluation.hr_summary_audio_url && (
                    <div className="audio-review-card">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Play size={16} style={{ color: 'var(--primary-light)' }} />
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>Play Voice Audio Summary</span>
                        <audio src={evaluation.hr_summary_audio_url} controls style={{ height: '32px', flexGrow: 1 }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Flags Warning Box */}
              {evaluation.flags && evaluation.flags.length > 0 && (
                <div style={{ display: 'flex', gap: '0.75rem', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '1rem', borderRadius: '0.75rem', marginBottom: '2rem' }}>
                  <AlertTriangle size={20} style={{ color: 'var(--warning)', flexShrink: 0 }} />
                  <div>
                    <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '0.1rem' }}>Recruiter Attention Flags</h5>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Heuristic signals detected concerns: {evaluation.flags.map(f => f.replace('_', ' ')).join(', ')}.
                    </p>
                  </div>
                </div>
              )}

              {/* 6 Dimension Breakdown */}
              <div style={{ borderTop: '1px solid var(--border-muted)', paddingTop: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '1.25rem' }}>Competency Dimension breakdown</h4>
                
                {scoresList.map(({ name, value }) => {
                  const percent = value * 10;
                  const color = value >= 7.0 ? '#10b981' : value >= 5.0 ? '#818cf8' : '#f59e0b';
                  const justification = evaluation.justifications?.[name] || 'Rating details generated from spoken answers.';
                  
                  return (
                    <div key={name} style={{ marginBottom: '1.5rem' }}>
                      <div className="score-bar-container">
                        <span className="score-label">{name.replace('_', ' ')}</span>
                        <div className="score-bar-bg">
                          <div className="score-bar-fill" style={{ width: `${percent}%`, background: color }}></div>
                        </div>
                        <span className="score-value" style={{ color }}>{value.toFixed(1)}</span>
                      </div>
                      <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', paddingLeft: '160px', marginTop: '-0.5rem' }}>
                        {justification}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="dashboard-card" style={{ textAlign: 'center', padding: '3rem' }}>
              <p style={{ color: 'var(--text-muted)' }}>Candidate has not completed screening assessment yet.</p>
            </div>
          )}

          {/* Transcripts review */}
          {session && (
            <div className="dashboard-card">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '1.5rem' }}>Interview Transcripts Review</h3>
              
              {/* Introduction Audio */}
              <div style={{ marginBottom: '2rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '0.5rem' }}>Voice Introduction</h4>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-muted)', padding: '1rem', borderRadius: '0.5rem', lineHeight: 1.5 }}>
                  {session.intro_transcript || 'No transcript recorded.'}
                </p>
              </div>

              {/* Follow-up Questions and Answers */}
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '1rem' }}>Spoken Q&A Assessment</h4>
                
                {session.followup_questions?.map((q, idx) => {
                  const answer = session.followup_answers?.[idx] || {};
                  // q may be a string (new format) or an object with .question (old format)
                  const questionText = typeof q === 'string' ? q : q?.question || `Question ${idx + 1}`;
                  return (
                    <div key={idx} style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--border-muted)', paddingLeft: '1rem' }}>
                      <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                        Question {idx + 1}: {questionText}
                      </p>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', background: 'rgba(255,255,255,0.01)', padding: '0.75rem', borderRadius: '0.5rem', lineHeight: 1.5 }}>
                        {answer.transcript || 'Waiting for candidate audio answer...'}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>

        {/* Right column - Metadata info cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="dashboard-card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-muted)', paddingBottom: '0.5rem' }}>
              Candidate Metadata
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <User size={16} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FULL NAME</p>
                  <p style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fff' }}>{candidate.name}</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <Mail size={16} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>EMAIL ADDRESS</p>
                  <p style={{ fontSize: '0.9rem', color: '#fff' }}>{candidate.email}</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <Phone size={16} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PHONE NUMBER</p>
                  <p style={{ fontSize: '0.9rem', color: '#fff' }}>{candidate.phone || 'N/A'}</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <Globe size={16} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DETECTED LANGUAGE</p>
                  <p style={{ fontSize: '0.9rem', color: '#fff', textTransform: 'uppercase' }}>{candidate.detected_language || 'N/A'}</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <Calendar size={16} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>APPLIED DATE</p>
                  <p style={{ fontSize: '0.9rem', color: '#fff' }}>{new Date(candidate.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Resume PDF */}
          <div className="dashboard-card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem', borderBottom: '1px solid var(--border-muted)', paddingBottom: '0.5rem' }}>
              Resume Attachment
            </h3>
            {candidate.resume_url ? (
              <a 
                href={candidate.resume_url} 
                target="_blank" 
                rel="noreferrer"
                className="btn btn-secondary" 
                style={{ width: '100%', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}
              >
                <FileText size={16} /> Open PDF Resume
              </a>
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center' }}>No resume uploaded.</p>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
