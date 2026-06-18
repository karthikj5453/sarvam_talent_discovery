import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { api } from '../services/api';
import { Briefcase, Users, LayoutDashboard, LogOut, Zap } from 'lucide-react';

export default function SidebarLayout({ children }) {
  const [hrUser, setHrUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api.getMe()
      .then(setHrUser)
      .catch(() => navigate('/login'));
  }, [navigate]);

  const initials = hrUser?.full_name
    ? hrUser.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : 'HR';

  const NAV_ITEMS = [
    { to: '/', icon: LayoutDashboard, label: 'Overview', exact: true },
    { to: '/jobs', icon: Briefcase, label: 'Jobs' },
    { to: '/candidates', icon: Users, label: 'Candidates' },
  ];

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
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
          {hrUser && (
            <div className="sidebar-user-card">
              <div className="user-avatar">{initials}</div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {hrUser.full_name || 'HR Lead'}
                </p>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {hrUser.email}
                </p>
              </div>
            </div>
          )}
          <button className="sidebar-logout-btn" onClick={() => api.logout()}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
