"use client"

import { useState } from "react"
import {
  MessageCircle,
  ArrowUp,
  X,
  Paperclip,
  Globe,
  Lightbulb,
  MoreHorizontal,
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

interface FloatingVideoChatProps {
  initialMessages?: Message[]
}

export default function FloatingVideoChat({
  initialMessages = [],
}: FloatingVideoChatProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [modalInput, setModalInput] = useState("")
  const [editorMessages, setEditorMessages] = useState<Message[]>(initialMessages)
  const { setIsSidebarExpanded } = useSidebarContext()

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
            <div className="fixed inset-0 flex items-end justify-center pb-24">
              <div className="w-full max-w-6xl max-h-[80vh] p-3 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100 dark:border-zinc-800 shadow-sm backdrop-blur-xl flex flex-col transition-all duration-500 ease-in-out">
                {/* Header */}
                <div className="flex items-start justify-between p-4 pb-2 flex-shrink-0">
                  <div className="flex items-start gap-2.5">
                    <div className="p-1.5 bg-[#3A3A3E] rounded-lg">
                      <MessageCircle className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-lg font-bold text-white mb-0.5">
                        Video Assistant
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
                <div className="h-[75vh] overflow-y-auto space-y-4 p-4">
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
