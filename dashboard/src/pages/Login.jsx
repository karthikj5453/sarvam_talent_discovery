import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Zap, Mail, Lock, ArrowRight, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async e => {
    e.preventDefault();
    setLoading(true); setError(null); setSuccessMsg(null);
    try {
      await api.login(email, password);
      await api.getMe();
      navigate('/');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const createDemoAccount = async () => {
    setLoading(true); setError(null); setSuccessMsg(null);
    const demoEmail = 'hr@company.com';
    const demoPassword = 'password123';
    try {
      await api.register({ email: demoEmail, password: demoPassword, full_name: 'Demo HR Lead', role: 'hr' });
      setSuccessMsg('Demo account created! Logging in…');
      await api.login(demoEmail, demoPassword);
      setTimeout(() => navigate('/'), 800);
    } catch (err) {
      if (err.message?.includes('already registered')) {
        try { await api.login(demoEmail, demoPassword); navigate('/'); } catch { setError('Demo login failed.'); }
      } else {
        setError(err.message || 'Could not create demo account.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {/* Left hero panel */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
        justifyContent: 'center', padding: '4rem 4rem 4rem 6rem',
        maxWidth: '600px',
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.35rem 0.9rem', borderRadius: '9999px',
          background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
          fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', color: 'var(--primary-light)',
          marginBottom: '2rem', textTransform: 'uppercase',
        }}>
          <Zap size={11} /> AI Hiring Platform
        </div>

        <h1 style={{
          fontSize: '3.5rem', fontWeight: 900, letterSpacing: '-0.04em',
          background: 'linear-gradient(135deg, #fff 0%, #c7d2fe 60%, #a78bfa 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          lineHeight: 1.1, marginBottom: '1.25rem',
        }}>
          Hire Smarter<br />with AI.
        </h1>

        <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.65, maxWidth: '380px', marginBottom: '2.5rem' }}>
          Sarvam Talent Discovery uses voice-based multilingual screening and Gemini AI to rank candidates across 6 competency dimensions.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[
            '🌐 10 Indian languages supported',
            '🤖 Gemini-powered competency scoring',
            '⚡ Results in under 5 minutes',
          ].map(feat => (
            <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              <CheckCircle size={14} style={{ color: 'var(--success)', flexShrink: 0 }} />
              {feat}
            </div>
          ))}
        </div>
      </div>

      {/* Right login card */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem', minWidth: '440px', flex: '0 0 auto' }}>
        <div className="login-card" style={{ width: '100%', maxWidth: '400px' }}>

          {/* Logo mark */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{
              width: 48, height: 48, borderRadius: '14px',
              background: 'linear-gradient(135deg, var(--primary), var(--accent))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 1rem', boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            }}>
              <Zap size={22} color="#fff" />
            </div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-white)', letterSpacing: '-0.02em' }}>
              Welcome back
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Sign in to your HR dashboard
            </p>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
              <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
            </div>
          )}
          {successMsg && (
            <div className="alert alert-success" style={{ marginBottom: '1.25rem' }}>
              <CheckCircle size={15} style={{ flexShrink: 0 }} /> {successMsg}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Mail size={11} /> HR Email
              </label>
              <input
                type="email" className="form-input"
                placeholder="hr@company.com"
                value={email} onChange={e => setEmail(e.target.value)} required
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Lock size={11} /> Password
              </label>
              <input
                type="password" className="form-input"
                placeholder="••••••••"
                value={password} onChange={e => setPassword(e.target.value)} required
              />
            </div>

            <button
              type="submit" className="btn btn-primary"
              disabled={loading} style={{ marginTop: '0.5rem', width: '100%' }}
            >
              {loading ? <><span className="spinner" /> Signing in…</> : <>Sign In <ArrowRight size={15} /></>}
            </button>
          </form>

          <div style={{ position: 'relative', margin: '1.75rem 0 1.25rem', textAlign: 'center' }}>
            <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: 1, background: 'var(--border)' }} />
            <span style={{ position: 'relative', background: '#111827', padding: '0 0.75rem', fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.06em' }}>
              DEMO MODE
            </span>
          </div>

          <button
            type="button" className="btn btn-secondary"
            onClick={createDemoAccount} disabled={loading} style={{ width: '100%' }}
          >
            <UserPlus size={14} /> One-click Demo Login
          </button>
        </div>
      </div>
    </div>
  );
}
