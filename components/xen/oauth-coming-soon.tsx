"use client"

import { Clock3 } from "lucide-react"
import { cn } from "@/lib/utils"

interface OAuthComingSoonProps {
  title?: string
  description?: string
  className?: string
}

export default function OAuthComingSoon({
  title = "Coming Soon",
  description = "OAuth-based project creation and integrations will be available soon.",
  className,
}: OAuthComingSoonProps) {
  return (
    <div
      className={cn(
        "w-full rounded-2xl border border-zinc-800 bg-zinc-900/90 p-8",
        "flex min-h-[320px] flex-col items-center justify-center text-center",
        className
      )}
    >
      <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800 text-zinc-300">
        <Clock3 className="h-6 w-6" />
      </div>
      <h2 className="mb-2 text-2xl font-semibold text-white">{title}</h2>
      <p className="max-w-xl text-sm text-zinc-400">{description}</p>
    </div>
  )
}

