import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Mic, Square, RotateCcw, ChevronRight, Volume2, CheckCircle, AlertCircle, Code } from 'lucide-react';
import Editor from '@monaco-editor/react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const FALLBACK_QUESTIONS = [
  'Describe a challenging technical problem you solved recently.',
  'How do you handle deadline pressure when shipping fast?',
  'What is your approach to learning a completely new technology?',
];

const STEPS = ['Apply', 'Intro', 'Interview', 'Done'];
const WAVEFORM_BARS = 12;

export default function Interview() {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // New State for Sandbox & Avatar
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [isEngineering, setIsEngineering] = useState(false);
  const [code, setCode] = useState('// Write your solution here...\n');

  // Proctoring State
  const [tabSwitches, setTabSwitches] = useState(0);
  const [pasteEvents, setPasteEvents] = useState(0);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const navigate = useNavigate();

  const sessionId = sessionStorage.getItem('screening_session_id');

  useEffect(() => {
    if (!sessionId) { navigate('/'); return; }

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitches(prev => prev + 1);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Fetch session details to load interview questions
    fetch(`${BASE_URL}/screening/${sessionId}`)
      .then(r => r.json())
      .then(data => {
        const qs = data.followup_questions?.length
          ? data.followup_questions.map(q => typeof q === 'string' ? q : q?.question || q)
          : FALLBACK_QUESTIONS;
        setQuestions(qs);
      })
      .catch(() => setQuestions(FALLBACK_QUESTIONS));

    // Fetch associated job details to determine if sandbox is needed (engineering role)
    fetch(`${BASE_URL}/screening/${sessionId}/job`)
      .then(res => res.json())
      .then(job => {
        if (job && job.title) {
          const titleLower = job.title.toLowerCase();
          if (titleLower.includes('engineer') || titleLower.includes('developer') || titleLower.includes('architect')) {
            setIsEngineering(true);
          }
        }
      })
      .catch(e => console.error('Failed to load job details for session:', e));

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [sessionId, navigate]);

  const speakQuestion = () => {
    if (!questions[currentIndex]) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(questions[currentIndex]);
    u.lang = 'en-IN';
    
    u.onstart = () => setIsAiSpeaking(true);
    u.onend = () => setIsAiSpeaking(false);
    u.onerror = () => setIsAiSpeaking(false);
    
    window.speechSynthesis.speak(u);
  };

  const startRecording = async () => {
    setError(null);
    audioChunksRef.current = [];
    window.speechSynthesis.cancel(); // stop AI if talking
    setIsAiSpeaking(false);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(t => t.stop());
      };
      mediaRecorderRef.current.start();
      setRecording(true);
    } catch {
      setError('Microphone access denied. Please allow mic access and try again.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleReset = () => { setAudioUrl(null); setAudioBlob(null); setError(null); };

  const handleSubmit = async () => {
    if (!audioBlob) return;
    setLoading(true);
    setError(null);
    try {
      // Send code along with transcript if we are using the sandbox
      // (This could be attached to the transcript later, but we upload standard answer first)
      await api.uploadAnswer(sessionId, currentIndex, audioBlob);
      setAudioUrl(null);
      setAudioBlob(null);

      if (currentIndex + 1 < questions.length) {
        setCurrentIndex(prev => prev + 1);
        setCode('// Next question code sandbox...\n');
      } else {
        await api.completeScreening(sessionId, { tab_switches: tabSwitches, paste_events: pasteEvents });
        navigate('/complete');
      }
    } catch (err) {
      setError(err.message || 'Failed to submit answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (questions.length === 0) {
    return (
      <div className="app-container" style={{ textAlign: 'center' }}>
        <div className="glass-card" style={{ padding: '4rem 2rem' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem', width: 32, height: 32 }} />
          <p style={{ color: 'var(--text-muted)' }}>Loading interview questions...</p>
        </div>
      </div>
    );
  }

  const isLast = currentIndex + 1 >= questions.length;

  return (
    <div className="app-container" style={{ maxWidth: isEngineering ? '1200px' : '560px' }}>
      <div className="progress-steps" style={{ marginBottom: '2rem' }}>
        {STEPS.map((s, i) => (
          <div key={s} className="step-item">
            <div className={`step-dot ${i === 2 ? 'active' : i < 2 ? 'done' : ''}`}>{i < 2 ? '✓' : i + 1}</div>
            {i < STEPS.length - 1 && <div className={`step-line ${i < 2 ? 'done' : ''}`} />}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        
        {/* Left Side: Interview Controls */}
        <div className="glass-card" style={{ flex: '1 1 500px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--primary-light)' }}>
              AI Interview
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              {currentIndex + 1} / {questions.length}
            </span>
          </div>

          <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, marginBottom: '1.75rem', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${((currentIndex) / questions.length) * 100}%`,
              background: 'linear-gradient(90deg, var(--primary), var(--accent))',
              borderRadius: 2,
              transition: 'width 0.5s ease'
            }} />
          </div>

          <div className="question-card">
            <div className="question-number">Question {currentIndex + 1}</div>
            <p className="question-text">{questions[currentIndex]}</p>
            <button className="speak-btn" onClick={speakQuestion} title="Read question aloud">
              <Volume2 size={15} />
            </button>
          </div>

          {error && (
            <div className="alert alert-error">
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              {error}
            </div>
          )}

          {/* AI Avatar OR Recording UI */}
          <div className="recording-area" style={{ padding: '1.5rem 0' }}>
            
            {isAiSpeaking ? (
              <div className="ai-avatar-container" style={{ textAlign: 'center', marginBottom: '1rem' }}>
                <div className="ai-avatar pulse" style={{
                  width: '100px', height: '100px', margin: '0 auto', borderRadius: '50%',
                  background: 'radial-gradient(circle, var(--primary-light) 0%, var(--primary) 60%, var(--accent) 100%)',
                  boxShadow: '0 0 30px var(--primary-glow)',
                  animation: 'avatarPulse 1s ease-in-out infinite alternate'
                }}></div>
                <p style={{ marginTop: '1rem', color: 'var(--primary-light)', fontSize: '0.85rem' }}>AI is speaking...</p>
              </div>
            ) : (
              <>
                {recording && (
                  <div className="waveform">
                    {Array.from({ length: WAVEFORM_BARS }).map((_, i) => (
                      <div key={i} className="waveform-bar" />
                    ))}
                  </div>
                )}

                {!audioUrl ? (
                  <>
                    <button
                      className={`record-btn ${recording ? 'recording' : 'idle'}`}
                      onClick={recording ? stopRecording : startRecording}
                      aria-label={recording ? 'Stop recording' : 'Start recording'}
                    >
                      {recording ? <Square size={26} color="#fff" /> : <Mic size={26} color="#fff" />}
                    </button>
                    <p className={`record-status ${recording ? 'live' : ''}`}>
                      {recording ? 'Recording… click to stop' : 'Click mic to answer'}
                    </p>
                  </>
                ) : (
                  <div className="audio-preview" style={{ width: '100%' }}>
                    <div className="audio-preview-label"><CheckCircle size={14} /> Answer recorded</div>
                    <audio src={audioUrl} controls />
                  </div>
                )}
              </>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '0.875rem', marginTop: '0.5rem' }}>
            {audioUrl && (
              <button className="btn btn-ghost" onClick={handleReset} disabled={loading} style={{ flexShrink: 0, width: 'auto', padding: '0.9rem 1.25rem' }}>
                <RotateCcw size={16} /> Redo
              </button>
            )}
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={!audioUrl || loading || isAiSpeaking}
            >
              {loading
                ? <><span className="spinner" /> Submitting...</>
                : isLast
                ? <>Complete Screening <CheckCircle size={16} /></>
                : <>Next Question <ChevronRight size={16} /></>
              }
            </button>
          </div>
        </div>

        {/* Right Side: Monaco Code Editor Sandbox (Engineering Only) */}
        {isEngineering && (
          <div className="glass-card" style={{ flex: '1 1 500px', display: 'flex', flexDirection: 'column' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
               <Code size={18} color="var(--primary-light)" />
               <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)' }}>Technical Sandbox</span>
             </div>
             <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
               You can use this editor to write code while answering. The AI is observing your approach.
             </p>
             <div 
               style={{ flex: 1, minHeight: '400px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-card)' }}
               onPasteCapture={(e) => {
                 const pastedData = e.clipboardData.getData('Text');
                 if (pastedData && pastedData.length > 20) {
                   setPasteEvents(prev => prev + 1);
                 }
               }}
             >
                <Editor
                  height="100%"
                  defaultLanguage="javascript"
                  theme="vs-dark"
                  value={code}
                  onChange={(val) => setCode(val)}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    padding: { top: 16 }
                  }}
                />
             </div>
          </div>
        )}
      </div>
      
      {/* Dynamic Avatar Animation */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes avatarPulse {
          0% { transform: scale(0.95); box-shadow: 0 0 20px rgba(67, 97, 238, 0.4); }
          100% { transform: scale(1.05); box-shadow: 0 0 50px rgba(67, 97, 238, 0.8); }
        }
      `}} />
    </div>
  );
}
