import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { refreshDatabase } from '../assets/api/index.js'; // <-- NEW: Import the fixed refresh function
import './css/Home.css';

function Home() {
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState('');

  // CORRECTED FUNCTION: This now calls the centralized function using the absolute URL.
  const handleRefreshDatabase = async () => {
    setRefreshing(true);
    setRefreshError('');
    try {
      // FIX: Call the imported function, which uses the hardcoded Render API URL.
      const response = await refreshDatabase(); 
      
      if (response && (response.message || response.status === 'ok')) {
        alert('Database refreshed successfully!');
      } else {
        // Handle cases where the API returns a 200 status but an unexpected payload
        throw new Error('Refresh completed but API response was unusual.');
      }
    } catch (error) {
      setRefreshError('Failed to refresh database.');
      // Provide a better error message if it's a network issue (like the server sleeping)
      const errorMessage = error.message.includes('Network Error') 
        ? 'Could not reach the API. Server may be asleep or unreachable.' 
        : error.message;
      alert('Error: ' + errorMessage);
      console.error(error);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="home-container">
      <h2>Welcome to Break The Monotony Workout!</h2>
      <p>Explore the features below to create, manage, and find your next workout.</p>
      
      <div className="features-grid">
        
        <Link to="/workout" className="feature-card-link">
          <div className="feature-card">
            <h3>Generate Workout</h3>
            <p>Create a new, randomized workout with a single click.</p>
          </div>
        </Link>
        
        <Link to="/add-exercise" className="feature-card-link">
          <div className="feature-card">
            <h3>Add Exercises</h3>
            <p>Expand your library by adding new exercises to the database.</p>
          </div>
        </Link>

        <Link to="/manage-body-parts" className="feature-card-link">
          <div className="feature-card">
            <h3>Manage Body Parts</h3>
            <p>Add, edit, or remove body parts from your database.</p>
          </div>
        </Link>

        <Link to="/manage-equipment" className="feature-card-link">
          <div className="feature-card">
            <h3>Manage Equipment</h3>
            <p>Keep your equipment list up to date and ready for use.</p>
          </div>
        </Link>

        <Link to="/manage-exercises" className="feature-card-link">
          <div className="feature-card">
            <h3>Manage Exercises</h3>
            <p>View, update, or delete existing exercises.</p>
          </div>
        </Link>

        {/* The corrected "Refresh Database" Card */}
        <div 
          className="feature-card" 
          onClick={!refreshing ? handleRefreshDatabase : null}
          style={{ cursor: refreshing ? 'not-allowed' : 'pointer' }}
        >
          <h3>Refresh Database</h3>
          <p>{refreshing ? 'Refreshing...' : 'Reset all data and start over.'}</p>
          {refreshError && <p className="error-message">{refreshError}</p>}
        </div>

      </div>
    </div>
  );
}

export default Home;
