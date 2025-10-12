import React, { useState } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom'; 
import SignUpPage from './SignUpPage_simple';
import './css/App.css';

function AppContent() {
  console.log('AppContent starting...');
  
  return (
    <Router>
      <div className="App">
        <h1>BTM Workout App Debug</h1>
        <Routes>
          <Route path="/" element={<SignUpPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/signin" element={<SignUpPage />} />
        </Routes>
      </div>
    </Router>
  );
}

function App() {
  return <AppContent />;
}

export default App;