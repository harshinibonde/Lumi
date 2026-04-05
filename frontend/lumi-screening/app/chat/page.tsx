"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import MemoryPanel from "@/components/MemoryPanel";
import { api } from "@/lib/api";
import { getState, setState, type ChatMessage } from "@/lib/state";
import { useToast } from "@/components/Toast";
import { useTTS } from "@/hooks/useTTS";
import { useSTT } from "@/hooks/useSTT";
import styles from "@/styles/chat.module.css";

export default function ChatPage() {
  const router = useRouter();
  const toast = useToast();
  const tts = useTTS();
  const stt = useSTT();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [proactiveMsg, setProactiveMsg] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const prevMsgCountRef = useRef(0);

  /* ─── Auth + Init ─────────────────────────────────────────────── */
  useEffect(() => {
    const s = getState();
    if (!s.userId) {
      router.replace("/login");
      return;
    }
    setMessages(s.chatHistory || []);
    setSessionId(s.sessionId);

    // Auto-start a session if we don't have one
    if (!s.sessionId) {
      api
        .startSession({ user_id: s.userId })
        .then((res) => {
          setSessionId(res.session_id);
          setState({ sessionId: res.session_id });
          if (res.response) {
            const greet: ChatMessage = {
              role: "assistant",
              text: res.response,
              at: Date.now(),
            };
            setMessages([greet]);
            setState({ chatHistory: [greet] });
            setProactiveMsg(res.response);
          }
        })
        .catch(() => {
          const s2 = getState();
          if (!s2.chatHistory || s2.chatHistory.length === 0) {
            const greet: ChatMessage = {
              role: "assistant",
              text: `Hello ${s2.userName || "there"}! I'm Lumi, your cognitive companion. Share a memory or ask me anything — I'm here for you.`,
              at: Date.now(),
            };
            setMessages([greet]);
            setState({ chatHistory: [greet] });
            setProactiveMsg(greet.text);
          }
        });
    }
  }, [router]);

  /* ─── Auto-scroll on new messages ─────────────────────────────── */
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [messages]);

  /* ─── Auto-speak new AI messages ──────────────────────────────── */
  useEffect(() => {
    if (messages.length > prevMsgCountRef.current) {
      const latest = messages[messages.length - 1];
      if (latest?.role === "assistant") {
        tts.speak(latest.text);
      }
    }
    prevMsgCountRef.current = messages.length;
  }, [messages, tts]);

  /* ─── STT transcript → input field ────────────────────────────── */
  useEffect(() => {
    if (stt.transcript) {
      setInput(stt.transcript);
    }
  }, [stt.transcript]);

  /* ─── Send message ────────────────────────────────────────────── */
  const sendMessage = useCallback(
    async (overrideText?: string) => {
      const s = getState();
      const text = (overrideText || input).trim();
      if (!text || !s.userId || sending) return;

      const userMsg: ChatMessage = { role: "user", text, at: Date.now() };
      const updated = [...messages, userMsg];
      setMessages(updated);
      setState({ chatHistory: updated });
      setInput("");
      stt.clearTranscript();
      setSending(true);

      try {
        const res = await api.chat({
          user_id: s.userId,
          message: userMsg.text,
          session_id: sessionId || undefined,
        });

        const aiMsg: ChatMessage = {
          role: "assistant",
          text: res.response,
          at: Date.now(),
        };
        const final = [...updated, aiMsg];
        setMessages(final);
        setState({
          chatHistory: final,
          sessionId: res.session_id || sessionId,
        });
        if (res.session_id) setSessionId(res.session_id);
      } catch {
        const mockResponses = [
          `That's a lovely thought, ${s.userName || "friend"}. Tell me more about what comes to mind when you think about that.`,
          `I appreciate you sharing that with me. Can you recall any specific details — perhaps a place, a colour, or a feeling connected to it?`,
          `Thank you for telling me that. Memories like these are so valuable. What else do you remember about that time?`,
          `That's really interesting! Let's explore that a bit more. Was there anyone special with you during that moment?`,
          `I hear you. Sometimes it helps to talk through these things. What was the best part of that experience for you?`,
        ];
        const mockText =
          mockResponses[Math.floor(Math.random() * mockResponses.length)];
        const aiMsg: ChatMessage = {
          role: "assistant",
          text: mockText,
          at: Date.now(),
        };
        const final = [...updated, aiMsg];
        setMessages(final);
        setState({ chatHistory: final });
        toast.push("Using mock responses (backend offline)", "info");
      } finally {
        setSending(false);
      }
    },
    [input, messages, sending, sessionId, toast, stt]
  );

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  function handleMicToggle() {
    if (stt.isListening) {
      stt.stopListening();
      // Auto-send after a short delay to let transcript finalize
      setTimeout(() => {
        const s = getState();
        const text = stt.transcript.trim();
        if (text && s.userId) {
          void sendMessage(text);
        }
      }, 500);
    } else {
      tts.stop(); // Stop any TTS before listening
      stt.startListening();
    }
  }

  function formatTime(ts: number): string {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        {/* Decorative Halos */}
        <div className={`${styles.halo} ${styles.halo1}`} />
        <div className={`${styles.halo} ${styles.halo2}`} />

        {/* Header */}
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.lumiIcon}>
              <Image src="/Lumi_logo.png" alt="Lumi" width={24} height={24} />
            </div>
            <div>
              <h2 className={styles.headerTitle}>LumiAI</h2>
              <span className={styles.headerStatus}>
                {sending
                  ? "Lumi is reflecting..."
                  : stt.isListening
                    ? "Listening..."
                    : "Session in progress"}
              </span>
            </div>
          </div>
          <div className={styles.headerRight}>
            {/* Mute / Unmute TTS */}
            {tts.supported && (
              <button
                className={`${styles.headerAction} ${tts.muted ? styles.headerActionMuted : ""}`}
                onClick={tts.toggleMute}
                title={tts.muted ? "Unmute Lumi" : "Mute Lumi"}
              >
                <span className="material-symbols-outlined">
                  {tts.muted ? "volume_off" : "volume_up"}
                </span>
              </button>
            )}

            {/* Memory Panel Toggle */}
            <button
              className={styles.headerAction}
              onClick={() => setMemoryOpen(true)}
              title="Life & Memories"
            >
              <span className="material-symbols-outlined">
                auto_stories
              </span>
            </button>

            {/* Clear Session */}
            <button
              className={styles.headerAction}
              onClick={() => {
                setState({ chatHistory: [], sessionId: null });
                setMessages([]);
                setSessionId(null);
                toast.push("Session cleared.", "info");
              }}
            >
              <span className="material-symbols-outlined">refresh</span>
            </button>
          </div>
        </header>

        {/* ─── Proactive Banner ─── */}
        {proactiveMsg && messages.length <= 1 && (
          <div className={styles.proactiveBanner}>
            <div className={styles.proactiveDot} />
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              notifications_active
            </span>
            <span>Lumi has a message for you</span>
            <button
              className={styles.proactiveAction}
              onClick={() => {
                tts.speak(proactiveMsg);
                setProactiveMsg(null);
              }}
            >
              Listen
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                play_arrow
              </span>
            </button>
          </div>
        )}

        {/* Chat Feed */}
        <section className={styles.feed} ref={feedRef}>
          {messages.length === 0 && (
            <div className={styles.emptyChat}>
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 48, opacity: 0.15 }}
              >
                forum
              </span>
              <p>Share a memory or ask a question to begin.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={msg.role === "user" ? styles.userRow : styles.aiRow}
            >
              {msg.role === "assistant" && (
                <div className={styles.aiAvatar}>
                  <Image
                    src="/Lumi_logo.png"
                    alt="Lumi"
                    width={18}
                    height={18}
                  />
                </div>
              )}
              <div
                className={
                  msg.role === "user" ? styles.userBubble : styles.aiBubble
                }
              >
                <p className={styles.msgText}>{msg.text}</p>
                <div className={styles.bubbleFooter}>
                  <span className={styles.timestamp}>
                    {formatTime(msg.at)}
                  </span>
                  {msg.role === "assistant" && tts.supported && (
                    <button
                      className={styles.speakerBtn}
                      onClick={() => tts.speak(msg.text)}
                      title="Read aloud"
                    >
                      <span
                        className="material-symbols-outlined"
                        style={{ fontSize: 14 }}
                      >
                        volume_up
                      </span>
                    </button>
                  )}
                </div>
              </div>
              {msg.role === "user" && (
                <div className={styles.userAvatar}>
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 14 }}
                  >
                    person
                  </span>
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className={styles.aiRow}>
              <div className={styles.aiAvatar}>
                <Image
                  src="/Lumi_logo.png"
                  alt="Lumi"
                  width={18}
                  height={18}
                />
              </div>
              <span className={styles.thinking}>Lumi is reflecting...</span>
            </div>
          )}
        </section>

        {/* ─── Input Area ─── */}
        <section className={styles.inputSection}>
          <div className={styles.inputWrap}>
            <div className={styles.inputGlow} />
            <div
              className={`${styles.inputBar} ${stt.isListening ? styles.inputBarListening : ""}`}
            >
              {/* Mic Button */}
              <button
                className={`${styles.micBtn} ${stt.isListening ? styles.micBtnActive : ""}`}
                onClick={handleMicToggle}
                title={stt.isListening ? "Stop listening" : "Speak"}
              >
                <span className="material-symbols-outlined">
                  {stt.isListening ? "stop_circle" : "mic"}
                </span>
                {stt.isListening && <span className={styles.micPulse} />}
              </button>

              <input
                className={styles.inputField}
                type="text"
                placeholder={
                  stt.isListening
                    ? "Listening..."
                    : "Share a memory or ask a question..."
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending}
              />
              <div className={styles.inputActions}>
                <button
                  className={styles.sendBtn}
                  onClick={() => void sendMessage()}
                  disabled={!input.trim() || sending}
                >
                  <span className="material-symbols-outlined">
                    arrow_upward
                  </span>
                </button>
              </div>
            </div>
          </div>
          <div className={styles.suggestions}>
            <button
              className={styles.suggestion}
              onClick={() => setInput("Tell me about my family")}
            >
              Tell me about my family
            </button>
            <button
              className={styles.suggestion}
              onClick={() =>
                setInput("What did we talk about yesterday?")
              }
            >
              Review Yesterday&apos;s Notes
            </button>
          </div>
        </section>
      </main>

      {/* Memory Panel */}
      <MemoryPanel open={memoryOpen} onClose={() => setMemoryOpen(false)} />

      <MobileNav />
    </div>
  );
}
