"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft, Sparkles } from "lucide-react";

interface TopicCardProps {
  onSubmit: (topic: string) => void;
  onBack: () => void;
}

const TopicCard = ({ onSubmit, onBack }: TopicCardProps) => {
  const [topic, setTopic] = useState("");

  return (
    <div className="floating-card w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 overflow-hidden bg-zinc-900 border-zinc-800 rounded-2xl">
      {/* Left gradient background */}
      <div className="relative m-3 md:m-4 min-h-[300px] rounded-xl overflow-hidden order-2 md:order-1">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-zinc-800 to-zinc-900" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-48 h-48 rounded-full bg-purple-500/10 blur-3xl" />
        </div>
      </div>

      {/* Right content */}
      <div className="flex flex-col justify-between p-10 md:p-14 order-1 md:order-2">
        <div>
          <p className="text-xs tracking-[0.3em] uppercase text-zinc-400">
            Step 1
          </p>
        </div>

        <div className="my-8">
          <h2 className="text-3xl md:text-4xl font-bold leading-tight text-white mb-2">
            What Will You
            <br />
            <span className="text-purple-400">Teach?</span>
          </h2>
          <p className="text-zinc-400 text-sm mt-4 mb-8">
            Enter a topic and let AI craft a complete course structure.
          </p>

          <div className="space-y-4">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && topic.trim() && onSubmit(topic.trim())}
              placeholder="e.g. Machine Learning Fundamentals"
              className="w-full bg-zinc-800 rounded-lg px-5 py-4 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm border border-zinc-700 transition-all"
            />
          </div>
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
            onClick={() => topic.trim() && onSubmit(topic.trim())}
            disabled={!topic.trim()}
            className="inline-flex items-center gap-3 rounded-lg bg-white hover:bg-gray-100 text-black px-3 py-1 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Sparkles size={16} /> Generate
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default TopicCard;
