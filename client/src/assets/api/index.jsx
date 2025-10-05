import axios from 'axios';

// API_BASE_URL: prefer the local backend when running on localhost/LAN for
// developer workflows; otherwise use the hosted Render URL for production.
export const API_BASE_URL = (() => {
    if (typeof window !== 'undefined') {
        try {
            const host = window.location.hostname || '';
            // If running locally (dev) or on a LAN IP, target the local Flask server
            if (host === 'localhost' || host === '127.0.0.1' || host.startsWith('192.')) {
                // Default Flask dev server port used in this project is 5000
                return `${window.location.protocol}//${host}:5000`;
            }
        } catch (e) {
            // fall through to production default
        }
    }
    return 'https://btm-workout.onrender.com';
})();

// ===================================
// GETTERS (Data Retrieval)
// ===================================

// 1. Get List of Body Parts (for dropdown)
export const getBodyParts = async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/body_parts_list`);
    return response.data; 
};

// 2. Get List of Equipment
export const getEquipmentList = async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/equipment_list`);
    return response.data; 
};

// 3. Get List of All Exercises
export const getExercisesList = async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/exercises_list`);
    return response.data;
};

// 4. Get List of Difficulties
export const getDifficulties = async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/difficulties`);
    return response.data;
};

// 5. Get Single Exercise Details
export const getExerciseDetails = async (name) => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/exercise/${name}`);
    return response.data;
};


// ===================================
// WORKOUT & UTILITY
// ===================================

// 6. Generate a Random Workout (for the main page)
export const generateWorkout = async (bodyPart, numExercises) => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/get_random_exercises`, {
        bodyPart: bodyPart,
        num_exercises: numExercises // use snake_case consistently
    });
    return response.data;
};

// 7. Refresh/Seed Database (for the tile)
export const refreshDatabase = async () => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/refresh_db`);
    return response.data;
};


// ===================================
// MANAGEMENT (POST/DELETE Operations)
// ===================================

// 8. Insert New Exercise (for Add Exercises Page)
export const insertExercise = async (exerciseData) => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/insert_exercise`, exerciseData);
    return response.data;
};

// 9. Add New Body Part (for Management Page)
export const addBodyPart = async (name) => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/add_body_part`, { name });
    return response.data;
};

// 10. Delete Body Part
export const deleteBodyPart = async (name) => {
    const response = await axios.delete(`${API_BASE_URL}/api/v1/delete_body_part/${name}`);
    return response.data;
};

// 11. Add New Equipment
export const addEquipment = async (name) => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/add_equipment`, { name });
    return response.data;
};

// 12. Delete Equipment
export const deleteEquipment = async (name) => {
    const response = await axios.delete(`${API_BASE_URL}/api/v1/delete_equipment/${name}`);
    return response.data;
};

// 13. Delete Exercise
export const deleteExercise = async (name) => {
    const response = await axios.delete(`${API_BASE_URL}/api/v1/delete_exercise/${name}`);
    return response.data;
};
