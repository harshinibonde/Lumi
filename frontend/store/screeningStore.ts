import { create } from "zustand";

type Intake = {
  age: number;
  gender: number;
  education: number;
  functional_assessment: number;
  adl: number;
  memory_complaints: number;
  behavioral_problems: number;
  setting: "clinical" | "home";
};

type Answer = {
  session_id: number;
  task_number: number;
  domain: string;
  answer_text: string;
  score_awarded?: number;
};

type ScreeningState = {
  token: string;
  user: any;
  screeningStatus: any;
  intake: Intake;
  session: any;
  answers: Answer[];
  result: any;
  setAuth: (token: string, user: any, screeningStatus: any) => void;
  setIntake: (intake: Partial<Intake>) => void;
  setSession: (session: any) => void;
  addAnswer: (answer: Answer) => void;
  setResult: (result: any) => void;
  resetScreening: () => void;
};

const defaultIntake: Intake = {
  age: 65,
  gender: 0,
  education: 1,
  functional_assessment: 5,
  adl: 5,
  memory_complaints: 0,
  behavioral_problems: 0,
  setting: "clinical"
};

export const useScreeningStore = create<ScreeningState>((set) => ({
  token: "",
  user: null,
  screeningStatus: null,
  intake: defaultIntake,
  session: null,
  answers: [],
  result: null,
  setAuth: (token, user, screeningStatus) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
      localStorage.removeItem("screening_banner_dismissed");
      localStorage.setItem("login_session_marker", String(Date.now()));
    }
    set({ token, user, screeningStatus });
  },
  setIntake: (intake) => set((s) => ({ intake: { ...s.intake, ...intake } })),
  setSession: (session) => set({ session }),
  addAnswer: (answer) => set((s) => ({ answers: [...s.answers, answer] })),
  setResult: (result) => set({ result }),
  resetScreening: () => set({ answers: [], session: null, result: null })
}));
