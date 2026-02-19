"use client"

import { Copy, ThumbsUp, ThumbsDown, RotateCcw, Share2, Settings, Plus, Sparkles } from "lucide-react";
import { useSidebarContext } from "../main/layout";

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  showActions?: boolean;
}

interface TopBarProps {
  onNewChat?: () => void;
}

// ── Top Bar ────────────────────────────────────────────────────────────────────
const TopBar = ({ onNewChat }: TopBarProps) => {
  const { isSidebarExpanded } = useSidebarContext()
  
  return (
    <div className={`flex items-center justify-between px-4 py-2 transition-all duration-300 ease-in-out ${
      isSidebarExpanded ? "ml-60" : "ml-16"
    } h-10`}>
      {/* Left – title + badge */}
      <div className="flex items-center gap-2">
        <span className="text-white text-sm font-semibold tracking-tight">Orbita GPT</span>
        <span className="flex items-center gap-0.5 bg-zinc-800 text-zinc-300 text-[10px] font-medium px-1.5 py-0.5 rounded-md border border-zinc-700/60">
          Plus
        </span>
      </div>

      {/* Right – actions */}
      <div className="flex items-center gap-1.5">
        {/* Configuration */}
        <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition-colors border border-transparent hover:border-zinc-700/50">
          <span>Configuration</span>
          <Settings className="w-3.5 h-3.5 text-zinc-400" />
        </button>

        {/* Share */}
        <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition-colors border border-transparent hover:border-zinc-700/50">
          <span>Share</span>
          <Share2 className="w-3.5 h-3.5 text-zinc-400" />
        </button>

        {/* New Chat */}
        <button 
          onClick={onNewChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-zinc-950 text-xs font-semibold hover:bg-zinc-100 transition-colors"
        >
          <span>New Chat</span>
          <Sparkles className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

// ── Chat Message ───────────────────────────────────────────────────────────────
const ChatMessage = ({ content, isUser, showActions = false }: ChatMessageProps) => {
  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-zinc-800 text-white px-3 py-2 rounded-2xl max-w-sm text-xs leading-relaxed">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <div className="text-zinc-300 text-xs leading-[1.6] max-w-xl">
        {content}
      </div>
      {showActions && (
        <div className="flex items-center gap-0.5 mt-2">
          <button className="p-1.5 rounded-md hover:bg-zinc-800/50 transition-colors">
            <Copy className="w-3.5 h-3.5 text-zinc-400" />
          </button>
          <button className="p-1.5 rounded-md hover:bg-zinc-800/50 transition-colors">
            <ThumbsUp className="w-3.5 h-3.5 text-zinc-400" />
          </button>
          <button className="p-1.5 rounded-md hover:bg-zinc-800/50 transition-colors">
            <ThumbsDown className="w-3.5 h-3.5 text-zinc-400" />
          </button>
          <button className="p-1.5 rounded-md hover:bg-zinc-800/50 transition-colors">
            <RotateCcw className="w-3.5 h-3.5 text-zinc-400" />
          </button>
          <button className="p-1.5 rounded-md hover:bg-zinc-800/50 transition-colors">
            <Share2 className="w-3.5 h-3.5 text-zinc-400" />
          </button>
        </div>
      )}
    </div>
  );
};

// ── Demo wrapper ───────────────────────────────────────────────────────────────
export const ChatLayout = () => (
  <div className="min-h-screen bg-zinc-950 flex flex-col">
    <TopBar />
    <div className="flex-1 px-6 py-6">
      <ChatMessage content="How does the new model compare to GPT-4?" isUser={true} />
      <ChatMessage
        content="The new model introduces several architectural improvements over GPT-4, including a more efficient attention mechanism and better long-context handling. Benchmarks show roughly 18% gains on reasoning tasks while maintaining similar inference latency."
        isUser={false}
        showActions={true}
      />
    </div>
  </div>
);

export { TopBar };
export default ChatMessage;