"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, IntakeData } from "@/lib/api";
import { useScreeningStore } from "@/store/screeningStore";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface UIStep {
  taskNumber: number;       // backend task 1-11
  domain: string;
  question: string;
  hint: string;
  inputType: "text" | "voice" | "canvas" | "checkbox";
  showImage?: "pencil" | "watch" | "pentagons";
  showCloseYourEyes?: boolean;
  checkboxLabels?: string[]; // for checkbox input type
  groupKey: string;         // groups sub-questions for the same backend task
  isLastInGroup: boolean;   // triggers API submission when true
  needsScoreAwarded: boolean; // true for MANUAL_TASKS (1,2,8,9,10,11)
}

interface StoredIntake extends IntakeData {
  setting: string;
}

// SpeechRecognition types (not in lib.dom.d.ts)
type SpeechResultEvent = Event & {
  readonly results: { [i: number]: { [j: number]: { transcript: string } } };
};
type AnyRecognition = {
  lang: string;
  interimResults: boolean;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  onresult: ((e: SpeechResultEvent) => void) | null;
  start: () => void;
  stop: () => void;
};

// ═══════════════════════════════════════════════════════════════════════════════
// AUTO-SCORING FUNCTIONS (replaces all caregiver scoring)
// ═══════════════════════════════════════════════════════════════════════════════

function getCurrentSeason(): string {
  const m = new Date().getMonth();
  if (m >= 2 && m <= 4) return "spring";
  if (m >= 5 && m <= 7) return "summer";
  if (m >= 8 && m <= 10) return "fall";
  return "winter";
}

function autoScoreOrientationTime(answers: string[]): number {
  const now = new Date();
  const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
  const expected = [
    now.getFullYear().toString(),
    getCurrentSeason(),
    now.getDate().toString(),
    days[now.getDay()],
    months[now.getMonth()],
  ];
  let score = 0;
  answers.forEach((ans, i) => {
    const n = ans.trim().toLowerCase();
    if (i === 0 && n.includes(expected[0])) score++;
    if (i === 1 && (n.includes(expected[1]) || (expected[1] === "fall" && n.includes("autumn")))) score++;
    if (i === 2 && n.includes(expected[2])) score++;
    if (i === 3 && n.includes(expected[3])) score++;
    if (i === 4 && n.includes(expected[4])) score++;
  });
  return score;
}

function autoScoreOrientationPlace(answers: string[]): number {
  // Require at least 3 chars, reject repeated/trivial tokens
  return answers.filter((a) => {
    const trimmed = a.trim();
    if (trimmed.length < 3) return false;
    const words = trimmed.split(/\s+/).filter((w) => w.length >= 2);
    if (words.length === 0) return false;
    const unique = new Set(words.map((w) => w.toLowerCase()));
    return unique.size >= 1;
  }).length;
}

function autoScoreReading(answer: string): number {
  const n = answer.toLowerCase();
  // Accept "close eyes", "shut eyes", "close your eyes", etc.
  const hasClose = n.includes("close") || n.includes("shut");
  const hasEyes = n.includes("eye");
  return hasClose && hasEyes ? 1 : 0;
}

function autoScoreWriting(answer: string): number {
  const words = answer.trim().split(/\s+/).filter((w) => w.length > 0);
  if (words.length < 3) return 0;
  // Must contain at least one common verb
  const commonVerbs = [
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "can", "could", "shall", "should", "may", "might",
    "go", "goes", "went", "gone", "like", "likes", "liked",
    "want", "wants", "wanted", "see", "sees", "saw", "seen",
    "eat", "eats", "ate", "run", "runs", "ran",
    "walk", "walks", "walked", "play", "plays", "played",
    "make", "makes", "made", "take", "takes", "took",
    "give", "gives", "gave", "know", "knows", "knew",
    "think", "thinks", "thought", "come", "comes", "came",
    "look", "looks", "looked", "feel", "feels", "felt",
    "say", "says", "said", "tell", "tells", "told",
    "write", "writes", "wrote", "read", "reads",
    "love", "loves", "loved", "need", "needs", "needed",
    "work", "works", "worked", "live", "lives", "lived",
  ];
  const lower = words.map((w) => w.toLowerCase().replace(/[^a-z]/g, ""));
  return lower.some((w) => commonVerbs.includes(w)) ? 1 : 0;
}

