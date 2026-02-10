"use client"

import { Copy, ThumbsUp, ThumbsDown, RotateCcw, Share2 } from "lucide-react";

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  showActions?: boolean;
}

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

export default ChatMessage;
