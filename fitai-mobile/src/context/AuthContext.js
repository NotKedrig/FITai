import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import * as authApi from '../api/auth';
import { apiRequest } from '../api/client';

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

  const fetchCurrentUser = useCallback(async (accessToken) => {
    try {
      const me = await apiRequest('/users/me', {
        method: 'GET',
        token: accessToken,
      });
      setUser(me);
    } catch (error) {
      console.warn('Failed to fetch current user', error);
      setUser(null);
      throw error;
    }
  }, []);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        if (storedToken) {
          setToken(storedToken);
          try {
            await fetchCurrentUser(storedToken);
          } catch (error) {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
            setToken(null);
          }
        }
      } catch (error) {
        console.warn('Failed to restore auth token', error);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (email, password) => {
      try {
        const result = await authApi.login(email, password);
        const accessToken = result.access_token;

        if (!accessToken) {
          throw new Error('No access token returned from server.');
        }

        await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
        setToken(accessToken);
        await fetchCurrentUser(accessToken);
      } catch (error) {
        throw error;
      }
    },
    [fetchCurrentUser]
  );

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
