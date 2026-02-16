"use client";

import { motion } from "framer-motion";
import { RotateCcw, Download, CheckCircle2 } from "lucide-react";

export interface CourseData {
  topic: string;
  outline: string[];
  description: string;
}

interface FinalCardProps {
  courseData: CourseData;
  onRestart: () => void;
  onComplete?: () => void;
}

const FinalCard = ({ courseData, onRestart, onComplete }: FinalCardProps) => {
  return (
    <div className="floating-card w-full max-w-5xl p-10 md:p-14 bg-zinc-900 border-zinc-800">
      <div className="text-center mb-10">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
          className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-purple-500/20 mb-6"
        >
          <CheckCircle2 className="text-purple-400" size={32} />
        </motion.div>
        <p className="text-xs tracking-[0.3em] uppercase text-zinc-400 mb-3">
          Complete
        </p>
        <h2 className="text-3xl md:text-4xl font-bold text-white">
          {courseData.topic}
        </h2>
        <p className="text-zinc-400 mt-3 max-w-lg mx-auto text-sm leading-relaxed">
          {courseData.description}
        </p>
      </div>

      <div className="bg-zinc-800/50 rounded-xl p-6 mb-8 border border-zinc-800">
        <h3 className="text-sm font-semibold tracking-[0.15em] uppercase text-zinc-400 mb-4">
          Modules
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {courseData.outline.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.08 }}
              className="flex items-center gap-3 bg-zinc-900 rounded-lg px-4 py-3 text-sm text-white border border-zinc-800"
            >
              <span className="text-purple-400 font-semibold text-xs">{String(i + 1).padStart(2, "0")}</span>
              {item}
            </motion.div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onRestart}
          className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
        >
          <RotateCcw size={16} /> New Course
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onComplete}
          className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-6 py-3 text-sm font-medium transition-all"
        >
          <Download size={16} /> Export
        </motion.button>
      </div>
    </div>
  );
};

export default FinalCard;
