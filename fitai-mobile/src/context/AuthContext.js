import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import * as authApi from '../api/auth';

const TOKEN_KEY = 'fitai_token';

export const AuthContext = createContext({
  token: null,
  user: null,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        if (storedToken) {
          setToken(storedToken);
        }
      } catch (error) {
        console.warn('Failed to restore auth token', error);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const result = await authApi.login(email, password);
      const accessToken = result.access_token;

      if (!accessToken) {
        throw new Error('No access token returned from server.');
      }

      await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
      setToken(accessToken);
      // If backend returns user info in future, set user here.
      setUser(null);
    } catch (error) {
      throw error;
    }
  }, []);

  const register = useCallback(
    async (email, username, password) => {
      try {
        await authApi.register(email, username, password);
        await login(email, password);
      } catch (error) {
        throw error;
      }
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    } catch (error) {
      console.warn('Failed to clear auth token', error);
    } finally {
      setToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      isLoading,
      login,
      register,
      logout,
    }),
    [token, user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

