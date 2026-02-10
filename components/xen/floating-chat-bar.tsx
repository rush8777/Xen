"use client"

import { useState } from "react"
import {
  MessageCircle,
  ArrowUp,
  X,
  Search,
  Sun,
  Moon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import ChatMessage from "@/components/xen/chat/chatmassegeui"
import ChatInput from "@/components/xen/chat/chatinputui"
import { useSidebarContext } from "@/components/xen/main/layout"

type Message = {
  id: number
  content: string
  isUser: boolean
}

type ChatHistoryItem = {
  id: string
  title: string
  timestamp: string
}

interface FloatingVideoChatProps {
  initialMessages?: Message[]
}

export default function FloatingVideoChat({
  initialMessages = [],
}: FloatingVideoChatProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [modalInput, setModalInput] = useState("")
  const [editorMessages, setEditorMessages] = useState<Message[]>(initialMessages)
  const [isDarkMode, setIsDarkMode] = useState(true)
  const { setIsSidebarExpanded } = useSidebarContext()

  // Sample chat history data
  const recentChats: ChatHistoryItem[] = [
    { id: "1", title: "Absolutely! Let me gather some...", timestamp: "Recent" },
    { id: "2", title: "Under tenancy law, landlord...", timestamp: "Recent" },
    { id: "3", title: "You'll need to gather evidence of...", timestamp: "Recent" },
    { id: "4", title: "That depends on your state's coa...", timestamp: "Recent" },
    { id: "5", title: "Yes, you can! I can help you draft...", timestamp: "Recent" },
  ]

  const lastWeekChats: ChatHistoryItem[] = [
    { id: "6", title: "That depends on your state's coa...", timestamp: "Last Week" },
    { id: "7", title: "Yes, you can! I can help you draft...", timestamp: "Last Week" },
    { id: "8", title: "Under tenancy law, landlord...", timestamp: "Last Week" },
  ]

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return
    
    // Add user message
    setEditorMessages(prev => [...prev, { id: Date.now(), content: message, isUser: true }])
    setModalInput("")
    
    // Simulate AI response
    setTimeout(() => {
      setEditorMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        content: "I understand you want to edit video. I can help you with trimming, adding captions, extracting clips, and more. What would you like to do?", 
        isUser: false 
      }])
    }, 1000)
  }

  return (
    <>
      {/* Backdrop - Only when expanded */}
      {isExpanded && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm transition-all duration-300 z-[50]" />
      )}
      
      <div className="fixed bottom-0 left-0 right-0 flex flex-col items-center pointer-events-none z-[60]">
        <div className="w-full max-w-md pointer-events-auto mb-4">
          {/* Expanded Chat Modal */}
          {isExpanded && (
            <div className="fixed inset-0 flex items-end justify-center pb-4 pr-8">
              <div className="w-full max-w-6xl max-h-[calc(80vh+5rem)] rounded-lg bg-white/5 dark:bg-zinc-900/70 border border-zinc-100 dark:border-zinc-800 shadow-sm backdrop-blur-xl flex overflow-hidden transition-all duration-500 ease-in-out pb-[5.5rem]">
                
                {/* Left Sidebar - Chat History */}
                <div className="w-64 h-full min-h-0 bg-black/20 backdrop-blur-sm border-r border-zinc-800 flex flex-col">
                  {/* Sidebar Header */}
                  <div className="p-4 border-b border-zinc-800 flex-shrink-0">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                        <MessageCircle className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-sm font-semibold text-white">JustLegal</span>
                    </div>
                  </div>

                  {/* Chat History List */}
                  <div className="flex-1 min-h-0 overflow-y-auto">
                    {/* Recent Section */}
                    <div className="p-3">
                      <h3 className="text-xs font-semibold text-zinc-500 mb-2 px-2">Recent</h3>
                      <div className="space-y-1">
                        {recentChats.map((chat) => (
                          <button
                            key={chat.id}
                            className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 transition-colors group"
                          >
                            <div className="flex items-start gap-2">
                              <MessageCircle className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
                              <span className="text-sm text-zinc-300 line-clamp-1 group-hover:text-white transition-colors">
                                {chat.title}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Last Week Section */}
                    <div className="p-3">
                      <h3 className="text-xs font-semibold text-zinc-500 mb-2 px-2">Last Week</h3>
                      <div className="space-y-1">
                        {lastWeekChats.map((chat) => (
                          <button
                            key={chat.id}
                            className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 transition-colors group"
                          >
                            <div className="flex items-start gap-2">
                              <MessageCircle className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
                              <span className="text-sm text-zinc-300 line-clamp-1 group-hover:text-white transition-colors">
                                {chat.title}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Sidebar Footer - Theme Toggle & User */}
                  <div className="p-4 border-t border-zinc-800 mt-auto flex-shrink-0">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs text-zinc-500">Theme</span>
                      <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1">
                        <button
                          onClick={() => setIsDarkMode(false)}
                          className={cn(
                            "p-1.5 rounded transition-colors",
                            !isDarkMode ? "bg-white text-black" : "text-zinc-500 hover:text-zinc-300"
                          )}
                        >
                          <Sun className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setIsDarkMode(true)}
                          className={cn(
                            "p-1.5 rounded transition-colors",
                            isDarkMode ? "bg-white text-black" : "text-zinc-500 hover:text-zinc-300"
                          )}
                        >
                          <Moon className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* User Profile */}
                    <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center">
                        <span className="text-xs font-semibold text-white">J</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">Jimmy</p>
                        <p className="text-xs text-zinc-500 truncate">jimmy@gmail.com</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Main Chat Area */}
                <div className="flex-1 flex flex-col">
                  {/* Header */}
                  <div className="flex items-start justify-between p-4 pb-2 flex-shrink-0 border-b border-zinc-800">
                    <div className="flex items-start gap-2.5">
                      <div className="p-1.5 bg-[#3A3A3E] rounded-lg">
                        <MessageCircle className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <h2 className="text-lg font-bold text-white mb-0.5">
                          Justlegal Chat
                        </h2>
                        <p className="text-[11px] text-gray-400">
                          Ask questions about video content.
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsExpanded(false)}
                      className="p-1.5 hover:bg-[#4A4A4E] rounded-lg transition-colors duration-200"
                    >
                      <X className="w-4 h-4 text-gray-400 hover:text-white" />
                    </button>
                  </div>

                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto space-y-4 p-4">
                    {editorMessages.map((msg) => (
                      <ChatMessage 
                        key={msg.id} 
                        content={msg.content} 
                        isUser={msg.isUser}
                        showActions={!msg.isUser}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Floating Chat Bar */}
          <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-6 py-2 shadow-lg">
            <MessageCircle className="h-5 w-5 text-zinc-400" />
            {!isExpanded ? (
              <input
                readOnly
                placeholder="Ask a question..."
                onClick={() => {
                  setIsExpanded(true)
                  setIsSidebarExpanded(false)
                }}
                className="flex-1 bg-transparent text-white placeholder-zinc-500 outline-none text-sm cursor-pointer"
              />
            ) : (
              <input
                value={modalInput}
                onChange={(e) => setModalInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage(modalInput)
                  }
                }}
                placeholder="Ask anything..."
                className="flex-1 bg-transparent text-white placeholder-zinc-500 outline-none text-sm"
                autoFocus
              />
            )}
            <button
              onClick={() => isExpanded ? setIsExpanded(false) : setIsExpanded(true)}
              className={`p-2 rounded-full transition-colors ${
                isExpanded
                  ? "bg-purple-600 hover:bg-purple-700 text-white"
                  : "bg-zinc-800/50 text-zinc-600"
              }`}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  )
}