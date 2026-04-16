"use client";

import { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

import { GlassCard } from "@/components/cards/GlassCard";

type FeatureCardProps = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      <GlassCard className="group h-full p-6 transition duration-300 hover:border-blue-200/60 hover:bg-white/45 hover:shadow-[0_24px_70px_rgba(96,165,250,0.22)]">
        <div className="mb-6 flex size-12 items-center justify-center rounded-2xl border border-white/30 bg-white/45 text-blue-600 shadow-[0_12px_30px_rgba(96,165,250,0.16)]">
          <Icon className="size-5" aria-hidden="true" />
        </div>
        <h3 className="text-xl font-semibold text-slate-950">{title}</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
      </GlassCard>
    </motion.div>
  );
}
