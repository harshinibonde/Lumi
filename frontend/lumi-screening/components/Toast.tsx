"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import styles from "../styles/toast.module.css";

type ToastType = "info" | "success" | "error";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastAPI {
  push: (message: string, type?: ToastType) => void;
}

const Ctx = createContext<ToastAPI>({ push: () => {} });

export function useToast(): ToastAPI {
  return useContext(Ctx);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string, type: ToastType = "info") => {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  return (
    <Ctx.Provider value={{ push }}>
      {children}
      <div className={styles.container} aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`${styles.toast} ${styles[t.type]}`}>
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
