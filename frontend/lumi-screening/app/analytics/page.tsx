"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import { api, type AnalyticsResponse } from "@/lib/api";
import { getState } from "@/lib/state";
import { useToast } from "@/components/Toast";
import styles from "@/styles/analytics.module.css";

export default function AnalyticsPage() {
  const router = useRouter();
  const toast = useToast();
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const s = getState();
    if (!s.userId) { router.replace("/login"); return; }

    api.analytics(s.userId)
      .then((res) => { setData(res); setLoading(false); })
      .catch(() => { toast.push("Could not load analytics.", "error"); setLoading(false); });
  }, [router, toast]);

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.inner}>
          <h1 className={styles.title}>Cognitive Progress</h1>
          <p className={styles.subtitle}>Your longitudinal engagement data and trends.</p>

          {loading ? (
            <div className={styles.loading}>Loading analytics...</div>
          ) : data ? (
            <>
              <section className={styles.metrics}>
                <article className={styles.metric}>
                  <span>Total Sessions</span>
                  <strong>{data.summary.approx_distinct_sessions}</strong>
                </article>
                <article className={styles.metric}>
                  <span>Chat Turns</span>
                  <strong>{data.summary.chat_turns}</strong>
                </article>
                <article className={styles.metric}>
                  <span>Avg Latency</span>
                  <strong>{data.summary.avg_latency_chat != null ? `${data.summary.avg_latency_chat.toFixed(1)}s` : "—"}</strong>
                </article>
                <article className={styles.metric}>
                  <span>Difficulty</span>
                  <strong>{data.summary.current_difficulty}</strong>
                </article>
              </section>

              {/* Session chart */}
              {data.sessions_by_day.length > 0 && (
                <section className={styles.chartSection}>
                  <h2 className={styles.sectionTitle}>Sessions by Day</h2>
                  <div className={styles.barChart}>
                    {data.sessions_by_day.slice(-14).map((d) => (
                      <div key={d.day} className={styles.barCol}>
                        <div className={styles.bar} style={{ height: `${Math.min(100, d.count * 20)}%` }} />
                        <span className={styles.barLabel}>{d.day.slice(-5)}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Difficulty timeline */}
              {data.difficulty_timeline.length > 0 && (
                <section className={styles.timelineSection}>
                  <h2 className={styles.sectionTitle}>Difficulty Changes</h2>
                  <div className={styles.timeline}>
                    {data.difficulty_timeline.map((d, i) => (
                      <div key={i} className={styles.timelineItem}>
                        <div className={styles.timelineDot} />
                        <div>
                          <strong>Level {d.from_level} → {d.to_level}</strong>
                          <span>{new Date(d.changed_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </>
          ) : (
            <div className={styles.loading}>No data available yet.</div>
          )}
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
