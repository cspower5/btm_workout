import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import './css/AuthPages.css';

function SignInPage() {
  console.log('SignInPage component mounting...');
  const { login, loading: authLoading, error: authError, clearError } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    }

    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formErrors = validateForm();
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }

    setMessage('');
    setErrors({});
    clearError(); // Clear any previous auth errors

    try {
      const result = await login({
        email: formData.email,
        password: formData.password,
        rememberMe: formData.rememberMe
      });

      if (result.success) {
        // Login successful
        setMessage('Login successful! Redirecting...');
        setTimeout(() => {
          navigate('/home'); // Redirect to main app
        }, 1500);
      } else {
        setMessage(result.error || 'Login failed. Please check your credentials.');
      }
      
    } catch (error) {
      console.error('Login error:', error);
      setMessage('Login failed. Please try again.');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h2 className="auth-title">Welcome Back</h2>
          <p className="auth-subtitle">Sign in to access your personalized workout experience</p>
        </div>

        <div className="auth-description">
          <h3>Break the Monotony</h3>
          <p>Transform your fitness routine with personalized, randomized workouts tailored to your equipment and body part preferences. No more boring, repetitive exercises - discover new movements and keep your workouts fresh and engaging.</p>
          <div className="auth-features">
            <div className="feature-item">✨ Personalized workout generation</div>
            <div className="feature-item">🎯 Target specific body parts</div>
            <div className="feature-item">🏋️ Filter by available equipment</div>
            <div className="feature-item">📚 Extensive exercise database</div>
          </div>
        </div>

        {(message || authError) && (
          <div className={`auth-message ${(message && message.includes('failed')) || authError ? 'error' : 'success'}`}>
            {authError || message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className={`form-input ${errors.email ? 'error' : ''}`}
              placeholder="Enter your email"
              autoComplete="email"
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className={`form-input ${errors.password ? 'error' : ''}`}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          <div className="auth-options">
            <div className="auth-checkbox-group">
              <input
                type="checkbox"
                id="rememberMe"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleInputChange}
                className="auth-checkbox"
              />
              <label htmlFor="rememberMe" className="auth-checkbox-label">Remember me for 30 days</label>
            </div>
          </div>

          <button 
            type="submit" 
            className="auth-submit"
            disabled={authLoading}
          >
            {authLoading ? (
              <div className="auth-loading">
                <span className="auth-spinner"></span>
                Signing In...
              </div>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/forgot-password" className="auth-link">
            Forgot your password?
          </Link>
          <div className="auth-link-secondary">
            Don't have an account?{' '}
            <Link 
              to="/signup" 
              className="auth-link"
              onClick={() => console.log('SignIn -> SignUp link clicked')}
            >
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignInPage;