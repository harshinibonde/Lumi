"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Navbar } from "@/components/layout/Navbar";
import type { User } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const [user, setUser] = useState<User | null>(null);
  const [screeningResults, setScreeningResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("auth_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      try {
        const meData = await api.getMe();
        setUser(meData);
        localStorage.setItem("user", JSON.stringify(meData));

        try {
          const results = await api.getScreeningResults();
          setScreeningResults(Array.isArray(results) ? results : []);
        } catch {
          setScreeningResults([]);
        }

      } catch (err) {
        setError("Session expired. Please log in again.");
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {}

    clearAuth();
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--cream)]">
        <p className="text-[#163328]">Loading dashboard...</p>
      </div>
    );
  }

  if (!user) return null;

  const hasScreenings = screeningResults.length > 0;
  const latest = screeningResults[0];

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />

      <main className="px-6 py-10">
        <div className="max-w-4xl mx-auto space-y-8">

          {/* Header */}
          <div>
            <h1 className="text-4xl font-serif text-[#163328]">Dashboard</h1>
            <p className="text-[#163328]/70">
              Welcome, {user.full_name || user.username}
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded">
              {error}
            </div>
          )}

          {/* Account Info */}
          <div className="bg-white/50 p-6 rounded-lg space-y-4 border">
            <h2 className="font-semibold text-[#163328]">Account Information</h2>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm">Username</p>
                <p className="font-semibold">{user.username}</p>
              </div>

              <div>
                <p className="text-sm">Role</p>
                <p className="font-semibold capitalize">{user.role}</p>
              </div>

              <div>
                <p className="text-sm">Email</p>
                <p className="font-semibold">{user.email || "-"}</p>
              </div>
            </div>
          </div>

          {/* Screening Status */}
          <div className="bg-white/50 p-6 rounded-lg space-y-4 border">
            <h2 className="font-semibold text-[#163328]">Screening Status</h2>

            {hasScreenings ? (
              <div className="bg-green-100 p-4 rounded">
                <p>
                  Latest Result: <strong>{latest.ml_prediction}</strong>
                </p>
                <p>MMSE Score: {latest.mmse_total}/30</p>
              </div>
            ) : (
              <div className="bg-yellow-100 p-4 rounded">
                No screenings completed yet
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="space-y-4">
            <h2 className="font-semibold text-[#163328]">Actions</h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

              {/* Start Screening */}
              <button
                onClick={() => router.push("/screening")}
                className="bg-[#163328] text-white px-6 py-3 rounded-lg"
              >
                Start Screening
              </button>

              {/* Chat */}
              <button
                disabled={!hasScreenings}
                onClick={() => router.push("/chat")}
                className={`px-6 py-3 rounded-lg ${
                  hasScreenings
                    ? "bg-[#163328] text-white"
                    : "bg-gray-300 text-gray-600 cursor-not-allowed"
                }`}
              >
                Talk to Lumi
              </button>

              {/* History */}
              <button
                onClick={() => router.push("/history")}
                className="border px-6 py-3 rounded-lg"
              >
                History
              </button>

              {/* Alerts */}
              <button
                onClick={() => router.push("/alerts")}
                className="border px-6 py-3 rounded-lg"
              >
                Alerts
              </button>

            </div>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="text-sm text-[#163328]"
          >
            Sign out
          </button>

        </div>
      </main>
    </div>
  );
}