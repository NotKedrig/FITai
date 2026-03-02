import { apiRequest } from './client';

export async function logSet(token, workoutId, exerciseId, weightKg, reps, rpe, isWarmup) {
  return apiRequest(`/workouts/${workoutId}/sets`, {
    method: 'POST',
    token,
    body: {
      exercise_id: exerciseId,
      weight_kg: weightKg,
      reps,
      rpe,
      is_warmup: isWarmup,
    },
  });
}

export async function deleteSet(token, setId) {
  return apiRequest(`/sets/${setId}`, {
    method: 'DELETE',
    token,
  });
}

