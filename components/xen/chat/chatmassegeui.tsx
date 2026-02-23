"use client"

import { Copy, ThumbsUp, ThumbsDown, RotateCcw, Share2, Settings, Sparkles, Database, PanelRight } from "lucide-react";
import type { ComponentProps } from "react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Typewriter from "typewriter-effect";
import { useSidebarContext } from "../main/layout";

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  isStreaming?: boolean;
  showActions?: boolean;
  ragActive?: boolean;
  contextChunksUsed?: number;
  courseAvailable?: boolean;
  courseTemplate?: "default" | "sonos_typo" | "pixel_brutalist";
  onOpenCourse?: () => void;
}

interface TopBarProps {
  onNewChat?: () => void;
  ragActive?: boolean;
  onToggleContext?: () => void;
  contextOpen?: boolean;
}

const markdownComponents = {
  h1: (props: ComponentProps<"h1">) => (
    <h1 {...props} className={`mt-4 first:mt-0 text-lg font-semibold text-white ${props.className ?? ""}`} />
  ),
  h2: (props: ComponentProps<"h2">) => (
    <h2 {...props} className={`mt-4 first:mt-0 text-base font-semibold text-zinc-100 ${props.className ?? ""}`} />
  ),
  h3: (props: ComponentProps<"h3">) => (
    <h3 {...props} className={`mt-3 first:mt-0 text-sm font-semibold text-zinc-100 ${props.className ?? ""}`} />
  ),
  p: (props: ComponentProps<"p">) => (
    <p {...props} className={`leading-6 mt-3 first:mt-0 text-zinc-300 ${props.className ?? ""}`} />
  ),
  ul: (props: ComponentProps<"ul">) => (
    <ul {...props} className={`my-3 ml-5 list-disc text-zinc-300 [&>li]:mt-1 ${props.className ?? ""}`} />
  ),
  ol: (props: ComponentProps<"ol">) => (
    <ol {...props} className={`my-3 ml-5 list-decimal text-zinc-300 [&>li]:mt-1 ${props.className ?? ""}`} />
  ),
  li: (props: ComponentProps<"li">) => (
    <li {...props} className={`leading-6 ${props.className ?? ""}`} />
  ),
  a: (props: ComponentProps<"a">) => (
    <a
      {...props}
      target="_blank"
      rel="noopener noreferrer"
      className={`underline underline-offset-4 text-sky-400 hover:text-sky-300 transition-colors ${props.className ?? ""}`}
    />
  ),
  blockquote: (props: ComponentProps<"blockquote">) => (
    <blockquote
      {...props}
      className={`my-3 border-l-2 border-zinc-700 pl-3 italic text-zinc-400 ${props.className ?? ""}`}
    />
  ),
  code: (props: ComponentProps<"code">) => (
    <code
      {...props}
      className={`rounded-md bg-zinc-800 px-1.5 py-0.5 font-mono text-[11px] text-zinc-100 ${props.className ?? ""}`}
    />
  ),
  pre: (props: ComponentProps<"pre">) => (
    <pre
      {...props}
      className={`my-3 overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900 p-3 text-[11px] ${props.className ?? ""}`}
    />
  ),
  table: (props: ComponentProps<"table">) => (
    <div className="my-3 w-full overflow-x-auto">
      <table {...props} className={`w-full text-xs text-zinc-300 ${props.className ?? ""}`} />
    </div>
  ),
  th: (props: ComponentProps<"th">) => (
    <th {...props} className={`border-b border-zinc-700 px-2 py-1.5 text-left font-medium text-zinc-100 ${props.className ?? ""}`} />
  ),
  td: (props: ComponentProps<"td">) => (
    <td {...props} className={`border-b border-zinc-800 px-2 py-1.5 align-top ${props.className ?? ""}`} />
  ),
  hr: (props: ComponentProps<"hr">) => (
    <hr {...props} className={`my-4 border-zinc-800 ${props.className ?? ""}`} />
  ),
};

