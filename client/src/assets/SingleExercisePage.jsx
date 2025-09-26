import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import './css/SingleExercisePage.css';

// --- ABSOLUTE URL FIX: Hardcoded host to ensure all API calls hit the Render server ---
const API_BASE_URL = 'https://btm-workout.onrender.com'; 

function SingleExercisePage() {
    const { name } = useParams();
    const [exercise, setExercise] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchExercise = async () => {
            setLoading(true);
            setError(null);
            try {
                // FIX: Use the absolute URL and the correct /api/v1/ path
                // encodeURIComponent is used to handle spaces and special characters in the exercise name
                const url = `${API_BASE_URL}/api/v1/exercise/${encodeURIComponent(name)}`;
                const response = await axios.get(url);
                
                // Note: The API should return a 404 if not found, caught below
                setExercise(response.data);
            } catch (err) {
                // Handle 404 errors specifically from the server if exercise name is wrong
                if (err.response && err.response.status === 404) {
                     setError("Exercise not found. Please check the URL or try generating a new workout.");
                } else {
                     setError("Failed to load exercise details due to a network error.");
                }
                console.error("Error fetching exercise details:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchExercise();
    }, [name]); // Re-fetch if the name parameter changes

    if (loading) return <div className="loading-message">Loading exercise details...</div>;
    if (error) return <div className="error-message">{error}</div>;
    if (!exercise) return <div className="not-found-message">Exercise data is unavailable.</div>;

    return (
        <div className="single-exercise-container">
            <div className="exercise-details">
                <h2>{exercise.name}</h2>
                {exercise.gifUrl && <img src={exercise.gifUrl} alt={exercise.name} />}
                <p><strong>Body Part:</strong> {exercise.bodyPart}</p>
                <p><strong>Target Muscle:</strong> {exercise.target}</p>
                <p><strong>Equipment:</strong> {exercise.equipment}</p>
                <p><strong>Difficulty:</strong> {exercise.difficulty}</p>
                <p><strong>Category:</strong> {exercise.category}</p>
                
                {exercise.description && (
                    <div className="section">
                        <h3>Description</h3>
                        <p>{exercise.description}</p>
                    </div>
                )}
                
                {exercise.instructions && (
                    <div className="section">
                        <h3>Instructions</h3>
                        <ul>
                            {exercise.instructions.map((instruction, index) => (
                                <li key={index}>{instruction}</li>
                            ))}
                        </ul>
                    </div>
                )}
                
                {exercise.secondaryMuscles && (
                    <div className="section">
                        <h3>Secondary Muscles</h3>
                        <p>{exercise.secondaryMuscles.join(', ')}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default SingleExercisePage;
