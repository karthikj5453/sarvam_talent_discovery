import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Briefcase, Users, LayoutDashboard, LogOut, Zap, Menu, X, Shield } from 'lucide-react';

export default function SidebarLayout({ children }) {
  const { user, logout, isHrOrAdmin } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect to login if auth context says user is gone (token expired + refresh failed)
  useEffect(() => {
    const token = localStorage.getItem('hr_token');
    if (!token) navigate('/login');
  }, [navigate]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location]);

  const initials = user?.full_name
    ? user.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : 'HR';

  const roleBadgeLabel = user?.role
    ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
    : '';

  const NAV_ITEMS = [
    { to: '/', icon: LayoutDashboard, label: 'Overview', exact: true },
    { to: '/jobs', icon: Briefcase, label: 'Jobs' },
    { to: '/candidates', icon: Users, label: 'Candidates' },
  ];

  return (
    <div className="dashboard-layout">
      {/* Sidebar Overlay for mobile */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        {/* Close Button for mobile */}
        <button 
          className="sidebar-close-btn" 
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>

        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Zap size={17} color="#fff" />
          </div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">Sarvam</span>
            <span className="sidebar-brand-sub">Talent Engine</span>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1 }}>
          <p className="nav-section-label" style={{ marginBottom: '0.5rem' }}>Navigation</p>
          <ul className="nav-links">
            {NAV_ITEMS.map(({ to, icon: Icon, label, exact }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={exact}
                  className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* User section */}
        <div className="sidebar-user">
          {user && (
            <div className="sidebar-user-card">
              <div className="user-avatar">{initials}</div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.full_name || 'HR Lead'}
                </p>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.email}
                </p>
                {roleBadgeLabel && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.2rem',
                    fontSize: '0.62rem', fontWeight: 700, textTransform: 'uppercase',
                    padding: '0.15rem 0.45rem', borderRadius: '999px', marginTop: '0.25rem',
                    background: user.role === 'admin' ? 'rgba(255, 180, 0, 0.15)' :
                                user.role === 'interviewer' ? 'rgba(100, 180, 255, 0.15)' :
                                'rgba(106, 133, 255, 0.2)',
                    color: user.role === 'admin' ? '#f6c90e' :
                           user.role === 'interviewer' ? '#60b4f6' : 'var(--primary-light)',
                    border: `1px solid ${user.role === 'admin' ? 'rgba(246,201,14,0.3)' :
                             user.role === 'interviewer' ? 'rgba(96,180,246,0.3)' :
                             'rgba(106,133,255,0.3)'}`,
                  }}>
                    <Shield size={9} />
                    {roleBadgeLabel}
                  </span>
                )}
              </div>
            </div>
          )}
          <button className="sidebar-logout-btn" onClick={logout}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        {/* Mobile Header Bar */}
        <header className="mobile-header">
          <button 
            className="menu-toggle-btn" 
            onClick={() => setSidebarOpen(true)}
            aria-label="Toggle menu"
          >
            <Menu size={20} />
          </button>
          <div className="mobile-header-brand">
            <div className="sidebar-brand-icon" style={{ width: 28, height: 28 }}>
              <Zap size={14} color="#fff" />
            </div>
            <span className="sidebar-brand-name" style={{ fontSize: '0.85rem' }}>Sarvam</span>
          </div>
          <div style={{ width: 20 }} />
        </header>

        {children}
      </main>
    </div>
  );
}
