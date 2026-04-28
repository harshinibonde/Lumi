"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";
import ClassificationBadge from "@/components/ClassificationBadge";
import DomainBreakdown from "@/components/DomainBreakdown";

export default function ReportPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const fetchReport = async () => {
      try {
        // GET /auth/me — get user_id for results lookup
        const meData = await api.getMe();

        // GET /ml/results/{user_id} — fetch all results, then find the matching one
        const results = await api.getResults();
        const match = results.find(
          (r: any) => String(r.id) === params.id || String(r.session_id) === params.id
        );

        if (match) {
          setReport(match);
        }
      } catch (err) {
        console.error("Failed to load report:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [params.id, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading report...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
        <Navbar />
        <main className="px-6 py-10 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-2xl space-y-8 pt-10">
            <div className="rounded-lg border border-[#163328]/10 bg-white/50 p-8 text-center space-y-4">
              <p className="text-lg text-[#163328]/75">Report not found</p>
              <p className="text-sm text-[#163328]/50">The requested assessment report could not be loaded.</p>
              <Link
                href="/history"
                className="inline-block rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
              >
                View All History
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const domainScores = report.domain_scores || {};

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-2xl space-y-8">
          <div className="pt-4">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Cognitive Report</h1>
            <p className="mt-2 text-[#163328]/75">
              Assessment #{params.id}
              {report.created_at && (
                <> — {new Date(report.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</>
              )}
            </p>
          </div>

          {/* Score Summary — from GET /ml/results/{user_id} */}
          <div className="space-y-6 rounded-lg border border-[#163328]/10 bg-white/50 p-8">
            <div className="space-y-4">
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <p className="text-sm font-medium text-[#163328]">MMSE Total Score</p>
                  <p className="text-3xl font-bold text-[#163328]">{report.mmse_total}/30</p>
                </div>
                <div className="w-full bg-[#163328]/10 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      report.mmse_total >= 27
                        ? "bg-emerald-600"
                        : report.mmse_total >= 18
                        ? "bg-amber-500"
                        : report.mmse_total >= 10
                        ? "bg-orange-500"
                        : "bg-rose-600"
                    }`}
                    style={{ width: `${Math.max(0, Math.min(100, (Number(report.mmse_total) / 30) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="border-t border-[#163328]/10 pt-4">
                <p className="text-sm font-medium text-[#163328] mb-3">Assessment Classification</p>
                <ClassificationBadge label={report.ml_prediction} />
              </div>

              <div className="border-t border-[#163328]/10 pt-4 grid gap-3">
                <div className="flex justify-between items-center p-3 bg-[#163328]/5 rounded-lg">
                  <p className="text-sm text-[#163328]/75">Model Confidence</p>
                  <p className="font-semibold text-[#163328]">
                    {report.ml_confidence ? `${(report.ml_confidence * 100).toFixed(1)}%` : "—"}
                  </p>
                </div>
                <div className="flex justify-between items-center p-3 bg-[#163328]/5 rounded-lg">
                  <p className="text-sm text-[#163328]/75">Rule-Based Assessment</p>
                  <p className="font-semibold text-[#163328]">{report.rule_based || "—"}</p>
                </div>
                <div className="flex justify-between items-center p-3 bg-[#163328]/5 rounded-lg">
                  <p className="text-sm text-[#163328]/75">Prediction Agreement</p>
                  <p className={`font-semibold ${report.agreement ? "text-emerald-600" : "text-amber-600"}`}>
                    {report.agreement ? "Model & Rule Agree" : "Flagged for Review"}
                  </p>
                </div>
              </div>

              {!report.agreement && (
                <div className="border border-amber-200 bg-amber-50 rounded-lg p-4">
                  <p className="text-sm text-amber-800">⚠️ This screening shows disagreement between assessment methods and has been flagged for clinical review.</p>
                </div>
              )}
            </div>

            {/* Individual Model Predictions */}
            <div className="border-t border-[#163328]/10 pt-4 space-y-3">
              <p className="text-sm font-medium text-[#163328]">Model Predictions</p>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">SVM</p>
                  <p className="font-semibold text-[#163328]">{report.svm_prediction || "—"}</p>
                </div>
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">Random Forest</p>
                  <p className="font-semibold text-[#163328]">{report.rf_prediction || "—"}</p>
                </div>
                <div className="rounded bg-[#163328]/5 p-3 text-center">
                  <p className="text-xs text-[#163328]/75">Neural Network</p>
                  <p className="font-semibold text-[#163328]">{report.mlp_prediction || "—"}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Domain Breakdown */}
          <div className="space-y-4 rounded-lg border border-[#163328]/10 bg-white/50 p-6">
            <h2 className="font-serif text-xl font-normal italic text-[#163328]">Domain Breakdown</h2>
            <DomainBreakdown scores={domainScores} />
          </div>

          {/* Report metadata */}
          <div className="bg-[#163328]/5 rounded-lg p-4 border border-[#163328]/10">
            <p className="text-sm text-[#163328]/75">This report contains:</p>
            <ul className="mt-2 space-y-2 text-sm text-[#163328]">
              <li>✓ Comprehensive screening assessment</li>
              <li>✓ Domain-by-domain breakdown</li>
              <li>✓ Multi-model ensemble prediction</li>
              <li>✓ Rule-based vs ML agreement analysis</li>
            </ul>
          </div>

          <div className="border-t border-[#163328]/10 pt-6 flex gap-3">
            <Link
              href="/history"
              className="flex-1 rounded-lg bg-[#163328] px-6 py-3 text-center text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
            >
              Back to History
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg border border-[#163328]/20 bg-white px-6 py-3 text-center text-sm font-semibold text-[#163328] hover:bg-white/70 transition"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
