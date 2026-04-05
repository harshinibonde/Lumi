"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import { getState } from "@/lib/state";
import type { AssessmentSubmitResponse, AssessmentDetailedResult } from "@/lib/api";
import styles from "@/styles/results.module.css";

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<AssessmentSubmitResponse | null>(null);

  useEffect(() => {
    const s = getState();
    if (!s.userId) { router.replace("/login"); return; }
    if (s.lastAssessmentResult) {
      setResult(s.lastAssessmentResult as unknown as AssessmentSubmitResponse);
    } else if (s.assessmentScore != null) {
      // Fallback for legacy state
      setResult({
        score: s.assessmentScore,
        max_score: 30,
        classification: "Assessment Complete",
        score_classification: "See Details",
      } as AssessmentSubmitResponse);
    } else {
      router.replace("/assessment");
    }
  }, [router]);

  if (!result) {
    return (
      <div className={styles.shell}>
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.loading}>Loading results...</div>
        </main>
        <MobileNav />
      </div>
    );
  }

  const detailed = Array.isArray(result.results) ? result.results : [];

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.inner}>
          <div className={styles.haloCenter} />

          {/* Score */}
          <div className={styles.scoreSection}>
            <span className={styles.scoreLabel}>Assessment Score</span>
            <h1 className={styles.scoreValue}>
              {result.score} / {result.max_score}
            </h1>
            <h2 className={styles.classification}>
              {result.score_classification || result.classification}
            </h2>
            <p className={styles.supportText}>
              LumiAI can help you stay active and engaged.
            </p>
          </div>

          {/* ML Pipeline */}
          {result.svm_classification && (
            <div className={styles.pipelineSection}>
              <span className={styles.pipelineLabel}>ML Analysis</span>
              <div className={styles.pipelineGrid}>
                <div className={styles.pipelineCard}>
                  <span className={styles.pipelineModel}>SVM</span>
                  <strong>{result.svm_classification}</strong>
                  <span className={styles.confidence}>
                    {result.svm_confidence != null ? `${Math.round(result.svm_confidence * 100)}%` : "—"}
                  </span>
                </div>
                <div className={styles.pipelineCard}>
                  <span className={styles.pipelineModel}>Random Forest</span>
                  <strong>{result.random_forest_classification}</strong>
                  <span className={styles.confidence}>
                    {result.random_forest_confidence != null ? `${Math.round(result.random_forest_confidence * 100)}%` : "—"}
                  </span>
                </div>
                <div className={styles.pipelineCard}>
                  <span className={styles.pipelineModel}>MLP</span>
                  <strong>{result.mlp_classification}</strong>
                  <span className={styles.confidence}>
                    {result.mlp_confidence != null ? `${Math.round(result.mlp_confidence * 100)}%` : "—"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* CTA */}
          <Link href="/chat" className={`btn btn--primary btn--pill btn--lg ${styles.ctaBtn}`}>
            Start Daily Exercises with LumiAI
            <span className="material-symbols-outlined">arrow_forward</span>
          </Link>

          {/* Detailed Review */}
          {detailed.length > 0 && (
            <div className={styles.reviewSection}>
              <span className={styles.reviewLabel}>Review Your Responses</span>
              <div className={styles.reviewList}>
                {detailed.filter((r) => !r.is_correct).map((r, i) => (
                  <div key={i} className={styles.reviewItem}>
                    <p className={styles.reviewQ}>{r.question}</p>
                    <p className={styles.reviewAnswer}>
                      Your answer: <span className={styles.strikeThrough}>{r.user_answer}</span>
                    </p>
                    <p className={styles.reviewCorrect}>
                      Correct: <strong>{r.correct_answer}</strong>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Meta */}
          <div className={styles.metaFooter}>
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>schedule</span>
            Completed {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
          </div>
          <Link href="/dashboard" className={styles.historyLink}>
            Return to Dashboard
          </Link>
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
