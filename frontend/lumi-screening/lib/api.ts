const BASE = "http://127.0.0.1:8000";

/* ─── Response Types ────────────────────────────────────────────── */

export interface HealthResponse {
  status: string;
  database: boolean;
}

export interface OllamaHealthResponse {
  reachable: boolean;
  model?: string;
}

export interface User {
  id: number;
  name: string;
  age: number;
  difficulty_level: number;
  caregiver_notes?: string;
  email?: string;
  patient_email?: string;
  caregiver_name?: string;
  caregiver_email?: string;
  gender?: string;
  education_years?: number;
}

export interface CreateUserPayload {
  name: string;
  age: number;
  patient_email: string;
  gender?: string;
  education_years?: number;
  handedness?: string;
  native_language?: string;
  lives_alone?: boolean;
  caregiver_name?: string;
  caregiver_email?: string;
  caregiver_notes?: string;
  email?: string;
}

export interface CreateUserResponse {
  user_id: number;
  name: string;
  message: string;
}

export interface OTPRequestPayload {
  patient_email: string;
}

export interface OTPRequestResponse {
  message: string;
  user_id: number;
}

export interface OTPVerifyPayload {
  user_id: number;
  otp: string;
}

export interface OTPVerifyResponse {
  user_id: number;
  session_token: string;
  name: string;
  message: string;
}

export interface ValidateSessionResponse {
  user_id: number;
  name: string;
  valid: boolean;
}

export interface AssessmentQuestion {
  id: string;
  question: string;
  category: string;
  weight: number;
  type: string;
  options: string[];
  prompt_words: string[];
}

export interface AssessmentQuestionsResponse {
  name: string;
  total_questions: number;
  total_points: number;
  questions: AssessmentQuestion[];
}

export interface AssessmentAnswerInput {
  question_id: string;
  answer: string | string[] | Record<string, string>;
  input_mode?: string;
}

export interface AssessmentSubmitPayload {
  user_id: number;
  answers: AssessmentAnswerInput[];
  session_token?: string;
}

export interface AssessmentDecision {
  action: string;
  should_alert_caregiver: boolean;
  should_redirect_to_support: boolean;
  message: string;
}

export interface AssessmentSubmitResponse {
  assessment_id: number;
  score: number;
  max_score: number;
  classification: string;
  score_classification: string;
  svm_classification: string;
  random_forest_classification: string;
  mlp_classification: string;
  svm_confidence: number;
  random_forest_confidence: number;
  mlp_confidence: number;
  pipeline_version: string;
  decision: AssessmentDecision;
  caregiver_alert_sent: boolean;
  voice_answer_count: number;
  redirect_to_support: boolean;
  results: AssessmentDetailedResult[];
}

export interface AssessmentDetailedResult {
  question_id: string;
  question: string;
  category: string;
  weight: number;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
}

export interface AnalyticsResponse {
  summary: {
    total_logs: number;
    chat_turns: number;
    proactive_opens: number;
    avg_latency_chat: number | null;
    avg_accuracy_chat: number | null;
    current_difficulty: number;
    approx_distinct_sessions: number;
  };
  series: AnalyticsSeriesRow[];
  difficulty_timeline: DifficultyChange[];
  sessions_by_day: SessionDay[];
  interaction_events_by_day: Record<string, number>;
  insights: Record<string, unknown>;
}

export interface AnalyticsSeriesRow {
  session_id: number;
  session_type: string;
  session_timestamp: string;
  task_type: string;
  accuracy: number | null;
  latency: number | null;
  hints_used: number;
  task_focus: string;
}

export interface DifficultyChange {
  from_level: number;
  to_level: number;
  changed_at: string;
}

export interface SessionDay {
  day: string;
  count: number;
}

export interface ChatPayload {
  user_id: number;
  message: string;
  session_id?: number;
  hints_used?: number;
  task_focus?: string;
}

export interface ChatResponse {
  response: string;
  latency_seconds: number;
  session_id: number;
}

export interface SessionStartPayload {
  user_id: number;
}

export interface SessionStartResponse {
  response: string;
  session_id: number;
  latency_seconds: number;
}

export interface CaregiverNotesPayload {
  caregiver_notes: string;
  memories: string[];
  session_token: string;
}

export interface LatestAssessmentResponse {
  assessment: Record<string, unknown> | null;
}

/* ─── Request helper ────────────────────────────────────────────── */

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return {} as T;
  return (await res.json()) as T;
}

/* ─── API object ────────────────────────────────────────────────── */

export const api = {
  /* Health */
  health: () => request<HealthResponse>("GET", "/health"),
  ollamaHealth: () => request<OllamaHealthResponse>("GET", "/health/ollama"),

  /* Auth */
  createUser: (p: CreateUserPayload) =>
    request<CreateUserResponse>("POST", "/users", p),
  requestOtp: (p: OTPRequestPayload) =>
    request<OTPRequestResponse>("POST", "/auth/request-otp", p),
  verifyOtp: (p: OTPVerifyPayload) =>
    request<OTPVerifyResponse>("POST", "/auth/verify-otp", p),
  validateSession: (token: string) =>
    request<ValidateSessionResponse>(
      "GET",
      `/auth/validate-session?session_token=${encodeURIComponent(token)}`
    ),
  logout: (session_token: string) =>
    request<{ message: string }>("POST", "/auth/logout", { session_token }),

  /* Users */
  getUser: (uid: number) => request<User>("GET", `/users/${uid}`),
  listUsers: () => request<{ users: User[] }>("GET", "/users"),
  saveCaregiverNotes: (uid: number, p: CaregiverNotesPayload) =>
    request<{ user_id: number; memories_stored: number; message: string }>(
      "POST",
      `/users/${uid}/caregiver-notes`,
      p
    ),

  /* Assessment */
  getAssessmentQuestions: () =>
    request<AssessmentQuestionsResponse>("GET", "/assessment/questions"),
  submitAssessment: (p: AssessmentSubmitPayload) =>
    request<AssessmentSubmitResponse>("POST", "/assessment/submit", p),
  latestAssessment: (uid: number) =>
    request<LatestAssessmentResponse>(
      "GET",
      `/assessment/latest/${uid}`
    ),

  /* Sessions */
  startSession: (p: SessionStartPayload) =>
    request<SessionStartResponse>("POST", "/sessions/start", p),

  /* Chat */
  chat: (p: ChatPayload) => request<ChatResponse>("POST", "/chat", p),

  /* Analytics */
  analytics: (uid: number, limit = 500) =>
    request<AnalyticsResponse>(
      "GET",
      `/users/${uid}/analytics?limit=${limit}`
    ),

  /* Meta */
  meta: () =>
    request<{ name: string; slogan: string }>("GET", "/meta"),
};
