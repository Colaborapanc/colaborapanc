import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_CONFIG, buildURL } from '../config/api';

const AUTH_TOKEN_KEY = 'userToken';
const authListeners = new Set();
const unauthorizedListeners = new Set();
const isLegacySessionToken = (token) => typeof token === 'string' && token.startsWith('session:');

const isFormData = (value) => typeof FormData !== 'undefined' && value instanceof FormData;

const parseResponse = async (response, meta) => {
  if (response.status === 204) return null;

  const contentType = response.headers.get('content-type') || '';
  let payload;
  if (contentType.includes('application/json')) {
    const raw = await response.text();
    payload = raw ? JSON.parse(raw) : null;
  } else {
    payload = await response.text();
  }

  if (!response.ok) {
    let detail = 'Erro na API';
    if (typeof payload === 'string') {
      detail = payload;
    } else if (payload?.detail || payload?.erro) {
      detail = payload?.detail || payload?.erro;
    } else if (payload && typeof payload === 'object') {
      const [firstField] = Object.keys(payload);
      const firstValue = payload[firstField];
      const firstMessage = Array.isArray(firstValue) ? firstValue[0] : firstValue;
      detail = firstField && firstMessage ? `${firstField}: ${firstMessage}` : 'Erro na API';
    }
    const error = new Error(detail);
    error.status = response.status;
    error.payload = payload;
    error.url = meta.url;
    error.method = meta.method;
    console.warn(`[HTTP] ${meta.method} ${meta.url} -> ${response.status}`, payload);
    throw error;
  }

  return payload;
};

export const getAuthToken = async () => AsyncStorage.getItem(AUTH_TOKEN_KEY);

export const setAuthToken = async (token) => {
  if (!token) {
    await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
    authListeners.forEach((listener) => listener(null));
    return;
  }
  await AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
  authListeners.forEach((listener) => listener(token));
};

export const subscribeAuthToken = (listener) => {
  authListeners.add(listener);
  return () => authListeners.delete(listener);
};

export const subscribeUnauthorized = (listener) => {
  unauthorizedListeners.add(listener);
  return () => unauthorizedListeners.delete(listener);
};

export async function httpRequest(pathOrUrl, options = {}) {
  const token = await getAuthToken();
  const url = buildURL(pathOrUrl);
  const method = options.method || 'GET';

  const headers = {
    ...API_CONFIG.headers,
    ...(options.headers || {}),
  };

  let normalizedBody = options.body;
  const hasBody = normalizedBody !== undefined && normalizedBody !== null;
  if (hasBody && !isFormData(normalizedBody)) {
    if (typeof normalizedBody !== 'string') {
      normalizedBody = JSON.stringify(normalizedBody);
    }
    if (!headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
  }
  if (isFormData(normalizedBody) && headers['Content-Type']) {
    delete headers['Content-Type'];
  }

  if (token && !isLegacySessionToken(token) && !headers.Authorization) {
    headers.Authorization = `Token ${token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_CONFIG.timeout);

  try {
    const response = await fetch(url, {
      ...options,
      method,
      headers,
      body: normalizedBody,
      credentials: 'include',
      signal: controller.signal,
    });
    const payload = await parseResponse(response, { url, method });
    return payload;
  } catch (error) {
    if (error?.status === 401) {
      await setAuthToken(null);
      unauthorizedListeners.forEach((listener) => listener(error));
    }
    if (error.name === 'AbortError') {
      const timeoutError = new Error(`Timeout na requisição (${API_CONFIG.timeout}ms)`);
      timeoutError.url = url;
      timeoutError.method = method;
      timeoutError.code = 'TIMEOUT';
      throw timeoutError;
    }

    if (error?.message?.includes('Network request failed')) {
      error.code = 'NETWORK';
    }

    console.warn(`[HTTP] ${method} ${url} falhou`, error?.message || error);
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const httpGet = (path, options = {}) => httpRequest(path, { ...options, method: 'GET' });
export const httpPost = (path, body, options = {}) => httpRequest(path, { ...options, method: 'POST', body });
export const httpPut = (path, body, options = {}) => httpRequest(path, { ...options, method: 'PUT', body });
export const httpPatch = (path, body, options = {}) => httpRequest(path, { ...options, method: 'PATCH', body });
export const httpDelete = (path, options = {}) => httpRequest(path, { ...options, method: 'DELETE' });
