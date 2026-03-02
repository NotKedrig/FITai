import { apiRequest } from './client';

export async function getExercises(token, search) {
  const params = [];
  if (search && search.trim()) {
    params.push(`search=${encodeURIComponent(search.trim())}`);
  }
  const query = params.length ? `?${params.join('&')}` : '';

  return apiRequest(`/exercises${query}`, {
    method: 'GET',
    token,
  });
}

