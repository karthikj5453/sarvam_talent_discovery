import React, { useEffect, useState } from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem('sarvam-theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sarvam-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <button
      onClick={toggleTheme}
      title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '36px',
        height: '36px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid var(--border-card)',
        color: 'var(--text-white)',
        cursor: 'pointer',
        transition: 'all 0.2s',
        position: 'absolute',
        top: '1.5rem',
        right: '1.5rem',
        zIndex: 50
      }}
      onMouseOver={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
      onMouseOut={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'}
    >
      {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
