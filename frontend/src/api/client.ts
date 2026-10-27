/**
 * Typed API Client for SmartHire 2.0 Backend
 * Secure token management (session-scoped), automatic JSON deserialization,
 * and standard error parsing without logging sensitive tokens or resume data.
 */

import type { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// In-memory token fallback if sessionStorage is unavailable
let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  inMemoryToken = token;
  try {
    if (token) {
      sessionStorage.setItem('smarthire_token', token);
    } else {
      sessionStorage.removeItem('smarthire_token');
    }
  } catch {
    // SessionStorage restricted/disabled (e.g. strict privacy mode)
  }
};

export const getAuthToken = (): string | null => {
  if (inMemoryToken) return inMemoryToken;
  try {
    const stored = sessionStorage.getItem('smarthire_token');
    if (stored) {
      inMemoryToken = stored;
      return stored;
    }
  } catch {
    // Ignore storage errors
  }
  return null;
};

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  let url = `${BASE_URL}${endpoint}`;

  if (options.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryStr = searchParams.toString();
    if (queryStr) {
      url += (url.includes('?') ? '&' : '?') + queryStr;
    }
  }

  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  // Add auth header if token is available and header not explicitly set
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Only set application/json if body is not FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Clear invalid/expired token and notify listeners
      setAuthToken(null);
      window.dispatchEvent(new CustomEvent('smarthire:unauthorized'));
    }

    if (!response.ok) {
      let errorPayload: ApiError = { status: response.status };
      try {
        const json = await response.json();
        errorPayload = {
          ...errorPayload,
          ...json,
          detail: json.detail || json.message || json.error,
        };
      } catch {
        errorPayload.detail = `Server error HTTP ${response.status}: ${response.statusText}`;
      }
      throw errorPayload;
    }

    // Parse JSON response
    return (await response.json()) as T;
  } catch (err) {
    if ((err as ApiError).status !== undefined) {
      throw err;
    }
    // Network error / offline
    throw {
      status: 0,
      detail: 'Unable to connect to SmartHire API server. Please ensure the backend is running.',
    } as ApiError;
  }
}
