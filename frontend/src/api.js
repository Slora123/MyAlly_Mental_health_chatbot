/**
 * api.js
 * Central place to configure the backend API base URL.
 *
 * In production (Vercel): VITE_API_BASE_URL is set to the HF Spaces URL.
 * In local dev: empty string — Vite proxy handles /api and /chat.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Wrapper around fetch that automatically prepends the backend base URL.
 * Drop-in replacement: use apiFetch('/chat', options) instead of fetch('/chat', options)
 */
export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  return fetch(url, options);
}
