import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('hr_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      setUser(null);
      localStorage.removeItem('hr_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email, password) => {
    const data = await api.login(email, password);
    const me = await api.getMe();
    setUser(me);
    return data;
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  // Convenience helpers
  const isAdmin = user?.role === 'admin';
  const isHrOrAdmin = user?.role === 'hr' || user?.role === 'admin';
  const isInterviewer = user?.role === 'interviewer';

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAdmin, isHrOrAdmin, isInterviewer, refreshUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
