import axios from 'axios';
import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Navigate, useLocation } from 'react-router';

import api from './api';

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
  authChecked: boolean;
  login: (data: Login) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: () => Promise<void>;
} = {
  user: null,
  authChecked: true,
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

  // The cached profile above is read optimistically so the UI can render
  // immediately, but it isn't proof the session is still valid (e.g. the
  // refresh token may have expired or been revoked while the browser was
  // closed). authChecked tracks whether we've confirmed that. Routes that
  // care about auth state (RequireAuth, Landing) should wait for this before
  // deciding where to send the user, otherwise a dead cached session causes
  // a flash into protected content followed by a bounce to /auth/login
  // instead of falling back to the public /explore page.
  const [authChecked, setAuthChecked] = useState(() => {
    return localStorage.getItem('userProfile') === null;
  });

  // When the api interceptor exhausts a token refresh, it dispatches
  // 'auth:session-expired' instead of forcing a redirect. Clear the cached
  // profile and user state so RequireAuth redirects protected routes while
  // public routes (e.g. /explore) keep rendering with anonymous data.
  useEffect(() => {
    function handleSessionExpired() {
      localStorage.removeItem('userProfile');
      setUser(null);
      setAuthChecked(true);
    }
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () =>
      window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, []);

  // Validate the cached profile on startup. /auth/test-token requires a
  // valid access token; if it's expired, the api interceptor transparently
  // refreshes it via the (httponly) refresh cookie and retries. If that
  // also fails, the interceptor dispatches 'auth:session-expired' (handled
  // above), which clears the stale profile and marks auth as checked.
  useEffect(() => {
    if (authChecked) return;

    let cancelled = false;

    api
      .post('/auth/test-token')
      .then((res) => {
        if (cancelled) return;
        localStorage.setItem('userProfile', JSON.stringify(res.data));
        setUser(res.data);
      })
      .catch(() => {
        if (cancelled) return;
        // auth:session-expired already cleared user/localStorage if the
        // refresh ultimately failed; defensively ensure user is cleared.
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) setAuthChecked(true);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setAuthChecked(true);
    }
  }

  async function logout() {
    localStorage.removeItem('userProfile');
    await axios
      .get('/api/v1/auth/remove-access-token', { withCredentials: true })
      .then(() => {
        setUser(null);
        setAuthChecked(true);
      });
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
    <AuthContext.Provider
      value={{ user, authChecked, login, logout, updateProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, authChecked } = useContext(AuthContext);
  const location = useLocation();

  // Wait for the cached profile to be verified before redirecting, so a
  // dead session isn't briefly treated as authenticated and then bounced
  // to /auth/login. Render nothing during the brief verification window.
  if (!authChecked) {
    return null;
  }

  if (!user) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return children;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, authChecked } = useContext(AuthContext);
  const location = useLocation();

  if (!authChecked) {
    return null;
  }

  if (!user || (user && !user.is_superuser)) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return children;
}

export default AuthContext;
