// Get the base URL from the environment variable (e.g., https://your-render-api.onrender.com)
const BASE_URL = import.meta.env.VITE_API_URL; 

if (!BASE_URL) {
  // Add a defensive check just in case the variable is missing
  console.error("CRITICAL ERROR: VITE_API_URL is missing. API calls will fail.");
}

export async function generateWorkout(bodyPart, numExercises) {
  // FIX: Prepend the BASE_URL to the API path
  const response = await fetch(`${BASE_URL}/api/get_random_exercises`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      bodyPart: bodyPart,
      numExercises: numExercises,
    }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown server error' }));
    throw new Error(errorData.error || `Failed to generate workout with status ${response.status}.`);
  }
  return response.json();
}

export async function getBodyParts() {
  // FIX: Prepend the BASE_URL to the API path
  const response = await fetch(`${BASE_URL}/api/body_parts_list`);
  if (!response.ok) {
    throw new Error('Failed to fetch body parts');
  }
  const data = await response.json();
  // Your API returns an array of objects like [{"name": "Chest"}, ...]
  return data.map(item => item.name);
}

export async function refreshDatabase() {
  // FIX: Prepend the BASE_URL to the API path
  const response = await fetch(`${BASE_URL}/api/refresh_db`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to refresh database');
  }
  return response.json();
}
