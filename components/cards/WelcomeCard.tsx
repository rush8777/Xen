"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface WelcomeCardProps {
  onStart: () => void;
}

const WelcomeCard = ({ onStart }: WelcomeCardProps) => {
  return (
    <div className="floating-card w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 overflow-hidden bg-zinc-900 border-zinc-800 rounded-2xl">
      {/* Left content */}
      <div className="flex flex-col justify-between p-10 md:p-14">
        <div>
          <p className="text-xs tracking-[0.3em] uppercase text-zinc-400 mb-2">
            AI Course Creator
          </p>
        </div>

        <div className="my-8">
          <h1 className="text-4xl md:text-5xl font-bold leading-tight text-white">
            Create Your
            <br />
            <span className="text-purple-400">Course</span>
          </h1>
          <p className="mt-6 text-zinc-400 leading-relaxed max-w-sm text-sm">
            Transform any topic into a beautifully structured course with the power of AI. Just describe what you want to teach.
          </p>
        </div>

        <div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onStart}
            className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-3 py-1 text-xs font-medium transition-colors"
          >
            Start <ArrowRight size={16} />
          </motion.button>
        </div>
      </div>

      {/* Right image */}
      <div className="relative m-3 md:m-4 min-h-[300px] rounded-xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-zinc-800 to-zinc-900" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-48 h-48 rounded-full bg-purple-500/10 blur-3xl" />
        </div>
      </div>
    </div>
  );
};

export default WelcomeCard;
