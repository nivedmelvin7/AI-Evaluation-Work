import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser, signIn, signOut, signUp } from '../api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((nextUser) => { if (active) setUser(nextUser); })
      .catch(() => { if (active) setUser(null); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
    async login(credentials) {
      const nextUser = await signIn(credentials);
      setUser(nextUser);
      return nextUser;
    },
    async signup(details) {
      const nextUser = await signUp(details);
      setUser(nextUser);
      return nextUser;
    },
    async logout() {
      await signOut();
      setUser(null);
    },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
