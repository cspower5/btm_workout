// ... in ExerciseList.jsx
import React from 'react';
import { Link } from 'react-router-dom'; // Import Link
import './css/ExerciseList.css';

function ExerciseList({ exercises }) {
  return (
    <div className="exercise-list-container">
      <h2>Your Workout Routine</h2>
      <div className="exercise-cards">
        {exercises.map((exercise, index) => (
          <Link to={`/exercise/${exercise.name}`} key={index} className="exercise-card">
            <h3>{exercise.name}</h3>
            <img src={exercise.gifUrl} alt={exercise.name} />
            <p><strong>Body Part:</strong> {exercise.bodyPart}</p>
            <p><strong>Target Muscle:</strong> {exercise.target}</p>
            <p><strong>Equipment:</strong> {exercise.equipment}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default ExerciseList;