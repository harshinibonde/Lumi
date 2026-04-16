"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/lib/auth";

export function useAuthHydration() {
  const hydrateAuth = useAuthStore((state) => state.hydrateAuth);

  useEffect(() => {
    hydrateAuth();
  }, [hydrateAuth]);
}
