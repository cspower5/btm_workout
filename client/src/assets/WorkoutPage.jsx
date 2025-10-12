import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { generateWorkout, getBodyParts, getEquipmentList } from './api/index.jsx';
import './css/WorkoutPage.css';

function WorkoutPage() {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [bodyParts, setBodyParts] = useState([]);
  const [selectedBodyPart, setSelectedBodyPart] = useState('');
  const [equipment, setEquipment] = useState([]);
  const [selectedEquipment, setSelectedEquipment] = useState('');
  const [exerciseCount, setExerciseCount] = useState(3);

  // WorkoutPage.jsx - Replace your existing fetchBodyParts function with this

  // FIX: Implemented a simple retry loop to handle server wake-up delays
  const fetchBodyParts = async (retries = 3) => {
    try {
      const data = await getBodyParts();
      // Sort body parts alphabetically
      const sortedBodyParts = data.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
      setBodyParts(sortedBodyParts);
    } catch (err) {
      if (retries > 0) {
        // Wait 1.5 seconds and try the call again
        await new Promise(resolve => setTimeout(resolve, 1500)); 
        console.warn(`Initial fetch failed. Retrying... Attempts remaining: ${retries - 1}`);
        return fetchBodyParts(retries - 1);
      }
      // Only set error if all retries fail
      setError('Failed to fetch body parts. The backend may be asleep or unreachable.');
      console.error(err);
    }
  };

  const fetchEquipment = async (retries = 3) => {
    try {
      const data = await getEquipmentList();
      // Sort equipment alphabetically
      const sortedEquipment = data.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
      setEquipment(sortedEquipment);
    } catch (err) {
      if (retries > 0) {
        // Wait 1.5 seconds and try the call again
        await new Promise(resolve => setTimeout(resolve, 1500)); 
        console.warn(`Equipment fetch failed. Retrying... Attempts remaining: ${retries - 1}`);
        return fetchEquipment(retries - 1);
      }
      // Only set error if all retries fail
      console.error('Failed to fetch equipment:', err);
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
      // Pass equipment only if it's selected (not empty string)
      const equipmentParam = selectedEquipment || null;
      const data = await generateWorkout(selectedBodyPart, exerciseCount, equipmentParam);
      setExercises(data);
    } catch (err) {
      // Clear previous exercises when an error occurs
      setExercises([]);
      
      // Handle 404 errors with user-friendly messages
      if (err.response && err.response.status === 404) {
        if (selectedEquipment) {
          setError(`Sorry, no exercises found for ${selectedBodyPart} using ${selectedEquipment}. Try selecting "Any Equipment" or a different combination.`);
        } else {
          setError(`Sorry, no exercises found for ${selectedBodyPart}. Please try a different body part.`);
        }
      } else {
        // Handle other errors
        setError(err.message || 'An error occurred while generating your workout. Please try again.');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBodyParts();
    fetchEquipment();
  }, []);

  return (
    <div className="workout-page-container">
      <h2 className="workout-page-title">Generate Workout</h2>
      <p className="workout-page-subtitle">Customize your workout by selecting a body part and number of exercises</p>
      
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
            Equipment (Optional):
            <select value={selectedEquipment} onChange={(e) => setSelectedEquipment(e.target.value)}>
              <option value="">Any Equipment</option>
              {equipment.map((equip, index) => (
                <option key={index} value={equip}>{equip}</option>
              ))}
            </select>
          </label>
          <label>
            Number of Exercises:
            <div className="number-input-container">
              <button 
                type="button"
                className="number-btn minus-btn"
                onClick={() => setExerciseCount(Math.max(1, exerciseCount - 1))}
                disabled={exerciseCount <= 1}
                aria-label="Decrease number of exercises"
              >
                −
              </button>
              <span className="number-display">{exerciseCount}</span>
              <button 
                type="button"
                className="number-btn plus-btn"
                onClick={() => setExerciseCount(Math.min(20, exerciseCount + 1))}
                disabled={exerciseCount >= 20}
                aria-label="Increase number of exercises"
              >
                +
              </button>
            </div>
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
                {exercise.reps != null && (
                  <p><strong>Reps:</strong> {exercise.reps}</p>
                )}
                {exercise.sets != null && (
                  <p><strong>Sets:</strong> {exercise.sets}</p>
                )}
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