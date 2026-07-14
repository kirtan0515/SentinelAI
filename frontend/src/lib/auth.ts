"use client";

import { create } from "zustand";
import api from "@/lib/api";
import type { User, TokenResponse } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    const response = await api.post<TokenResponse>("/auth/login", {
      email,
      password,
    });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);

    const userResponse = await api.get<User>("/auth/me");
    set({ user: userResponse.data, isAuthenticated: true, isLoading: false });
  },

  register: async (email: string, username: string, password: string, fullName?: string) => {
    await api.post("/auth/register", {
      email,
      username,
      password,
      full_name: fullName || null,
    });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false, isLoading: false });
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  refreshUser: async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      const response = await api.get<User>("/auth/me");
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
