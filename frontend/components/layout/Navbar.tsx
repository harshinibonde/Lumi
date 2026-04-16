"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

const publicLinks = [
  { href: "/", label: "Home" },
  { href: "/#about", label: "About" },
  { href: "/#features", label: "Features" },
];

const patientLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/screening", label: "Screening" },
  { href: "/chat", label: "Chat" },
  { href: "/caregiver/memory", label: "Memory Vault" },
  { href: "/history", label: "History" },
  { href: "/alerts", label: "Alerts" },
];

const caregiverLinks = [
  { href: "/caregiver", label: "Hub" },
  { href: "/caregiver/memory", label: "Memory Vault" },
  { href: "/history", label: "History" },
  { href: "/alerts", label: "Alerts" },
];

export function Navbar() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("user");
    setIsLoggedIn(Boolean(token));
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        setUserRole(parsed.role || null);
      } catch {
        setUserRole(null);
      }
    }
  }, []);

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith("/#")) {
      e.preventDefault();
      const sectionId = href.replace("/#", "");
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
        setIsOpen(false);
      } else {
        // If not on the landing page, navigate there
        router.push(href);
      }
    } else {
      setIsOpen(false);
    }
  };

  // POST /auth/logout
  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // Even if backend fails, clear local state
    }
    clearAuth();
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    localStorage.removeItem("screening_status");
    setIsLoggedIn(false);
    setUserRole(null);
    setIsOpen(false);
    router.push("/login");
  };

  const links = isLoggedIn
    ? userRole === "caregiver"
      ? caregiverLinks
      : patientLinks
    : publicLinks;

  return (
    <header className="absolute left-0 right-0 top-0 z-50 bg-transparent">
      <nav className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6 sm:px-10" aria-label="Primary navigation">
        <Link href="/" className="font-serif text-2xl font-semibold text-[#163328]">
          Lumi
        </Link>

        <div className="hidden items-center gap-9 md:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={(e) => handleScroll(e, link.href)}
              className="text-sm font-medium text-[#163328]/75 underline-offset-8 hover:text-[#163328] hover:underline cursor-pointer"
            >
              {link.label}
            </a>
          ))}
        </div>

        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            className="hidden rounded-full bg-white/20 px-5 py-2.5 text-sm font-semibold text-[#163328] ring-1 ring-[#163328]/15 md:inline-flex hover:bg-white/30 transition"
          >
            Sign Out
          </button>
        ) : (
          <Link
            href="/login"
            className="hidden rounded-full bg-white/20 px-5 py-2.5 text-sm font-semibold text-[#163328] ring-1 ring-[#163328]/15 md:inline-flex hover:bg-white/30 transition"
          >
            Get Started
          </Link>
        )}

        <button
          type="button"
          className="inline-flex size-10 items-center justify-center rounded-full bg-white/20 text-[#163328] ring-1 ring-[#163328]/10 md:hidden hover:bg-white/30 transition"
          aria-expanded={isOpen}
          aria-controls="mobile-navigation"
          onClick={() => setIsOpen((value) => !value)}
        >
          <span className="sr-only">Toggle navigation</span>
          {isOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </nav>

      {isOpen ? (
        <div id="mobile-navigation" className="mx-6 rounded-2xl bg-[#fff9ee]/95 p-5 text-[#163328] md:hidden">
          <div className="grid gap-4">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleScroll(e, link.href)}
                className="text-sm font-medium cursor-pointer hover:text-[#163328]/70"
              >
                {link.label}
              </a>
            ))}
            {isLoggedIn ? (
              <button
                onClick={handleLogout}
                className="mt-2 rounded-full bg-[#163328] px-5 py-3 text-center text-sm font-semibold text-[#fff9ee] hover:bg-[#163328]/90 transition"
              >
                Sign Out
              </button>
            ) : (
              <Link
                href="/login"
                className="mt-2 rounded-full bg-[#163328] px-5 py-3 text-center text-sm font-semibold text-[#fff9ee] hover:bg-[#163328]/90 transition"
              >
                Get Started
              </Link>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
