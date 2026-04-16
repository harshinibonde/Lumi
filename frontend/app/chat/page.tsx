"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";
import type { User } from "@/lib/api";

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [chat, setChat] = useState<any[]>([]);
  const [sending, setSending] = useState(false);
  const [usedMemories, setUsedMemories] = useState(false);
  const [classification, setClassification] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // GET /auth/me — verify authentication and get user profile
    const init = async () => {
      try {
        const meData = await api.getMe();
        setUser(meData);

        // Check if user has completed screening by checking screening history
        // GET /screening/results
        try {
          const results = await api.getScreeningResults();
          if (!results || results.length === 0) {
            router.push("/screening");
            return;
          }
        } catch {
          // If screening results fail, still allow chat if user exists
        }

        // GET /chat/history — load previous chat messages
        try {
          const history = await api.getChatHistory();
          setChat(Array.isArray(history) ? history : []);
        } catch {
          setChat([]);
        }
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

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  // POST /chat/message — send message and receive AI reply
  const send = async () => {
    if (!msg.trim() || sending) return;

    try {
      setSending(true);
      const response = await api.sendMessage(msg.trim());

      setUsedMemories(Boolean(response?.context_used));
      setClassification(response?.classification || null);

      // Text-to-speech for assistant reply
      if (response?.reply) {
        const utterance = new SpeechSynthesisUtterance(response.reply);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }

      setMsg("");

      // Refresh chat history — GET /chat/history
      const history = await api.getChatHistory();
      setChat(Array.isArray(history) ? history : []);
    } catch (err: any) {
      console.error("Chat send error:", err);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--cream)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-[#163328]/75 text-sm">Loading chat...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="pt-10">
            <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Chat with Lumi</h1>
            <p className="mt-2 text-[#163328]/75">Your AI companion for cognitive support</p>
          </div>

          {/* Classification badge from /chat/message response */}
          {classification && (
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#163328]/60">Communication mode:</span>
              <span className="inline-block px-3 py-1 rounded-full bg-[#163328]/10 text-xs font-semibold text-[#163328] capitalize">
                {classification}
              </span>
            </div>
          )}

          {usedMemories && (
            <div className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-700 border border-emerald-200">
              ✓ Using your memory vault for personalized responses
            </div>
          )}

          {/* Chat messages from GET /chat/history */}
          <div className="rounded-lg border border-[#163328]/10 bg-white/50 p-4 space-y-3 h-[60vh] overflow-y-auto">
            {chat.length === 0 ? (
              <p className="text-center text-[#163328]/50 py-8">Start a conversation with Lumi</p>
            ) : (
              chat.map((m: any) => (
                <div
                  key={m.id}
                  className={`p-4 rounded-lg ${
                    m.role === "assistant"
                      ? "bg-[#163328]/5 text-[#163328]"
                      : "bg-[#163328] text-white"
                  }`}
                >
                  <p className="text-xs uppercase font-semibold opacity-75 mb-1">
                    {m.role === "assistant" ? "Lumi" : "You"}
                  </p>
                  <p className="text-sm">{m.content}</p>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Message input → POST /chat/message */}
          <div className="flex gap-3">
            <input
              id="chat-input"
              className="flex-1 rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
              value={msg}
              onChange={(e) => setMsg(e.target.value)}
              placeholder={sending ? "Sending..." : "Type your message..."}
              onKeyDown={handleKeyDown}
              disabled={sending}
            />
            <button
              id="chat-send"
              className="rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white hover:bg-[#163328]/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={send}
              disabled={sending || !msg.trim()}
            >
              {sending ? "..." : "Send"}
            </button>
          </div>

          {/* Navigation links */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-sm text-[#163328]/75 hover:text-[#163328] transition"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
