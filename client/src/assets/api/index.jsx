import axios from 'axios';

// API_BASE_URL: prefer the local backend when running on localhost/LAN for
// developer workflows; otherwise use the hosted Render URL for production.
// In dev: use /api (proxied by Vite to localhost:5000)
// In prod: use the full Onrender URL
const BASE_URL = import.meta.env.VITE_API_URL 
    || (import.meta.env.PROD ? 'https://btm-workout.onrender.com' : '/api');

// ===================================
// GETTERS (Data Retrieval)
// ===================================

// 1. Get List of Body Parts (for dropdown)
export const getBodyParts = async () => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.get(`${BASE_URL}/v1/body_parts_list`, {
        headers
    });
    return response.data; 
};

// 2. Get List of Equipment
export const getEquipmentList = async () => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.get(`${BASE_URL}/v1/equipment_list`, {
        headers
    });
    return response.data; 
};

// 3. Get List of All Exercises
export const getExercisesList = async () => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.get(`${BASE_URL}/v1/exercises_list`, {
        headers
    });
    return response.data;
};

// 4. Get List of Difficulties
export const getDifficulties = async () => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.get(`${BASE_URL}/v1/difficulties`, {
        headers
    });
    return response.data;
};

// 5. Get Single Exercise Details
export const getExerciseDetails = async (name) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.get(`${BASE_URL}/v1/exercise/${name}`, {
        headers
    });
    return response.data;
};


// ===================================
// WORKOUT & UTILITY
// ===================================

// 6. Generate a Random Workout (for the main page)
export const generateWorkout = async (bodyPart, numExercises, equipment = null) => {
    const requestData = {
        bodyPart: bodyPart,
        num_exercises: numExercises // use snake_case consistently
    };
    
    // Only add equipment to request if it's specified
    if (equipment) {
        requestData.equipment = equipment;
    }
    
    const response = await axios.post(`${BASE_URL}/v1/get_random_exercises`, requestData);
    return response.data;
};

// 7. Refresh/Seed Database (for the tile)
export const refreshDatabase = async () => {
    const response = await axios.post(`${BASE_URL}/v1/refresh_db`);
    return response.data;
};


// ===================================
// MANAGEMENT (POST/DELETE Operations)
// ===================================

// 8. Insert New Exercise (for Add Exercises Page)
export const insertExercise = async (exerciseData) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.post(`${BASE_URL}/v1/insert_exercise`, exerciseData, {
        headers
    });
    return response.data;
};

// 9. Add New Body Part (for Management Page)
export const addBodyPart = async (name) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.post(`${BASE_URL}/v1/add_body_part`, { name }, {
        headers
    });
    return response.data;
};

// 10. Delete Body Part
export const deleteBodyPart = async (name) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.delete(`${BASE_URL}/v1/delete_body_part/${name}`, {
        headers
    });
    return response.data;
};

// 11. Add New Equipment
export const addEquipment = async (name) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.post(`${BASE_URL}/v1/add_equipment`, { name }, {
        headers
    });
    return response.data;
};

// 12. Delete Equipment
export const deleteEquipment = async (name) => {
    // Get the token from localStorage
    const token = localStorage.getItem('authToken');
    
    const headers = {};
    
    // Add Authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.delete(`${BASE_URL}/v1/delete_equipment/${name}`, {
        headers
    });
    return response.data;
};

// 13. Delete Exercise
export const deleteExercise = async (name) => {
    const response = await axios.delete(`${BASE_URL}/v1/delete_exercise/${name}`);
    return response.data;
};
