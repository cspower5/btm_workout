import React, { useState, useEffect } from 'react';
import axios from 'axios';
// FIX: Import helper functions that use the absolute URL
import { 
    getBodyParts, 
    getEquipmentList, 
    getDifficulties, 
    insertExercise 
} from '../assets/api/index.jsx'; 
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
    const [equipmentList, setEquipmentList] = useState([]);
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
                
                // Helpers may return arrays or objects. Normalize to arrays of strings.
                const normalize = (val) => {
                    if (!val) return [];
                    if (Array.isArray(val)) return val.map(x => (typeof x === 'string' ? x : x.name || x));
                    if (val && Array.isArray(val.body_parts)) return val.body_parts;
                    if (val && Array.isArray(val.equipment_list)) return val.equipment_list;
                    if (val && Array.isArray(val.difficulties)) return val.difficulties;
                    return [];
                };

                setBodyParts(normalize(bodyPartsRes));
                setEquipmentList(normalize(equipmentRes));
                setDifficulties(normalize(difficultiesRes));

            } catch (err) {
                console.error("Failed to fetch dropdown data:", err);
                setMessage("Failed to load form options. Please check the server.");
                setIsError(true);
            }
        };
        fetchDropdownData();
    }, []);

    // FIX: Update the cleanup useEffect to use simple string comparison
    useEffect(() => {
        // This useEffect handles clearing selections if the list changes
        // It now checks if the selected string is IN the list of available strings.
        if (formData.bodyPart && !bodyParts.includes(formData.bodyPart)) {
            setFormData(prevState => ({ ...prevState, bodyPart: '' }));
        }
        if (formData.equipment && !equipmentList.includes(formData.equipment)) {
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

    // Note: The map logic below relies on the component receiving string arrays
    return (
        <div className="form-container">
            <h2>Add New Exercise</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Name:</label>
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>Target:</label>
                    <input type="text" name="target" value={formData.target} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>Secondary Muscles (comma-separated):</label>
                    <input type="text" name="secondaryMuscles" value={formData.secondaryMuscles} onChange={handleChange} />
                </div>
                <div className="form-group">
                    <label>Instructions (period-separated):</label>
                    <textarea name="instructions" value={formData.instructions} onChange={handleChange} />
                </div>
                <div className="form-group">
                    <label>Description:</label>
                    <textarea name="description" value={formData.description} onChange={handleChange} />
                </div>
                
                <div className="form-group">
                    <label>Body Part:</label>
                    {bodyParts.length > 0 ? (
                        <select name="bodyPart" value={formData.bodyPart} onChange={handleChange} required>
                            <option value="">--Select--</option>
                            {/* The mapping logic is now correct for string arrays */}
                            {bodyParts.map((part, index) => (
                                <option key={index} value={part}>{part}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="error">Loading Body Parts...</p>
                    )}
                </div>
                
                <div className="form-group">
                    <label>Equipment:</label>
                    {equipmentList.length > 0 ? (
                        <select name="equipment" value={formData.equipment} onChange={handleChange} required>
                            <option value="">--Select--</option>
                            {equipmentList.map((eq, index) => (
                                <option key={index} value={eq}>{eq}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="error">Loading Equipment...</p>
                    )}
                </div>
                
                <div className="form-group">
                    <label>Difficulty:</label>
                    <select name="difficulty" value={formData.difficulty} onChange={handleChange} required>
                        <option value="">--Select--</option>
                        {difficulties.map(diff => (
                            // Assuming difficulties returns a simple string array 
                            <option key={diff} value={diff}>{diff}</option>
                        ))}
                    </select>
                </div>
                
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
