import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      await api.ensureCsrf();
      const me = await api.getMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (username, password) => {
    const result = await api.login(username, password);
    if (result.mfa_required) {
      return result;
    }
    setUser(result);
    return result;
  };

  const verifyMfa = async (mfaToken, code) => {
    const me = await api.verifyMfa(mfaToken, code);
    setUser(me);
    return me;
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  const register = async (payload) => {
    const me = await api.register(payload);
    setUser(me);
    return me;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, verifyMfa, logout, register, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
