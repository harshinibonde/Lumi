"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";
import type { User } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

interface ChatSession {
  id: number;
  created_at?: string;
}

// ─── Helper: speak with preferred voice ───────────────────────────────────────

function speakText(text: string, isMuted: boolean) {
  if (isMuted || typeof window === "undefined") return;
  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find((v) => {
    const name = v.name.toLowerCase();
    return name.includes("zira") || name.includes("female") || name.includes("samantha");
  });
  if (preferredVoice) utterance.voice = preferredVoice;
  utterance.rate = 0.95;
  utterance.pitch = 1.15;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const router = useRouter();

  // Core state
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [usedMemories, setUsedMemories] = useState(false);
  const [classification, setClassification] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);

  // Sidebar state
  const [sessionsList, setSessionsList] = useState<ChatSession[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Audio state
  const [isMuted, setIsMuted] = useState(false);

  // Voice input state
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");

  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // ── Pre-load TTS voices ──────────────────────────────────────────────────
  useEffect(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  // ── Load sessions list ───────────────────────────────────────────────────
  const refreshSessions = useCallback(async () => {
    try {
      const sessions = await api.getSessions();
      setSessionsList(Array.isArray(sessions) ? sessions : []);
    } catch {
      setSessionsList([]);
    }
  }, []);

  // ── Init ────────────────────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) { router.push("/login"); return; }

    const init = async () => {
      try {
        const meData = await api.getMe();
        setUser(meData);

        try {
          const results = await api.getScreeningResults();
          if (!results || results.length === 0) { router.push("/screening"); return; }
        } catch { /* allow chat even if screening check fails */ }

        try {
          const sessions = await api.getSessions();
          const sessionArray = Array.isArray(sessions) ? sessions : [];
          setSessionsList(sessionArray);

          let currentSessionId = null;
          if (sessionArray.length > 0) {
            currentSessionId = sessionArray[0].id;
            setSessionId(currentSessionId);
            const history = await api.getChatHistory(currentSessionId);
            setChat(Array.isArray(history) ? history : []);
          } else {
            const newSess = await api.createSession();
            currentSessionId = newSess.session_id ?? newSess.id;
            setSessionId(currentSessionId);
            setSessionsList([{ id: currentSessionId }]);
            setChat([]);
          }
        } catch { setChat([]); }
      } catch {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        router.push("/login");
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, [router]);

  // ── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, sending]);

  // ── Auto-resize textarea ─────────────────────────────────────────────────
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + "px";
    }
  }, [msg]);

  // ── Switch session ───────────────────────────────────────────────────────
  const switchSession = async (id: number) => {
    try {
      setSending(true);
      setSessionId(id);
      const history = await api.getChatHistory(id);
      setChat(Array.isArray(history) ? history : []);
      setSidebarOpen(false);
    } catch {
      setChat([]);
    } finally {
      setSending(false);
    }
  };

  // ── New Chat ─────────────────────────────────────────────────────────────
  const createNewSession = async () => {
    try {
      setSending(true);
      const res = await api.createSession();
      const newId = res.session_id ?? res.id; // backend returns { session_id }
      setSessionId(newId);
      setChat([]);
      await refreshSessions();
      setSidebarOpen(false);
    } catch (err) {
      console.error("Failed to create session", err);
    } finally {
      setSending(false);
    }
  };

  // ── Proactive Chat ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId || sending) return;
    const timeout = setTimeout(async () => {
      try {
        setSending(true);
        const response = await api.triggerProactiveChat(sessionId);
        if (response?.reply) {
          speakText(response.reply, isMuted);
        }
        const history = await api.getChatHistory(sessionId);
        setChat(Array.isArray(history) ? history : []);
      } catch (err) {
        console.error("Proactive failed", err);
      } finally {
        setSending(false);
      }
    }, 60000);
    return () => clearTimeout(timeout);
  }, [sessionId, chat, sending, isMuted]);

  // ── Send message ─────────────────────────────────────────────────────────
  const send = async () => {
    if (!msg.trim() || sending || !sessionId) return;
    const userMessage = msg.trim();

    const tempId = Date.now();
    setChat((prev) => [...prev, { id: tempId, role: "user", content: userMessage }]);
    setMsg("");
    setSending(true);

    try {
      const response = await api.sendMessage(userMessage, sessionId);
      setUsedMemories(Boolean(response?.context_used));
      setClassification(response?.classification || null);

      if (response?.reply) {
        speakText(response.reply, isMuted);
      }

      const history = await api.getChatHistory(sessionId);
      setChat(Array.isArray(history) ? history : []);
    } catch (err: any) {
      console.error("Chat send error:", err);
      setChat((prev) => prev.filter((m) => m.id !== tempId));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // ── Voice Input (Web Speech API — browser-native, no backend needed) ─────
  const recognitionRef = useRef<any>(null);

  const startVoice = () => {
    setVoiceError("");

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceError("Voice input is not supported in this browser. Try Chrome or Edge.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onstart = () => {
      setIsListening(true);
      setMsg(""); // clear existing text while recording
    };

    recognition.onresult = (event: any) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setMsg(transcript); // live preview as you speak
    };

    recognition.onerror = (event: any) => {
      if (event.error === "not-allowed") {
        setVoiceError("Microphone permission denied. Please allow access in browser settings.");
      } else if (event.error === "no-speech") {
        setVoiceError("No speech detected. Please try again.");
      } else {
        setVoiceError(`Voice error: ${event.error}`);
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      inputRef.current?.focus();
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopVoice = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  // ── Format time ──────────────────────────────────────────────────────────
  const formatTime = (dateStr?: string) => {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch { return ""; }
  };

  const formatSessionDate = (dateStr?: string) => {
    if (!dateStr) return "Session";
    try {
      return new Date(dateStr).toLocaleDateString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch { return "Session"; }
  };

  // ── Loading state ────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-[#163328]/60 text-sm">Loading chat...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  // ─── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)] flex flex-col">
      <Navbar />

      {/* Page body below navbar */}
      <div className="flex flex-1 pt-20 overflow-hidden relative">

        {/* ── Sidebar overlay for mobile ── */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/20 backdrop-blur-sm md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ── History Sidebar ── */}
        <aside
          className={`
            fixed md:relative z-30 md:z-auto top-0 md:top-auto left-0 h-full md:h-auto
            w-72 md:w-64 bg-white/80 backdrop-blur-xl border-r border-[#163328]/8
            flex flex-col pt-20 md:pt-0 transition-transform duration-300 ease-in-out
            ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          `}
        >
          {/* Sidebar header */}
          <div className="px-4 py-4 border-b border-[#163328]/8 flex items-center justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[#163328]/40">Chat History</p>
              <p className="text-sm font-medium text-[#163328] mt-0.5">{sessionsList.length} session{sessionsList.length !== 1 ? "s" : ""}</p>
            </div>
            <button
              onClick={createNewSession}
              disabled={sending}
              aria-label="New chat"
              className="w-8 h-8 rounded-full bg-[#163328] text-white flex items-center justify-center hover:bg-[#1e4435] transition disabled:opacity-50"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </button>
          </div>

          {/* Session list */}
          <div className="flex-1 overflow-y-auto py-2 px-2 space-y-1">
            {sessionsList.length === 0 ? (
              <p className="text-xs text-[#163328]/40 text-center mt-8 px-4">No sessions yet</p>
            ) : (
              sessionsList.map((s, idx) => (
                <button
                  key={s.id}
                  onClick={() => switchSession(s.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-150 flex items-center gap-3 group ${
                    sessionId === s.id
                      ? "bg-[#163328] text-white"
                      : "text-[#163328]/70 hover:bg-[#163328]/6 hover:text-[#163328]"
                  }`}
                >
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold ${
                    sessionId === s.id ? "bg-white/20 text-white" : "bg-[#163328]/10 text-[#163328]/60"
                  }`}>
                    {idx + 1}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-xs truncate">
                      {s.created_at ? formatSessionDate(s.created_at) : `Session ${idx + 1}`}
                    </p>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* ── Main Chat Area ── */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 sm:px-6">

            {/* Header Controls */}
            <div className="flex justify-between items-center mb-2 pt-2">
              <div className="flex items-center gap-3">
                {/* Mobile sidebar toggle */}
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  aria-label="Toggle history sidebar"
                  className="md:hidden w-9 h-9 rounded-xl flex items-center justify-center border border-[#163328]/12 bg-white text-[#163328] hover:bg-[#163328]/5 transition"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
                  </svg>
                </button>
                <div>
                  <p className="text-[#163328]/50 text-xs font-medium tracking-widest uppercase mb-0.5">Your Memory Companion</p>
                  <h1 className="text-2xl font-light text-[#163328] tracking-tight">Lumi</h1>
                </div>
              </div>

              {/* Mute toggle button */}
              <button
                onClick={() => {
                  setIsMuted((prev) => {
                    if (!prev) window.speechSynthesis.cancel();
                    return !prev;
                  });
                }}
                aria-label={isMuted ? "Unmute Lumi" : "Mute Lumi"}
                className={`flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-medium transition-all duration-200 ${
                  isMuted
                    ? "border-red-200 bg-red-50 text-red-600 hover:bg-red-100"
                    : "border-[#163328]/15 bg-white text-[#163328] hover:bg-[#163328]/5"
                }`}
              >
                {isMuted ? (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 9.75 19.5 12m0 0 2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6 4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
                    </svg>
                    Muted
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
                    </svg>
                    Sound On
                  </>
                )}
              </button>
            </div>

            {/* Status badges */}
            {(classification || usedMemories) && (
              <div className="flex items-center gap-2 flex-wrap py-2 px-1">
                {classification && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#163328]/8 text-xs font-medium text-[#163328]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#163328]/50" />
                    {classification} mode
                  </span>
                )}
                {usedMemories && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-xs font-medium text-emerald-700 border border-emerald-200/60">
                    <svg className="w-3 h-3" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm3.22 5.72-3.5 3.5a.75.75 0 0 1-1.06 0l-1.5-1.5a.75.75 0 1 1 1.06-1.06l.97.97 2.97-2.97a.75.75 0 0 1 1.06 1.06z"/></svg>
                    Using memory vault
                  </span>
                )}
              </div>
            )}

            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto space-y-1 py-4 scroll-smooth" style={{ minHeight: 0 }}>
              {chat.length === 0 && !sending ? (
                <div className="flex-1 flex items-center justify-center h-full min-h-[40vh]">
                  <div className="text-center space-y-4 max-w-sm px-4">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#163328] to-[#2a5a43] flex items-center justify-center mx-auto shadow-lg shadow-[#163328]/10">
                      <svg className="w-8 h-8 text-white/90" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="font-serif text-xl text-[#163328] font-medium">Hi{user.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}!</h2>
                      <p className="text-sm text-[#163328]/55 mt-1 leading-relaxed">
                        I&apos;m Lumi, your memory companion. How are you feeling today?
                      </p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-2 pt-2">
                      {["How are you?", "Tell me about my day", "I need some help"].map((suggestion) => (
                        <button
                          key={suggestion}
                          onClick={() => { setMsg(suggestion); inputRef.current?.focus(); }}
                          className="px-3.5 py-2 rounded-full border border-[#163328]/15 bg-white/60 text-xs font-medium text-[#163328]/70 hover:bg-white hover:border-[#163328]/25 hover:text-[#163328] transition-all duration-200"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {chat.map((m, i) => {
                    const isUser = m.role === "user";
                    const showAvatar = i === 0 || chat[i - 1]?.role !== m.role;

                    return (
                      <div
                        key={m.id}
                        className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"} ${showAvatar ? "mt-4" : "mt-0.5"}`}
                        style={{ animation: "fadeSlideIn 0.25s ease-out" }}
                      >
                        <div className={`flex-shrink-0 ${showAvatar ? "visible" : "invisible"}`}>
                          {isUser ? (
                            <div className="w-8 h-8 rounded-full bg-[#163328] flex items-center justify-center text-white text-xs font-bold">
                              {(user.full_name?.[0] || "U").toUpperCase()}
                            </div>
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#163328] to-[#2a5a43] flex items-center justify-center shadow-sm">
                              <svg className="w-4 h-4 text-white/90" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                              </svg>
                            </div>
                          )}
                        </div>

                        <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
                          {showAvatar && (
                            <p className={`text-[10px] font-semibold uppercase tracking-wider mb-1 px-1 ${isUser ? "text-right text-[#163328]/40" : "text-left text-[#163328]/40"}`}>
                              {isUser ? "You" : "Lumi"}
                            </p>
                          )}
                          <div
                            className={`px-4 py-2.5 text-sm leading-relaxed ${
                              isUser
                                ? "bg-[#163328] text-white rounded-2xl rounded-tr-md"
                                : "bg-white border border-[#163328]/8 text-[#163328] rounded-2xl rounded-tl-md shadow-sm"
                            }`}
                          >
                            <p className="whitespace-pre-wrap">{m.content}</p>
                          </div>
                          {m.created_at && (
                            <p className={`text-[10px] mt-1 px-1 ${isUser ? "text-right" : "text-left"} text-[#163328]/30`}>
                              {formatTime(m.created_at)}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {/* Typing indicator */}
                  {sending && (
                    <div className="flex gap-2.5 mt-4" style={{ animation: "fadeSlideIn 0.25s ease-out" }}>
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#163328] to-[#2a5a43] flex items-center justify-center shadow-sm flex-shrink-0">
                        <svg className="w-4 h-4 text-white/90" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                        </svg>
                      </div>
                      <div className="items-start">
                        <p className="text-[10px] font-semibold uppercase tracking-wider mb-1 px-1 text-[#163328]/40">Lumi</p>
                        <div className="bg-white border border-[#163328]/8 rounded-2xl rounded-tl-md px-5 py-3 shadow-sm">
                          <div className="flex gap-1.5 items-center h-4">
                            <span className="w-2 h-2 rounded-full bg-[#163328]/30 animate-bounce" style={{ animationDelay: "0ms" }} />
                            <span className="w-2 h-2 rounded-full bg-[#163328]/30 animate-bounce" style={{ animationDelay: "150ms" }} />
                            <span className="w-2 h-2 rounded-full bg-[#163328]/30 animate-bounce" style={{ animationDelay: "300ms" }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* ── Fixed input bar ── */}
            <div className="sticky bottom-0 bg-gradient-to-t from-[var(--cream)] via-[var(--cream)] to-transparent pt-4 pb-5">
              {/* Voice error */}
              {voiceError && (
                <p className="text-xs text-red-500 mb-2 px-1">{voiceError}</p>
              )}
              <div className="relative flex items-end gap-2 rounded-2xl border border-[#163328]/12 bg-white shadow-lg shadow-[#163328]/5 p-2 transition-all focus-within:border-[#163328]/25 focus-within:shadow-xl focus-within:shadow-[#163328]/8">

                {/* Voice input button */}
                <button
                  type="button"
                  onClick={isListening ? stopVoice : startVoice}
                  disabled={sending}
                  aria-label={isListening ? "Stop recording" : "Start voice input"}
                  className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    isListening
                      ? "bg-red-500 text-white animate-pulse shadow-md shadow-red-500/30"
                      : "bg-[#163328]/8 text-[#163328]/50 hover:bg-[#163328]/15 hover:text-[#163328] disabled:opacity-40"
                  }`}
                >
                  {isListening ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="6" width="12" height="12" rx="2" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                    </svg>
                  )}
                </button>

                {/* Text input */}
                <textarea
                  ref={inputRef}
                  id="chat-input"
                  className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-[#163328] placeholder:text-[#163328]/35 outline-none max-h-30 leading-relaxed"
                  rows={1}
                  value={msg}
                  onChange={(e) => setMsg(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isListening ? "Listening…" : "Message Lumi..."}
                  disabled={sending || isListening}
                />

                {/* Send button */}
                <button
                  id="chat-send"
                  className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    msg.trim() && !sending
                      ? "bg-[#163328] text-white hover:bg-[#1e4435] shadow-md shadow-[#163328]/20 scale-100"
                      : "bg-[#163328]/8 text-[#163328]/30 cursor-not-allowed scale-95"
                  }`}
                  onClick={send}
                  disabled={sending || !msg.trim()}
                  aria-label="Send message"
                >
                  <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M3.105 2.289a.75.75 0 0 0-.826.95l1.414 4.925A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.896 28.896 0 0 0 15.293-7.154.75.75 0 0 0 0-1.115A28.897 28.897 0 0 0 3.105 2.289Z" />
                  </svg>
                </button>
              </div>
              <p className="text-center text-[10px] text-[#163328]/30 mt-2">
                Lumi adapts responses based on your cognitive profile · Press Enter to send
              </p>
            </div>
          </div>
        </main>
      </div>

      {/* Keyframe animation */}
      <style jsx>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
