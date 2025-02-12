import axios from 'axios';

// Create an axios instance with default api settings
const api = axios.create({
  baseURL: import.meta.env.VITE_API_V1_STR,
  withCredentials: true, // Include JWT access cookie with requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Handle expired sessions with response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login page
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export default api;
