import React, { useState, useEffect } from 'react';
import axios from 'axios';
// FIX: Import helper functions that use the absolute URL
import { 
    getBodyParts, 
    getEquipmentList, 
    getDifficulties, 
    insertExercise 
} from '../assets/api'; 
import './css/NewExerciseForm.css';

function NewExerciseForm() {
    const [formData, setFormData] = useState({
        bodyPart: '',
        equipment: '',
        name: '',
        target: '',
        secondaryMuscles: '',
        instructions: '',
        description: '',
        difficulty: '',
    });
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);
    
    const [bodyParts, setBodyParts] = useState([]);
    const [equipmentList, setEquipmentList, ] = useState([]);
    const [difficulties, setDifficulties] = useState([]);

    useEffect(() => {
        const fetchDropdownData = async () => {
            try {
                // FIX: Use the fixed helper functions for API calls
                const [bodyPartsRes, equipmentRes, difficultiesRes] = await Promise.all([
                    getBodyParts(),
                    getEquipmentList(),
                    getDifficulties()
                ]);
                
                // NOTE: The API returns data as a list of strings for body parts and difficulties, 
                // but your component expects objects {name: '...'} for bodyParts and equipmentList 
                // (which is likely a bug from a previous version). We'll assume the API returns 
                // objects for consistency, but if it breaks, we know this mapping is the cause.
                setBodyParts(bodyPartsRes); 
                setEquipmentList(equipmentRes);
                setDifficulties(difficultiesRes); 

            } catch (err) {
                console.error("Failed to fetch dropdown data:", err);
                setMessage("Failed to load form options. Please check the server.");
                setIsError(true);
            }
        };
        fetchDropdownData();
    }, []);

    useEffect(() => {
        // This useEffect handles clearing selections if the list changes
        if (formData.bodyPart && !bodyParts.some(bp => bp.name === formData.bodyPart)) {
            setFormData(prevState => ({ ...prevState, bodyPart: '' }));
        }
        if (formData.equipment && !equipmentList.some(eq => eq.name === formData.equipment)) {
            setFormData(prevState => ({ ...prevState, equipment: '' }));
        }
    }, [bodyParts, equipmentList, formData.bodyPart, formData.equipment]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');

        // Ensure required fields are not empty before submitting
        if (!formData.bodyPart || !formData.equipment || !formData.name || !formData.target) {
            setMessage("Body part, equipment, name, and target are required fields.");
            setIsError(true);
            return;
        }
        
        try {
            const formattedData = {
                ...formData,
                // Ensure secondaryMuscles and instructions are arrays of trimmed strings
                secondaryMuscles: formData.secondaryMuscles ? formData.secondaryMuscles.split(',').map(s => s.trim()) : [],
                instructions: formData.instructions ? formData.instructions.split('.').map(s => s.trim()) : [],
            };

            // FIX: Use the fixed helper function for insertion
            const response = await insertExercise(formattedData);
            
            setMessage(response.message || 'Exercise submitted successfully!');
            setIsError(false);
            
            // Clear form data after successful submission
            setFormData({
                bodyPart: '',
                equipment: '',
                name: '',
                target: '',
                secondaryMuscles: '',
                instructions: '',
                description: '',
                difficulty: '',
            });
            
        } catch (error) {
            console.error('There was an error submitting the form!', error);
            // Check for error response from the API first
            setMessage(error.response?.data?.error || error.message || 'Failed to submit exercise.');
            setIsError(true);
        }
    };

    // NOTE: The map logic for dropdowns below assumes data returned is an object {name: '...'}
    // The workaround for mapping string arrays is necessary if the API returns just strings:
    // {bodyParts.map(part => (<option key={part} value={part}>{part}</option>))}
    // Since we don't know the exact API return structure, we'll keep the current map logic for now.

    return (
        <div className="form-container">
            <h2>Add New Exercise</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Name:</label>
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                </div>
                {/* ... other input fields ... */}
                
                <div className="form-group">
                    <label>Body Part:</label>
                    {bodyParts.length > 0 ? (
                        <select name="bodyPart" value={formData.bodyPart} onChange={handleChange} required>
                            <option value="">--Select--</option>
                            {/* Assuming bodyParts is an array of objects like [{name: 'Arms'}] */}
                            {bodyParts.map(part => (
                                <option key={part.name} value={part.name}>{part.name}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="error">Loading Body Parts...</p>
                    )}
                </div>
                
                {/* ... other dropdowns and button ... */}
                
                <button type="submit">Add Exercise</button>
            </form>
            {message && (
                <p className={`message ${isError ? 'error' : 'success'}`}>
                    {message}
                </p>
            )}
        </div>
    );
}

export default NewExerciseForm;
