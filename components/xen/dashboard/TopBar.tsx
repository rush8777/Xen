"use client"

import { Search, Bell, Sparkles, LayoutGrid } from "lucide-react"
import { cn } from "@/lib/utils"

interface TopBarProps {
  title?: string
  credits?: number
}

export default function TopBar({ title = "Projects", credits = 360 }: TopBarProps) {
  return (
    <div className={cn(
      "flex items-center justify-between px-4 py-2.5",
      "backdrop-blur-sm"
    )}>

      {/* Left — page title */}
      <div className="flex items-center gap-2">
        <LayoutGrid className="w-4 h-4 text-zinc-400" strokeWidth={1.6} />
        <span className="text-sm font-semibold text-zinc-200 tracking-tight">
          {title}
        </span>
      </div>

      {/* Right — credits + search + notifications */}
      <div className="flex items-center gap-1">

        {/* Credits pill */}
        <button className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium",
          "bg-zinc-800/80 border border-zinc-700/50 text-zinc-300",
          "hover:border-zinc-600 hover:text-white transition-all duration-150"
        )}>
          <Sparkles className="w-3.5 h-3.5 text-blue-400" strokeWidth={1.8} />
          {credits} credits
        </button>

        {/* Search */}
        <button className={cn(
          "p-2 rounded-lg text-zinc-500 transition-all duration-150",
          "hover:text-white hover:bg-zinc-800"
        )}>
          <Search className="w-4 h-4" strokeWidth={1.8} />
        </button>

        {/* Notifications */}
        <button className={cn(
          "relative p-2 rounded-lg text-zinc-500 transition-all duration-150",
          "hover:text-white hover:bg-zinc-800"
        )}>
          <Bell className="w-4 h-4" strokeWidth={1.8} />
          {/* red dot */}
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-red-500 ring-1 ring-zinc-950" />
        </button>

      </div>
    </div>
  )
}
