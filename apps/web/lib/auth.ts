"use client";

import { useEffect, useState } from "react";
import { API_UNAUTHORIZED_EVENT, apiRequest, User } from "./api";

export const TOKEN_STORAGE_KEY = "personal_knowledge_radar_token";

export function readStoredToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    function handleUnauthorized() {
      clearToken();
      setTokenState(null);
      setUser(null);
    }

    window.addEventListener(API_UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(API_UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

  useEffect(() => {
    const saved = readStoredToken();
    if (!saved) {
      setIsLoading(false);
      return;
    }
    setTokenState(saved);
    apiRequest<User>("/api/auth/me", {}, saved)
      .then(setUser)
      .catch(() => {
        clearToken();
        setTokenState(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function setToken(nextToken: string) {
    storeToken(nextToken);
    setTokenState(nextToken);
  }

  async function signOut() {
    const currentToken = token;
    try {
      if (currentToken) await apiRequest("/api/auth/logout", { method: "POST" }, currentToken);
    } finally {
      clearToken();
      setTokenState(null);
      setUser(null);
    }
  }

  async function refreshUser(authToken = token) {
    if (!authToken) return null;
    const me = await apiRequest<User>("/api/auth/me", {}, authToken);
    setUser(me);
    return me;
  }

  return { token, user, isLoading, setToken, setUser, refreshUser, signOut };
}
