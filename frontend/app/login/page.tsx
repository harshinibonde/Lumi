"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import api from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Navbar } from "@/components/layout/Navbar";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const onLogin = async () => {
    if (!username || !password) {
      setError("Please enter both username and password");
      return;
    }

    try {
      setIsLoading(true);
      setError("");

      // POST /auth/login
      const data = await api.login({ username, password });

      // Persist token + user in localStorage
      localStorage.setItem("auth_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("screening_status", JSON.stringify(data.screening_status));

      // Update zustand auth store
      setAuth(data.access_token, data.user.role);

      // Route based on role
      if (data.user.role === "caregiver") {
        router.push("/caregiver");
      } else {
        router.push("/dashboard");
      }
    } catch (e: any) {
      setError(e.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onLogin();
    }
  };

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-16 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-md pt-20">
          <div className="space-y-8">
            <div className="text-center">
              <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Lumi</h1>
              <p className="mt-2 text-lg text-[#163328]/75">Welcome back</p>
            </div>

            <div className="space-y-6 rounded-xl border border-[#163328]/10 bg-white/50 p-8">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Username</label>
                <input
                  id="login-username"
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Password</label>
                <input
                  id="login-password"
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={isLoading}
                />
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                  {error}
                </div>
              )}

              <button
                id="login-submit"
                className="w-full rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-[#fff9ee] transition hover:bg-[#163328]/90 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={onLogin}
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign in"}
              </button>

              <div className="text-center text-sm">
                <span className="text-[#163328]/75">Don't have an account? </span>
                <Link href="/register" className="font-semibold text-[#163328] hover:underline">
                  Create one
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
