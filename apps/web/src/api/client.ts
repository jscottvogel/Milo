/**
 * API Client for Milo Web App
 * Automatically injects the authentication token and base URL.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
// Default to the PoC dev tenant token for now if none is in local storage.
// In a real implementation with Cognito, this would come from the auth provider.
const DEFAULT_DEV_TOKEN = 'dev_00000000-0000-0000-0000-000000000001';

export function getToken(): string {
  return localStorage.getItem('milo_token') || DEFAULT_DEV_TOKEN;
}

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

export async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const token = getToken();
  
  const headers = new Headers(options.headers);
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Handle query params
  let url = `${API_BASE_URL}${endpoint}`;
  if (options.params) {
    const urlObj = new URL(url);
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined) {
        urlObj.searchParams.append(key, String(value));
      }
    });
    url = urlObj.toString();
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.error && errorData.error.message) {
        errorMessage = errorData.error.message;
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (e) {
      // Not JSON
      const text = await response.text();
      if (text) errorMessage = text;
    }
    throw new Error(errorMessage);
  }

  // Return null for 204 No Content
  if (response.status === 204) {
    return null as any;
  }

  return response.json();
}
