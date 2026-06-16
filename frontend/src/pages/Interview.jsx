import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Mic, Square, RotateCcw, ArrowRight, Volume2, CheckCircle2, AlertCircle } from 'lucide-react';

const FALLBACK_QUESTIONS = [
  { question: "Describe a challenging technical problem you solved recently." },
  { question: "How do you handle deadline pressure and shipping fast?" },
  { question: "What is your approach to learning new technologies?" }
];

export default function Interview() {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const navigate = useNavigate();

  const sessionId = sessionStorage.getItem('screening_session_id');

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    async function loadSession() {
      try {
        const session = await api.getScreeningSession(sessionId); // Note: we should add this helper or fetch directly
        const qList = session.followup_questions && session.followup_questions.length > 0 
          ? session.followup_questions 
          : FALLBACK_QUESTIONS;
        setQuestions(qList);
      } catch (_) {
        setQuestions(FALLBACK_QUESTIONS);
      }
    }
    
    // Fetch session details directly
    fetch(`http://localhost:8000/screening/${sessionId}`)
      .then(res => res.json())
      .then(data => {
        const qList = data.followup_questions && data.followup_questions.length > 0 
          ? data.followup_questions 
          : FALLBACK_QUESTIONS;
        setQuestions(qList);
      })
      .catch(() => {
        setQuestions(FALLBACK_QUESTIONS);
      });
  }, [sessionId, navigate]);

  const speakQuestion = () => {
    if (questions.length === 0) return;
    const utterance = new SpeechSynthesisUtterance(questions[currentIndex].question);
    utterance.lang = 'en-IN'; // Indian English accent
    window.speechSynthesis.speak(utterance);
  };

  const startRecording = async () => {
    setError(null);
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      setError('Could not access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleReset = () => {
    setAudioUrl(null);
    setAudioBlob(null);
    setError(null);
  };

  const handleSubmitAnswer = async () => {
    if (!audioBlob) return;
    setLoading(true);
    setError(null);

    try {
      // 1. Upload the answer audio to S3 + trigger transcription
      await api.uploadAnswer(sessionId, currentIndex, audioBlob);
      
      // Reset recording state
      setAudioUrl(null);
      setAudioBlob(null);

      if (currentIndex + 1 < questions.length) {
        // Move to next question
        setCurrentIndex(prev => prev + 1);
      } else {
        // 2. All questions answered! Mark screening complete
        await api.completeScreening(sessionId);
        navigate('/complete');
      }
    } catch (err) {
      setError(err.message || 'Failed to upload answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (questions.length === 0) {
    return (
      <div className="app-container">
        <div className="glass-card" style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--text-muted)' }}>Loading interview questions...</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex].question;

  return (
    <div className="app-container">
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '1rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Screen Q&A</span>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Question <strong>{currentIndex + 1}</strong> of {questions.length}
          </span>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '1rem', padding: '1.75rem', marginBottom: '2.5rem', position: 'relative' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.5, color: '#fff', paddingRight: '2.5rem' }}>
            {currentQuestion}
          </h2>
          <button 
            onClick={speakQuestion}
            style={{ position: 'absolute', right: '1.25rem', top: '1.5rem', background: 'rgba(99, 102, 241, 0.1)', border: 'none', width: '36px', height: '36px', borderRadius: '50%', display: 'flex', alignItems: 'center', justify: 'center', cursor: 'pointer', transition: 'all 0.2s' }}
            title="Read question aloud"
          >
            <Volume2 size={16} style={{ color: 'var(--primary)' }} />
          </button>
        </div>

        {error && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', padding: '1rem', borderRadius: '0.75rem', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.9rem' }}>{error}</span>
          </div>
        )}

        <div className="recording-container" style={{ margin: '1.5rem 0' }}>
          {recording && (
            <div className="waveform">
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
              <div className="waveform-bar"></div>
            </div>
          )}

          {!audioUrl ? (
            <button 
              className={`record-btn-glow ${recording ? 'recording' : ''}`}
              onClick={recording ? stopRecording : startRecording}
            >
              {recording ? <Square size={32} color="#fff" /> : <Mic size={32} color="#fff" />}
            </button>
          ) : (
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
              <p style={{ color: 'var(--success)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckCircle2 size={16} /> Answer recorded successfully
              </p>
              <audio src={audioUrl} controls style={{ width: '100%', maxWidth: '300px' }} />
            </div>
          )}

          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            {recording ? 'Recording answer...' : audioUrl ? 'Listen to your response' : 'Click mic to record your response'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '3rem' }}>
          {audioUrl && (
            <button className="btn" onClick={handleReset} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff' }} disabled={loading}>
              <RotateCcw size={18} /> Record Again
            </button>
          )}
          
          <button 
            className="btn btn-primary"
            onClick={handleSubmitAnswer}
            disabled={!audioBlob || loading}
          >
            {loading ? 'Submitting...' : currentIndex + 1 < questions.length ? 'Next Question' : 'Complete Screening'}
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
