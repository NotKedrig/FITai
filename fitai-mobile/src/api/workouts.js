import { apiRequest } from './client';

export async function getWorkouts(token) {
  return apiRequest('/workouts', {
    method: 'GET',
    token,
  });
}

export async function startWorkout(token, name, notes) {
  return apiRequest('/workouts', {
    method: 'POST',
    token,
    body: {
      name,
      notes,
    },
  });
}

export async function endWorkout(token, workoutId) {
  return apiRequest(`/workouts/${workoutId}/end`, {
    method: 'POST',
    token,
  });
}

