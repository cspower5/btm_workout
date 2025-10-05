import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from './api/index.jsx';
import './css/ManageItemsPage.css';

function ManageItemsPage({ title, fetchUrl, deleteUrl }) {
    const [items, setItems] = useState([]);
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);

    const fetchItems = async () => {
        try {
            // If the provided fetchUrl is a relative path (starts with '/'),
            // prefix it with the absolute API base so requests go to the
            // configured backend (Render) instead of the origin the app
            // is served from.
            const fullFetchUrl = fetchUrl.startsWith('/') ? `${API_BASE_URL}${fetchUrl}` : fetchUrl;
            const response = await axios.get(fullFetchUrl);
            // Ensure items is always an array of simple names or objects with `name`
            const data = response.data || [];
            // Some endpoints return objects (e.g., exercises) while others return strings.
            // Normalize to an array where each element is either the string name or
            // an object { name: <string>, ... } so rendering and deletion work.
            const normalized = data.map((it) => {
                if (it && typeof it === 'object') {
                    // backend may return { name } or { exercise_name } or full exercise docs
                    return it.name || it.exercise_name || it.exercise_name || it;
                }
                return it;
            });
            setItems(normalized);
            setMessage('');
            setIsError(false);
        } catch (error) {
            setMessage('Failed to fetch items.');
            setIsError(true);
        }
    };

    const handleDelete = async (maybeItem) => {
        setMessage('');
        setIsError(false);
        // Accept either the name string or an object containing the name
        const name = (maybeItem && typeof maybeItem === 'object') ? (maybeItem.name || maybeItem.exercise_name || maybeItem) : maybeItem;
        if (window.confirm(`Are you sure you want to delete '${name}'?`)) {
            const encodedName = encodeURIComponent(name);
            const urlToDelete = deleteUrl.startsWith('/') ? `${API_BASE_URL}${deleteUrl}` : deleteUrl;
            const fullDeleteUrl = `${urlToDelete}/${encodedName}`;
            
            // This line will show the URL being sent to the backend
            console.log("Attempting to delete with URL:", fullDeleteUrl);

            try {
                const response = await axios.delete(fullDeleteUrl);
                setMessage(response.data.message);
                setIsError(false);
                // Remove the item from state regardless of whether it was stored as
                // a plain string or an object with a `name` property.
                setItems(items.filter((item) => {
                    if (item && typeof item === 'object') return (item.name || item.exercise_name || item) !== name;
                    return item !== name;
                }));
            } catch (error) {
                setMessage(error.response.data.error || 'Failed to delete item.');
                setIsError(true);
            }
        }
    };

    useEffect(() => {
        fetchItems();
    }, [fetchUrl]);

    return (
        <div className="manage-container">
            <h2>Manage {title}</h2>
            {message && (
                <p className={`message ${isError ? 'error' : 'success'}`}>
                    {message}
                </p>
            )}
            <ul className="item-list">
                {items.length > 0 ? (
                    items.map((item, index) => (
                        <li key={index} className="item-list-item">
                            <span>{item.name || item}</span>
                            <button onClick={() => handleDelete(item.name || item)}>Delete</button>
                        </li>
                    ))
                ) : (
                    <p>No items found.</p>
                )}
            </ul>
        </div>
    );
}

export default ManageItemsPage;
