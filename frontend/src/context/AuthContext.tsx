/**
 * Authentication Context & Role Management
 * Provides session-scoped auth state, role checks, and automatic token expiry handling.
 * Does NOT persist credentials or sensitive payloads to localStorage.
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from 'react';
import type { User } from '../api/types';
import { setAuthToken, getAuthToken } from '../api/client';
import { loginUser, registerUser, getCurrentUserProfile } from '../api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isRecruiter: boolean;
  isCandidate: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    role: 'candidate' | 'recruiter';
  }) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    setAuthToken(null);
    setTokenState(null);
    setUser(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const profile = await getCurrentUserProfile();
      setUser(profile);
    } catch {
      // Token expired or invalid
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    refreshProfile();

    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('smarthire:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('smarthire:unauthorized', handleUnauthorized);
    };
  }, [refreshProfile, logout]);

  const login = async (credentials: { email: string; password: string }) => {
    const response = await loginUser(credentials);
    setAuthToken(response.access_token);
    setTokenState(response.access_token);
    setUser(response.user);
  };

  const register = async (payload: {
    email: string;
    password: string;
    full_name: string;
    role: 'candidate' | 'recruiter';
  }) => {
    await registerUser(payload);
    // After registration, log user in automatically
    await login({ email: payload.email, password: payload.password });
  };

  const isRecruiter = user?.role === 'recruiter' || user?.role === 'admin';
  const isCandidate = user?.role === 'candidate';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        isRecruiter,
        isCandidate,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
