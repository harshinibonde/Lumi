import Link from "next/link";

const heroImage = "/media/lumi-hero-caregiver.jpg";

export function HeroSection() {
  return (
    <section className="relative flex h-screen items-center overflow-hidden">
      <img
        src={heroImage}
        alt="Caregiver sharing a warm moment with an elderly person outdoors"
        className="absolute inset-0 h-full w-full object-cover object-center blur-sm"
      />
      <div className="absolute inset-0 bg-white/20" aria-hidden="true" />

      <div className="relative z-10 w-full px-6 pl-6 sm:pl-10 lg:pl-16">
        <div className="max-w-[600px] pt-16 text-left">
          <p className="mb-6 text-xs font-semibold uppercase text-[#163328]/65">
            Welcome to Lumi
          </p>
          <h1 className="font-serif text-5xl font-normal italic leading-[0.98] text-[#163328] sm:text-6xl lg:text-7xl">
            Lighting the path to clearer memories
          </h1>
          <p className="mt-7 max-w-[500px] text-lg leading-8 text-[#263a33]">
            A calm AI companion designed to support patients and caregivers with clarity and care.
          </p>

          <div className="mt-9 flex items-center gap-4 max-sm:flex-col max-sm:items-stretch">
            <Link
              href="/screening"
              className="rounded-full bg-[#163328] px-6 py-3 text-center text-sm font-semibold text-[#fff9ee]"
            >
              Start Screening
            </Link>
            <Link
              href="#about"
              className="rounded-full bg-transparent px-6 py-3 text-center text-sm font-semibold text-[#163328] ring-1 ring-[#163328]/20"
            >
              Learn More
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
