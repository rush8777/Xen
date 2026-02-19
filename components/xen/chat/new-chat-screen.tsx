"use client"

import { useState } from "react";
import {
  Paperclip,
  Command,
  Navigation,
  CreditCard,
  FileText,
  Building2,
  CalendarDays,
  Clock3,
  BarChart3,
  Layers,
  Monitor,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────────
interface PromptSuggestion {
  icon: React.ReactNode;
  label: string;
}

// ── Data ───────────────────────────────────────────────────────────────────────
const suggestions: PromptSuggestion[] = [
  { icon: <CreditCard className="w-3.5 h-3.5 shrink-0" />, label: "Consolidate financial data from all subsidiaries" },
  { icon: <FileText className="w-3.5 h-3.5 shrink-0" />, label: "Generate monthly income statement" },
  { icon: <Building2 className="w-3.5 h-3.5 shrink-0" />, label: "Reconcile the bank accounts for March" },
  { icon: <CalendarDays className="w-3.5 h-3.5 shrink-0" />, label: "Book a journal entry" },
  { icon: <Clock3 className="w-3.5 h-3.5 shrink-0" />, label: "Provide a 12-month cash flow forecast" },
  { icon: <BarChart3 className="w-3.5 h-3.5 shrink-0" />, label: "Generate quarterly profit and loss statement" },
  { icon: <Layers className="w-3.5 h-3.5 shrink-0" />, label: "Show budget variance for Q1 compared to actuals" },
  { icon: <Monitor className="w-3.5 h-3.5 shrink-0" />, label: "Create a real-time financial performance dashboard" },
];

// ── Sub-components ─────────────────────────────────────────────────────────────
const SuggestionCard = ({ icon, label, onClick }: PromptSuggestion & { onClick: () => void }) => (
  <button onClick={onClick} className="flex items-start gap-2.5 px-3.5 py-3 rounded-xl bg-white/5 backdrop-blur-xl border border-white/10 hover:border-white/20 hover:bg-white/10 transition-all text-left group">
    <span className="text-zinc-400 group-hover:text-zinc-300 transition-colors mt-0.5">{icon}</span>
    <span className="text-zinc-300 group-hover:text-white text-xs leading-snug transition-colors">{label}</span>
  </button>
);

// ── Main Component ─────────────────────────────────────────────────────────────
interface NewChatScreenProps {
  onStartChat: (message: string) => void;
}

const NewChatScreen = ({ onStartChat }: NewChatScreenProps) => {
  const [input, setInput] = useState("");

  const handleStartChat = () => {
    if (input.trim()) {
      onStartChat(input);
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="min-h-screen bg-[#0F0F12] flex flex-col items-center justify-between px-6 py-12">

      {/* ── Center content ── */}
      <div className="w-full max-w-2xl flex flex-col items-start gap-8">

        {/* Greeting */}
        <div>
          <h1 className="text-white text-3xl font-bold leading-tight tracking-tight">
            Hi, Gustavo
          </h1>
          <h2 className="text-white text-3xl font-bold leading-tight tracking-tight">
            What can{" "}
            <span className="text-blue-400">I help you</span>{" "}
            with?
          </h2>
          <p className="text-zinc-500 text-xs mt-2.5 leading-relaxed">
            Choose a prompt below or write your own to start chatting with Orbita GPT.
          </p>
        </div>

        {/* Input box */}
        <div className="w-full rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 overflow-hidden">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or make a request..."
            rows={2}
            className="w-full bg-transparent text-white placeholder-zinc-500 text-xs px-4 pt-3.5 pb-2 resize-none outline-none leading-relaxed"
          />
          {/* Toolbar */}
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
              <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all text-[11px] font-medium">
                <Paperclip className="w-3 h-3" />
                <span>Attach</span>
              </button>
              <button className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all">
                <Command className="w-3 h-3" />
              </button>
            </div>
            {/* Send button */}
            <button
              onClick={handleStartChat}
              className={`p-2 rounded-lg transition-all ${
                input.trim()
                  ? "bg-purple-600 hover:bg-purple-700 text-white"
                  : "bg-zinc-800/50 text-zinc-600 cursor-not-allowed"
              }`}
            >
              <Navigation className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Suggestion grid */}
        <div className="w-full grid grid-cols-2 gap-2">
          {suggestions.map((s, i) => (
            <SuggestionCard key={i} icon={s.icon} label={s.label} onClick={() => handleSuggestionClick(s.label)} />
          ))}
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="flex items-center gap-2 text-zinc-600 text-[10px] mt-12">
        <span>2024 Orbita GPT</span>
        <span>·</span>
        <button className="hover:text-zinc-400 transition-colors">Privacy Policy</button>
        <span>·</span>
        <button className="hover:text-zinc-400 transition-colors">Support</button>
      </footer>
    </div>
  );
};

export default NewChatScreen;
