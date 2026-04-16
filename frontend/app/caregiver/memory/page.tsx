"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";

// ─── Types ────────────────────────────────────────────────────────────────────

interface User {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

interface Memory {
  id: number;
  category: string;
  content: string;
  ingested: number;
  created_at: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function MemoryVaultPage() {
  const router = useRouter();

  // ── State ──────────────────────────────────────────────────────────────────
  const [user, setUser] = useState<User | null>(null);
  const [category, setCategory] = useState("routine");
  const [content, setContent] = useState("");
  const [memories, setMemories] = useState<Memory[]>([]);

  const [memoriesLoading, setMemoriesLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // ── Load logged-in user from localStorage ─────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const raw = localStorage.getItem("user");
      if (raw) {
        const u = JSON.parse(raw);
        if (u?.id && u?.full_name) {
          setUser(u);
        }
      }
    } catch {
      // silently ignore
    }
  }, [router]);

  // ── Fetch memories for logged-in user ─────────────────────────────────────
  const refreshMemories = useCallback(async () => {
    try {
      setMemoriesLoading(true);
      const rows: Memory[] = await api.getMemories();
      setMemories(rows);
    } catch {
      setMemories([]);
    } finally {
      setMemoriesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.id) refreshMemories();
  }, [user, refreshMemories]);

  // ── Save memory ───────────────────────────────────────────────────────────
  const save = async () => {
    setSaveError("");
    setSaveSuccess(false);

    if (!content.trim()) {
      setSaveError("Memory content cannot be empty.");
      return;
    }

    try {
      setSaving(true);
      await api.addMemory({ category, content: content.trim() });
      setContent("");
      setSaveSuccess(true);
      await refreshMemories();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to save memory.";
      setSaveError(detail);
    } finally {
      setSaving(false);
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-2xl space-y-8">

          {/* Header */}
          <div className="pt-4 space-y-1">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">
              {user?.full_name ? `${user.full_name}'s Memory Vault` : "Memory Vault"}
            </h1>
            <p className="text-[#163328]/70">
              Manage your personal memories
            </p>
          </div>

          {/* Memory creation form */}
          <div className="space-y-6 rounded-lg border border-[#163328]/10 bg-white/50 p-8">

            {/* Category */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#163328]">Category</label>
              <select
                id="memory-category"
                className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="routine">Daily Routine</option>
                <option value="family">Family &amp; Relationships</option>
                <option value="interests">Interests &amp; Hobbies</option>
                <option value="medical">Medical History</option>
                <option value="preferences">Preferences</option>
              </select>
            </div>

            {/* Content */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#163328]">Memory Content</label>
              <textarea
                id="memory-content"
                className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30 min-h-32 resize-none"
                value={content}
                onChange={(e) => { setContent(e.target.value); if (saveError) setSaveError(""); }}
                placeholder="Describe an important memory, person, place, or preference…"
              />
            </div>

            {/* Errors / success */}
            {saveError && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {saveError}
              </div>
            )}
            {saveSuccess && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700 font-medium">
                ✓ Memory saved and indexed successfully.
              </div>
            )}

            <button
              id="save-memory-btn"
              className="w-full rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 disabled:opacity-50 disabled:cursor-not-allowed transition"
              onClick={save}
              disabled={saving || !content.trim()}
            >
              {saving ? "Saving…" : "Save Memory"}
            </button>
          </div>

          {/* Saved memories list */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-2xl font-normal italic text-[#163328]">Saved Memories</h2>
              {!memoriesLoading && (
                <span className="text-sm text-[#163328]/60">{memories.length} total</span>
              )}
            </div>

            {memoriesLoading ? (
              <div className="flex items-center gap-3 rounded-lg bg-[#163328]/5 border border-[#163328]/10 px-5 py-4">
                <div className="w-4 h-4 border-2 border-[#163328] border-t-transparent rounded-full animate-spin shrink-0" />
                <p className="text-sm text-[#163328]/70">Loading memories…</p>
              </div>
            ) : memories.length === 0 ? (
              <div className="rounded-lg border border-[#163328]/10 bg-[#163328]/5 p-6 text-center">
                <p className="text-[#163328]/75">No memories saved yet. Add the first one above.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {memories.map((m) => (
                  <div key={m.id} className="rounded-lg border border-[#163328]/10 bg-white/50 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="inline-block px-3 py-1 bg-[#163328]/10 text-[#163328] text-xs font-semibold rounded capitalize">
                        {m.category}
                      </span>
                      <span className={`text-xs font-semibold px-2 py-1 rounded ${m.ingested ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                        {m.ingested ? "✓ Indexed" : "Pending"}
                      </span>
                    </div>
                    <p className="text-sm text-[#163328] mt-2">{m.content}</p>
                    <p className="text-xs text-[#163328]/50 mt-2">
                      {new Date(m.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info box */}
          <div className="space-y-2 rounded-lg bg-[#163328]/5 border border-[#163328]/10 p-4">
            <p className="text-sm font-semibold text-[#163328]">About Memory Vault</p>
            <p className="text-sm text-[#163328]/75">
              Memories are indexed into the AI system and used to provide more personalised, meaningful support during conversations.
            </p>
          </div>

        </div>
      </main>
    </div>
  );
}
