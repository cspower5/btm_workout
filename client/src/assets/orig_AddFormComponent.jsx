import React, { useState } from 'react';
import axios from 'axios';
import './css/NewExerciseForm.css'; // We'll reuse this style sheet

function AddFormComponent({ title, apiEndpoint, placeholder }) {
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');

        try {
            const response = await axios.post(apiEndpoint, { name });
            setMessage(response.data.message);
            setIsError(false);
            setName(''); // Clear the input field on success
        } catch (error) {
            setMessage(error.response.data.error || 'Failed to add item.');
            setIsError(true);
        }
    };

    return (
        <div className="form-container">
            <h2>{title}</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>{title}:</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={placeholder}
                        required
                    />
                </div>
                <button type="submit">Add</button>
            </form>
            {message && (
                <p className={`message ${isError ? 'error' : 'success'}`}>
                    {message}
                </p>
            )}
        </div>
    );
}

export default AddFormComponent;
