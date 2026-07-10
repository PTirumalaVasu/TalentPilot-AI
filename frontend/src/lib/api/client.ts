import axios from 'axios';

/**
 * Shared axios instance for the whole app. `withCredentials: true` is required
 * on every request so the backend's HttpOnly session cookie (Story 1.2) is
 * sent/accepted across the Vite dev-server (:5173) -> FastAPI (:8000) origin
 * pair (backend's CORS `allow_credentials=True`, see backend/app/main.py).
 */
export const apiClient = axios.create({
  withCredentials: true,
});

type UnauthorizedHandler = () => void;

let unauthorizedHandler: UnauthorizedHandler | null = null;

/**
 * Registered by AuthProvider so a 401 from *any* request (not just the one
 * a protected page happened to make) can flip shared auth state to
 * unauthenticated. This is the frontend's mirror of Story 1.6's backend
 * "every protected router 401s" guarantee - it catches mid-session expiry,
 * not just the initial route-guard check.
 */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      unauthorizedHandler?.();
    }
    return Promise.reject(error);
  }
);
