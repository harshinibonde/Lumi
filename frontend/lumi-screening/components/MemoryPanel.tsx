"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { getState } from "@/lib/state";
import { useToast } from "@/components/Toast";
import styles from "@/styles/memory-panel.module.css";

interface PersonEntry {
  name: string;
  relation: string;
  note: string;
}

interface EventEntry {
  date: string;
  description: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function MemoryPanel({ open, onClose }: Props) {
  const toast = useToast();
  const [people, setPeople] = useState<PersonEntry[]>([]);
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [preferences, setPreferences] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load existing caregiver notes on open
  useEffect(() => {
    if (!open) return;
    const s = getState();
    if (!s.userId) return;

    setLoading(true);
    api
      .getUser(s.userId)
      .then((user) => {
        const raw = user.caregiver_notes || "";
        try {
          const parsed = JSON.parse(raw);
          setPeople(parsed.people || []);
          setEvents(parsed.events || []);
          setPreferences(parsed.preferences || "");
          setNotes(parsed.notes || "");
        } catch {
          // Legacy plain text — put in notes
          setNotes(raw);
          setPeople([]);
          setEvents([]);
          setPreferences("");
        }
      })
      .catch(() => {
        toast.push("Could not load memory data", "error");
      })
      .finally(() => setLoading(false));
  }, [open, toast]);

  const addPerson = () =>
    setPeople((p) => [...p, { name: "", relation: "", note: "" }]);
  const removePerson = (i: number) =>
    setPeople((p) => p.filter((_, idx) => idx !== i));
  const updatePerson = (i: number, field: keyof PersonEntry, value: string) =>
    setPeople((p) => p.map((item, idx) => (idx === i ? { ...item, [field]: value } : item)));

  const addEvent = () =>
    setEvents((e) => [...e, { date: "", description: "" }]);
  const removeEvent = (i: number) =>
    setEvents((e) => e.filter((_, idx) => idx !== i));
  const updateEvent = (i: number, field: keyof EventEntry, value: string) =>
    setEvents((e) => e.map((item, idx) => (idx === i ? { ...item, [field]: value } : item)));

  const save = useCallback(async () => {
    const s = getState();
    if (!s.userId) return;

    setSaving(true);
    const structured = {
      people: people.filter((p) => p.name.trim()),
      events: events.filter((e) => e.description.trim()),
      preferences: preferences.trim(),
      notes: notes.trim(),
    };

    try {
      await api.saveCaregiverNotes(s.userId, {
        caregiver_notes: JSON.stringify(structured),
        memories: [
          ...structured.people.map(
            (p) => `${p.name} (${p.relation}): ${p.note}`
          ),
          ...structured.events.map((e) => `${e.date}: ${e.description}`),
          structured.preferences,
          structured.notes,
        ].filter(Boolean),
        session_token: s.sessionToken || "",
      });
      toast.push("Memories saved ✓", "success");
    } catch {
      toast.push("Could not save — backend offline", "error");
    } finally {
      setSaving(false);
    }
  }, [people, events, preferences, notes, toast]);

  return (
    <>
      {/* Overlay */}
      {open && <div className={styles.overlay} onClick={onClose} />}

      <aside className={`${styles.panel} ${open ? styles.open : ""}`}>
        {/* Header */}
        <header className={styles.header}>
          <div>
            <h2 className={styles.title}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                favorite
              </span>
              Life & Memories
            </h2>
            <p className={styles.subtitle}>
              Caregiver-provided context for Lumi
            </p>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </header>

        {loading ? (
          <div className={styles.loading}>Loading...</div>
        ) : (
          <div className={styles.body}>
            {/* ─── Key People ─── */}
            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  group
                </span>
                Key People
              </h3>
              {people.map((p, i) => (
                <div key={i} className={styles.card}>
                  <div className={styles.cardRow}>
                    <input
                      className={styles.input}
                      placeholder="Name"
                      value={p.name}
                      onChange={(e) => updatePerson(i, "name", e.target.value)}
                    />
                    <input
                      className={styles.input}
                      placeholder="Relationship"
                      value={p.relation}
                      onChange={(e) =>
                        updatePerson(i, "relation", e.target.value)
                      }
                    />
                  </div>
                  <input
                    className={styles.input}
                    placeholder="Important details (e.g. visits every Sunday)"
                    value={p.note}
                    onChange={(e) => updatePerson(i, "note", e.target.value)}
                  />
                  <button
                    className={styles.removeBtn}
                    onClick={() => removePerson(i)}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                      delete
                    </span>
                  </button>
                </div>
              ))}
              <button className={styles.addBtn} onClick={addPerson}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  add
                </span>
                Add Person
              </button>
            </section>

            {/* ─── Important Events ─── */}
            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  event
                </span>
                Life Events
              </h3>
              {events.map((e, i) => (
                <div key={i} className={styles.card}>
                  <input
                    className={styles.input}
                    placeholder="When (e.g. Summer 1985)"
                    value={e.date}
                    onChange={(ev) => updateEvent(i, "date", ev.target.value)}
                  />
                  <input
                    className={styles.input}
                    placeholder="What happened (e.g. Built treehouse for Mary)"
                    value={e.description}
                    onChange={(ev) =>
                      updateEvent(i, "description", ev.target.value)
                    }
                  />
                  <button
                    className={styles.removeBtn}
                    onClick={() => removeEvent(i)}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                      delete
                    </span>
                  </button>
                </div>
              ))}
              <button className={styles.addBtn} onClick={addEvent}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  add
                </span>
                Add Event
              </button>
            </section>

            {/* ─── Preferences ─── */}
            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  tune
                </span>
                Preferences & Triggers
              </h3>
              <textarea
                className={styles.textarea}
                rows={3}
                placeholder="e.g. Loves gardening, avoid mentioning hospital visits, best in the morning..."
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
              />
            </section>

            {/* ─── Free Notes ─── */}
            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  edit_note
                </span>
                Caregiver Notes
              </h3>
              <textarea
                className={styles.textarea}
                rows={4}
                placeholder="Any additional context for Lumi..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </section>
          </div>
        )}

        {/* Save Button */}
        <footer className={styles.footer}>
          <button
            className={styles.saveBtn}
            onClick={save}
            disabled={saving || loading}
          >
            {saving ? "Saving..." : "Save Memories"}
          </button>
        </footer>
      </aside>
    </>
  );
}
