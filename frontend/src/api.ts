import axios, { AxiosError, AxiosInstance } from 'axios';

// Create an axios instance with default api settings
const api = axios.create({
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

export default api;
