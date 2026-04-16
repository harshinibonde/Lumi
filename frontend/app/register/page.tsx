"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

import { api, RegisterPayload } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState<RegisterPayload>({
    username: "",
    password: "",
    full_name: "",
    email: "",
    role: "patient"
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!form.full_name || !form.email || !form.username || !form.password) {
      setError("Please fill in all required fields.");
      return;
    }

    try {
      setIsLoading(true);
      await api.register(form);
      setSuccess("Account created successfully. Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 900);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((item: any) => item?.msg).filter(Boolean).join("; ") || "Registration failed");
      } else {
        const fallback = e?.message === "Network Error"
          ? "Cannot connect to backend API. Make sure the backend is running on http://127.0.0.1:8000."
          : e?.message || "Registration failed";
        setError(detail || fallback);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-16 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-md pt-20">
          <div className="space-y-8">
            <div className="text-center">
              <h1 className="font-serif text-4xl font-normal italic text-[#163328]">Create Account</h1>
              <p className="mt-2 text-lg text-[#163328]/75">Join Lumi</p>
            </div>

            <form className="space-y-6 rounded-xl border border-[#163328]/10 bg-white/50 p-8" onSubmit={submit}>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Full Name</label>
                <input
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  placeholder="Your full name"
                  value={form.full_name}
                  onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Email</label>
                <input
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  type="email"
                  placeholder="your.email@example.com"
                  value={form.email}
                  onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Username</label>
                <input
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  placeholder="Choose a username"
                  value={form.username}
                  onChange={(e) => setForm((s) => ({ ...s, username: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Password</label>
                <input
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  type="password"
                  placeholder="Create a password"
                  value={form.password}
                  onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#163328]">Role</label>
                <select
                  className="w-full rounded-lg border border-[#163328]/20 bg-white px-4 py-3 text-[#163328] outline-none transition focus:ring-2 focus:ring-[#163328]/30"
                  value={form.role}
                  onChange={(e) => setForm((s) => ({ ...s, role: e.target.value as "patient" | "caregiver" }))}
                >
                  <option value="patient">Patient</option>
                  <option value="caregiver">Caregiver</option>
                </select>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                  {error}
                </div>
              )}

              {success && (
                <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700 border border-emerald-200">
                  {success}
                </div>
              )}

              <button
                type="submit"
                className="w-full rounded-lg bg-[#163328] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#163328]/90 disabled:opacity-50"
                disabled={isLoading}
              >
                {isLoading ? "Creating account..." : "Create account"}
              </button>

              <div className="text-center text-sm">
                <span className="text-[#163328]/75">Already have an account? </span>
                <Link href="/login" className="font-semibold text-[#163328] hover:underline">
                  Sign in
                </Link>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
