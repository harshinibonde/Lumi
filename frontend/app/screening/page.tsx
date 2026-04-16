"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useScreeningStore } from "../../store/screeningStore";
import { Navbar } from "@/components/layout/Navbar";

export default function ScreeningIntakePage() {
  const router = useRouter();
  const setIntakeStore = useScreeningStore((s) => s.setIntake);

  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const [intake, setIntake] = useState({
    age: "",
    gender: "",
    education: "",
    functional_assessment: "",
    adl: "",
    memory_complaints: "",
    behavioral_problems: "",
    setting: "home" as "clinical" | "home",
  });

  useEffect(() => {
    localStorage.removeItem("intake");

    const token = localStorage.getItem("auth_token");
    const user = localStorage.getItem("user");

    if (!token || !user) {
      router.push("/login");
      return;
    }

    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Checking authentication...
      </div>
    );
  }

  const start = async () => {
    if (
      !intake.age ||
      !intake.gender ||
      !intake.education ||
      !intake.functional_assessment ||
      !intake.adl ||
      !intake.memory_complaints ||
      !intake.behavioral_problems
    ) {
      alert("Please fill all fields");
      return;
    }

    try {
      setStarting(true);

      const payload = {
        age: Number(intake.age),
        gender: Number(intake.gender),
        education: Number(intake.education),
        functional_assessment: Number(intake.functional_assessment),
        adl: Number(intake.adl),
        memory_complaints: Number(intake.memory_complaints),
        behavioral_problems: Number(intake.behavioral_problems),
        setting: intake.setting,
      };

      setIntakeStore(payload);

      localStorage.setItem("intake", JSON.stringify(payload));
      router.push("/screening/tasks");
      
    } catch (error) {
      console.error("Screening error:", error);
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />

      <main className="px-6 py-10">
        <div className="max-w-2xl mx-auto space-y-8">

          <div className="text-center">
            <h1 className="text-4xl font-serif text-[#163328]">Cognitive Screening</h1>
            <p className="text-[#163328]/70">Assessment Information</p>
          </div>

          <div className="bg-white/50 p-8 rounded-xl space-y-6 border">

            {/* Age */}
            <div>
              <label className="text-sm text-[#163328]">Age</label>
              <input
                type="number"
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.age}
                onChange={(e) => setIntake({ ...intake, age: e.target.value })}
              />
            </div>

            {/* Gender */}
            <div>
              <label className="text-sm text-[#163328]">Gender</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.gender}
                onChange={(e) => setIntake({ ...intake, gender: e.target.value })}
              >
                <option value="">Select</option>
                <option value="0">Female</option>
                <option value="1">Male</option>
              </select>
            </div>

            {/* Education */}
            <div>
              <label className="text-sm text-[#163328]">Education</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.education}
                onChange={(e) => setIntake({ ...intake, education: e.target.value })}
              >
                <option value="">Select</option>
                <option value="5">Primary School</option>
                <option value="10">10th</option>
                <option value="12">12th</option>
                <option value="15">Graduate</option>
                <option value="17">Postgraduate</option>
                <option value="20">PhD</option>
              </select>
            </div>

            {/* Functional */}
            <div>
              <label className="text-sm text-[#163328]">Functional Ability</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.functional_assessment}
                onChange={(e) =>
                  setIntake({ ...intake, functional_assessment: e.target.value })
                }
              >
                <option value="">Select</option>
                <option value="0">No difficulty</option>
                <option value="1">Mild</option>
                <option value="2">Moderate</option>
                <option value="3">Severe</option>
              </select>
            </div>

            {/* ADL */}
            <div>
              <label className="text-sm text-[#163328]">Daily Activities (ADL)</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.adl}
                onChange={(e) => setIntake({ ...intake, adl: e.target.value })}
              >
                <option value="">Select</option>
                <option value="0">Independent</option>
                <option value="1">Mild help</option>
                <option value="2">Moderate help</option>
                <option value="3">Dependent</option>
              </select>
            </div>

            {/* Memory */}
            <div>
              <label className="text-sm text-[#163328]">Memory Complaints</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.memory_complaints}
                onChange={(e) =>
                  setIntake({ ...intake, memory_complaints: e.target.value })
                }
              >
                <option value="">Select</option>
                <option value="0">No</option>
                <option value="1">Yes</option>
              </select>
            </div>

            {/* Behavior */}
            <div>
              <label className="text-sm text-[#163328]">Behavioral Problems</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.behavioral_problems}
                onChange={(e) =>
                  setIntake({ ...intake, behavioral_problems: e.target.value })
                }
              >
                <option value="">Select</option>
                <option value="0">No</option>
                <option value="1">Yes</option>
              </select>
            </div>

            {/* Setting */}
            <div>
              <label className="text-sm text-[#163328]">Assessment Setting</label>
              <select
                className="w-full px-4 py-3 border rounded-lg"
                value={intake.setting}
                onChange={(e) =>
                  setIntake({ ...intake, setting: e.target.value as "clinical" | "home" })
                }
              >
                <option value="home">Home</option>
                <option value="clinical">Clinical</option>
              </select>
            </div>

            <button
              onClick={start}
              disabled={starting}
              className="w-full bg-[#163328] text-white py-3 rounded-lg"
            >
              {starting ? "Starting..." : "Begin Screening"}
            </button>

          </div>
        </div>
      </main>
    </div>
  );
}