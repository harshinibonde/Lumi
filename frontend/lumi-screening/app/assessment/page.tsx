"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import { api, type AssessmentQuestion } from "@/lib/api";
import { getState, setState } from "@/lib/state";
import { useToast } from "@/components/Toast";
import styles from "@/styles/assessment.module.css";

function speak(text: string, onUnsupported: () => void): void {
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) { onUnsupported(); return; }
  const u = new SpeechSynthesisUtterance(String(text || ""));
  u.rate = 0.95;
  u.pitch = 1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

export default function AssessmentPage() {
  const router = useRouter();
  const toast = useToast();
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const s = getState();
    if (!s.userId) { router.replace("/login"); return; }

    api.getAssessmentQuestions()
      .then((res) => {
        setQuestions(res.questions);
        // Restore saved answers if available
        const saved = getState().answers;
        if (saved && Object.keys(saved).length > 0) {
          setAnswers(saved);
          setIndex(getState().currentQuestionIndex || 0);
        }
        setState({ assessmentStartedAt: Date.now() });
        setLoading(false);
      })
      .catch(() => {
        toast.push("Could not load assessment questions.", "error");
        setLoading(false);
      });
  }, [router, toast]);

  const total = questions.length;
  const q = questions[Math.max(0, Math.min(index, total - 1))];
  const pct = total > 0 ? ((index + 1) / total) * 100 : 0;
  const currentAnswer = q ? (answers[q.id] || "") : "";
  const canNext = currentAnswer.trim().length > 0;

  const updateAnswer = useCallback(
    (value: string) => {
      if (!q) return;
      const next = { ...answers, [q.id]: value };
      setAnswers(next);
      setState({ answers: next, currentQuestionIndex: index });
    },
    [answers, index, q]
  );

  const finishAssessment = useCallback(async () => {
    const s = getState();
    const allAnswers = { ...answers };
    setSubmitting(true);

    try {
      const payload = {
        user_id: s.userId as number,
        answers: questions.map((q) => ({
          question_id: q.id,
          answer: allAnswers[q.id] || "",
          input_mode: "text",
        })),
        session_token: s.sessionToken || undefined,
      };

      const res = await api.submitAssessment(payload);

      setState({
        assessmentScore: res.score,
        lastAssessmentResult: res as unknown as Record<string, unknown>,
        answers: {},
        currentQuestionIndex: 0,
      });

      router.push("/results");
    } catch {
      toast.push("Error submitting assessment. Please try again.", "error");
      setSubmitting(false);
    }
  }, [answers, questions, router, toast]);

  function onNext() {
    if (!canNext || submitting) return;
    if (index >= total - 1) {
      void finishAssessment();
      return;
    }
    const ni = index + 1;
    setIndex(ni);
    setState({ currentQuestionIndex: ni, answers });
  }

  function onBack() {
    const ni = Math.max(0, index - 1);
    setIndex(ni);
    setState({ currentQuestionIndex: ni, answers });
  }

  if (loading || !q) {
    return (
      <div className={styles.shell}>
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.loadingWrap}>
            <div className={styles.pulse} />
            <p>Preparing your assessment...</p>
          </div>
        </main>
        <MobileNav />
      </div>
    );
  }

  const isChoice = q.type === "multiple_choice" && q.options.length > 0;

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        {/* Top Navigation */}
        <nav className={styles.topNav}>
          <div className={styles.topLeft}>
            <button className={styles.backBtn} onClick={() => router.push("/dashboard")}>
              <span className="material-symbols-outlined">arrow_back</span>
              <span>Back</span>
            </button>
          </div>
          <div className={styles.topCenter}>
            <span className={styles.brandMark}>Lumi</span>
          </div>
          <div className={styles.topRight}>
            <span className={styles.counter}>Question {index + 1} of {total}</span>
          </div>
        </nav>

        {/* Main Content */}
        <section className={styles.content}>
          <div className={styles.haloCenter} />

          <div className={styles.questionArea}>
            {/* Category Pill */}
            <span className={styles.category}>{q.category}</span>

            {/* Question */}
            <h1 className={styles.question}>{q.question}</h1>

            {/* Read Aloud */}
            <button
              className={styles.readAloud}
              onClick={() => speak(q.question, () => toast.push("TTS not supported.", "error"))}
            >
              <span className="material-symbols-outlined">volume_up</span>
              <span>Read Out Loud</span>
            </button>

            {/* Answer Area */}
            <div className={styles.answerArea}>
              {isChoice ? (
                <div className={styles.choiceGrid}>
                  {q.options.map((opt) => {
                    const on = currentAnswer.toLowerCase() === opt.toLowerCase();
                    return (
                      <button
                        key={opt}
                        className={`${styles.choiceBtn} ${on ? styles.choiceOn : ""}`}
                        onClick={() => updateAnswer(opt)}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <textarea
                  className={styles.textInput}
                  value={currentAnswer}
                  placeholder="Type your answer here..."
                  rows={1}
                  onChange={(e) => updateAnswer(e.target.value)}
                />
              )}

              {/* Voice Input */}
              <div className={styles.voiceSection}>
                <div className={styles.micRipple}>
                  <button className={styles.micBtn} onClick={() => toast.push("Voice input coming soon.", "info")}>
                    <span className="material-symbols-outlined" style={{ fontSize: 32 }}>mic</span>
                  </button>
                </div>
                <p className={styles.voiceLabel}>Voice Input</p>
                <p className={styles.voiceHint}>Or speak clearly to respond</p>
              </div>
            </div>

            {/* Navigation */}
            <div className={styles.navBtns}>
              <button className={`btn btn--ghost ${styles.navBtn}`} onClick={onBack} disabled={index === 0}>
                <span className="material-symbols-outlined">arrow_back</span>
                Back
              </button>
              <button
                className={`btn btn--primary btn--pill ${styles.navBtn} ${styles.nextBtn}`}
                onClick={onNext}
                disabled={!canNext || submitting}
              >
                {submitting ? "Submitting..." : index === total - 1 ? "Finish Assessment" : "Next Question"}
                <span className="material-symbols-outlined">arrow_forward</span>
              </button>
            </div>

            <p className={styles.reassure}>Take your time. There is no rush.</p>
          </div>
        </section>

        {/* Progress Bar */}
        <footer className={styles.progressFooter}>
          <div className={styles.progressTrack}>
            <div className={styles.progressFill} style={{ width: `${pct}%` }} />
          </div>
        </footer>
      </main>
      <MobileNav />
    </div>
  );
}
