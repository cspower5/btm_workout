import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import './css/SingleExercisePage.css';

function SingleExercisePage() {
    const { name } = useParams();
    const [exercise, setExercise] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchExercise = async () => {
            try {
                const response = await axios.get(`/api/exercise/${name}`);
                setExercise(response.data);
            } catch (err) {
                setError("Failed to load exercise details.");
                console.error("Error fetching exercise details:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchExercise();
    }, [name]); // Re-fetch if the name parameter changes

    if (loading) return <div className="loading-message">Loading exercise details...</div>;
    if (error) return <div className="error-message">{error}</div>;
    if (!exercise) return <div className="not-found-message">Exercise not found.</div>;

    return (
        <div className="single-exercise-container">
            <div className="exercise-details">
                <h2>{exercise.name}</h2>
                <img src={exercise.gifUrl} alt={exercise.name} />
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
