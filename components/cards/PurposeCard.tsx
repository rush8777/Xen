"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft } from "lucide-react";

interface PurposeCardProps {
  onSelect: (purpose: string) => void;
  onBack: () => void;
}

const purposes = [
  {
    id: "personal",
    label: "For personal use",
    icon: "👤",
  },
  {
    id: "work",
    label: "For work",
    icon: "💼",
  },
  {
    id: "education",
    label: "For education",
    subtitle: "As a student or educator",
    icon: "🎓",
  },
];

const PurposeCard = ({ onSelect, onBack }: PurposeCardProps) => {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="floating-card w-full max-w-5xl p-10 md:p-14 bg-zinc-900 border-zinc-800">
      <div className="text-center mb-10">
        <h2 className="text-3xl md:text-4xl font-bold leading-tight text-white mb-3">
          How do you plan to
          <br />
          <span className="text-purple-400">use this?</span>
        </h2>
        <p className="text-zinc-400 text-sm">
          We use your answers to personalize your experience
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {purposes.map((purpose) => (
          <motion.button
            key={purpose.id}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setSelected(purpose.id)}
            className={`flex flex-col items-center rounded-xl border-2 p-6 transition-all ${
              selected === purpose.id
                ? "border-purple-500 bg-purple-500/10 ring-2 ring-purple-500/20"
                : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
            }`}
          >
            <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4 text-3xl">
              {purpose.icon}
            </div>
            <span className="text-sm font-semibold text-white">
              {purpose.label}
            </span>
            {purpose.subtitle && (
              <span className="text-xs text-zinc-400 mt-1">
                {purpose.subtitle}
              </span>
            )}
          </motion.button>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} /> Back
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => selected && onSelect(selected)}
          disabled={!selected}
          className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-6 py-3 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          Continue <ArrowRight size={16} />
        </motion.button>
      </div>
    </div>
  );
};

export default PurposeCard;
