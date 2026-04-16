"use client";

import { create } from "zustand";

export type UserRole = "patient" | "caregiver";

type AuthState = {
  token: string | null;
  role: UserRole | null;
  setAuth: (token: string, role: UserRole) => void;
  clearAuth: () => void;
  hydrateAuth: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  role: null,
  setAuth: (token, role) => {
    localStorage.setItem("auth_token", token);
    localStorage.setItem("user_role", role);
    set({ token, role });
  },
  clearAuth: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_role");
    set({ token: null, role: null });
  },
  hydrateAuth: () => {
    const token = localStorage.getItem("auth_token");
    const role = localStorage.getItem("user_role") as UserRole | null;
    set({ token, role: role === "patient" || role === "caregiver" ? role : null });
  },
}));
