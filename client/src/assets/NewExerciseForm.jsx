import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
                const [bodyPartsRes, equipmentRes, difficultiesRes] = await Promise.all([
                    axios.get('/api/body_parts_list'),
                    axios.get('/api/equipment_list'),
                    axios.get('/api/difficulties')
                ]);
                setBodyParts(bodyPartsRes.data);
                setEquipmentList(equipmentRes.data);
                setDifficulties(difficultiesRes.data);
            } catch (err) {
                console.error("Failed to fetch dropdown data:", err);
                setMessage("Failed to load form options. Please check the server.");
                setIsError(true);
            }
        };
        fetchDropdownData();
    }, []);

    useEffect(() => {
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
                secondaryMuscles: formData.secondaryMuscles.split(',').map(s => s.trim()),
                instructions: formData.instructions.split('.').map(s => s.trim()),
            };

            const response = await axios.post('/api/insert_exercise', formattedData);
            setMessage(response.data.message);
            setIsError(false);
            
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
            setMessage(error.response.data.error || 'Failed to submit exercise.');
            setIsError(true);
        }
    };

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
                            {bodyParts.map(part => (
                                <option key={part.name} value={part.name}>{part.name}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="error">Please add a body part before adding an exercise.</p>
                    )}
                </div>
                
                <div className="form-group">
                    <label>Equipment:</label>
                    {equipmentList.length > 0 ? (
                        <select name="equipment" value={formData.equipment} onChange={handleChange} required>
                            <option value="">--Select--</option>
                            {equipmentList.map(eq => (
                                <option key={eq.name} value={eq.name}>{eq.name}</option>
                            ))}
                        </select>
                    ) : (
                        <p className="error">Please add a piece of equipment before adding an exercise.</p>
                    )}
                </div>
                
                <div className="form-group">
                    <label>Difficulty:</label>
                    <select name="difficulty" value={formData.difficulty} onChange={handleChange} required>
                        <option value="">--Select--</option>
                        {difficulties.map(diff => (
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
