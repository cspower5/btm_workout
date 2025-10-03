import React, { useState } from 'react';
import axios from 'axios';
import './css/NewExerciseForm.css'; // We'll reuse this style sheet

// FIX: Change prop from 'apiEndpoint' to 'apiFunction'
function AddFormComponent({ title, apiFunction, placeholder }) {
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');

        // Ensure the input field has data
        if (!name) {
            setMessage(`Please enter a value for ${title}.`);
            setIsError(true);
            return;
        }

        try {
            // Call the provided helper with the raw name string. Helpers expect a
            // single `name` argument (e.g. addBodyPart(name)).
            const response = await apiFunction(name);
            
            setMessage(response.message);
            setIsError(false);
            setName(''); // Clear the input field on success
        } catch (error) {
            console.error('There was an error submitting the form!', error.response || error);
            // Check for error response from the API first
            setMessage(error.response?.data?.error || error.message || 'Failed to add item.');
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
