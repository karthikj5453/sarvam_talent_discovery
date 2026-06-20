import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, User, Mail, Phone, Calendar, Globe, FileText, CheckCircle, XCircle, Play, AlertTriangle, Download, Trash2 } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const PIPELINE_STAGES = [
  { key: 'applied', label: 'Applied' },
  { key: 'screened', label: 'Screened' },
  { key: 'shortlisted', label: 'Shortlisted' },
  { key: 'interviewing', label: 'Interviewing' },
  { key: 'offered', label: 'Offered' },
  { key: 'rejected', label: 'Rejected' },
];

export default function CandidateDetails() {
  const { candidateId } = useParams();
  const { isHrOrAdmin } = useAuth();
  const [candidate, setCandidate] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [session, setSession] = useState(null);
  const [notes, setNotes] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const navigate = useNavigate();

  const dossierRef = useRef(null);

  const loadData = async () => {
    try {
      const candWithScore = await api.getCandidate(candidateId);
      setCandidate(candWithScore.candidate);
      setEvaluation(candWithScore.score || null);

      const sessions = await api.getCandidateSessions(candidateId).catch(() => []);
      const latestSession = sessions?.[0];
      if (latestSession) {
        setSession(latestSession);
      } else if (candWithScore.score?.session_id) {
        try {
          const sessData = await api.getScreeningSession(candWithScore.score.session_id);
          setSession(sessData);
        } catch (_) { /* optional */ }
      }

      const [notesData, timelineData] = await Promise.all([
        api.getNotes(candidateId).catch(() => []),
        api.getTimeline(candidateId).catch(() => []),
      ]);
      setNotes(notesData);
      setTimeline(timelineData);
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
    if (!isHrOrAdmin) return;
    setStatusLoading(true);
    setStatusMessage(null);
    try {
      await api.updateCandidateStatus(candidateId, newStatus);
      setStatusMessage(`Status updated to ${newStatus}.`);
      await loadData();
    } catch (err) {
      setStatusMessage(err.message || 'Failed to update status.');
    } finally {
      setStatusLoading(false);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await api.addNote(candidateId, newNote.trim());
      setNewNote('');
      const notesData = await api.getNotes(candidateId);
      setNotes(notesData);
    } catch (err) {
      setStatusMessage(err.message || 'Failed to add note.');
    }
  };

  const handleDeleteCandidate = async () => {
    if (!window.confirm("Are you sure you want to permanently delete this candidate and all their associated data (audio files, resume, scores)? This cannot be undone.")) return;
    try {
      await api.deleteCandidate(candidateId);
      navigate('/candidates');
    } catch (err) {
      alert(err.message || 'Failed to delete candidate.');
    }
  };

  const handleGeneratePdf = async () => {
    if (!dossierRef.current) return;
    setPdfGenerating(true);
    
    // Temporarily make the hidden dossier visible for capture
    const originalStyle = dossierRef.current.style.display;
    dossierRef.current.style.display = 'block';
    dossierRef.current.style.position = 'absolute';
    dossierRef.current.style.top = '-9999px';
    
    try {
      const canvas = await html2canvas(dossierRef.current, { scale: 2, useCORS: true, logging: false });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`${candidate.name.replace(/\s+/g, '_')}_Dossier.pdf`);
    } catch (e) {
      setStatusMessage('PDF generation failed. Please try again.');
    } finally {
      dossierRef.current.style.display = originalStyle;
      setPdfGenerating(false);
    }
  };

  if (loading) {
    return <p style={{ color: 'var(--text-secondary)' }}>Loading candidate profile details...</p>;
  }

  if (error || !candidate) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--error)', marginBottom: '1rem' }}>{error || 'Candidate profile not found.'}</p>
        <Link to="/candidates" className="btn btn-secondary"><ArrowLeft size={16} /> Back to Directory</Link>
      </div>
    );
  }

  const scoresList = evaluation ? [
    { name: 'Technical Depth', value: evaluation.technical_depth },
    { name: 'First Principles', value: evaluation.first_principles },
    { name: 'Shipping Velocity', value: evaluation.shipping_velocity },
    { name: 'Ownership Signals', value: evaluation.ownership_signals },
    { name: 'Curiosity Depth', value: evaluation.curiosity_depth },
    { name: 'Multilingual Fluency', value: evaluation.multilingual_fluency },
    { name: 'Emotional Intelligence', value: evaluation.eq_score || 0 },
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
            <p style={{ color: 'var(--text-muted)' }}>Applicant Profile Review</p>
          </div>

          <div className="action-buttons-row" style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
             {evaluation && (
              <button 
                className="btn btn-secondary" 
                onClick={handleGeneratePdf}
                disabled={pdfGenerating}
              >
                <Download size={16} /> {pdfGenerating ? 'Generating...' : 'Export Dossier'}
              </button>
             )}
            {isHrOrAdmin && (
              <button 
                className="btn btn-secondary" 
                style={{ color: 'var(--error)', borderColor: 'rgba(239, 71, 111, 0.2)' }}
                onClick={handleDeleteCandidate}
                title="Permanently Delete Candidate"
              >
                <Trash2 size={16} /> Delete
              </button>
            )}
            {isHrOrAdmin && (
              <>
                <button 
                  className="btn btn-secondary" 
                  style={{ color: 'var(--error)', borderColor: 'rgba(239, 71, 111, 0.2)' }}
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
              </>
            )}
          </div>
        </div>
        {statusMessage && (
          <div className="alert alert-info" style={{ marginTop: '1rem' }}>{statusMessage}</div>
        )}

        {/* Pipeline stage selector */}
        {isHrOrAdmin && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
            {PIPELINE_STAGES.map(stage => (
              <button
                key={stage.key}
                className={`btn ${candidate.status === stage.key ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem', width: 'auto' }}
                disabled={statusLoading || candidate.status === stage.key}
                onClick={() => handleStatusChange(stage.key)}
              >
                {stage.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="details-grid">
        
        {/* Left column - Assessment metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {evaluation ? (
            <div className="dashboard-card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                AI Recruiter Assessment Report
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '2rem', marginBottom: '2rem', alignItems: 'center' }}>
                <div style={{ textAlign: 'center', background: 'var(--bg-glass)', border: '1px solid var(--border-card)', padding: '1.5rem', borderRadius: '0.75rem' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>OVERALL SCORE</p>
                  <h3 style={{ fontSize: '3rem', fontWeight: 800, color: evaluation.total_score >= 6.0 ? 'var(--success)' : 'var(--primary-light)' }}>
                    {evaluation.total_score.toFixed(1)}
                  </h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>out of 10.0</p>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>Executive HR Summary</h4>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                    {evaluation.hr_summary}
                  </p>
                  
                  {evaluation.hr_summary_audio_url && (
                    <div style={{ marginTop: '1rem', background: 'var(--bg-glass)', border: '1px solid var(--border-card)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Play size={16} style={{ color: 'var(--primary-light)' }} />
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-light)' }}>Play Voice Audio Summary</span>
                        <audio src={evaluation.hr_summary_audio_url} controls style={{ height: '32px', flexGrow: 1 }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Flags Warning Box */}
              {evaluation.flags && evaluation.flags.length > 0 && (
                <div style={{ display: 'flex', gap: '0.75rem', background: 'rgba(252, 163, 17, 0.1)', border: '1px solid rgba(252, 163, 17, 0.2)', padding: '1rem', borderRadius: '0.75rem', marginBottom: '2rem' }}>
                  <AlertTriangle size={20} style={{ color: 'var(--warning)', flexShrink: 0 }} />
                  <div>
                    <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '0.1rem' }}>Recruiter Attention Flags</h5>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-body)' }}>
                      Heuristic signals detected concerns: {evaluation.flags.map(f => f.replace('_', ' ')).join(', ')}.
                    </p>
                  </div>
                </div>
              )}

              {/* Proctoring Warning Box */}
              {session?.proctoring_flags && (session.proctoring_flags.tab_switches > 0 || session.proctoring_flags.paste_events > 0) && (
                <div style={{ display: 'flex', gap: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '1rem', borderRadius: '0.75rem', marginBottom: '2rem' }}>
                  <AlertTriangle size={20} style={{ color: 'var(--error)', flexShrink: 0 }} />
                  <div>
                    <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '0.1rem' }}>Proctoring Alerts Detected</h5>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-body)' }}>
                      Candidate left the interview tab {session.proctoring_flags.tab_switches} times and triggered {session.proctoring_flags.paste_events} paste warnings.
                    </p>
                  </div>
                </div>
              )}

              {/* Radar Chart */}
              <div style={{ borderTop: '1px solid var(--border-card)', paddingTop: '1.5rem', marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '1.25rem' }}>Competency Dimension Radar</h4>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer>
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={scoresList}>
                      <PolarGrid stroke="rgba(255,255,255,0.1)" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: 'var(--text-muted)' }} />
                      <Radar name={candidate.name} dataKey="value" stroke="var(--primary)" fill="var(--primary-glow)" fillOpacity={0.6} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
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
              
              <div style={{ marginBottom: '2rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '0.5rem' }}>Voice Introduction</h4>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-light)', background: 'var(--bg-glass)', border: '1px solid var(--border-card)', padding: '1rem', borderRadius: '0.5rem', lineHeight: 1.5 }}>
                  {session.intro_transcript || 'No transcript recorded.'}
                </p>
                {session.intro_audio_url && (
                  <audio src={session.intro_audio_url} controls style={{ width: '100%', marginTop: '0.5rem', height: 36 }} />
                )}
              </div>

              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '1rem' }}>Spoken Q&A Assessment</h4>
                {session.followup_questions?.map((q, idx) => {
                  const answer = session.followup_answers?.[idx] || {};
                  const questionText = typeof q === 'string' ? q : q?.question || `Question ${idx + 1}`;
                  return (
                    <div key={idx} style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--border-card)', paddingLeft: '1rem' }}>
                      <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                        Question {idx + 1}: {questionText}
                      </p>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-light)', background: 'var(--bg-glass)', padding: '0.75rem', borderRadius: '0.5rem', lineHeight: 1.5 }}>
                        {answer.transcript || 'Waiting for candidate audio answer...'}
                      </p>
                      {answer.answer_audio_url && (
                        <audio src={answer.answer_audio_url} controls style={{ width: '100%', marginTop: '0.5rem', height: 32 }} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="dashboard-card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-card)', paddingBottom: '0.5rem' }}>
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

              {candidate.github_url && (
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <Globe size={16} style={{ color: 'var(--text-muted)' }} />
                  <div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>GITHUB</p>
                    <a href={candidate.github_url} target="_blank" rel="noreferrer" style={{ fontSize: '0.9rem', color: 'var(--primary-light)' }}>
                      {candidate.github_url.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <CheckCircle size={16} style={{ color: candidate.consent_given ? 'var(--success)' : 'var(--text-muted)' }} />
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DATA CONSENT</p>
                  <p style={{ fontSize: '0.9rem', color: '#fff' }}>{candidate.consent_given ? 'Given' : 'Not recorded'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recruiter Notes */}
          <div className="dashboard-card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' }}>Recruiter Notes</h3>
            <form onSubmit={handleAddNote} style={{ marginBottom: '1rem' }}>
              <textarea
                className="form-input"
                rows={3}
                placeholder="Add a note about this candidate..."
                value={newNote}
                onChange={e => setNewNote(e.target.value)}
                style={{ width: '100%', marginBottom: '0.5rem', resize: 'vertical' }}
              />
              <button type="submit" className="btn btn-secondary" style={{ width: 'auto', padding: '0.5rem 1rem' }} disabled={!newNote.trim()}>
                Add Note
              </button>
            </form>
            {notes.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No notes yet.</p>
            ) : (
              notes.map(note => (
                <div key={note.id} style={{ padding: '0.75rem', background: 'var(--bg-glass)', borderRadius: '0.5rem', marginBottom: '0.5rem', border: '1px solid var(--border-card)' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-light)', lineHeight: 1.5 }}>{note.content}</p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                    {note.author_name} · {new Date(note.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Activity Timeline */}
          {timeline.length > 0 && (
            <div className="dashboard-card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' }}>Activity Timeline</h3>
              {timeline.slice(0, 8).map(item => (
                <div key={item.id} style={{ paddingLeft: '1rem', borderLeft: '2px solid var(--border-card)', marginBottom: '0.75rem' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-light)' }}>
                    <strong>{item.actor_name}</strong> — {item.action.replace(/_/g, ' ')}
                  </p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}

          <div className="dashboard-card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem', borderBottom: '1px solid var(--border-card)', paddingBottom: '0.5rem' }}>
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

          {candidate.resume_parsed_data && (
            <div className="dashboard-card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', marginBottom: '1rem', borderBottom: '1px solid var(--border-card)', paddingBottom: '0.5rem' }}>
                AI Extracted Resume Data
              </h3>
              
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Summary</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>{candidate.resume_parsed_data.summary || 'N/A'}</p>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Skills</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                  {(candidate.resume_parsed_data.skills || []).map((s, i) => (
                    <span key={i} className="badge badge-primary" style={{ fontSize: '0.7rem' }}>{s}</span>
                  ))}
                  {(!candidate.resume_parsed_data.skills || candidate.resume_parsed_data.skills.length === 0) && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>N/A</span>
                  )}
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Experience</h4>
                {(candidate.resume_parsed_data.experience || []).map((exp, idx) => (
                  <div key={idx} style={{ marginBottom: '0.75rem' }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>{exp.title} <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>at {exp.company}</span></p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{exp.duration}</p>
                  </div>
                ))}
                {(!candidate.resume_parsed_data.experience || candidate.resume_parsed_data.experience.length === 0) && (
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>N/A</span>
                )}
              </div>

              <div>
                <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>Education</h4>
                {(candidate.resume_parsed_data.education || []).map((edu, idx) => (
                  <div key={idx} style={{ marginBottom: '0.5rem' }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>{edu.degree}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{edu.institution} ({edu.year})</p>
                  </div>
                ))}
                {(!candidate.resume_parsed_data.education || candidate.resume_parsed_data.education.length === 0) && (
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>N/A</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Hidden Dossier for PDF Generation */}
      {evaluation && (
        <div 
          ref={dossierRef} 
          style={{ 
            display: 'none', 
            width: '800px', 
            background: '#ffffff', 
            color: '#111827', 
            padding: '40px',
            fontFamily: 'Inter, sans-serif' 
          }}
        >
          <div style={{ borderBottom: '2px solid #4361ee', paddingBottom: '1rem', marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '28px', color: '#111827', margin: 0 }}>Candidate Dossier: {candidate.name}</h1>
            <p style={{ fontSize: '14px', color: '#6b7280', margin: '4px 0 0 0' }}>Generated by Sarvam AI Talent Platform</p>
          </div>
          
          <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
             <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '16px', color: '#374151', textTransform: 'uppercase', marginBottom: '1rem' }}>Executive Summary</h3>
                <p style={{ fontSize: '14px', lineHeight: 1.6, color: '#4b5563' }}>{evaluation.hr_summary}</p>
             </div>
             <div style={{ flex: '0 0 250px', background: '#f3f4f6', padding: '1.5rem', borderRadius: '8px' }}>
                <p style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', margin: 0 }}>Overall Score</p>
                <h2 style={{ fontSize: '48px', color: '#4361ee', margin: '8px 0' }}>{evaluation.total_score.toFixed(1)}<span style={{fontSize: '20px', color: '#9ca3af'}}>/10</span></h2>
             </div>
          </div>
          
          {/* Radar Chart For PDF Capture */}
          <div style={{ marginBottom: '2rem' }}>
             <h3 style={{ fontSize: '16px', color: '#374151', textTransform: 'uppercase', marginBottom: '1rem' }}>Competency Radar</h3>
             <div style={{ width: '100%', height: '400px', background: '#f9fafb', borderRadius: '8px', padding: '1rem' }}>
                 <ResponsiveContainer>
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={scoresList}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: '#4b5563', fontSize: 12 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: '#9ca3af' }} />
                      <Radar name={candidate.name} dataKey="value" stroke="#4361ee" fill="#4361ee" fillOpacity={0.6} />
                    </RadarChart>
                  </ResponsiveContainer>
             </div>
          </div>
          
          {/* Transcript Snippets */}
          {session && session.followup_questions?.length > 0 && (
             <div>
               <h3 style={{ fontSize: '16px', color: '#374151', textTransform: 'uppercase', marginBottom: '1rem' }}>Interview Excerpts</h3>
               {session.followup_questions.map((q, idx) => {
                  const answer = session.followup_answers?.[idx] || {};
                  const questionText = typeof q === 'string' ? q : q?.question || `Question ${idx + 1}`;
                  return (
                    <div key={idx} style={{ marginBottom: '1.5rem', borderLeft: '3px solid #e5e7eb', paddingLeft: '1rem' }}>
                      <p style={{ fontSize: '14px', fontWeight: 700, color: '#374151', margin: '0 0 8px 0' }}>Q: {questionText}</p>
                      <p style={{ fontSize: '13px', color: '#4b5563', margin: 0, fontStyle: 'italic' }}>
                        A: "{answer.transcript || 'No answer recorded.'}"
                      </p>
                    </div>
                  );
               })}
             </div>
          )}
        </div>
      )}
    </div>
  );
}
