export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  at: number;
}

export interface LumiState {
  userId: number | null;
  userName: string;
  userAge: number | null;
  sessionToken: string | null;
  sessionId: number | null;
  currentQuestionIndex: number;
  answers: Record<string, string>;
  assessmentScore: number | null;
  difficultyLevel: number;
  chatHistory: ChatMessage[];
  categoryScores: Record<string, { score: number; max: number }>;
  assessmentStartedAt: number | null;
  lastAssessmentResult: Record<string, unknown> | null;
}

const KEY = "lumiState";

const defaults: LumiState = {
  userId: null,
  userName: "",
  userAge: null,
  sessionToken: null,
  sessionId: null,
  currentQuestionIndex: 0,
  answers: {},
  assessmentScore: null,
  difficultyLevel: 1,
  chatHistory: [],
  categoryScores: {},
  assessmentStartedAt: null,
  lastAssessmentResult: null,
};

export function getState(): LumiState {
  if (typeof window === "undefined") return { ...defaults };
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return { ...defaults };
    const parsed = JSON.parse(raw) as Partial<LumiState>;
    return { ...defaults, ...parsed };
  } catch {
    return { ...defaults };
  }
}

export function setState(patch: Partial<LumiState>): LumiState {
  const next = { ...getState(), ...patch };
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem(KEY, JSON.stringify(next));
  }
  return next;
}

export function resetState(): void {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(KEY);
  }
}

export function isAuthenticated(): boolean {
  const s = getState();
  return !!(s.userId && s.sessionToken);
}
