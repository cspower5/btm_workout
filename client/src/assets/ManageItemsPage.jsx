import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getExercisesList, getBodyParts, getEquipmentList, deleteBodyPart, deleteEquipment, deleteExercise } from './api/index.jsx';
import './css/ManageItemsPage.css';

function ManageItemsPage({ title, itemType }) {
    const [items, setItems] = useState([]);
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);

    const fetchItems = async () => {
        try {
            let data = [];
            
            // Use the appropriate API function based on itemType
            if (itemType === 'exercises') {
                data = await getExercisesList();
                console.log("Fetched exercises data:", data);
            } else if (itemType === 'body_parts') {
                data = await getBodyParts();
            } else if (itemType === 'equipment') {
                data = await getEquipmentList();
            }
            
            // For exercises, keep the full object to display index fields
            // For other items (body parts, equipment), normalize to simple names
            const normalized = data.map((it) => {
                if (itemType === 'exercises' && it && typeof it === 'object') {
                    // For exercises, keep the full object with all fields
                    return {
                        name: it.name || it.exercise_name,
                        bodyPart: it.bodyPart || it.body_part,
                        equipment: it.equipment,
                        // Keep the original object for reference
                        original: it
                    };
                } else if (it && typeof it === 'object') {
                    // For other endpoints, extract just the name
                    return it.name || it.exercise_name || it;
                }
                return it;
            });
            
            // Sort items alphabetically (Issue 2: Ascending alphabetical order)
            const sorted = normalized.sort((a, b) => {
                let nameA, nameB;
                if (itemType === 'exercises') {
                    // For exercises, sort by exercise name
                    nameA = (typeof a === 'object' ? a.name : a).toString().toLowerCase();
                    nameB = (typeof b === 'object' ? b.name : b).toString().toLowerCase();
                } else {
                    // For other items, use the existing logic
                    nameA = (typeof a === 'object' ? (a.name || a.exercise_name || a) : a).toString().toLowerCase();
                    nameB = (typeof b === 'object' ? (b.name || b.exercise_name || b) : b).toString().toLowerCase();
                }
                return nameA.localeCompare(nameB);
            });
            
            setItems(sorted);
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
        let name, displayName;
        if (maybeItem && typeof maybeItem === 'object') {
            name = maybeItem.name || maybeItem.exercise_name || maybeItem;
            // For exercises, create a descriptive display name
            if (maybeItem.bodyPart && maybeItem.equipment) {
                displayName = `${name} (${maybeItem.bodyPart}, ${maybeItem.equipment})`;
            } else {
                displayName = name;
            }
        } else {
            name = maybeItem;
            displayName = name;
        }
        
        if (window.confirm(`Are you sure you want to delete '${displayName}'?`)) {
            try {
                let response;
                
                // Use the appropriate API delete function based on itemType
                if (itemType === 'exercises') {
                    response = await deleteExercise(name);
                } else if (itemType === 'body_parts') {
                    response = await deleteBodyPart(name);
                } else if (itemType === 'equipment') {
                    response = await deleteEquipment(name);
                }
                
                setMessage(response.message);
                setIsError(false);
                // Remove the item from state regardless of whether it was stored as
                // a plain string or an object with a `name` property.
                setItems(items.filter((item) => {
                    if (item && typeof item === 'object') {
                        const itemName = item.name || item.exercise_name || item;
                        return itemName !== name;
                    }
                    return item !== name;
                }));
            } catch (error) {
                setMessage(error.response?.data?.error || error.message || 'Failed to delete item.');
                setIsError(true);
            }
        }
    };

    useEffect(() => {
        fetchItems();
    }, [itemType]);

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
                            {/* Show all three index fields for exercises */}
                            {item && typeof item === 'object' && item.bodyPart && item.equipment ? (
                                <div className="exercise-details">
                                    <div className="exercise-name">{item.name}</div>
                                    <div className="exercise-meta">
                                        <span className="body-part">{item.bodyPart}</span>
                                        <span className="equipment">{item.equipment}</span>
                                    </div>
                                </div>
                            ) : (
                                <span>{item.name || item}</span>
                            )}
                            <button onClick={() => handleDelete(item)}>Delete</button>
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
