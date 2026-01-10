/**
 * Authentication Context Provider
 * Manages JWT token and user authentication state
 */

import React, { createContext, useState, useEffect } from "react";
import type { AuthMe } from "../types";
import { api } from "../api/endpoints";

export interface AuthState {
  token: string | null;
  me: AuthMe | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "mmc_token";

function readToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function persistToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(readToken());
  const [meState, setMeState] = useState<AuthMe | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = () => {
    setToken(null);
    setMeState(null);
    persistToken(null);
  };

  const login = (newToken: string) => {
    setToken(newToken);
    persistToken(newToken);
  };

  // On mount or token change, fetch user info
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    api
      .getMe()
      .then((user) => {
        setMeState(user);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch user info:", err);
        logout();
        setIsLoading(false);
      });
  }, [token]);

  const value: AuthState = {
    token,
    me: meState,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
