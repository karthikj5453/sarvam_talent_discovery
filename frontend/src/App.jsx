import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Apply from './pages/Apply';
import Intro from './pages/Intro';
import Interview from './pages/Interview';
import Complete from './pages/Complete';
import ThemeToggle from './components/ThemeToggle';

export default function App() {
  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', justifyContent: 'center' }}>
        <ThemeToggle />
        <Routes>
          <Route path="/" element={<Apply />} />
          <Route path="/intro" element={<Intro />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/complete" element={<Complete />} />
        </Routes>
      </div>
    </Router>
  );
}
