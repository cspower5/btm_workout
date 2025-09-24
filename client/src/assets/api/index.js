export async function generateWorkout(bodyPart, numExercises) {
  const response = await fetch('/api/get_random_exercises', {
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
    throw new Error('Failed to generate workout.');
  }
  return response.json();
}

export async function getBodyParts() {
  const response = await fetch('/api/body_parts_list');
  if (!response.ok) {
    throw new Error('Failed to fetch body parts');
  }
  const data = await response.json();
  // Your API returns an array of objects like [{"name": "Chest"}, ...], so we map it to an array of strings
  return data.map(item => item.name);
}

export async function refreshDatabase() {
  const response = await fetch('/api/refresh_db', {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to refresh database');
  }
  return response.json();
}
