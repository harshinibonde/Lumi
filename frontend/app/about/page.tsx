import { Navbar } from "@/components/layout/Navbar";
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-4xl pt-16 pb-12">
          <div className="text-center space-y-4 mb-16">
            <h1 className="font-serif text-5xl font-normal italic leading-tight text-[#163328] sm:text-6xl">
              About Lumi
            </h1>
            <p className="text-xl text-[#163328]/75 font-medium">
              Lighting the path to clearer memories
            </p>
            <div className="w-20 h-1 bg-[#163328] mx-auto rounded-full mt-6"></div>
          </div>

          <div className="space-y-12">
            {/* Vision Statement */}
            <div className="bg-gradient-to-br from-[#163328]/5 to-[#163328]/10 rounded-2xl p-8 sm:p-12 border border-[#163328]/20">
              <p className="text-lg sm:text-xl leading-relaxed text-[#163328]">
                Lumi is an AI-powered cognitive support companion designed to help patients and caregivers navigate the challenges of memory loss and cognitive decline. We believe that everyone deserves access to compassionate, intelligent care tools that can make a real difference.
              </p>
            </div>

            {/* Mission Section */}
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-3xl font-normal italic text-[#163328] mb-4">Our Mission</h2>
                <p className="text-lg leading-8 text-[#424844]">
                  To bring gentle cognitive support into everyday care, helping families notice what matters with patience, clarity, and warmth. Through advanced screening tools and AI-powered conversations, Lumi empowers both patients and their caregivers to stay connected and informed.
                </p>
              </div>
            </div>

            {/* Values Section */}
            <div className="space-y-6">
              <h2 className="font-serif text-3xl font-normal italic text-[#163328]">Our Values</h2>
              <div className="grid sm:grid-cols-3 gap-5">
                <div className="bg-white/40 backdrop-blur-sm p-6 rounded-xl border border-[#163328]/10 hover:border-[#163328]/30 hover:bg-white/60 transition">
                  <div className="text-3xl mb-3">💚</div>
                  <h3 className="font-semibold text-[#163328] mb-2">Compassion</h3>
                  <p className="text-sm text-[#424844]">Designing with empathy for patients and caregivers</p>
                </div>
                <div className="bg-white/40 backdrop-blur-sm p-6 rounded-xl border border-[#163328]/10 hover:border-[#163328]/30 hover:bg-white/60 transition">
                  <div className="text-3xl mb-3">🎯</div>
                  <h3 className="font-semibold text-[#163328] mb-2">Clarity</h3>
                  <p className="text-sm text-[#424844]">Making complex care simple and understandable</p>
                </div>
                <div className="bg-white/40 backdrop-blur-sm p-6 rounded-xl border border-[#163328]/10 hover:border-[#163328]/30 hover:bg-white/60 transition">
                  <div className="text-3xl mb-3">🔬</div>
                  <h3 className="font-semibold text-[#163328] mb-2">Science</h3>
                  <p className="text-sm text-[#424844]">Built with latest AI and clinical research</p>
                </div>
              </div>
            </div>

            {/* Why We Exist */}
            <div className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 sm:p-10 border border-[#163328]/20">
              <h2 className="font-serif text-3xl font-normal italic text-[#163328] mb-4">Why We Exist</h2>
              <p className="text-lg leading-8 text-[#424844]">
                Cognitive decline affects millions globally, yet many lack access to affordable, compassionate support tools. Lumi exists to close this gap—providing intelligent, personalized cognitive care that meets people where they are, whether in clinical settings or at home. Built with the latest in AI and machine learning, Lumi provides personalized cognitive assessments, memory tracking, and meaningful support—all designed with the user's wellbeing at the center.
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-16 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/screening"
              className="rounded-full bg-[#163328] px-8 py-3 text-center text-sm font-semibold text-[#fff9ee] hover:bg-[#163328]/90 transition"
            >
              Start Screening
            </Link>
            <Link
              href="/"
              className="rounded-full border border-[#163328] px-8 py-3 text-center text-sm font-semibold text-[#163328] hover:bg-white/50 transition"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
