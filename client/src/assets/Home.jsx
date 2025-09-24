import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './css/Home.css';

function Home() {
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState('');

  const handleRefreshDatabase = async () => {
    setRefreshing(true);
    setRefreshError('');
    try {
      const response = await fetch('/api/refresh-database', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to refresh database.');
      }
      alert('Database refreshed successfully!');
    } catch (error) {
      setRefreshError('Failed to refresh database.');
      alert('Error: ' + error.message);
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

        {/* The new "Refresh Database" Card with the API call */}
        <div className="feature-card" onClick={!refreshing ? handleRefreshDatabase : null}>
          <h3>Refresh Database</h3>
          <p>{refreshing ? 'Refreshing...' : 'Reset all data and start over.'}</p>
          {refreshError && <p className="error-message">{refreshError}</p>}
        </div>

      </div>
    </div>
  );
}

export default Home;
