"use client"

import { useState } from "react";
import { Paperclip, Globe, Lightbulb, MoreHorizontal, ArrowUp } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
}

const ChatInput = ({ onSend }: ChatInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSend(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit}>
        {/* Floating Chatbar */}
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 shadow-lg">
          <Paperclip className="w-4 h-4 text-zinc-400 cursor-pointer hover:text-zinc-300 transition-colors" />
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            className="flex-1 bg-transparent text-white placeholder-zinc-500 outline-none text-xs"
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
            >
              <Globe className="w-3.5 h-3.5 text-zinc-400" />
              <span className="text-xs text-zinc-400">Search</span>
            </button>
            <button
              type="button"
              className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
            >
              <Lightbulb className="w-3.5 h-3.5 text-zinc-400" />
              <span className="text-xs text-zinc-400">Reason</span>
            </button>
            <button
              type="button"
              className="p-1.5 rounded-full hover:bg-zinc-800/50 transition-colors"
            >
              <MoreHorizontal className="w-4 h-4 text-zinc-400" />
            </button>
            <button
              type="submit"
              disabled={!message.trim()}
              className={`p-2 rounded-full transition-colors ${
                message.trim()
                  ? "bg-purple-600 hover:bg-purple-700 text-white"
                  : "bg-zinc-800/50 text-zinc-600 cursor-not-allowed"
              }`}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>
      <p className="text-center text-[10px] text-zinc-500 mt-2">
        AI can make mistakes. Please double-check responses.
      </p>
    </div>
  );
};

export default ChatInput;
