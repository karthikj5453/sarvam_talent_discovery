import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Mic, Square, RotateCcw, Send, AlertCircle, Info } from 'lucide-react';

export default function Intro() {
  const [session, setSession] = useState(null);
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const navigate = useNavigate();

  const sessionId = sessionStorage.getItem('screening_session_id');
  const candidateName = sessionStorage.getItem('candidate_name') || 'Candidate';

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
    } else {
      async function loadSession() {
        try {
          const s = await api.startScreening(sessionStorage.getItem('candidate_id') || '');
          setSession(s);
        } catch (_) {
          // It's okay if session load fails, we already have sessionId
        }
      }
      loadSession();
    }
  }, [sessionId, navigate]);

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
        // Stop all audio tracks to release microphone
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

  const handleSubmit = async () => {
    if (!audioBlob) return;
    setLoading(true);
    setError(null);

    try {
      await api.uploadIntro(sessionId, audioBlob);
      navigate('/interview');
    } catch (err) {
      setError(err.message || 'Failed to upload audio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <h1 className="title-gradient" style={{ fontSize: '2rem' }}>Hello, {candidateName}!</h1>
        <p className="subtitle" style={{ marginBottom: '1.5rem' }}>
          Let's start with a brief voice introduction.
        </p>

        <div style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '1rem', borderRadius: '0.75rem', display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
          <Info size={20} style={{ color: 'var(--primary)', flexShrink: 0 }} />
          <p style={{ fontSize: '0.875rem', color: 'var(--text-light)', lineHeight: 1.4 }}>
            <strong>Language Agnostic:</strong> You can speak in <strong>English, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, or Punjabi</strong>. Speak naturally for up to 30 seconds, describing your experience and interest.
          </p>
        </div>

        {error && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', padding: '1rem', borderRadius: '0.75rem', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.9rem' }}>{error}</span>
          </div>
        )}

        <div className="recording-container">
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
              <p style={{ fontSize: '0.9rem', color: 'var(--success)', fontWeight: 500 }}>✓ Recording ready to upload</p>
              <audio src={audioUrl} controls style={{ width: '100%', maxWidth: '300px' }} />
            </div>
          )}

          <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>
            {recording ? 'Recording... click to stop' : audioUrl ? 'Review your voice introduction' : 'Click microphone to start recording'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          {audioUrl && (
            <button className="btn" onClick={handleReset} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff' }} disabled={loading}>
              <RotateCcw size={18} /> Record Again
            </button>
          )}
          <button 
            className="btn btn-primary" 
            onClick={handleSubmit} 
            disabled={!audioBlob || loading}
          >
            <Send size={18} /> {loading ? 'Uploading...' : 'Next Step'}
          </button>
        </div>
      </div>
    </div>
  );
}
