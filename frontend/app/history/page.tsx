"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";

export default function HistoryPage() {
  const router = useRouter();
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // GET /screening/results — fetch all screening results for authenticated user
    const fetchHistory = async () => {
      try {
        const data = await api.getScreeningResults();
        setResults(Array.isArray(data) ? data : []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [router]);

  const getBadgeColor = (prediction: string) => {
    switch (prediction) {
      case "Normal": return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "Mild": return "bg-amber-100 text-amber-800 border-amber-200";
      case "Moderate": return "bg-orange-100 text-orange-800 border-orange-200";
      case "Severe": return "bg-rose-100 text-rose-800 border-rose-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="pt-10">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Screening History</h1>
            <p className="mt-2 text-[#163328]/75">
              {results.length > 0
                ? `${results.length} assessment${results.length > 1 ? "s" : ""} completed`
                : "Your past assessments and results"}
            </p>
          </div>

          {results.length === 0 ? (
            <div className="rounded-lg border border-[#163328]/10 bg-white/50 p-8 text-center space-y-4">
              <p className="text-lg text-[#163328]/75">No screening history available yet.</p>
              <p className="text-sm text-[#163328]/50">Start your first cognitive screening to track your progression over time.</p>
              <Link
                href="/screening"
                className="inline-block rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
              >
                Start Screening
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Each result from GET /screening/results */}
              {results.map((result: any, index: number) => {
                const domainScores = result.domain_scores || {};
                return (
                  <div
                    key={result.id || index}
                    className="rounded-lg border border-[#163328]/10 bg-white/50 p-6 space-y-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-[#163328]/75">
                          {result.created_at
                            ? new Date(result.created_at).toLocaleDateString("en-US", {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                              })
                            : "Unknown date"}
                        </p>
                        <div className="flex items-center gap-3 mt-2">
                          <p className="text-2xl font-bold text-[#163328]">
                            {result.mmse_total}/30
                          </p>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getBadgeColor(result.ml_prediction)}`}>
                            {result.ml_prediction}
                          </span>
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <p className="text-xs text-[#163328]/50">Confidence</p>
                        <p className="text-sm font-semibold text-[#163328]">
                          {result.ml_confidence ? `${(result.ml_confidence * 100).toFixed(1)}%` : "—"}
                        </p>
                        <p className={`text-xs font-medium ${result.agreement ? "text-emerald-600" : "text-amber-600"}`}>
                          {result.agreement ? "✓ Agreed" : "⚠ Flagged"}
                        </p>
                      </div>
                    </div>

                    {/* Domain Score Breakdown */}
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 pt-2 border-t border-[#163328]/10">
                      {[
                        { key: "orientation_score", label: "Orient.", max: 10 },
                        { key: "registration_score", label: "Regist.", max: 3 },
                        { key: "attention_score", label: "Attn.", max: 5 },
                        { key: "recall_score", label: "Recall", max: 3 },
                        { key: "language_score", label: "Lang.", max: 8 },
                        { key: "visuospatial_score", label: "Visual", max: 1 },
                      ].map(({ key, label, max }) => (
                        <div key={key} className="text-center p-2 rounded bg-[#163328]/5">
                          <p className="text-xs text-[#163328]/60">{label}</p>
                          <p className="text-sm font-semibold text-[#163328]">
                            {domainScores[key] ?? "—"}/{max}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Link to detailed report */}
                    <div className="pt-2">
                      <Link
                        href={`/report/${result.id || result.session_id}`}
                        className="text-xs font-semibold text-[#163328] hover:underline"
                      >
                        View Full Report →
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Link
              href="/screening"
              className="rounded-lg bg-[#163328] px-6 py-3 text-center text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
            >
              New Screening
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg border border-[#163328]/20 bg-white px-6 py-3 text-center text-sm font-semibold text-[#163328] hover:bg-white/70 transition"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
