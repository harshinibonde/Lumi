"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import { api, type AnalyticsResponse } from "@/lib/api";
import { getState, isAuthenticated } from "@/lib/state";
import { useToast } from "@/components/Toast";
import styles from "@/styles/dashboard.module.css";

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const router = useRouter();
  const toast = useToast();
  const [name, setName] = useState("");
  const [difficulty, setDifficulty] = useState(1);
  const [totalSessions, setTotalSessions] = useState(0);
  const [chatTurns, setChatTurns] = useState(0);
  const [avgAccuracy, setAvgAccuracy] = useState<number | null>(null);
  const [llmOnline, setLlmOnline] = useState(false);
  const [llmModel, setLlmModel] = useState("Unknown");
  const [sessionsByDay, setSessionsByDay] = useState<{ day: string; count: number }[]>([]);
  const [syncedAt, setSyncedAt] = useState("-");

  useEffect(() => {
    let mounted = true;

    const run = async () => {
      const s = getState();
      if (!s.userId) {
        router.replace("/login");
        return;
      }

      if (!mounted) return;
      setName(s.userName || "there");
      setDifficulty(s.difficultyLevel || 1);

      try {
        const [analytics, llm] = await Promise.allSettled([
          api.analytics(s.userId),
          api.ollamaHealth(),
        ]);

        if (!mounted) return;

        if (analytics.status === "fulfilled") {
          const a = analytics.value;
          setTotalSessions(a.summary.approx_distinct_sessions || 0);
          setChatTurns(a.summary.chat_turns || 0);
          setAvgAccuracy(a.summary.avg_accuracy_chat);
          setDifficulty(a.summary.current_difficulty || 1);
          setSessionsByDay(a.sessions_by_day || []);
        }

        if (llm.status === "fulfilled") {
          setLlmOnline(llm.value.reachable);
          setLlmModel(llm.value.model || "Unknown");
        }

        setSyncedAt(new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }));
      } catch {
        if (!mounted) return;
        toast.push("Could not load dashboard data.", "error");
      }
    };

    void run();
    return () => { mounted = false; };
  }, [router, toast]);

  const hello = useMemo(() => `${greeting()}, ${name || "there"}`, [name]);
  const initials = (name || "U").split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]?.toUpperCase() ?? "").join("") || "U";

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.inner}>
          {/* Welcome */}
          <section className={styles.welcome}>
            <div>
              <h1 className={styles.greeting}>{hello}</h1>
              <p className={styles.greetSub}>Here is your cognitive wellness summary.</p>
            </div>
            <div className={styles.avatarWrap}>
              <div className={styles.avatar}>{initials}</div>
              <span className={styles.level}>Level {difficulty}</span>
            </div>
          </section>

          {/* Metrics */}
          <section className={styles.metrics}>
            <article className={styles.metric}>
              <span className={styles.metricLabel}>Sessions</span>
              <strong className={styles.metricValue}>{totalSessions}</strong>
            </article>
            <article className={styles.metric}>
              <span className={styles.metricLabel}>Chat Turns</span>
              <strong className={styles.metricValue}>{chatTurns}</strong>
            </article>
            <article className={styles.metric}>
              <span className={styles.metricLabel}>Avg Accuracy</span>
              <strong className={styles.metricValue}>
                {avgAccuracy != null ? `${Math.round(avgAccuracy * 100)}%` : "—"}
              </strong>
            </article>
            <article className={styles.metric}>
              <span className={styles.metricLabel}>Difficulty</span>
              <strong className={styles.metricValue}>{difficulty}</strong>
            </article>
          </section>

          {/* Grid */}
          <section className={styles.grid}>
            {/* Activity Chart */}
            <article className={styles.panel}>
              <h2 className={styles.panelTitle}>Recent Activity</h2>
              {sessionsByDay.length > 0 ? (
                <div className={styles.barChart}>
                  {sessionsByDay.slice(-7).map((d) => (
                    <div key={d.day} className={styles.barCol}>
                      <div
                        className={styles.bar}
                        style={{ height: `${Math.min(100, d.count * 25)}%` }}
                      />
                      <span className={styles.barLabel}>{d.day.slice(-5)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.empty}>
                  <span className="material-symbols-outlined" style={{ fontSize: 36, opacity: 0.3 }}>bar_chart</span>
                  <p>No session data yet. Start your first assessment.</p>
                </div>
              )}
            </article>

            {/* Quick Actions */}
            <article className={styles.panel}>
              <h2 className={styles.panelTitle}>Quick Actions</h2>
              <div className={styles.actions}>
                <Link href="/assessment" className={styles.actionBtn}>
                  <span className="material-symbols-outlined">psychology_alt</span>
                  <div>
                    <strong>Start Assessment</strong>
                    <p>Take a cognitive screening</p>
                  </div>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </Link>
                <Link href="/chat" className={styles.actionBtn}>
                  <span className="material-symbols-outlined">forum</span>
                  <div>
                    <strong>Talk to Lumi</strong>
                    <p>Start a memory conversation</p>
                  </div>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </Link>
                <Link href="/analytics" className={styles.actionBtn}>
                  <span className="material-symbols-outlined">analytics</span>
                  <div>
                    <strong>View Progress</strong>
                    <p>See your trend reports</p>
                  </div>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </Link>
              </div>
            </article>
          </section>

          {/* System Status */}
          <section className={styles.sys}>
            <div className={styles.sysRow}>
              <span className={`${styles.dot} ${llmOnline ? styles.dotOk : styles.dotErr}`} />
              Ollama: {llmOnline ? "Connected" : "Offline"} — {llmModel}
            </div>
            <div className={styles.sysRow}>Last sync: {syncedAt}</div>
          </section>
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