// ── Top Bar ────────────────────────────────────────────────────────────────────
const TopBar = ({ onNewChat, ragActive, onToggleContext, contextOpen }: TopBarProps) => {
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
        {ragActive && (
          <span className="flex items-center gap-1 bg-purple-900/40 text-purple-300 text-[10px] font-medium px-1.5 py-0.5 rounded-md border border-purple-700/50">
            <Database className="w-2.5 h-2.5" />
            RAG
          </span>
        )}
      </div>

      {/* Right – actions */}
      <div className="flex items-center gap-1.5">
        {/* Retrieved Context */}
        <button
          onClick={onToggleContext}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition-colors border ${
            contextOpen ? "border-zinc-600/70 bg-zinc-900/60" : "border-transparent hover:border-zinc-700/50"
          }`}
          title="Show retrieved context"
        >
          <span>Context</span>
          <PanelRight className="w-3.5 h-3.5 text-zinc-400" />
        </button>

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
const ChatMessage = ({
  content,
  isUser,
  isStreaming = false,
  showActions = false,
  ragActive,
  contextChunksUsed,
  courseAvailable = false,
  courseTemplate = "default",
  onOpenCourse,
}: ChatMessageProps) => {
  const [animatedContent, setAnimatedContent] = useState(content);

  useEffect(() => {
    if (isUser) {
      setAnimatedContent(content);
      return;
    }

    if (!content) {
      setAnimatedContent("");
      return;
    }

    const timer = window.setInterval(() => {
      setAnimatedContent((prev) => {
        if (prev === content) return prev;
        if (!content.startsWith(prev)) return content;
        const step = isStreaming ? 2 : 3;
        const nextLength = Math.min(content.length, prev.length + step);
        return content.slice(0, nextLength);
      });
    }, 12);

    return () => window.clearInterval(timer);
  }, [content, isStreaming, isUser]);

  const showTypingCursor = isStreaming || animatedContent.length < content.length;

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
        {isStreaming && !animatedContent.trim() ? (
          <div className="py-1">
            <div className="text-zinc-400 text-xs">
              <Typewriter
                options={{
                  strings: [
                    "Thinking through your request...",
                    "Analyzing context...",
                    "Generating response...",
                  ],
                  autoStart: true,
                  loop: true,
                  delay: 18,
                  deleteSpeed: 14,
                }}
              />
            </div>
          </div>
        ) : (
          <>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {animatedContent}
            </ReactMarkdown>
            {showTypingCursor && (
              <span
                aria-hidden
                className="inline-block ml-1 h-3 w-1.5 rounded-sm bg-zinc-400 align-middle animate-pulse"
              />
            )}
          </>
        )}
      </div>
      {courseAvailable && !isStreaming && (
        <div className="mt-3 max-w-xl rounded-2xl border border-zinc-700/70 bg-zinc-900/70 p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="h-10 w-10 shrink-0 rounded-lg border border-zinc-700 bg-zinc-950/80 flex items-center justify-center text-zinc-400 text-xs">
                {"</>"}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-zinc-100">
                  {courseTemplate === "sonos_typo"
                    ? "SonosTypoCourse"
                    : courseTemplate === "pixel_brutalist"
                    ? "PixelBrutalistCourse"
                    : "TeachCanvasKitCourse"}
                </div>
                <div className="text-xs text-zinc-400">Course Template • TSX</div>
              </div>
            </div>
            <button
              onClick={onOpenCourse}
              className="shrink-0 rounded-xl border border-zinc-600 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-100 hover:bg-zinc-800 transition-colors"
            >
              Open Course
            </button>
          </div>
        </div>
      )}
      {showActions && !isStreaming && (
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
          {ragActive && contextChunksUsed !== undefined && contextChunksUsed > 0 && (
            <span className="ml-1 flex items-center gap-1 text-[9px] text-purple-400 border border-purple-800/50 bg-purple-900/20 px-1.5 py-0.5 rounded-md">
              <Database className="w-2.5 h-2.5" />
              {contextChunksUsed} video {contextChunksUsed === 1 ? "segment" : "segments"} used
            </span>
          )}
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
