import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Mic, Square, RotateCcw, ChevronRight, AlertCircle, CheckCircle } from 'lucide-react';

const STEPS = ['Apply', 'Intro', 'Interview', 'Done'];
const WAVEFORM_BARS = 12;

export default function Intro() {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const mimeTypeRef = useRef('audio/webm');
  const navigate = useNavigate();

  const sessionId = sessionStorage.getItem('screening_session_id');
  const candidateName = sessionStorage.getItem('candidate_name') || 'there';

  useEffect(() => {
    if (!sessionId) navigate('/');
  }, [sessionId, navigate]);

  const startRecording = async () => {
    setError(null);
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
      mimeTypeRef.current = mimeType;
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeTypeRef.current });
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
      await api.uploadIntro(sessionId, audioBlob, mimeTypeRef.current);
      navigate('/interview');
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Progress */}
      <div className="progress-steps" style={{ marginBottom: '2rem' }}>
        {STEPS.map((s, i) => (
          <div key={s} className="step-item">
            <div className={`step-dot ${i === 1 ? 'active' : i < 1 ? 'done' : ''}`}>{i < 1 ? '✓' : i + 1}</div>
            {i < STEPS.length - 1 && <div className={`step-line ${i < 1 ? 'done' : ''}`} />}
          </div>
        ))}
      </div>

      <div className="glass-card">
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <h1 className="title-gradient" style={{ fontSize: '1.85rem' }}>Hi, {candidateName}!</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Record a 20–30 second voice introduction about yourself.
          </p>
        </div>

        {/* Language tip */}
        <div className="alert alert-info" style={{ marginBottom: '1.75rem' }}>
          <span style={{ fontSize: '1rem' }}>🌐</span>
          <span style={{ fontSize: '0.85rem', lineHeight: 1.4 }}>
            <strong>Speak naturally in any Indian language</strong> — Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, or Punjabi.
          </span>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            {error}
          </div>
        )}

        {/* Recording UI */}
        <div className="recording-area">
          {/* Waveform (only while recording) */}
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
                {recording ? <Square size={28} color="#fff" /> : <Mic size={28} color="#fff" />}
              </button>
              <p className={`record-status ${recording ? 'live' : ''}`}>
                {recording ? 'Recording… click to stop' : 'Click the mic to start'}
              </p>
            </>
          ) : (
            <div className="audio-preview" style={{ width: '100%' }}>
              <div className="audio-preview-label">
                <CheckCircle size={14} /> Recording ready
              </div>
              <audio src={audioUrl} controls />
            </div>
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
            disabled={!audioBlob || loading}
          >
            {loading ? <><span className="spinner" /> Uploading...</> : <>Next Step <ChevronRight size={16} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}
