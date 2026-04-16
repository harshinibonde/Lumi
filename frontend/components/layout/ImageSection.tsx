"use client";

import { motion } from "framer-motion";

export function ImageSection() {
  return (
    <section id="about" className="px-4 py-20 sm:py-24 lg:px-6">
      <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[0.95fr_1.05fr]">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-120px" }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="overflow-hidden rounded-2xl border border-white/25 bg-white/30 p-3 shadow-[0_28px_90px_rgba(15,23,42,0.13)] backdrop-blur-xl"
        >
          <img
            src="https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=1200&q=85"
            alt="Caregiver assisting an elderly person in warm light"
            className="aspect-[4/3] w-full rounded-2xl object-cover shadow-[0_18px_50px_rgba(15,23,42,0.16)]"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-120px" }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
        >
          <p className="text-sm font-bold uppercase text-blue-700">Care that understands</p>
          <h2 className="mt-4 text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl">
            Care that understands
          </h2>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            Lumi helps bridge the gap between memory and care through intelligent, compassionate support.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/20 bg-white/35 p-5 backdrop-blur-xl">
              <p className="text-3xl font-semibold text-blue-700">24/7</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Gentle guidance when a question needs an answer.</p>
            </div>
            <div className="rounded-2xl border border-white/20 bg-white/35 p-5 backdrop-blur-xl">
              <p className="text-3xl font-semibold text-violet-700">Care</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Insights shaped for patients, families, and caregivers.</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
