"use client"

import { useState, useRef, useEffect } from "react"
import ChatInput from "./chatinputui"
import ChatMessage from "./chatmassegeui"
import { useSidebarContext } from "../main/layout"
import { TopBar } from "./chatmassegeui"
import NewChatScreen from "./new-chat-screen"

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

const ChatContainer = () => {
  const { isSidebarExpanded } = useSidebarContext()
  const [isChatActive, setIsChatActive] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [chatId, setChatId] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const res = await fetch(`${API_BASE_URL}/api/chats/send-message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          message: content,
          user_id: null
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err?.detail || `Request failed (${res.status})`)
      }

      const data: {
        chat_id: number
        messages: Array<{ role: string; content: string }>
      } = await res.json()

      setChatId(data.chat_id)

      const assistant = [...(data.messages || [])].reverse().find(m => m.role === "assistant")
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: assistant?.content || "No response received.",
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (e: any) {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${e?.message || "Failed to send message"}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartChat = (message: string) => {
    setIsChatActive(true)
    // Add welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      content: "Hello! I'm your AI assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date()
    }
    setMessages([welcomeMessage])
    // Send the initial message
    setTimeout(() => handleSendMessage(message), 100)
  }

  const handleNewChat = () => {
    setIsChatActive(false)
    setMessages([])
    setIsLoading(false)
    setChatId(null)
  }

  return (
    <div className="flex flex-col h-full bg-[#0F0F12] relative">
      {!isChatActive ? (
        <NewChatScreen onStartChat={handleStartChat} />
      ) : (
        <>
          {/* Top Bar - Fixed at very top, full width */}
          <div className="fixed top-0 left-0 right-0 z-20">
            <TopBar onNewChat={handleNewChat} />
          </div>
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 pt-12 pb-32">
            <div className="max-w-4xl mx-auto">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  content={message.content}
                  isUser={message.isUser}
                  showActions={!message.isUser}
                />
              ))}
              {isLoading && (
                <div className="mb-4">
                  <div className="text-zinc-300 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Chat Input - Fixed at bottom */}
          <div className={`fixed bottom-0 right-0 bg-[#0F0F12] px-6 py-4 z-10 transition-all duration-300 ease-in-out ${
            isSidebarExpanded ? "left-60" : "left-16"
          }`}>
            <div className="max-w-2xl mx-auto">
              <ChatInput onSend={handleSendMessage} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatContainer
