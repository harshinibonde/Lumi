"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import styles from "../../styles/auth.module.css";
import { api } from "../../lib/api";
import { setState } from "../../lib/state";
import { useToast } from "../../components/Toast";

type Mode = "signin" | "signup";
type Step = "form" | "otp";

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>("signin");
  const [step, setStep] = useState<Step>("form");

  /* Sign-in fields */
  const [email, setEmail] = useState("");

  /* Signup fields */
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [gender, setGender] = useState("");
  const [caregiverName, setCaregiverName] = useState("");
  const [caregiverEmail, setCaregiverEmail] = useState("");

  /* OTP */
  const [otp, setOtp] = useState("");
  const [pendingUserId, setPendingUserId] = useState<number | null>(null);

  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const toast = useToast();

  const testUsers = [
    { id: 6, name: "Margaret Thompson", age: 72, label: "Normal (Score 28)" },
    { id: 7, name: "Arthur Reynolds", age: 78, label: "Mild Impairment (Score 22)" },
    { id: 8, name: "Evelyn Chen", age: 81, label: "Moderate Impairment (Score 17)" },
    { id: 9, name: "Robert O'Brien", age: 85, label: "Severe Impairment (Score 10)" },
    { id: 10, name: "Dorothy Patel", age: 69, label: "High Normal (Score 30)" },
  ];

  function devLoginAs(u: typeof testUsers[0]) {
    setState({
      userId: u.id,
      userName: u.name,
      userAge: u.age,
      sessionToken: "dev-token-bypass",
      currentQuestionIndex: 0,
      answers: {},
      assessmentScore: null,
      categoryScores: {},
      sessionId: null,
    });
    toast.push(`Logged in as ${u.name}`, "success");
    router.push("/dashboard");
  }

  async function handleSignIn(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      const res = await api.requestOtp({ patient_email: email.trim() });
      setPendingUserId(res.user_id);
      setStep("otp");
      toast.push("OTP sent to your email", "success");
    } catch {
      toast.push("Could not send OTP. Check if user exists.", "error");
    } finally {
      setLoading(false);
    }
  }

  async function handleSignUp(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !signupEmail.trim() || !age.trim()) return;
    setLoading(true);
    try {
      const res = await api.createUser({
        name: name.trim(),
        age: Number(age),
        patient_email: signupEmail.trim(),
        gender: gender || undefined,
        caregiver_name: caregiverName || undefined,
        caregiver_email: caregiverEmail || undefined,
      });
      setPendingUserId(res.user_id);
      setStep("otp");
      toast.push("Account created! Check your email for OTP.", "success");
    } catch {
      toast.push("Could not create account. Email may already exist.", "error");
    } finally {
      setLoading(false);
    }
  }

  async function handleOtpVerify(e: FormEvent) {
    e.preventDefault();
    if (!otp.trim() || !pendingUserId) return;
    setLoading(true);
    try {
      const res = await api.verifyOtp({ user_id: pendingUserId, otp: otp.trim() });
      setState({
        userId: res.user_id,
        userName: res.name,
        sessionToken: res.session_token,
        currentQuestionIndex: 0,
        answers: {},
        assessmentScore: null,
        categoryScores: {},
        sessionId: null,
      });
      toast.push(`Welcome, ${res.name}!`, "success");
      router.push("/dashboard");
    } catch {
      toast.push("Invalid OTP. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  }

  if (step === "otp") {
    return (
      <main className={styles.page}>
        <div className={`${styles.halo} ${styles.haloTopLeft}`} />
        <div className={`${styles.halo} ${styles.haloBottomRight}`} />
        <div className={styles.content}>
          <div className={styles.brandArea}>
            <Image src="/Lumi_logo.png" alt="Lumi" width={48} height={48} />
          </div>
          <h1 className={styles.title}>Enter Verification Code</h1>
          <p className={styles.subtitle}>We&apos;ve sent a code to your email address.</p>

          <div className={styles.card}>
            <form className={styles.form} onSubmit={handleOtpVerify}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="otp">Verification Code</label>
                <input
                  className={styles.input}
                  id="otp"
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  autoComplete="one-time-code"
                />
              </div>
              <button className={`btn btn--primary btn--fullWidth btn--pill ${styles.submitBtn}`} type="submit" disabled={loading}>
                {loading ? "Verifying..." : "Verify & Continue"}
              </button>
            </form>
            <div className={styles.switchArea}>
              <p>
                Didn&apos;t receive it?{" "}
                <button className={styles.switchLink} onClick={() => setStep("form")}>Go back</button>
              </p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={`${styles.halo} ${styles.haloTopLeft}`} />
      <div className={`${styles.halo} ${styles.haloBottomRight}`} />

      <div className={styles.content}>
        <div className={styles.brandArea}>
          <Image src="/Lumi_logo.png" alt="Lumi" width={48} height={48} />
        </div>
        <h1 className={styles.title}>
          {mode === "signin" ? "Welcome Back" : "Create Your Profile"}
        </h1>
        <p className={styles.subtitle}>
          {mode === "signin"
            ? "Return to your sanctuary of mindfulness."
            : "Set up your personal cognitive wellness profile."}
        </p>

        <div className={styles.card}>
          {mode === "signin" ? (
            <form className={styles.form} onSubmit={handleSignIn}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="signin-email">Email Address</label>
                <input
                  className={styles.input}
                  id="signin-email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <button className={`btn btn--primary btn--fullWidth btn--pill ${styles.submitBtn}`} type="submit" disabled={loading}>
                {loading ? "Sending OTP..." : "Sign In"}
              </button>
            </form>
          ) : (
            <form className={styles.form} onSubmit={handleSignUp}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="signup-name">Full Name</label>
                <input className={styles.input} id="signup-name" type="text" placeholder="Your full name" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className={styles.fieldRow}>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="signup-age">Age</label>
                  <input className={styles.input} id="signup-age" type="number" min={18} max={110} placeholder="Age" value={age} onChange={(e) => setAge(e.target.value)} />
                </div>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="signup-gender">Gender</label>
                  <select className={styles.input} id="signup-gender" value={gender} onChange={(e) => setGender(e.target.value)}>
                    <option value="">Select</option>
                    <option>Male</option>
                    <option>Female</option>
                    <option>Other</option>
                  </select>
                </div>
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="signup-email">Patient Email</label>
                <input className={styles.input} id="signup-email" type="email" placeholder="patient@example.com" value={signupEmail} onChange={(e) => setSignupEmail(e.target.value)} />
              </div>
              <div className={styles.fieldRow}>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="caregiver-name">Caregiver Name</label>
                  <input className={styles.input} id="caregiver-name" type="text" placeholder="Optional" value={caregiverName} onChange={(e) => setCaregiverName(e.target.value)} />
                </div>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="caregiver-email">Caregiver Email</label>
                  <input className={styles.input} id="caregiver-email" type="email" placeholder="Optional" value={caregiverEmail} onChange={(e) => setCaregiverEmail(e.target.value)} />
                </div>
              </div>
              <button className={`btn btn--primary btn--fullWidth btn--pill ${styles.submitBtn}`} type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Account"}
              </button>
            </form>
          )}

          <div className={styles.switchArea}>
            <p>
              {mode === "signin" ? (
                <>New to Lumi? <button className={styles.switchLink} onClick={() => setMode("signup")}>Create Account</button></>
              ) : (
                <>Already have an account? <button className={styles.switchLink} onClick={() => setMode("signin")}>Sign In</button></>
              )}
            </p>
          </div>

          <div className={styles.devArea}>
            <p className={styles.devTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>science</span>
              Test Users (no backend needed)
            </p>
            <div className={styles.devGrid}>
              {testUsers.map((u) => (
                <button key={u.id} className={styles.devBtn} onClick={() => devLoginAs(u)} type="button">
                  <strong>{u.name}</strong>
                  <span>{u.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.quote}>
          &ldquo;Healing is not a destination, but a journey taken one breath at a time.&rdquo;
        </div>
      </div>
    </main>
  );
}
