"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import api from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";

export default function CaregiverPage() {
  const router = useRouter();
  const [patientResults, setPatientResults] = useState<any[]>([]);
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
        // GET /auth/me — verify caregiver role
        const meData = await api.getMe();
        if (meData.role !== "caregiver") {
          router.push("/dashboard");
          return;
        }

        // GET /analytics/caregiver/patients — fetch linked patient results
        try {
          const caregiverData = await api.getCaregiverPatients();
          setPatientResults(caregiverData.results || []);
        } catch {
          setPatientResults([]);
        }
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const getBadgeColor = (prediction: string) => {
    switch (prediction) {
      case "Normal": return "bg-emerald-100 text-emerald-800";
      case "Mild": return "bg-amber-100 text-amber-800";
      case "Moderate": return "bg-orange-100 text-orange-800";
      case "Severe": return "bg-rose-100 text-rose-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading caregiver hub...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="pt-10">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Caregiver Hub</h1>
            <p className="mt-2 text-[#163328]/75">Manage care, track progress, and access memory vault</p>
          </div>

          {/* Patient Overview — from GET /analytics/caregiver/patients */}
          {patientResults.length > 0 && (
            <section className="space-y-4">
              <h2 className="font-serif text-2xl font-normal italic text-[#163328]">Patient Overview</h2>
              <div className="space-y-3">
                {patientResults.map((result: any, index: number) => (
                  <div key={result.id || index} className="rounded-lg border border-[#163328]/10 bg-white/50 p-4 hover:shadow-md transition">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[#163328]/60">
                          Patient #{result.user_id} — {result.created_at ? new Date(result.created_at).toLocaleDateString() : ""}
                        </p>
                        <div className="flex items-center gap-3 mt-1">
                          <p className="text-xl font-bold text-[#163328]">{result.mmse_total}/30</p>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getBadgeColor(result.ml_prediction)}`}>
                            {result.ml_prediction}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs font-medium ${result.agreement ? "text-emerald-600" : "text-amber-600"}`}>
                          {result.agreement ? "✓ Agreed" : "⚠ Review"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Navigation cards */}
          <div className="grid gap-6 md:grid-cols-2">
            <Link
              href="/caregiver/memory"
              className="group rounded-lg border border-[#163328]/10 bg-white/50 p-6 transition hover:border-[#163328]/30 hover:bg-white/70"
            >
              <div className="space-y-3">
                <h2 className="font-serif text-2xl font-normal italic text-[#163328] group-hover:text-[#163328]/90">
                  Memory Vault
                </h2>
                <p className="text-sm text-[#163328]/75">Create and manage memory entries to personalize AI responses and track important moments</p>
                <p className="text-xs font-semibold text-[#163328] group-hover:underline">Manage Memories →</p>
              </div>
            </Link>

            <Link
              href="/dashboard"
              className="group rounded-lg border border-[#163328]/10 bg-white/50 p-6 transition hover:border-[#163328]/30 hover:bg-white/70"
            >
              <div className="space-y-3">
                <h2 className="font-serif text-2xl font-normal italic text-[#163328] group-hover:text-[#163328]/90">
                  Dashboard
                </h2>
                <p className="text-sm text-[#163328]/75">View cognitive assessments, progress charts, and care analytics for comprehensive oversight</p>
                <p className="text-xs font-semibold text-[#163328] group-hover:underline">View Dashboard →</p>
              </div>
            </Link>
          </div>

          {/* Quick Actions — buttons now wired to routes */}
          <div className="space-y-4">
            <h2 className="font-serif text-2xl font-normal italic text-[#163328]">Quick Actions</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <button
                id="caregiver-start-screening"
                onClick={() => router.push("/screening")}
                className="rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
              >
                Start Screening
              </button>
              <button
                id="caregiver-view-history"
                onClick={() => router.push("/history")}
                className="rounded-lg border border-[#163328]/20 bg-white/50 px-6 py-3 text-sm font-semibold text-[#163328] hover:bg-white/70 transition"
              >
                View History
              </button>
              <button
                id="caregiver-check-alerts"
                onClick={() => router.push("/alerts")}
                className="rounded-lg border border-[#163328]/20 bg-white/50 px-6 py-3 text-sm font-semibold text-[#163328] hover:bg-white/70 transition"
              >
                Check Alerts
              </button>
            </div>
          </div>

          {/* Caregiver Resources */}
          <div className="space-y-4">
            <h2 className="font-serif text-2xl font-normal italic text-[#163328]">Caregiver Resources</h2>
            <div className="space-y-3">
              <div className="rounded-lg bg-white/50 border border-[#163328]/10 p-4">
                <h3 className="font-semibold text-[#163328] mb-2">For Memory Vault</h3>
                <p className="text-sm text-[#163328]/75">Record important biographical information, favorite activities, and meaningful relationships to enhance personalized AI support</p>
              </div>
              <div className="rounded-lg bg-white/50 border border-[#163328]/10 p-4">
                <h3 className="font-semibold text-[#163328] mb-2">For Analytics</h3>
                <p className="text-sm text-[#163328]/75">Monitor longitudinal trends in cognitive capability and identify optimal times for clinical interventions</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