function computeScore(
  taskNumber: number,
  answers: string[],
  hasDrawn: boolean,
  checkedCount?: number
): number {
  switch (taskNumber) {
    case 1: return autoScoreOrientationTime(answers);
    case 2: return autoScoreOrientationPlace(answers);
    case 8: return checkedCount ?? 0;
    case 9: return autoScoreReading(answers[0] ?? "");
    case 10: return autoScoreWriting(answers[0] ?? "");
    case 11: return hasDrawn ? 1 : 0;
    default: return 0;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SPEECH RECOGNITION HELPER
// ═══════════════════════════════════════════════════════════════════════════════

function createRecognitionInstance(): AnyRecognition | null {
  if (typeof window === "undefined") return null;
  const SR =
    (window as Window & { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown })
      .SpeechRecognition ??
    (window as Window & { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition;
  if (!SR) return null;
  return new (SR as new () => AnyRecognition)();
}

// ═══════════════════════════════════════════════════════════════════════════════
// INLINE SVG ILLUSTRATIONS
// ═══════════════════════════════════════════════════════════════════════════════

function PencilIllustration() {
  return (
    <svg viewBox="0 0 200 200" width="180" height="180" className="mx-auto">
      {/* pencil body */}
      <rect x="60" y="30" width="30" height="120" rx="2" fill="#F7DC6F" stroke="#B7950B" strokeWidth="2" />
      {/* eraser */}
      <rect x="60" y="20" width="30" height="15" rx="3" fill="#F1948A" stroke="#C0392B" strokeWidth="1.5" />
      <line x1="60" y1="35" x2="90" y2="35" stroke="#B7950B" strokeWidth="1.5" />
      {/* metal band */}
      <rect x="58" y="145" width="34" height="10" rx="1" fill="#BDC3C7" stroke="#7F8C8D" strokeWidth="1" />
      {/* tip */}
      <polygon points="60,155 90,155 75,185" fill="#F5CBA7" stroke="#B7950B" strokeWidth="1.5" />
      <polygon points="71,175 79,175 75,185" fill="#2C3E50" />
      {/* wood grain lines */}
      <line x1="72" y1="35" x2="72" y2="145" stroke="#D4AC0D" strokeWidth="0.5" opacity="0.5" />
      <line x1="80" y1="35" x2="80" y2="145" stroke="#D4AC0D" strokeWidth="0.5" opacity="0.5" />
    </svg>
  );
}

function WatchIllustration() {
  return (
    <svg viewBox="0 0 200 200" width="180" height="180" className="mx-auto">
      {/* band top */}
      <rect x="70" y="10" width="60" height="50" rx="8" fill="#795548" stroke="#4E342E" strokeWidth="2" />
      {/* band bottom */}
      <rect x="70" y="140" width="60" height="50" rx="8" fill="#795548" stroke="#4E342E" strokeWidth="2" />
      {/* watch case */}
      <circle cx="100" cy="100" r="48" fill="#E0E0E0" stroke="#424242" strokeWidth="3" />
      {/* watch face */}
      <circle cx="100" cy="100" r="40" fill="white" stroke="#616161" strokeWidth="1.5" />
      {/* hour markers */}
      {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => (
        <line
          key={deg}
          x1={100 + 34 * Math.cos((deg - 90) * Math.PI / 180)}
          y1={100 + 34 * Math.sin((deg - 90) * Math.PI / 180)}
          x2={100 + 38 * Math.cos((deg - 90) * Math.PI / 180)}
          y2={100 + 38 * Math.sin((deg - 90) * Math.PI / 180)}
          stroke="#333" strokeWidth="2"
        />
      ))}
      {/* hour hand (10:10) */}
      <line x1="100" y1="100" x2="85" y2="72" stroke="#333" strokeWidth="3" strokeLinecap="round" />
      {/* minute hand */}
      <line x1="100" y1="100" x2="115" y2="72" stroke="#333" strokeWidth="2" strokeLinecap="round" />
      {/* center dot */}
      <circle cx="100" cy="100" r="3" fill="#333" />
      {/* crown */}
      <rect x="147" y="95" width="8" height="10" rx="2" fill="#9E9E9E" stroke="#616161" strokeWidth="1" />
    </svg>
  );
}

function PentagonsReference() {
  // Two overlapping regular pentagons
  const pentagon = (cx: number, cy: number, r: number): string => {
    const pts: string[] = [];
    for (let k = 0; k < 5; k++) {
      const angle = -Math.PI / 2 + (2 * Math.PI * k) / 5;
      pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
    }
    return pts.join(" ");
  };
  return (
    <svg viewBox="0 0 320 200" width="280" height="180" className="mx-auto">
      <polygon
        points={pentagon(120, 100, 65)}
        fill="none" stroke="#333" strokeWidth="2.5"
      />
      <polygon
        points={pentagon(200, 100, 65)}
        fill="none" stroke="#333" strokeWidth="2.5"
      />
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// STEP BUILDER — 20 individual questions mapping to 11 backend tasks
// ═══════════════════════════════════════════════════════════════════════════════

function buildSteps(
  registrationWords: string[],
  attentionVariant: string
): UIStep[] {
  return [
    // ── Orientation Time (task 1, 5 sub-questions, MANUAL) ─────────────────
    { taskNumber: 1, domain: "Orientation", question: "What year is it?", hint: "Enter the current year (e.g. 2026)", inputType: "text", groupKey: "task1", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 1, domain: "Orientation", question: "What season is it?", hint: "Spring, Summer, Fall/Autumn, or Winter", inputType: "text", groupKey: "task1", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 1, domain: "Orientation", question: "What is today's date (day of the month)?", hint: "Enter the number (e.g. 17)", inputType: "text", groupKey: "task1", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 1, domain: "Orientation", question: "What day of the week is it?", hint: "Monday, Tuesday, Wednesday…", inputType: "text", groupKey: "task1", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 1, domain: "Orientation", question: "What month is it?", hint: "Enter the current month", inputType: "text", groupKey: "task1", isLastInGroup: true, needsScoreAwarded: true },

    // ── Orientation Place (task 2, 5 sub-questions, MANUAL) ────────────────
    { taskNumber: 2, domain: "Orientation", question: "What country are we in?", hint: "Enter the country name", inputType: "text", groupKey: "task2", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 2, domain: "Orientation", question: "What state or province are we in?", hint: "Enter the state or province", inputType: "text", groupKey: "task2", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 2, domain: "Orientation", question: "What city or town are we in?", hint: "Enter the city name", inputType: "text", groupKey: "task2", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 2, domain: "Orientation", question: "What building or place are we in?", hint: "e.g. home, hospital, office", inputType: "text", groupKey: "task2", isLastInGroup: false, needsScoreAwarded: true },
    { taskNumber: 2, domain: "Orientation", question: "What floor or street address?", hint: "Enter the floor number or address", inputType: "text", groupKey: "task2", isLastInGroup: true, needsScoreAwarded: true },

    // ── Registration (task 3, auto-scored by backend) ─────────────────────
    { taskNumber: 3, domain: "Registration", question: `Listen carefully and repeat these 3 words: ${registrationWords.join(", ")}`, hint: "Say or type all three words", inputType: "voice", groupKey: "task3", isLastInGroup: true, needsScoreAwarded: false },

    // ── Attention (task 4, auto-scored by backend) ────────────────────────
    { taskNumber: 4, domain: "Attention", question: attentionVariant === "serial_7s" ? "Starting from 100, subtract 7 each time. Tell me each result." : "Spell the word WORLD backwards.", hint: attentionVariant === "serial_7s" ? "e.g., 93, 86, 79, 72, 65" : "Type the letters: D, L, R, O, W", inputType: "text", groupKey: "task4", isLastInGroup: true, needsScoreAwarded: false },

    // ── Recall (task 5, auto-scored by backend) ───────────────────────────
    { taskNumber: 5, domain: "Recall", question: "What were the 3 words I asked you to remember earlier?", hint: "Try to recall all three words", inputType: "text", groupKey: "task5", isLastInGroup: true, needsScoreAwarded: false },

    // ── Naming (task 6, 2 sub-questions, auto-scored by backend) ──────────
    { taskNumber: 6, domain: "Language", question: "What is this object?", hint: "Type the name of the object shown below", inputType: "text", showImage: "pencil", groupKey: "task6", isLastInGroup: false, needsScoreAwarded: false },
    { taskNumber: 6, domain: "Language", question: "What is this object?", hint: "Type the name of the object shown below", inputType: "text", showImage: "watch", groupKey: "task6", isLastInGroup: true, needsScoreAwarded: false },

    // ── Repetition (task 7, auto-scored by backend) ──────────────────────
    { taskNumber: 7, domain: "Language", question: "Repeat this sentence exactly: \"No ifs, ands, or buts.\"", hint: "Say or type the sentence exactly as shown", inputType: "voice", groupKey: "task7", isLastInGroup: true, needsScoreAwarded: false },

    // ── 3‑Stage Command (task 8, MANUAL — checkbox UI) ────────────────────
    { taskNumber: 8, domain: "Language", question: "Follow these 3 instructions and check each step you completed:", hint: "Check each step after completing it", inputType: "checkbox", checkboxLabels: ["Take a piece of paper in your right hand", "Fold it in half", "Put it on the floor"], groupKey: "task8", isLastInGroup: true, needsScoreAwarded: true },

    // ── Reading (task 9, MANUAL — frontend auto-scores) ──────────────────
    { taskNumber: 9, domain: "Language", question: "Read the instruction below and perform it.", hint: "Action required", inputType: "text", showCloseYourEyes: true, groupKey: "task9", isLastInGroup: true, needsScoreAwarded: true },

    // ── Writing (task 10, MANUAL — frontend auto-scores) ─────────────────
    { taskNumber: 10, domain: "Language", question: "Write a complete, meaningful sentence about anything you like.", hint: "Must contain a subject and a verb", inputType: "text", groupKey: "task10", isLastInGroup: true, needsScoreAwarded: true },

    // ── Copying (task 11, MANUAL — canvas drawing) ───────────────────────
    { taskNumber: 11, domain: "Visuospatial", question: "Copy the drawing of two intersecting pentagons shown below.", hint: "Draw using your mouse or touch screen", inputType: "canvas", showImage: "pentagons", groupKey: "task11", isLastInGroup: true, needsScoreAwarded: true },
  ];
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function ScreeningTasksPage() {
  const router = useRouter();
  const setStoreResult = useScreeningStore((s) => s.setResult);

  // ── Session state ──────────────────────────────────────────────────────────
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [steps, setSteps] = useState<UIStep[]>([]);
  const [initError, setInitError] = useState("");
  const [initializing, setInitializing] = useState(true);

  // ── Question flow ──────────────────────────────────────────────────────────
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [groupAnswers, setGroupAnswers] = useState<Record<string, string[]>>({});
  const [validationError, setValidationError] = useState("");

  // ── UI control ─────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // ── Canvas state ───────────────────────────────────────────────────────────
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef(false);
  const [hasDrawn, setHasDrawn] = useState(false);

  // ── Checkbox state (for 3-stage command) ────────────────────────────────
  const [checkedSteps, setCheckedSteps] = useState<boolean[]>([false, false, false]);

  // ── Action task state (for Task 9) ─────────────────────────────────────────
  const [task9Completed, setTask9Completed] = useState(false);

  const currentStep = steps[currentStepIndex] ?? null;

  // ── Session Initialization ─────────────────────────────────────────────────

  useEffect(() => {
    const init = async () => {
      try {
        const raw = localStorage.getItem("intake");
        if (!raw) { router.push("/screening"); return; }

        const intake: StoredIntake = JSON.parse(raw);
        const setting = intake.setting ?? "home";

        const res = await api.startScreening(setting);
        setSessionId(res.session.id);

        const v = res.variants ?? {};
        const regWords: string[] = v.registration_words ?? ["apple", "table", "penny"];
        const attVariant: string = v.attention_variant ?? "serial_7s";

        setSteps(buildSteps(regWords, attVariant));
      } catch (err: unknown) {
        setInitError(err instanceof Error ? err.message : "Failed to start session");
      } finally {
        setInitializing(false);
      }
    };
    init();
  }, [router]);

  // ── Text-to-Speech ────────────────────────────────────────────────────────

  const speakQuestion = useCallback(() => {
    if (!currentStep) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(currentStep.question.replace(/\n/g, ". "));
    u.lang = "en-US";
    window.speechSynthesis.speak(u);
  }, [currentStep]);

  // ── Voice Input ────────────────────────────────────────────────────────────

  const startVoiceInput = useCallback(() => {
    const recognition = createRecognitionInstance();
    if (!recognition) {
      setValidationError("Voice input not supported in this browser. Please type your answer.");
      return;
    }
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => {
      setIsListening(false);
      setValidationError("Voice recognition failed. Please type your answer.");
    };
    recognition.onresult = (event: SpeechResultEvent) => {
      setAnswer(event.results[0][0].transcript);
      setValidationError("");
    };
    recognition.start();
  }, []);

  // ── Canvas Drawing ────────────────────────────────────────────────────────

  const getCoords = (e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    if ("touches" in e) {
      return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    }
    return { x: (e as React.MouseEvent).clientX - rect.left, y: (e as React.MouseEvent).clientY - rect.top };
  };

  const onCanvasDown = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    isDrawingRef.current = true;
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const { x, y } = getCoords(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const onCanvasMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawingRef.current) return;
    e.preventDefault();
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const { x, y } = getCoords(e);
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#163328";
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasDrawn(true);
  };

  const onCanvasUp = () => { isDrawingRef.current = false; };

  const clearCanvas = () => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx || !canvasRef.current) return;
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    setHasDrawn(false);
  };

  // ── Complete Test ──────────────────────────────────────────────────────────

  const completeTest = useCallback(async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const raw = localStorage.getItem("intake");
      if (!raw) throw new Error("Intake data missing");

      const stored: StoredIntake = JSON.parse(raw);
      const intake: IntakeData = {
        age: Number(stored.age),
        gender: Number(stored.gender),
        education: Number(stored.education),
        functional_assessment: Number(stored.functional_assessment),
        adl: Number(stored.adl),
        memory_complaints: Number(stored.memory_complaints),
        behavioral_problems: Number(stored.behavioral_problems),
      };

      const result = await api.completeScreening({ session_id: sessionId, intake });
      setStoreResult(result);
      router.push("/results");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err instanceof Error ? err.message : "Failed to complete test");
      setValidationError(`Completion error: ${detail}`);
    } finally {
      setLoading(false);
    }
  }, [sessionId, router, setStoreResult]);

  // ── Submit Answer & Advance ────────────────────────────────────────────────

  const handleNext = useCallback(async () => {
    if (!sessionId || !currentStep) return;
    setValidationError("");

    // ── Get current answer value ──
    let stepAnswer =
      currentStep.inputType === "canvas"
        ? canvasRef.current?.toDataURL() ?? ""
        : currentStep.inputType === "checkbox"
        ? (currentStep.checkboxLabels ?? []).filter((_, i) => checkedSteps[i]).join("; ") || "none completed"
        : answer.trim();

    if (currentStep.taskNumber === 9) {
      stepAnswer = "completed";
    }

    // ── Validate ──
    if (currentStep.inputType === "canvas") {
      if (!hasDrawn) { setValidationError("Please draw your answer on the canvas."); return; }
    } else if (currentStep.inputType === "checkbox") {
      // 0 checked is a valid score (patient may fail all steps)
    } else if (currentStep.taskNumber === 9) {
      if (!task9Completed) { setValidationError("Please confirm you have completed the instruction."); return; }
    } else {
      if (!stepAnswer) { setValidationError("Please provide an answer before continuing."); return; }
    }

    // ── Buffer answer for group ──
    const newGroupAnswers = { ...groupAnswers };
    if (!newGroupAnswers[currentStep.groupKey]) newGroupAnswers[currentStep.groupKey] = [];
    newGroupAnswers[currentStep.groupKey].push(stepAnswer);
    setGroupAnswers(newGroupAnswers);

    // ── If last in group → submit to backend ──
    if (currentStep.isLastInGroup) {
      const allAnswers = newGroupAnswers[currentStep.groupKey];
      const combinedText = allAnswers.join(", ");

      const payload: {
        session_id: number;
        task_number: number;
        domain: string;
        answer_text: string;
        score_awarded?: number;
      } = {
        session_id: sessionId,
        task_number: currentStep.taskNumber,
        domain: currentStep.domain,
        answer_text: combinedText,
      };

      // For MANUAL_TASKS, compute score automatically
      if (currentStep.needsScoreAwarded) {
        if (currentStep.taskNumber === 9) {
          payload.score_awarded = 1;
        } else {
          const checkCount = currentStep.inputType === "checkbox" ? checkedSteps.filter(Boolean).length : undefined;
          payload.score_awarded = computeScore(currentStep.taskNumber, allAnswers, hasDrawn, checkCount);
        }
      }

      try {
        setLoading(true);
        await api.submitAnswer(payload);
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          (err instanceof Error ? err.message : "Submission failed");
        setValidationError(`Error: ${detail}`);
        setLoading(false);
        return;
      } finally {
        setLoading(false);
      }
    }

    // ── Advance or complete ──
    setAnswer("");
    setHasDrawn(false);
    setCheckedSteps([false, false, false]);
    setTask9Completed(false);

    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      await completeTest();
    }
  }, [sessionId, currentStep, answer, hasDrawn, checkedSteps, groupAnswers, currentStepIndex, steps.length, completeTest, task9Completed]);

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════

  // ── Loading state ──
  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--cream)]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#163328] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-[#163328]/75 text-sm">Starting your session…</p>
        </div>
      </div>
    );
  }

  // ── Init error ──
  if (initError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--cream)] p-6">
        <div className="max-w-md w-full bg-white/60 rounded-xl border border-red-200 p-8 text-center space-y-4">
          <p className="text-red-700 font-semibold">Session failed to start</p>
          <p className="text-[#163328]/70 text-sm">{initError}</p>
          <button onClick={() => router.push("/screening")} className="mt-4 px-6 py-2 bg-[#163328] text-white rounded-lg text-sm">
            Go back to intake
          </button>
        </div>
      </div>
    );
  }

  // ── Questions not loaded yet ──
  if (!currentStep) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--cream)]">
        <p className="text-[#163328]/70">Loading questions…</p>
      </div>
    );
  }

  const progressPercent = Math.round((currentStepIndex / steps.length) * 100);

  // ── Main UI ───────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)] flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-2xl space-y-5">

        {/* Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm text-[#163328]/60">
            <span>Question {currentStepIndex + 1} of {steps.length}</span>
            <span className="font-medium text-[#163328]">{currentStep.domain}</span>
          </div>
          <div className="w-full h-1.5 bg-[#163328]/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#163328] rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl border border-[#163328]/10 p-6 sm:p-8 space-y-5 shadow-sm">

          {/* Question text */}
          <div className="space-y-2">
            <p className="text-lg sm:text-xl font-serif text-[#163328] leading-relaxed whitespace-pre-line">
              {currentStep.question}
            </p>
            <p className="text-sm text-[#163328]/50 italic">{currentStep.hint}</p>
          </div>

          {/* TTS button */}
          <button type="button" onClick={speakQuestion} className="inline-flex items-center gap-2 text-sm text-[#163328]/60 hover:text-[#163328] transition-colors">
            <span>🔊</span><span>Read aloud</span>
          </button>

          {/* CLOSE YOUR EYES instruction banner */}
          {currentStep.showCloseYourEyes && (
            <div className="bg-[#163328] text-white text-center py-6 rounded-xl">
              <p className="text-3xl font-bold tracking-widest">CLOSE YOUR EYES</p>
            </div>
          )}

          {/* Object images */}
          {currentStep.showImage === "pencil" && (
            <div className="flex justify-center p-4 bg-gray-50 rounded-xl border border-gray-200">
              <PencilIllustration />
            </div>
          )}
          {currentStep.showImage === "watch" && (
            <div className="flex justify-center p-4 bg-gray-50 rounded-xl border border-gray-200">
              <WatchIllustration />
            </div>
          )}

          {/* Pentagon reference + drawing canvas */}
          {currentStep.showImage === "pentagons" && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-[#163328]">Reference image:</p>
              <div className="flex justify-center p-3 bg-gray-50 rounded-xl border border-gray-200">
                <PentagonsReference />
              </div>
            </div>
          )}

          {/* Input area */}
          {currentStep.inputType === "canvas" ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-[#163328]">Your drawing:</p>
              <div className="border-2 border-[#163328]/20 rounded-xl overflow-hidden bg-white">
                <canvas
                  ref={canvasRef}
                  width={560}
                  height={300}
                  className="w-full cursor-crosshair touch-none"
                  onMouseDown={onCanvasDown}
                  onMouseMove={onCanvasMove}
                  onMouseUp={onCanvasUp}
                  onMouseLeave={onCanvasUp}
                  onTouchStart={onCanvasDown}
                  onTouchMove={onCanvasMove}
                  onTouchEnd={onCanvasUp}
                />
              </div>
              <button type="button" onClick={clearCanvas} className="text-sm text-red-500 hover:text-red-700 transition-colors">
                ✕ Clear drawing
              </button>
            </div>
          ) : currentStep.inputType === "checkbox" && currentStep.checkboxLabels ? (
            <div className="space-y-3">
              {currentStep.checkboxLabels.map((label, i) => (
                <label
                  key={i}
                  className="flex items-center gap-3 p-4 rounded-lg border border-[#163328]/20 bg-white cursor-pointer hover:bg-[#163328]/5 transition select-none"
                >
                  <input
                    type="checkbox"
                    checked={checkedSteps[i] ?? false}
                    onChange={(e) => {
                      const next = [...checkedSteps];
                      next[i] = e.target.checked;
                      setCheckedSteps(next);
                    }}
                    className="w-5 h-5 rounded border-[#163328]/30 text-[#163328] accent-[#163328] focus:ring-[#163328]/30"
                  />
                  <span className="text-[#163328]">
                    <span className="font-medium">Step {i + 1}:</span> {label}
                  </span>
                </label>
              ))}
            </div>
          ) : currentStep.taskNumber === 9 ? (
            <div className="space-y-3">
              <button
                type="button"
                className={`w-full py-4 rounded-lg border-2 transition-all font-semibold ${
                  task9Completed
                    ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                    : "border-[#163328]/20 bg-white text-[#163328] hover:bg-[#163328]/5"
                }`}
                onClick={() => { setTask9Completed(true); if (validationError) setValidationError(""); }}
              >
                {task9Completed ? "✓ Instruction Completed" : "I have completed this instruction"}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                id={`answer-step-${currentStepIndex}`}
                value={answer}
                onChange={(e) => { setAnswer(e.target.value); if (validationError) setValidationError(""); }}
                placeholder="Type your answer here…"
                rows={2}
                className="w-full px-4 py-3 rounded-lg border border-[#163328]/20 bg-white text-[#163328] placeholder-[#163328]/30 resize-none focus:outline-none focus:ring-2 focus:ring-[#163328]/30 transition"
              />

              {/* Voice input */}
              <button
                type="button"
                onClick={startVoiceInput}
                disabled={isListening || loading}
                className={`inline-flex items-center gap-2 text-sm transition-colors ${
                  isListening ? "text-red-500 animate-pulse" : "text-[#163328]/60 hover:text-[#163328]"
                }`}
              >
                <span>🎤</span>
                <span>{isListening ? "Listening…" : "Use voice input"}</span>
              </button>
            </div>
          )}

          {/* Validation error */}
          {validationError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {validationError}
            </div>
          )}

          {/* Submit button */}
          <button
            id={`submit-step-${currentStepIndex}`}
            type="button"
            onClick={handleNext}
            disabled={loading}
            className="w-full py-3 bg-[#163328] text-white rounded-lg font-semibold hover:bg-[#163328]/90 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? "Submitting…" : currentStepIndex === steps.length - 1 ? "Complete Assessment" : "Next Question"}
          </button>
        </div>
      </div>
    </div>
  );
}