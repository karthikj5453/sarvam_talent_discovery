import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Lock, Mail, AlertCircle, ArrowRight, UserPlus } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await api.login(email, password);
      // Retrieve the current user to verify access
      await api.getMe();
      navigate('/');
    } catch (err) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const createDemoAccount = async () => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    const demoEmail = 'hr@company.com';
    const demoPassword = 'password123';

    try {
      // Register demo HR
      await api.register({
        email: demoEmail,
        password: demoPassword,
        full_name: 'Demo HR Lead',
        role: 'hr'
      });
      setSuccessMsg(`Account created! Email: ${demoEmail}, Password: ${demoPassword}. Logging in...`);
      // Automatically login
      await api.login(demoEmail, demoPassword);
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (err) {
      // If user already exists, just log in
      if (err.message && err.message.includes('already registered')) {
        try {
          await api.login(demoEmail, demoPassword);
          navigate('/');
        } catch (_) {
          setError(`Demo account exists but login failed: ${err.message}`);
        }
      } else {
        setError(err.message || 'Could not auto-generate demo account.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', width: '100%', minHeight: '100vh', justifyContent: 'center', alignItems: 'center', background: 'radial-gradient(circle at top, #0f172a 0%, #080c14 100%)' }}>
      <div style={{ maxWidth: '420px', width: '100%', padding: '2rem' }}>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-muted)', borderRadius: '1rem', padding: '2.5rem', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', backdropFilter: 'blur(10px)' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <span style={{ fontSize: '2.5rem' }}>🎙️</span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.5rem', letterSpacing: '-0.025em' }}>Sarvam Talent Engine</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Hiring Dashboard Portal</p>
          </div>

          {error && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.12)', color: '#f87171', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.15)', fontSize: '0.85rem' }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid rgba(16, 185, 129, 0.15)', fontSize: '0.85rem' }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                <Mail size={14} /> HR EMAIL
              </label>
              <input
                type="email"
                className="form-input"
                placeholder="hr@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                <Lock size={14} /> PASSWORD
              </label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
              style={{ marginTop: '0.5rem', width: '100%' }}
            >
              {loading ? 'Authenticating...' : 'Sign In'} <ArrowRight size={16} />
            </button>
          </form>

          <div style={{ position: 'relative', margin: '2rem 0 1.5rem 0', textAlign: 'center' }}>
            <hr style={{ border: 'none', borderTop: '1px solid var(--border-muted)' }} />
            <span style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: '#131c2c', padding: '0 0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>DEVELOPMENT</span>
          </div>

          <button 
            type="button"
            className="btn btn-secondary"
            onClick={createDemoAccount}
            disabled={loading}
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            <UserPlus size={14} /> One-Click Demo Account Login
          </button>
        </div>
      </div>
    </div>
  );
}
