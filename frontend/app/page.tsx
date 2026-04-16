"use client";

import { Navbar } from "@/components/layout/Navbar";
import { useRouter } from "next/navigation";

export default function LandingPage() {
  const router = useRouter();

  const handleStartAssessment = () => {
    const token = localStorage.getItem("auth_token");

    if (!token) {
      router.push("/login");
    } else {
      router.push("/screening");
    }
  };

  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      
      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      <section className="relative h-screen w-full overflow-hidden">
        <img
          src="/media/background_image.jpg"
          alt="Caregiver sharing a warm moment with an elderly person outdoors"
          className="absolute inset-0 h-full w-full object-cover object-center blur-sm"
        />
        <div className="absolute inset-0 bg-white/20"></div>

        <div className="relative z-10 flex h-full items-center pl-6 sm:pl-10 lg:pl-16">
          <div className="max-w-xl">
            <p className="text-xs font-semibold uppercase text-[#163328]/65">Welcome to Lumi</p>
            <h1 className="font-serif text-5xl font-normal italic leading-[0.98] text-[#163328] sm:text-6xl lg:text-7xl mt-4">
              Lighting the path to clearer memories
            </h1>
            <p className="mt-7 max-w-[500px] text-lg leading-8 text-[#263a33]">
              A calm AI companion designed to support patients and caregivers with clarity and care.
            </p>

            <div className="mt-9 flex items-center gap-4 max-sm:flex-col max-sm:items-stretch">
              <button
                onClick={handleStartAssessment}
                className="rounded-full bg-[#163328] px-6 py-3 text-center text-sm font-semibold text-[#fff9ee] hover:bg-[#163328]/90 transition"
              >
                Start Screening
              </button>
              <button
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="rounded-full bg-transparent px-6 py-3 text-center text-sm font-semibold text-[#163328] ring-1 ring-[#163328]/20 hover:bg-white/20 transition"
              >
                Learn More
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-24 px-6 sm:px-10 lg:px-16 bg-[var(--cream)]">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h2 className="font-serif text-4xl font-normal italic text-[#163328]">
            About Lumi
          </h2>

          <p className="text-lg text-[var(--ink)]/70 max-w-2xl mx-auto leading-relaxed">
            Lumi is an AI-powered cognitive companion designed to support patients and caregivers with clarity and care. We combine advanced cognitive screening with intelligent, compassionate support to help families navigate cognitive health.
          </p>

          <div className="grid md:grid-cols-2 gap-6 mt-12 max-w-5xl mx-auto">
            <div className="bg-white/40 backdrop-blur-md p-6 rounded-xl shadow-sm border border-white/20 hover:shadow-md transition">
              <h3 className="font-semibold text-[#163328] mb-2">Personalized Care</h3>
              <p className="text-sm text-[var(--ink)]/70">
                Adaptive support tailored to each individual's needs, preferences, and cognitive profile.
              </p>
            </div>

            <div className="bg-white/40 backdrop-blur-md p-6 rounded-xl shadow-sm border border-white/20 hover:shadow-md transition">
              <h3 className="font-semibold text-[#163328] mb-2">Compassionate AI</h3>
              <p className="text-sm text-[var(--ink)]/70">
                Designed to respond with clarity, warmth, and understanding to support better outcomes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 sm:px-10 lg:px-16 bg-white/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16 space-y-4">
            <h2 className="font-serif text-4xl font-normal italic text-[#163328]">
              Features
            </h2>
            <p className="text-lg text-[var(--ink)]/70 max-w-2xl mx-auto">
              Everything you need for better cognitive care
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl bg-white/40 backdrop-blur-md shadow-sm hover:shadow-md transition border border-white/20">
              <h3 className="text-lg font-semibold text-[#163328] mb-3">
                Cognitive Screening
              </h3>
              <p className="text-sm text-[var(--ink)]/70">
                Identify cognitive changes early with guided, comprehensive MMSE assessments.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-white/40 backdrop-blur-md shadow-sm hover:shadow-md transition border border-white/20">
              <h3 className="text-lg font-semibold text-[#163328] mb-3">
                AI Chat Companion
              </h3>
              <p className="text-sm text-[var(--ink)]/70">
                Engage in meaningful conversations with an intelligent, context-aware assistant.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-white/40 backdrop-blur-md shadow-sm hover:shadow-md transition border border-white/20">
              <h3 className="text-lg font-semibold text-[#163328] mb-3">
                Memory Tracking
              </h3>
              <p className="text-sm text-[var(--ink)]/70">
                Store and organize important memories to personalize AI responses over time.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-white/40 backdrop-blur-md shadow-sm hover:shadow-md transition border border-white/20">
              <h3 className="text-lg font-semibold text-[#163328] mb-3">
                Caregiver Support
              </h3>
              <p className="text-sm text-[var(--ink)]/70">
                Comprehensive dashboard and analytics to help caregivers provide informed care.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 sm:px-10 lg:px-16 text-center bg-[var(--cream)]">
        <div className="max-w-2xl mx-auto">
          <h2 className="font-serif text-3xl font-normal italic text-[#163328] mb-6">
            Start Your Cognitive Check
          </h2>
          <p className="text-lg text-[var(--ink)]/70 mb-8 max-w-xl mx-auto">
            Take the first step toward better cognitive health. Our guided screening takes just 5-10 minutes.
          </p>
          <button
            onClick={handleStartAssessment}
            className="inline-block bg-[#163328] text-white px-8 py-4 rounded-full font-semibold hover:bg-[#163328]/90 transition hover:shadow-lg"
          >
            Begin Screening
          </button>
        </div>
      </section>

    </div>
  );
}