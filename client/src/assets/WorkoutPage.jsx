import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { generateWorkout, getBodyParts } from './api';
import './css/WorkoutPage.css';

function WorkoutPage() {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [bodyParts, setBodyParts] = useState([]);
  const [selectedBodyPart, setSelectedBodyPart] = useState('');
  const [exerciseCount, setExerciseCount] = useState(3);

  const fetchBodyParts = async () => {
    try {
      const data = await getBodyParts();
      setBodyParts(data);
    } catch (err) {
      setError('Failed to fetch body parts.');
      console.error(err);
    }
  };

  const handleGenerateWorkout = async () => {
    if (!selectedBodyPart) {
      setError('Please select a body part.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await generateWorkout(selectedBodyPart, exerciseCount);
      setExercises(data);
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBodyParts();
  }, []);

  return (
    <div className="workout-page-container">
      <div className="controls">
        <div className="form-fields">
          <label>
            Body Part:
            <select value={selectedBodyPart} onChange={(e) => setSelectedBodyPart(e.target.value)}>
              <option value="">-- Select --</option>
              {bodyParts.map((part, index) => (
                <option key={index} value={part}>{part}</option>
              ))}
            </select>
          </label>
          <label>
            Number of Exercises:
            <input 
              type="number" 
              value={exerciseCount} 
              onChange={(e) => setExerciseCount(Math.max(1, e.target.value))} 
              min="1"
            />
          </label>
        </div>
        <button onClick={handleGenerateWorkout} disabled={loading}>
          {loading ? 'Generating...' : 'Generate Workout'}
        </button>
      </div>

      {loading && <p>Generating your workout...</p>}
      {error && <p className="error-message">{error}</p>}

      <div className="workout-list">
        {exercises.length > 0 ? (
          exercises.map((exercise, index) => (
            <Link to={`/exercise/${encodeURIComponent(exercise.name)}`} key={index} className="exercise-card-link">
              <div className="exercise-card">
                <h3>{exercise.name}</h3>
                <p><strong>Body Part:</strong> {exercise.bodyPart}</p>
                <p><strong>Equipment:</strong> {exercise.equipment}</p>
                <p><strong>Reps:</strong> {exercise.reps}</p>
                <p><strong>Sets:</strong> {exercise.sets}</p>
              </div>
            </Link>
          ))
        ) : (
          <p>Select your options and click "Generate Workout".</p>
        )}
      </div>
    </div>
  );
}

export default WorkoutPage;