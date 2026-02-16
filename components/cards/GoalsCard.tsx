"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Presentation, FileText, Sparkles, Globe, Share2, ImageIcon, HelpCircle } from "lucide-react";

interface GoalsCardProps {
  onSubmit: (goals: string[]) => void;
  onBack: () => void;
}

const goals = [
  { id: "scratch", label: "Create courses from scratch", icon: Presentation },
  { id: "notes", label: "Turn my notes into courses", icon: FileText },
  { id: "enhance", label: "Enhance existing materials", icon: Sparkles },
  { id: "website", label: "Build a learning portal", icon: Globe },
  { id: "social", label: "Create social media assets", icon: Share2 },
  { id: "images", label: "Generate images with AI", icon: ImageIcon },
  { id: "unsure", label: "Not sure yet", icon: HelpCircle },
];

const GoalsCard = ({ onSubmit, onBack }: GoalsCardProps) => {
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  return (
    <div className="floating-card w-full max-w-5xl p-10 md:p-14 bg-zinc-900 border-zinc-800">
      <div className="text-center mb-8">
        <h2 className="text-3xl md:text-4xl font-bold leading-tight text-white mb-3">
          What do you plan
          <br />
          <span className="text-purple-400">to do?</span>
        </h2>
        <p className="text-zinc-400 text-sm">
          Select all that apply
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-10">
        {goals.map((goal) => {
          const Icon = goal.icon;
          const isSelected = selected.includes(goal.id);
          return (
            <motion.button
              key={goal.id}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => toggle(goal.id)}
              className={`relative flex flex-col items-center gap-2 rounded-xl border-2 px-3 py-5 transition-all ${
                isSelected
                  ? "border-purple-500 bg-purple-500/10 ring-2 ring-purple-500/20"
                  : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
              }`}
            >
              {/* Checkbox indicator */}
              <div
                className={`absolute top-2 right-2 h-4 w-4 rounded border transition-colors ${
                  isSelected
                    ? "bg-purple-500 border-purple-500"
                    : "border-zinc-700"
                }`}
              >
                {isSelected && (
                  <svg viewBox="0 0 14 14" className="h-full w-full text-white">
                    <path
                      d="M3 7l3 3 5-5"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>
              <Icon size={22} className={isSelected ? "text-purple-400" : "text-zinc-400"} />
              <span className="text-xs font-medium text-white text-center leading-tight">
                {goal.label}
              </span>
            </motion.button>
          );
        })}
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
          onClick={() => selected.length > 0 && onSubmit(selected)}
          disabled={selected.length === 0}
          className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-6 py-3 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          Continue <ArrowRight size={16} />
        </motion.button>
      </div>
    </div>
  );
};

export default GoalsCard;
