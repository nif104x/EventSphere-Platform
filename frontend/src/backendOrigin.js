/** Base URL for FastAPI (Jinja pages, non-proxied HTML). Trailing slash stripped. */
export function getBackendOrigin() {
  return (import.meta.env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
}
