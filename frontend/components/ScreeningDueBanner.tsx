"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useScreeningStore } from "../store/screeningStore";

export default function ScreeningDueBanner() {
  const user = useScreeningStore((s) => s.user);
  const screeningStatus = useScreeningStore((s) => s.screeningStatus);

  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setDismissed(localStorage.getItem("screening_banner_dismissed") === "1");
  }, []);

  const screeningDue = Boolean(user?.screening_due ?? screeningStatus?.screening_due);
  const daysOverdue = Number(user?.days_overdue ?? screeningStatus?.days_overdue ?? 0);

  if (!screeningDue || dismissed) return null;

  return (
    <section className="fixed top-0 left-0 right-0 z-50 border-b border-amber-300 bg-amber-100 text-amber-900 shadow-sm">
      <div className="mx-auto max-w-6xl px-4 py-3 flex flex-wrap items-center gap-3 justify-between">
        <p className="font-medium">
          Your 3-month cognitive screening is due {daysOverdue > 0 ? `(${daysOverdue} days overdue)` : ""}
        </p>
        <div className="flex items-center gap-2">
          <Link href="/screening" className="rounded-lg bg-amber-700 text-white px-3 py-1.5 text-sm font-semibold">
            Begin screening now
          </Link>
          <button
            className="rounded-lg border border-amber-500 px-3 py-1.5 text-sm"
            onClick={() => {
              localStorage.setItem("screening_banner_dismissed", "1");
              setDismissed(true);
            }}
            type="button"
          >
            Dismiss
          </button>
        </div>
      </div>
    </section>
  );
}
