"use client"

import { useRouter } from "next/navigation"
import { MessageCircle, ArrowUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface FloatingVideoChatProps {
  initialMessages?: any[]
}

export default function FloatingVideoChat({
  initialMessages = [],
}: FloatingVideoChatProps) {
  const router = useRouter()

  return (
    <div className="fixed bottom-0 left-0 right-0 flex flex-col items-center pointer-events-none z-[60]">
      <div className="w-full max-w-md pointer-events-auto mb-4">
        {/* Floating Chat Bar */}
        <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-6 py-2 shadow-lg">
          <MessageCircle className="h-5 w-5 text-zinc-400" />
          <input
            readOnly
            placeholder="Ask a question..."
            onClick={() => {
              router.push('/chat')
            }}
            className="flex-1 bg-transparent text-white placeholder-zinc-500 outline-none text-sm cursor-pointer"
          />
          <button
            onClick={() => router.push('/chat')}
            className="p-2 rounded-full transition-colors bg-zinc-800/50 text-zinc-600 hover:bg-purple-600 hover:text-white"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}