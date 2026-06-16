import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { api } from '../services/api';
import { Briefcase, Users, LayoutDashboard, LogOut, User } from 'lucide-react';

export default function SidebarLayout({ children }) {
  const [hrUser, setHrUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    async function loadMe() {
      try {
        const user = await api.getMe();
        setHrUser(user);
      } catch (_) {
        navigate('/login');
      }
    }
    loadMe();
  }, [navigate]);

  const handleLogout = () => {
    api.logout();
  };

  return (
    <div className="dashboard-layout">
      <div className="sidebar">
        <div className="sidebar-title">
          <span>🎙️</span> Sarvam Discovery
        </div>

        <nav style={{ flexGrow: 1, marginTop: '1rem' }}>
          <ul className="nav-links">
            <li>
              <NavLink 
                to="/" 
                className={({ isActive }) => `nav-link ${isActive && location.pathname === '/' ? 'active' : ''}`}
              >
                <LayoutDashboard size={18} /> Overview
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/jobs" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Briefcase size={18} /> Jobs
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/candidates" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Users size={18} /> Candidates
              </NavLink>
            </li>
          </ul>
        </nav>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', borderTop: '1px solid var(--border-muted)', paddingTop: '1.5rem' }}>
          {hrUser && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0 0.5rem' }}>
              <div style={{ background: 'var(--primary-glow)', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={16} style={{ color: 'var(--primary-light)' }} />
              </div>
              <div style={{ minWidth: 0, flexGrow: 1 }}>
                <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {hrUser.full_name || 'HR Lead'}
                </p>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {hrUser.email}
                </p>
              </div>
            </div>
          )}
          
          <button 
            onClick={handleLogout}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '0.75rem 0.5rem', fontSize: '0.9rem', fontWeight: 500, width: '100%', borderRadius: '0.5rem', transition: 'background 0.2s' }}
            onMouseEnter={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.05)'}
            onMouseLeave={(e) => e.target.style.background = 'transparent'}
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </div>

      <div className="main-content">
        {children}
      </div>
    </div>
  );
}
