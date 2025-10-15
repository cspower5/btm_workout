import React, { useState } from 'react';
//import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { HashRouter, Routes, Route, Link, Navigate, useLocation} from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Home from './Home';
import WorkoutPage from './WorkoutPage';
import NewExerciseForm from './NewExerciseForm';
import SingleExercisePage from './SingleExercisePage';
import AddBodyPartPage from './AddBodyPartPage';
import AddEquipmentPage from './AddEquipmentPage';
import ManageItemsPage from './ManageItemsPage';
import SignUpPage from './SignUpPage';
import SignInPage from './SignInPage';
import './css/App.css';
import logoPng from './images/btm_workout_logo.png';

function AppContent() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated, user, logout, loading } = useAuth();
  const location = useLocation();
  const isAuthPage = location.pathname === '/signup' || location.pathname === '/signin';

  const toggleMobileMenu = () => setMobileMenuOpen((s) => !s);
  const closeMobileMenu = () => setMobileMenuOpen(false);
  const handleLogout = () => { logout(); closeMobileMenu(); };

  // Hamburger icon for mobile
  const Hamburger = ({ open, onToggle }) => (
    <button className={`hamburger ${open ? 'open' : ''}`} onClick={onToggle} aria-label="Toggle navigation" aria-expanded={open}>
      <span className="hamburger-box"><span className="hamburger-inner" /></span>
    </button>
  );

  // Popout menu for mobile
  const MobileMenu = ({ open, onClose }) => (
    <div className={`mobile-menu-overlay${open ? ' open' : ''}`} onClick={onClose}>
      <nav className="mobile-menu" onClick={e => e.stopPropagation()}>
        <ul>
          <li><Link to="/home" onClick={onClose}>Home</Link></li>
          <li><Link to="/workout" onClick={onClose}>Generate Workout</Link></li>
          <li><Link to="/add-exercise" onClick={onClose}>Add Exercise</Link></li>
          <li><Link to="/add-body-part" onClick={onClose}>Add Body Part</Link></li>
          <li><Link to="/add-equipment" onClick={onClose}>Add Equipment</Link></li>
          <li><Link to="/manage-body-parts" onClick={onClose}>Manage Body Parts</Link></li>
          <li><Link to="/manage-equipment" onClick={onClose}>Manage Equipment</Link></li>
          <li><Link to="/manage-exercises" onClick={onClose}>Manage Exercises</Link></li>
          <li><button onClick={handleLogout} className="logout-btn">Log Out</button></li>
        </ul>
      </nav>
    </div>
  );

  return (
    <div className="App">
      {/* Header */}
      {isAuthPage ? (
        <header className="auth-header-simple">
          <div className="header-brand">
            <h1 className="header-title">Break the Monotony Workout</h1>
            <p className="header-subtitle">Tired of the same routine? Break the Monotony chooses your exercises so you can keep your workouts fresh and your results moving.</p>
          </div>
        </header>
      ) : (
        <header className="App-header">
          <div className="header-brand">
            <h1 className="header-title">Welcome to Break the Monotony Workout</h1>
            <p className="header-subtitle">Tired of the same routine? Break the Monotony chooses your exercises so you can keep your workouts fresh and your results moving.</p>
          </div>
          {isAuthenticated && (
            <nav className="header-nav desktop-nav">
              <ul className="nav-links">
                <li><Link to="/home">Home</Link></li>
                <li><Link to="/workout">Generate Workout</Link></li>
                <li><Link to="/add-exercise">Add Exercise</Link></li>
                <li><Link to="/add-body-part">Add Body Part</Link></li>
                <li><Link to="/add-equipment">Add Equipment</Link></li>
                <li><Link to="/manage-body-parts">Manage Body Parts</Link></li>
                <li><Link to="/manage-equipment">Manage Equipment</Link></li>
                <li><Link to="/manage-exercises">Manage Exercises</Link></li>
              </ul>
            </nav>
          )}
          {isAuthenticated && (
            <div className="mobile-hamburger">
              <Hamburger open={mobileMenuOpen} onToggle={toggleMobileMenu} />
            </div>
          )}
          {isAuthenticated && <MobileMenu open={mobileMenuOpen} onClose={closeMobileMenu} />}
          {isAuthenticated && (
            <div className="user-info-section">
              <span className="username">Welcome, {user?.username || user?.first_name}</span>
              <button onClick={handleLogout} className="logout-btn">Log Out</button>
            </div>
          )}
        </header>
      )}
      <main>
        <Routes key={location.pathname}>
          <Route path="/" element={<Navigate to="/signup" replace />} />
          <Route path="/signup" element={<SignUpPage key="signup" />} />
          <Route path="/signin" element={<SignInPage key="signin" />} />
          <Route path="/home" element={isAuthenticated ? <Home /> : <Navigate to="/signin" replace />} />
          <Route path="/workout" element={isAuthenticated ? <WorkoutPage /> : <Navigate to="/signin" replace />} />
          <Route path="/add-exercise" element={isAuthenticated ? <NewExerciseForm /> : <Navigate to="/signin" replace />} />
          <Route path="/add-body-part" element={isAuthenticated ? <AddBodyPartPage /> : <Navigate to="/signin" replace />} />
          <Route path="/add-equipment" element={isAuthenticated ? <AddEquipmentPage /> : <Navigate to="/signin" replace />} />
          <Route path="/exercise/:name" element={isAuthenticated ? <SingleExercisePage /> : <Navigate to="/signin" replace />} />
          <Route path="/manage-body-parts" element={isAuthenticated ? <ManageItemsPage title="Body Parts" fetchUrl="/api/v1/body_parts_list" deleteUrl="/api/v1/delete_body_part" /> : <Navigate to="/signin" replace />} />
          <Route path="/manage-equipment" element={isAuthenticated ? <ManageItemsPage title="Equipment" fetchUrl="/api/v1/equipment_list" deleteUrl="/api/v1/delete_equipment" /> : <Navigate to="/signin" replace />} />
          <Route path="/manage-exercises" element={isAuthenticated ? <ManageItemsPage title="Exercises" fetchUrl="/api/v1/exercises_list" deleteUrl="/api/v1/delete_exercise" /> : <Navigate to="/signin" replace />} />
        </Routes>
      </main>
      {/* Footer */}
      {isAuthPage ? (
        <footer className="auth-footer-simple">
          <div className="auth-footer-logo">
            <img src={logoPng} alt="BTM Workout Logo" />
          </div>
          <p>© 2024 BTM Workout. All rights reserved.</p>
        </footer>
      ) : (
        <footer className="footer-nav">
          {isAuthenticated && (
            <nav className="footer-nav desktop-nav">
              <ul>
                <li><Link to="/home">Home</Link></li>
                <li><Link to="/workout">Generate Workout</Link></li>
                <li><Link to="/add-exercise">Add Exercise</Link></li>
                <li><Link to="/add-body-part">Add Body Part</Link></li>
                <li><Link to="/add-equipment">Add Equipment</Link></li>
                <li><Link to="/manage-body-parts">Manage Body Parts</Link></li>
                <li><Link to="/manage-equipment">Manage Equipment</Link></li>
                <li><Link to="/manage-exercises">Manage Exercises</Link></li>
              </ul>
            </nav>
          )}
          {isAuthenticated && (
            <div className="mobile-hamburger">
              <Hamburger open={mobileMenuOpen} onToggle={toggleMobileMenu} />
            </div>
          )}
          {isAuthenticated && <MobileMenu open={mobileMenuOpen} onClose={closeMobileMenu} />}
          <div className="footer-logo">
            <img src={logoPng} alt="BTM Workout Logo" />
          </div>
          <p>© 2024 BTM Workout. All rights reserved.</p>
        </footer>
      )}
    </div>
  );
}

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </HashRouter>
  );
}