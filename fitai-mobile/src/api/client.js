import { API_URL } from '../config/api';

export async function apiRequest(
  path,
  { method = 'GET', body, token, headers: customHeaders = {} } = {}
) {
  const url = `${API_URL}${path}`;

  const finalHeaders = {
    Accept: 'application/json',
    ...customHeaders,
  };

  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  const isUrlSearchParamsObject =
    body &&
    typeof body === 'object' &&
    typeof body.append === 'function' &&
    typeof body.toString === 'function';
  const isUrlSearchParamsInstance =
    typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams;
  const isUrlEncodedBody =
    isUrlSearchParamsObject ||
    isUrlSearchParamsInstance ||
    finalHeaders['Content-Type'] === 'application/x-www-form-urlencoded';

  if (body && !isFormData && !isUrlEncodedBody && !finalHeaders['Content-Type']) {
    finalHeaders['Content-Type'] = 'application/json';
  }

  if (token) {
    finalHeaders.Authorization = `Bearer ${token}`;
  }

  const headers = finalHeaders;

  console.log('API REQUEST URL:', url);
  console.log('API REQUEST METHOD:', method);
  console.log('API REQUEST HEADERS:', headers);
  console.log('API REQUEST BODY TYPE:', typeof body);
  console.log('API REQUEST BODY RAW:', body);

  const options = {
    method,
    headers,
  };

  if (body !== undefined && body !== null) {
    if (isFormData) {
      options.body = body;
    } else if (isUrlEncodedBody) {
      if (isUrlSearchParamsObject || isUrlSearchParamsInstance) {
        options.body = body.toString();
      } else if (typeof body === 'string') {
        options.body = body;
      } else {
        options.body = String(body);
      }
    } else if (typeof body === 'string') {
      options.body = body;
    } else {
      options.body = JSON.stringify(body);
    }
  }

  try {
    const response = await fetch(url, options);

    console.log('API RESPONSE STATUS:', response.status);
    console.log('API RESPONSE OK:', response.ok);
    try {
      console.log(
        'API RESPONSE HEADERS:',
        Object.fromEntries(response.headers.entries())
      );
    } catch (headersError) {
      console.log('API RESPONSE HEADERS: <unavailable>', headersError);
    }

    let data = null;
    try {
      const cloned = response.clone();
      data = await cloned.json();
      console.log('API RESPONSE BODY JSON:', data);
    } catch (parseError) {
      console.log('API RESPONSE BODY NOT JSON', parseError);
    }

    if (!response.ok) {
      let message =
        (data && (data.detail || data.message || data.error)) ||
        `HTTP ${response.status}`;

      if (typeof message !== 'string') {
        try {
          message = JSON.stringify(message);
        } catch {
          message = `HTTP ${response.status}`;
        }
      }

      const error = new Error(message);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (error) {
    console.log('FETCH ERROR OBJECT:', error);
    console.log('FETCH ERROR MESSAGE:', error && error.message);
    console.log('FETCH ERROR STACK:', error && error.stack);

    if (error instanceof TypeError && error.message === 'Network request failed') {
      throw new Error('Network error. Please check your connection and try again.');
    }
    throw error;
  }
}

