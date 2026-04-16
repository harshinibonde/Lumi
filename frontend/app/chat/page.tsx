"use client";

import { useEffect, useRef, useState } from "react";
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

// ─── Component ────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [usedMemories, setUsedMemories] = useState(false);
  const [classification, setClassification] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // ── Init ────────────────────────────────────────────────────────────────────
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
          const history = await api.getChatHistory();
          setChat(Array.isArray(history) ? history : []);
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

  // ── Auto-scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, sending]);

  // ── Auto-resize textarea ────────────────────────────────────────────────────
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + "px";
    }
  }, [msg]);

  // ── Send message ────────────────────────────────────────────────────────────
  const send = async () => {
    if (!msg.trim() || sending) return;
    const userMessage = msg.trim();

    // Optimistic UI — add user message immediately
    const tempId = Date.now();
    setChat((prev) => [...prev, { id: tempId, role: "user", content: userMessage }]);
    setMsg("");
    setSending(true);

    try {
      const response = await api.sendMessage(userMessage);
      setUsedMemories(Boolean(response?.context_used));
      setClassification(response?.classification || null);

      // Text-to-speech
      if (response?.reply) {
        const utterance = new SpeechSynthesisUtterance(response.reply);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }

      // Refresh full history from server
      const history = await api.getChatHistory();
      setChat(Array.isArray(history) ? history : []);
    } catch (err: any) {
      console.error("Chat send error:", err);
      // Remove optimistic message and show error
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

  // ── Format time ─────────────────────────────────────────────────────────────
  const formatTime = (dateStr?: string) => {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch { return ""; }
  };

  // ── Loading state ───────────────────────────────────────────────────────────
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

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)] flex flex-col">
      <Navbar />

      {/* Main chat area — fills remaining space */}
      <div className="flex-1 flex flex-col pt-20 pb-0 max-w-3xl w-full mx-auto px-4 sm:px-6">

        {/* Status badges */}
        {(classification || usedMemories) && (
          <div className="flex items-center gap-2 flex-wrap py-3 px-1">
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
                {/* Lumi avatar */}
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#163328] to-[#2a5a43] flex items-center justify-center mx-auto shadow-lg shadow-[#163328]/10">
                  <svg className="w-8 h-8 text-white/90" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
                  </svg>
                </div>
                <div>
                  <h2 className="font-serif text-xl text-[#163328] font-medium">Hi{user.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}!</h2>
                  <p className="text-sm text-[#163328]/55 mt-1 leading-relaxed">
                    I&apos;m Lumi, your AI companion. How are you feeling today?
                  </p>
                </div>
                {/* Suggestion chips */}
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
                    {/* Avatar */}
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

                    {/* Message bubble */}
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

        {/* ── Fixed input bar ───────────────────────────────────────────────── */}
        <div className="sticky bottom-0 bg-gradient-to-t from-[var(--cream)] via-[var(--cream)] to-transparent pt-4 pb-5">
          <div className="relative flex items-end gap-2 rounded-2xl border border-[#163328]/12 bg-white shadow-lg shadow-[#163328]/5 p-2 transition-all focus-within:border-[#163328]/25 focus-within:shadow-xl focus-within:shadow-[#163328]/8">
            <textarea
              ref={inputRef}
              id="chat-input"
              className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-[#163328] placeholder:text-[#163328]/35 outline-none max-h-30 leading-relaxed"
              rows={1}
              value={msg}
              onChange={(e) => setMsg(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Lumi..."
              disabled={sending}
            />
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
