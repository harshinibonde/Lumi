"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * useTTS — Text-to-Speech hook using the browser SpeechSynthesis API.
 *
 * Every AI message is read aloud unless muted. Rate is slowed for elderly
 * listeners. Preferences are persisted to localStorage.
 */

const STORAGE_KEY = "lumi_tts_muted";

export function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [supported, setSupported] = useState(false);
  const utterRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    const ok = typeof window !== "undefined" && "speechSynthesis" in window;
    setSupported(ok);
    if (ok) {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "true") setMuted(true);
    }
  }, []);

  const toggleMute = useCallback(() => {
    setMuted((prev) => {
      const next = !prev;
      localStorage.setItem(STORAGE_KEY, String(next));
      if (next && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      }
      return next;
    });
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!supported || muted || !text.trim()) return;
      // Cancel anything in progress
      window.speechSynthesis.cancel();

      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 0.85; // Slower for elderly
      utter.pitch = 1.0;
      utter.volume = 1.0;

      // Try to pick a warm, clear voice
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.toLowerCase().includes("female") ||
            v.name.toLowerCase().includes("samantha") ||
            v.name.toLowerCase().includes("zira") ||
            v.name.toLowerCase().includes("google"))
      );
      if (preferred) utter.voice = preferred;

      utter.onstart = () => setIsSpeaking(true);
      utter.onend = () => setIsSpeaking(false);
      utter.onerror = () => setIsSpeaking(false);

      utterRef.current = utter;
      window.speechSynthesis.speak(utter);
    },
    [supported, muted]
  );

  const stop = useCallback(() => {
    if (supported) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [supported]);

  return { speak, stop, toggleMute, isSpeaking, muted, supported };
}
