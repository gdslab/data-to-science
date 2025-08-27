import axios, { AxiosError, AxiosInstance } from 'axios';

// Create an axios instance with default api settings
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_V1_STR,
  withCredentials: true, // Include JWT access cookie with requests
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve();
  });
  failedQueue = [];
};

// Handle expired sessions with response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const originalRequest = (error.config || {}) as any;

    // Only try refresh once, and never refresh the refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/auth/refresh-token'
    ) {
      if (isRefreshing) {
        // Queue up this request until the refresh finishes
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: () => resolve(api(originalRequest)),
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      return new Promise((resolve, reject) => {
        api
          .post('/auth/refresh-token')
          .then(() => {
            processQueue(null);
            resolve(api(originalRequest));
          })
          .catch((err) => {
            processQueue(err);
            window.location.href = '/auth/login';
            reject(err);
          })
          .finally(() => {
            isRefreshing = false;
          });
      });
    }

    return Promise.reject(error);
  }
);

// Export utility function to refresh tokens for uploads
let tokenCheckPromise: Promise<boolean> | null = null;
let lastTokenCheckTs = 0;
const TOKEN_CHECK_COOLDOWN_MS = 10000; // 10s cooldown to avoid spamming

export async function refreshTokenIfNeeded(): Promise<boolean> {
  const now = Date.now();
  if (tokenCheckPromise) return tokenCheckPromise;
  if (now - lastTokenCheckTs < TOKEN_CHECK_COOLDOWN_MS) return true;

  tokenCheckPromise = (async () => {
    try {
      // Simple authenticated request; interceptor will refresh on 401
      await api.post('/auth/test-token');
      return true;
    } catch (_err) {
      // Retry once after interceptor attempted refresh
      try {
        await api.post('/auth/test-token');
        return true;
      } catch (_err2) {
        // Interceptor should redirect on failure; signal false for callers
        return false;
      }
    } finally {
      lastTokenCheckTs = Date.now();
      tokenCheckPromise = null;
    }
  })();

  return tokenCheckPromise;
}

export default api;
