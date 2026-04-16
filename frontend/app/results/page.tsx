"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api } from "@/lib/api";
import ClassificationBadge from "@/components/ClassificationBadge";
import DomainBreakdown from "@/components/DomainBreakdown";
import { useScreeningStore } from "@/store/screeningStore";
import { Navbar } from "@/components/layout/Navbar";

export default function ResultsPage() {
  const router = useRouter();
  const storeResult = useScreeningStore((s) => s.result);
  const [result, setResult] = useState<any>(storeResult);
  const [loading, setLoading] = useState(!storeResult);

  useEffect(() => {
    // If result is already in zustand store (just completed a screening), use it
    if (storeResult) {
      setResult(storeResult);
      setLoading(false);
      return;
    }

    // Otherwise, fetch latest result from GET /screening/results
    const fetchLatest = async () => {
      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const results = await api.getScreeningResults();
        if (Array.isArray(results) && results.length > 0) {
          setResult(results[0]); // Most recent result
        }
      } catch {
        // Failed to fetch
      } finally {
        setLoading(false);
      }
    };

    fetchLatest();
  }, [storeResult, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
        <Navbar />
        <main className="px-6 py-16 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-2xl">
            <div className="rounded-lg border border-[#163328]/10 bg-white/50 p-6 text-center space-y-4">
              <p className="text-[#163328]">No screening results available yet.</p>
              <Link
                href="/screening"
                className="inline-block rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
              >
                Start Screening
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-2xl space-y-6">
          <div className="pt-4">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Screening Results</h1>
            <p className="mt-2 text-[#163328]/75">Your cognitive assessment summary</p>
          </div>

          {/* Score Summary — from POST /screening/complete or GET /screening/results */}
          <div className="space-y-6 rounded-lg border border-[#163328]/10 bg-white/50 p-8">
            <div className="space-y-4">
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <p className="text-sm font-medium text-[#163328]">MMSE Total Score</p>
                  <p className="text-3xl font-bold text-[#163328]">{result.mmse_total}/30</p>
                </div>
                <div className="w-full bg-[#163328]/10 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      result.mmse_total >= 27
                        ? "bg-emerald-600"
                        : result.mmse_total >= 18
                        ? "bg-amber-500"
                        : result.mmse_total >= 10
                        ? "bg-orange-500"
                        : "bg-rose-600"
                    }`}
                    style={{ width: `${Math.max(0, Math.min(100, (Number(result.mmse_total) / 30) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="border-t border-[#163328]/10 pt-4">
                <p className="text-sm font-medium text-[#163328] mb-3">Assessment Classification</p>
                <ClassificationBadge label={result.ml_prediction} />
              </div>

              <div className="border-t border-[#163328]/10 pt-4 grid gap-3">
                <div className="flex justify-between items-center p-3 bg-[#163328]/5 rounded-lg">
                  <p className="text-sm text-[#163328]/75">Model Confidence</p>
                  <p className="font-semibold text-[#163328]">{(result.ml_confidence * 100).toFixed(1)}%</p>
                </div>
                <div className="flex justify-between items-center p-3 bg-[#163328]/5 rounded-lg">
                  <p className="text-sm text-[#163328]/75">Prediction Agreement</p>
                  <p className={`font-semibold ${result.agreement ? "text-emerald-600" : "text-amber-600"}`}>
                    {result.agreement ? "Model & Rule Agree" : "Flagged for Review"}
                  </p>
                </div>
              </div>

              {!result.agreement && (
                <div className="border border-amber-200 bg-amber-50 rounded-lg p-4">
                  <p className="text-sm text-amber-800">⚠️ This screening shows disagreement between assessment methods and has been flagged for clinical review.</p>
                </div>
              )}
            </div>

            <div className="border-t border-[#163328]/10 pt-4 space-y-3">
              <p className="text-sm font-medium text-[#163328]">Model Predictions</p>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">SVM</p>
                  <p className="font-semibold text-[#163328]">{result.svm_prediction}</p>
                </div>
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">Random Forest</p>
                  <p className="font-semibold text-[#163328]">{result.rf_prediction}</p>
                </div>
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">Neural Network</p>
                  <p className="font-semibold text-[#163328]">{result.mlp_prediction}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4 rounded-lg border border-[#163328]/10 bg-white/50 p-6">
            <h2 className="font-serif text-xl font-normal italic text-[#163328]">Domain Breakdown</h2>
            <DomainBreakdown scores={result.domain_scores} />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              id="results-chat"
              onClick={() => router.push("/chat")}
              className="flex-1 rounded-lg bg-[#163328] px-6 py-3 text-center text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
            >
              Chat with Lumi
            </button>
            <button
              id="results-dashboard"
              onClick={() => router.push("/dashboard")}
              className="rounded-lg border border-[#163328]/20 bg-white px-6 py-3 text-center text-sm font-semibold text-[#163328] hover:bg-white/70 transition"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
