"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import { getState, resetState } from "@/lib/state";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import styles from "@/styles/settings.module.css";

export default function SettingsPage() {
  const router = useRouter();
  const toast = useToast();
  const [name, setName] = useState("");
  const [llmOnline, setLlmOnline] = useState(false);
  const [llmModel, setLlmModel] = useState("Unknown");
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    const s = getState();
    if (!s.userId) { router.replace("/login"); return; }
    setName(s.userName || "User");

    Promise.allSettled([api.health(), api.ollamaHealth()]).then(([health, ollama]) => {
      if (health.status === "fulfilled") setBackendOnline(true);
      if (ollama.status === "fulfilled") {
        setLlmOnline(ollama.value.reachable);
        setLlmModel(ollama.value.model || "Unknown");
      }
    });
  }, [router]);

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.inner}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>Manage your Lumi experience.</p>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Profile</h2>
            <div className={styles.row}>
              <span>Name</span>
              <strong>{name}</strong>
            </div>
            <div className={styles.row}>
              <span>User ID</span>
              <strong>{getState().userId || "—"}</strong>
            </div>
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>System Status</h2>
            <div className={styles.row}>
              <span>Backend</span>
              <div className={styles.statusChip}>
                <span className={`${styles.dot} ${backendOnline ? styles.dotOk : styles.dotErr}`} />
                {backendOnline ? "Connected" : "Offline"}
              </div>
            </div>
            <div className={styles.row}>
              <span>Ollama LLM</span>
              <div className={styles.statusChip}>
                <span className={`${styles.dot} ${llmOnline ? styles.dotOk : styles.dotErr}`} />
                {llmOnline ? `Connected — ${llmModel}` : "Offline"}
              </div>
            </div>
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Privacy</h2>
            <p className={styles.privacyNote}>
              All your data stays on this device. No cloud storage, no telemetry, no external requests.
            </p>
          </section>

          <button
            className={`btn btn--ghost ${styles.signOutBtn}`}
            onClick={() => {
              resetState();
              toast.push("Signed out successfully.", "info");
              router.push("/login");
            }}
          >
            Sign Out
          </button>
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
