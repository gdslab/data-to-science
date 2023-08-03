import axios from 'axios';
import { ReactNode, createContext, useState } from 'react';

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
}

const context: {
  user: User | null;
  login: (data: Login) => Promise<void>;
  logout: () => Promise<void>;
} = {
  user: null,
  login: async () => {},
  logout: async () => {},
};

const AuthContext = createContext(context);

export function AuthContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    let userProfile = localStorage.getItem('userProfile');
    if (userProfile) {
      return JSON.parse(userProfile);
    }
    return null;
  });

  async function login(data: { username: string; password: string }) {
    try {
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
    } catch (err) {
      throw err;
    }
  }

  async function logout() {
    localStorage.removeItem('userProfile');
    try {
      await axios.get('/api/v1/auth/remove-access-token').then(() => setUser(null));
    } catch (err) {
      throw err;
    }
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
