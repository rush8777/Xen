"use client"

import { useState, useRef, useEffect } from "react";
import { Paperclip, Globe, Lightbulb, MoreHorizontal, ArrowUp } from "lucide-react";
import { useProjects } from './useProjects';

interface ChatInputProps {
  onSend: (
    message: string,
    mentionedProject?: string,
    clarificationAnswers?: Record<string, string>,
    courseModeEnabled?: boolean
  ) => void;
  courseModeEnabled?: boolean;
  onToggleCourseMode?: () => void;
}

const ChatInput = ({ onSend, courseModeEnabled, onToggleCourseMode }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [mentionText, setMentionText] = useState("");
  const [filteredProjects, setFilteredProjects] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [internalCourseModeEnabled, setInternalCourseModeEnabled] = useState(false);
  const { projects, loading } = useProjects();
  const inputRef = useRef<HTMLInputElement>(null);
  const effectiveCourseModeEnabled =
    typeof courseModeEnabled === "boolean"
      ? courseModeEnabled
      : internalCourseModeEnabled;

  const handleToggleCourseMode = () => {
    if (onToggleCourseMode) {
      onToggleCourseMode();
      return;
    }
    setInternalCourseModeEnabled((prev) => !prev);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursor = inputRef.current?.selectionStart || 0;
    const textBeforeCursor = value.slice(0, cursor);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    // Check if we're still in an active mention (cursor is after @ and no space after)
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      // Only show suggestions if there's no space after @ (active mention)
      if (!textAfterAt.includes(' ')) {
        const mention = textAfterAt;
        setMentionText(mention);
        setFilteredProjects(projects.filter(p => p.toLowerCase().includes(mention.toLowerCase())));
        setShowSuggestions(true);
        setSelectedIndex(0);
      } else {
        // If there's a space after @, hide suggestions (mention is complete)
        setShowSuggestions(false);
      }
    } else {
      // No @ found before cursor, hide suggestions
      setShowSuggestions(false);
    }
    setMessage(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showSuggestions) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % filteredProjects.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => prev === 0 ? filteredProjects.length - 1 : prev - 1);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        selectProject(filteredProjects[selectedIndex]);
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    }
    if (e.key === "Enter" && !e.shiftKey && !showSuggestions) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      const loweredMessage = message.toLowerCase();
      let mentionedProject: string | undefined;
      let bestIndex = -1;

      for (const project of projects) {
        const atMention = `@${project.toLowerCase()}`;
        const idx = loweredMessage.lastIndexOf(atMention);
        if (idx > bestIndex) {
          bestIndex = idx;
          mentionedProject = project;
        }
      }

      if (!mentionedProject) {
        const fallbackMentions = [...message.matchAll(/@([^\s@]+)/g)];
        const lastMention = fallbackMentions[fallbackMentions.length - 1];
        mentionedProject = lastMention?.[1];
      }

      onSend(message, mentionedProject, undefined, effectiveCourseModeEnabled);
      setMessage("");
    }
  };

  const selectProject = (project: string) => {
    const cursor = inputRef.current?.selectionStart || 0;
    const textBeforeCursor = message.slice(0, cursor);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    if (lastAtIndex !== -1) {
      const mentionStart = lastAtIndex + 1;
      const mentionEnd = cursor;
      const newMessage = message.slice(0, mentionStart) + project + ' ' + message.slice(mentionEnd);
      setMessage(newMessage);
      setShowSuggestions(false);

      // Position cursor after the project name and space
      setTimeout(() => {
        if (inputRef.current) {
          const newCursorPosition = mentionStart + project.length + 1;
          inputRef.current.setSelectionRange(newCursorPosition, newCursorPosition);
          inputRef.current.focus();
        }
      }, 0);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit}>
        {/* Floating Chatbar */}
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 shadow-lg">
          <Paperclip className="w-4 h-4 text-zinc-400 cursor-pointer hover:text-zinc-300 transition-colors" />
          <input
            ref={inputRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
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
              onClick={handleToggleCourseMode}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-full transition-colors ${
                effectiveCourseModeEnabled
                  ? "bg-emerald-700/80 text-emerald-100 hover:bg-emerald-700"
                  : "bg-zinc-800/50 hover:bg-zinc-800"
              }`}
            >
              <Lightbulb className="w-3.5 h-3.5 text-zinc-400" />
              <span className="text-xs">Course Mode</span>
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
      {showSuggestions && filteredProjects.length > 0 && (
        <div className="absolute bottom-full mb-2 w-full bg-zinc-800 border border-zinc-600 rounded-md shadow-lg max-h-40 overflow-y-auto z-50">
          {filteredProjects.map((project, index) => (
            <div
              key={project}
              className={`px-3 py-2 text-xs text-white cursor-pointer hover:bg-zinc-700 ${index === selectedIndex ? 'bg-zinc-600' : ''}`}
              onMouseDown={(e) => e.preventDefault()} // Prevent blur
              onClick={() => selectProject(project)}
            >
              @{project}
            </div>
          ))}
        </div>
      )}
      <p className="text-center text-[10px] text-zinc-500 mt-2">
        AI can make mistakes. Please double-check responses.
      </p>
    </div>
  );
};

export default ChatInput;
