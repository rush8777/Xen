"use client";

import { motion } from "framer-motion";

interface GeneratingCardProps {
  topic: string;
}

const GeneratingCard = ({ topic }: GeneratingCardProps) => {
  return (
    <div className="floating-card w-full max-w-5xl p-14 md:p-20 flex flex-col items-center justify-center text-center min-h-[400px] bg-zinc-900 border-zinc-800">
      <div className="relative mb-10">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute inset-0 rounded-full border-2 border-purple-500/30"
            style={{ width: 64 + i * 30, height: 64 + i * 30, top: -(i * 15), left: -(i * 15) }}
            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.1, 0.3] }}
            transition={{ duration: 2, delay: i * 0.4, repeat: Infinity }}
          />
        ))}
        <motion.div
          className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        >
          <div className="w-3 h-3 rounded-full bg-purple-500" />
        </motion.div>
      </div>

      <p className="text-xs tracking-[0.3em] uppercase text-zinc-400 mb-4">
        Generating
      </p>
      <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
        Crafting Your Course
      </h2>
      <p className="text-zinc-400 max-w-md">
        AI is building a comprehensive outline for <span className="text-white font-medium">"{topic}"</span>
      </p>
    </div>
  );
};

export default GeneratingCard;
