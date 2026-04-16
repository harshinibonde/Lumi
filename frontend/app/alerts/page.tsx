"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";
import type { User } from "@/lib/api";

export default function AlertsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [alertCount, setAlertCount] = useState(0);
  const [analyticsSignals, setAnalyticsSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const fetchAlerts = async () => {
      try {
        // GET /auth/me — get user profile for screening_due status
        const meData = await api.getMe();
        setUser(meData);

        // GET /chat/signals/{user_id} — get behavioral signal alerts
        try {
          const signalData = await api.getChatSignals(meData.id);
          setSignals(signalData.signals || []);
          setAlertCount(signalData.alert_count || 0);
        } catch {
          setSignals([]);
        }

        // GET /analytics/me — get analytics signals
        try {
          const analyticsData = await api.getMyAnalytics();
          setAnalyticsSignals(analyticsData.signals || []);
        } catch {
          setAnalyticsSignals([]);
        }
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading alerts...</p>
        </div>
      </div>
    );
  }

  // Build alert items from backend data
  const alertItems: { type: string; color: string; title: string; description: string; time?: string }[] = [];

  // Screening due alert from GET /auth/me
  if (user?.screening_due) {
    alertItems.push({
      type: "screening",
      color: "bg-amber-500",
      title: "Screening Due",
      description: user.days_overdue
        ? `Your cognitive screening is ${user.days_overdue} day${user.days_overdue > 1 ? "s" : ""} overdue. Please complete a new assessment.`
        : `Your next screening is due${user.days_until_due ? ` in ${user.days_until_due} days` : " soon"}.`,
      time: user.next_due || undefined,
    });
  }

  // Behavioral signal alerts from GET /chat/signals/{user_id}
  const recentAlertSignals = signals.filter((s: any) => s.alert_keywords && s.alert_keywords.length > 0).slice(0, 10);
  for (const signal of recentAlertSignals) {
    alertItems.push({
      type: "cognitive",
      color: "bg-rose-500",
      title: "Behavioral Signal Detected",
      description: `Keywords: ${(signal.alert_keywords || []).join(", ")}${signal.message_excerpt ? ` — "${signal.message_excerpt.slice(0, 80)}..."` : ""}`,
      time: signal.created_at,
    });
  }

  // High confusion signals from GET /chat/signals
  const highConfusionSignals = signals.filter((s: any) => (s.confusion_score || 0) > 0.7).slice(0, 5);
  for (const signal of highConfusionSignals) {
    if (!recentAlertSignals.includes(signal)) {
      alertItems.push({
        type: "confusion",
        color: "bg-orange-500",
        title: "Elevated Confusion Detected",
        description: `Confusion score: ${Number(signal.confusion_score).toFixed(2)}${signal.message_excerpt ? ` — "${signal.message_excerpt.slice(0, 80)}..."` : ""}`,
        time: signal.created_at,
      });
    }
  }

  const hasAlerts = alertItems.length > 0;

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="pt-10">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Care Alerts</h1>
            <p className="mt-2 text-[#163328]/75">
              {hasAlerts
                ? `${alertItems.length} active alert${alertItems.length > 1 ? "s" : ""}`
                : "Important notifications and care insights"}
            </p>
          </div>

          {/* Summary strip */}
          {alertCount > 0 && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-4">
              <p className="text-sm font-medium text-rose-900">
                ⚠ {alertCount} behavioral alert{alertCount > 1 ? "s" : ""} detected in the last 90 days
              </p>
            </div>
          )}

          {!hasAlerts ? (
            <div className="rounded-lg border border-[#163328]/10 bg-white/50 p-8 text-center space-y-4">
              <p className="text-lg text-[#163328]/75">No active alerts</p>
              <p className="text-sm text-[#163328]/50">All systems healthy. Alerts will appear here when care adjustments are recommended.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alertItems.map((alert, index) => (
                <div key={index} className="rounded-lg bg-white/50 border border-[#163328]/10 p-4 hover:shadow-md transition">
                  <div className="flex items-start gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${alert.color} mt-1.5 flex-shrink-0`}></div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <h3 className="font-semibold text-[#163328] mb-1">{alert.title}</h3>
                        {alert.time && (
                          <span className="text-xs text-[#163328]/50">
                            {new Date(alert.time).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[#163328]/75">{alert.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Alert Types Reference */}
          <div className="mt-8">
            <h2 className="font-serif text-2xl font-normal italic text-[#163328] mb-4">Alert Types</h2>
            <div className="space-y-4">
              <div className="rounded-lg bg-white/50 border border-[#163328]/10 p-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-500 mt-1.5 flex-shrink-0"></div>
                  <div>
                    <h3 className="font-semibold text-[#163328] mb-1">Screening Reminders</h3>
                    <p className="text-sm text-[#163328]/75">Time to complete your regular cognitive assessment</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg bg-white/50 border border-[#163328]/10 p-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-rose-500 mt-1.5 flex-shrink-0"></div>
                  <div>
                    <h3 className="font-semibold text-[#163328] mb-1">Behavioral Signals</h3>
                    <p className="text-sm text-[#163328]/75">Alert keywords detected in chat conversations</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg bg-white/50 border border-[#163328]/10 p-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-orange-500 mt-1.5 flex-shrink-0"></div>
                  <div>
                    <h3 className="font-semibold text-[#163328] mb-1">Cognitive Changes</h3>
                    <p className="text-sm text-[#163328]/75">Elevated confusion or notable changes in language patterns</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <Link
              href="/dashboard"
              className="inline-block rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
