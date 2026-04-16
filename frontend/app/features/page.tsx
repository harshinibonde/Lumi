import { Navbar } from "@/components/layout/Navbar";
import Link from "next/link";

const features = [
  {
    icon: "🧠",
    title: "Cognitive Screening",
    description: "Comprehensive MMSE assessments to identify cognitive changes early",
    benefits: ["Evidence-based testing", "Quick results", "Detailed reports"],
  },
  {
    icon: "💬",
    title: "AI Companion Chat",
    description: "Intelligent, compassionate conversations personalized to your needs",
    benefits: ["Context-aware responses", "Empathetic support", "24/7 availability"],
  },
  {
    icon: "📝",
    title: "Memory Vault",
    description: "Store and organize important memories to personalize care",
    benefits: ["Personal histories", "Preference tracking", "Enhanced personalization"],
  },
  {
    icon: "👥",
    title: "Caregiver Dashboard",
    description: "Analytics and insights to support informed care decisions",
    benefits: ["Progress tracking", "Alert system", "Care recommendations"],
  },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-[var(--cream)] text-[var(--ink)]">
      <Navbar />
      <main className="px-6 py-10 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-5xl pt-12">
          {/* Header */}
          <div className="text-center mb-20 space-y-4">
            <h1 className="font-serif text-5xl font-normal italic leading-tight text-[#163328] sm:text-6xl">
              Features
            </h1>
            <p className="text-xl text-[#163328]/75 font-medium">
              Everything you need for better cognitive care
            </p>
            <div className="w-20 h-1 bg-[#163328] mx-auto rounded-full mt-6"></div>
          </div>

          {/* Features Grid */}
          <div className="grid sm:grid-cols-2 gap-8 mb-16">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group rounded-2xl bg-white/40 backdrop-blur-sm p-8 border border-[#163328]/10 hover:border-[#163328]/30 hover:bg-white/60 hover:shadow-lg transition duration-300"
              >
                <div className="text-5xl mb-4 group-hover:scale-110 transition duration-300">
                  {feature.icon}
                </div>
                <h2 className="text-2xl font-semibold text-[#163328] mb-3">
                  {feature.title}
                </h2>
                <p className="text-lg text-[#424844] mb-6 leading-relaxed">
                  {feature.description}
                </p>
                
                {/* Benefits List */}
                <div className="space-y-2">
                  {feature.benefits.map((benefit, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm text-[#163328]/75">
                      <span className="text-[#163328] font-semibold mt-0.5">✓</span>
                      <span>{benefit}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* For Everyone Section */}
          <div className="mb-16">
            <h2 className="font-serif text-3xl font-normal italic text-[#163328] mb-8 text-center">For Everyone</h2>
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-6 border border-emerald-200">
                <h3 className="text-lg font-semibold text-emerald-900 mb-3">👤 For Patients</h3>
                <ul className="space-y-2 text-sm text-emerald-800">
                  <li>✓ Easy-to-use interface</li>
                  <li>✓ Compassionate AI support</li>
                  <li>✓ Clear cognitive assessments</li>
                  <li>✓ Personal memory preservation</li>
                </ul>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
                <h3 className="text-lg font-semibold text-blue-900 mb-3">👨‍👩‍👧 For Caregivers</h3>
                <ul className="space-y-2 text-sm text-blue-800">
                  <li>✓ Comprehensive dashboard</li>
                  <li>✓ Progress tracking</li>
                  <li>✓ Care recommendations</li>
                  <li>✓ Informed decision-making</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Key Differentiators */}
          <div className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 sm:p-10 border border-[#163328]/20 mb-16">
            <h2 className="font-serif text-3xl font-normal italic text-[#163328] mb-6">Why Choose Lumi</h2>
            <div className="grid sm:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-4xl mb-3">🏥</div>
                <h3 className="font-semibold text-[#163328] mb-2">Evidence-Based</h3>
                <p className="text-sm text-[#424844]">Built on proven cognitive assessment methods</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">🤖</div>
                <h3 className="font-semibold text-[#163328] mb-2">AI-Powered</h3>
                <p className="text-sm text-[#424844]">Latest machine learning for personalization</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">❤️</div>
                <h3 className="font-semibold text-[#163328] mb-2">Compassionate</h3>
                <p className="text-sm text-[#424844]">Designed with users' wellbeing first</p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
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
