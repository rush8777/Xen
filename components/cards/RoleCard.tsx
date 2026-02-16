"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Megaphone, Phone, Headphones, Users, Award, Code, Calculator, Pen, PenTool, MoreHorizontal, GraduationCap } from "lucide-react";

interface RoleCardProps {
  onSelect: (role: string) => void;
  onBack: () => void;
}

const roles = [
  { id: "instructor", label: "Instructor", icon: GraduationCap },
  { id: "marketing", label: "Marketing", icon: Megaphone },
  { id: "sales", label: "Sales & Service", icon: Phone },
  { id: "support", label: "Customer Support", icon: Headphones },
  { id: "people", label: "People or Legal", icon: Users },
  { id: "leadership", label: "Leadership", icon: Award },
  { id: "engineering", label: "Engineering or Data", icon: Code },
  { id: "ops", label: "Ops and Finance", icon: Calculator },
  { id: "creator", label: "Creator", icon: Pen },
  { id: "design", label: "Design or Product", icon: PenTool },
  { id: "other", label: "Other", icon: MoreHorizontal },
];

const RoleCard = ({ onSelect, onBack }: RoleCardProps) => {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="floating-card w-full max-w-5xl p-10 md:p-14 bg-zinc-900 border-zinc-800">
      <div className="text-center mb-8">
        <h2 className="text-3xl md:text-4xl font-bold leading-tight text-white mb-3">
          Which best describes
          <br />
          <span className="text-purple-400">your role?</span>
        </h2>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-10">
        {roles.map((role) => {
          const Icon = role.icon;
          return (
            <motion.button
              key={role.id}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setSelected(role.id)}
              className={`flex flex-col items-center gap-2 rounded-xl border-2 px-3 py-5 transition-all ${
                selected === role.id
                  ? "border-purple-500 bg-purple-500/10 ring-2 ring-purple-500/20"
                  : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
              }`}
            >
              <Icon size={22} className={selected === role.id ? "text-purple-400" : "text-zinc-400"} />
              <span className="text-xs font-medium text-white text-center leading-tight">
                {role.label}
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

export default RoleCard;
