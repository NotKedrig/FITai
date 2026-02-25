import { apiRequest } from './client';

export async function register(email, username, password) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: {
      email,
      username,
      password,
    },
  });
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.append('email', email);
  body.append('password', password);

  return apiRequest('/auth/login', {
    method: 'POST',
    body,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
}

