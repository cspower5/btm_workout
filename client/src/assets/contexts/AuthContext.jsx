import React, { createContext, useContext, useReducer, useEffect } from 'react';

// API Base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_URL 
  || (import.meta.env.PROD ? 'https://btm-workout.onrender.com' : '/api');

// Auth action types
const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_USER: 'SET_USER',
  AUTH_ERROR: 'AUTH_ERROR'
};

// Initial auth state
const initialState = {
  user: null,
  isAuthenticated: false,
  loading: true, // Changed from false to true - must wait for auth check
  error: null,
  token: null
};

// Auth reducer to manage state transitions
function authReducer(state, action) {
  console.log("authReducer called", { state, action });
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload,
        error: null
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        loading: false,
        error: null
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: null
      };

    case AUTH_ACTIONS.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        loading: false,
        error: null
      };

    case AUTH_ACTIONS.AUTH_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false,
        isAuthenticated: false,
        user: null,
        token: null
      };

    default:
      return state;
  }
}

// Create Auth Context
const AuthContext = createContext();

// Auth Provider Component
export function AuthProvider({ children }) {
  console.log("AuthProvider started");
  // Log initial state
  console.log("Initial auth state:", initialState);

  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing token on app startup
  useEffect(() => {
    console.log("useEffect: running checkAuthStatus");
    checkAuthStatus();
  }, []);

  // Check if user is already logged in (token in localStorage)
  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const userData = localStorage.getItem('userData');
      console.log("checkAuthStatus: token:", token, "userData:", userData);

      if (token && userData) {
        // Verify token with backend
        let response;
        try {
          response = await fetch(`${API_BASE_URL}/v1/auth/verify`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            }
          });
        } catch (fetchErr) {
          console.error("checkAuthStatus: fetch error", fetchErr);
          dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
          return;
        }
        console.log("checkAuthStatus: verify response status:", response && response.status);
        if (response && response.ok) {
          let user;
          try {
            user = JSON.parse(userData);
          } catch (jsonErr) {
            console.error("checkAuthStatus: userData JSON parse error", jsonErr);
            localStorage.removeItem('authToken');
            localStorage.removeItem('userData');
            dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
            return;
          }
          dispatch({
            type: AUTH_ACTIONS.LOGIN_SUCCESS,
            payload: { user, token }
          });
          console.log("checkAuthStatus: LOGIN_SUCCESS dispatched", { user, token });
        } else {
          // Token is invalid, clear storage
          console.warn("checkAuthStatus: token invalid or verify failed", response && response.status);
          localStorage.removeItem('authToken');
          localStorage.removeItem('userData');
          dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
        }
      } else {
        console.log("checkAuthStatus: no token or userData found");
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Clear potentially corrupted data
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
    }
  };

  // Login function
  const login = async (credentials) => {
    dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });

    try {
      // Call the actual backend API
  const response = await fetch(`${API_BASE_URL}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password
        })
      });

      const data = await response.json();

      if (data.success) {
        // Store in localStorage
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('userData', JSON.stringify(data.user));

        // Update state
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: { user: data.user, token: data.access_token }
        });

        return { success: true, user: data.user };
      } else {
        const errorMessage = data.errors ? Object.values(data.errors).join(', ') : 'Login failed';
        dispatch({
          type: AUTH_ACTIONS.AUTH_ERROR,
          payload: errorMessage
        });
        return { success: false, error: errorMessage };
      }

    } catch (error) {
      const errorMessage = 'Login failed. Please check your connection.';
      dispatch({
        type: AUTH_ACTIONS.AUTH_ERROR,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  // Register function
  const register = async (userData) => {
    dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });

    try {
      // Call the actual backend API
  const response = await fetch(`${API_BASE_URL}/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: userData.username,
          email: userData.email,
          password: userData.password,
          first_name: userData.firstName,
          last_name: userData.lastName
        })
      });

      const data = await response.json();

      if (data.success) {
        // Store in localStorage
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('userData', JSON.stringify(data.user));

        // Update state
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: { user: data.user, token: data.access_token }
        });

        return { success: true, user: data.user };
      } else {
        const errorMessage = data.errors ? Object.values(data.errors).join(', ') : 'Registration failed';
        dispatch({
          type: AUTH_ACTIONS.AUTH_ERROR,
          payload: errorMessage
        });
        return { success: false, error: errorMessage };
      }

    } catch (error) {
      const errorMessage = 'Registration failed. Please check your connection.';
      dispatch({
        type: AUTH_ACTIONS.AUTH_ERROR,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = () => {
    // Clear localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');

    // Update state
    dispatch({ type: AUTH_ACTIONS.LOGOUT });
  };

  // Update user data
  const updateUser = (userData) => {
    const updatedUser = { ...state.user, ...userData };
    localStorage.setItem('userData', JSON.stringify(updatedUser));
    dispatch({
      type: AUTH_ACTIONS.SET_USER,
      payload: updatedUser
    });
  };

  // Clear auth error
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.AUTH_ERROR, payload: null });
  };

  // Context value
  const value = {
    // State
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    loading: state.loading,
    error: state.error,
    token: state.token,

    // Actions
    login,
    register,
    logout,
    updateUser,
    clearError,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  console.log("useAuth called");
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Export auth actions for external use if needed
export { AUTH_ACTIONS };