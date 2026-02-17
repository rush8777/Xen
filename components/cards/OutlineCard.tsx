"use client";

import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft, BookOpen } from "lucide-react";

export interface CourseData {
  topic: string;
  outline: string[];
  description: string;
}

interface OutlineCardProps {
  courseData: CourseData;
  onNext: () => void;
  onBack: () => void;
}

const OutlineCard = ({ courseData, onNext, onBack }: OutlineCardProps) => {
  return (
    <div className="floating-card w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 overflow-hidden bg-zinc-900 border-zinc-800 rounded-2xl">
      {/* Left content */}
      <div className="flex flex-col justify-between p-10 md:p-14">
        <div>
          <p className="text-xs tracking-[0.3em] uppercase text-zinc-400">
            Course Outline
          </p>
        </div>

        <div className="my-6">
          <h2 className="text-3xl font-bold leading-tight text-white mb-2">
            {courseData.topic}
          </h2>
          <p className="text-zinc-400 text-sm mb-6 leading-relaxed">
            {courseData.description}
          </p>

          <div className="space-y-3">
            {courseData.outline.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-3 text-sm"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-xs font-medium text-zinc-400 border border-zinc-700">
                  {i + 1}
                </span>
                <span className="text-white">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onBack}
            className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={16} /> Edit Topic
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onNext}
            className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-3 py-1 text-xs font-medium transition-colors"
          >
            <BookOpen size={16} /> Finalize
          </motion.button>
        </div>
      </div>

      {/* Right gradient background */}
      <div className="relative m-3 md:m-4 min-h-[300px] rounded-xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-zinc-800 to-zinc-900" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-48 h-48 rounded-full bg-purple-500/10 blur-3xl" />
        </div>
      </div>
    </div>
  );
};

export default OutlineCard;
