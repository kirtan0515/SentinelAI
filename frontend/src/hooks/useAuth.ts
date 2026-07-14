"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";

export function useAuth() {
  const store = useAuthStore();

  useEffect(() => {
    if (!store.user && !store.isAuthenticated) {
      store.refreshUser();
    }
  }, []);

  return store;
}

export function useRequireAuth() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, refreshUser } = useAuthStore();

  useEffect(() => {
    refreshUser();
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  return { user, isAuthenticated, isLoading };
}
