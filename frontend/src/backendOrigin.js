import { DEFAULT_API_ORIGIN } from './apiOrigin';

/** Base URL for FastAPI (Jinja pages, non-proxied HTML). Trailing slash stripped. */
export function getBackendOrigin() {
  const fallback = import.meta.env.DEV ? 'http://127.0.0.1:8000' : DEFAULT_API_ORIGIN;
  return (import.meta.env.VITE_BACKEND_ORIGIN || fallback).replace(/\/$/, '');
}
