import axios from 'axios';
import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Navigate, useLocation } from 'react-router';

interface Login {
  username: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_approved: boolean;
  is_email_confirmed: boolean;
  is_superuser: boolean;
  pending_email: string | null;
  profile_url: string | null;
  api_access_token: string | null;
  created_at: string;
  last_login_at: string | null;
  last_activity_at: string | null;
  exts: string[];
}

const context: {
  user: User | null;
  login: (data: Login) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: () => Promise<void>;
} = {
  user: null,
  login: async () => {},
  logout: async () => {},
  updateProfile: async () => {},
};

const AuthContext = createContext(context);

export function AuthContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const userProfile = localStorage.getItem('userProfile');
    if (userProfile) {
      return JSON.parse(userProfile);
    }
    return null;
  });

  // When the api interceptor exhausts a token refresh, it dispatches
  // 'auth:session-expired' instead of forcing a redirect. Clear the cached
  // profile and user state so RequireAuth redirects protected routes while
  // public routes (e.g. /explore) keep rendering with anonymous data.
  useEffect(() => {
    function handleSessionExpired() {
      localStorage.removeItem('userProfile');
      setUser(null);
    }
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () =>
      window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, []);

  async function login(data: { username: string; password: string }) {
    await axios.post('/api/v1/auth/access-token', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      withCredentials: true,
    });
    const currentUser = await axios.get('/api/v1/users/current', {
      withCredentials: true,
    });
    if (currentUser) {
      localStorage.setItem('userProfile', JSON.stringify(currentUser.data));
      setUser(currentUser.data);
    }
  }

  async function logout() {
    localStorage.removeItem('userProfile');
    await axios
      .get('/api/v1/auth/remove-access-token', { withCredentials: true })
      .then(() => setUser(null));
  }

  async function updateProfile() {
    const currentUser = await axios.get('/api/v1/users/current', {
      withCredentials: true,
    });
    if (currentUser) {
      localStorage.setItem('userProfile', JSON.stringify(currentUser.data));
      setUser(currentUser.data);
    }
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useContext(AuthContext);
  const location = useLocation();

  if (!user) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return children;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useContext(AuthContext);
  const location = useLocation();

  if (!user || (user && !user.is_superuser)) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return children;
}

export default AuthContext;
