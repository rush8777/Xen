"use client"

import { useState, useRef } from "react";
import { Paperclip, Globe, MoreHorizontal, ArrowUp } from "lucide-react";
import { useProjects } from './useProjects';

interface ChatInputProps {
  onSend: (
    message: string,
    mentionedProject?: string
  ) => void;
}

const ChatInput = ({ onSend }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredProjects, setFilteredProjects] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { projects } = useProjects();
  const inputRef = useRef<HTMLInputElement>(null);

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

      onSend(message, mentionedProject);
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
        <div className="w-full rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 overflow-hidden">
          <input
            ref={inputRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
            placeholder="Ask a question or make a request..."
            className="w-full bg-transparent text-white placeholder-zinc-500 text-xs px-4 pt-3.5 pb-2 outline-none leading-relaxed"
          />
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
              <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all text-[11px] font-medium">
                <Paperclip className="w-3 h-3" />
                <span>Attach</span>
              </button>
              <button className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all">
                <Globe className="w-3 h-3" />
              </button>
            </div>
            <button
              type="submit"
              disabled={!message.trim()}
              className={`p-2 rounded-lg transition-all ${
                message.trim()
                  ? "bg-purple-600 hover:bg-purple-700 text-white"
                  : "bg-zinc-800/50 text-zinc-600 cursor-not-allowed"
              }`}
            >
              <ArrowUp className="w-3.5 h-3.5" />
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
