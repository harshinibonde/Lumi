import axios from "axios";

const API_BASE = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
});

// 🔐 Attach token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// 🚨 Handle auth errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export interface RegisterPayload {
  username: string;
  password?: string;
  full_name: string;
  email: string;
  role: "patient" | "caregiver";
}

export interface IntakeData {
  age: number;
  gender: number;
  education: number;
  functional_assessment: number;
  adl: number;
  memory_complaints: number;
  behavioral_problems: number;
}

export const apiClient = {
  // 🔐 AUTH
  login: async (data: { username: string; password: string }) => {
    const res = await api.post("/auth/login", data);
    return res.data;
  },

  register: async (data: RegisterPayload) => {
    const res = await api.post("/auth/register", data);
    return res.data;
  },

  getMe: async () => {
    const res = await api.get("/auth/me");
    return res.data;
  },

  logout: async () => {
    await api.post("/auth/logout");
  },

  // 🧠 SCREENING

  startScreening: async (setting: string) => {
    const res = await api.post("/screening/start", {
      setting,
    });
    return res.data;
  },

  submitAnswer: async (data: {
    session_id: number;
    task_number: number;
    domain: string;
    answer_text: string;
    score_awarded?: number;
  }) => {
    const res = await api.post("/screening/answer", data);
    return res.data;
  },

  completeScreening: async (data: {
    session_id: number;
    intake: IntakeData;
  }) => {
    const res = await api.post("/screening/complete", data);
    return res.data;
  },

  getResults: async () => {
    const res = await api.get("/screening/results");
    return res.data;
  },

  getScreeningResults: async () => {
    const res = await api.get("/screening/results");
    return res.data;
  },

  getCaregiverPatients: async () => {
    const res = await api.get("/analytics/caregiver/patients");
    return res.data;
  },

  // Returns { id, full_name, email } for the patient linked to the authed caregiver
  getLinkedPatient: async (): Promise<{ id: number; full_name: string; email: string }> => {
    const res = await api.get("/analytics/caregiver/patient");
    return res.data;
  },

  // 🧠 MEMORY VAULT
  getMemories: async () => {
    const res = await api.get("/memory");
    return res.data;
  },

  addMemory: async (data: { category: string; content: string }) => {
    const res = await api.post("/memory", data);
    return res.data;
  },

  // Lists all patients + whether linked (for caregiver link-patient UI)
  getPatientsList: async (): Promise<Array<{ id: number; full_name: string; email: string; linked: boolean }>> => {
    const res = await api.get("/analytics/caregiver/patients-list");
    return res.data;
  },

  // Links a patient to the authenticated caregiver
  linkPatient: async (patientId: number) => {
    const res = await api.post("/analytics/caregiver/link", { patient_id: patientId });
    return res.data;
  },
};

export { apiClient as api };
export default apiClient;