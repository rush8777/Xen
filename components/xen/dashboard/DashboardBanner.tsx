"use client"

import { ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface DashboardBannerProps {
  className?: string
}

export default function DashboardBanner({ className }: DashboardBannerProps) {
  return (
    <div
      className={cn(
        "relative h-56 w-full overflow-hidden border border-gray-200 dark:border-[#2F2F37]",
        "bg-gray-100 dark:bg-[#0F0F12] text-white",
        className
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(100%_90%_at_0%_0%,rgba(53,109,180,0.35),transparent_55%),radial-gradient(65%_90%_at_100%_100%,rgba(0,194,184,0.25),transparent_55%),linear-gradient(120deg,#1a1c24_0%,#0F0F12_55%,#161922_100%)] dark:bg-[radial-gradient(100%_90%_at_0%_0%,rgba(53,109,180,0.35),transparent_55%),radial-gradient(65%_90%_at_100%_100%,rgba(0,194,184,0.25),transparent_55%),linear-gradient(120deg,#1a1c24_0%,#0F0F12_55%,#161922_100%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.22)_0%,rgba(255,255,255,0.06)_45%,rgba(255,255,255,0.18)_100%)] dark:bg-[linear-gradient(to_right,rgba(0,0,0,0.38)_0%,rgba(0,0,0,0.15)_45%,rgba(0,0,0,0.35)_100%)]" />

      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: "repeat",
        }}
      />

      <div className="absolute -top-16 left-[22%] h-56 w-56 rounded-full bg-cyan-400/10 blur-3xl" />
      <div className="absolute -bottom-20 right-20 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl" />

      <div className="pointer-events-none absolute right-0 bottom-0 h-48 w-96">
        <img 
          src="/images/icons/war.png" 
          alt="Girl illustration" 
          className="h-full w-full object-contain"
        />
      </div>

      <p className="absolute right-5 top-4 z-20 text-xs font-medium tracking-wide text-white/80">Obsidian</p>

      <div className="relative z-10 flex h-full max-w-[62%] flex-col justify-center px-6 py-5 sm:px-8">
        <h2 className="text-3xl font-extrabold leading-[1.05] tracking-tight text-white">
          Transform Videos into
          <br />
          Strategic Insights
        </h2>

        <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-200">
          Transform any social media video into actionable insights. Start analyzing comments, trends, and audience behavior today.
        </p>

        <button
          className={cn(
            "mt-4 inline-flex w-fit items-center gap-2 rounded-full border border-white/55 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-white",
            "transition-colors duration-200 hover:bg-white/10"
          )}
        >
          FEATURES
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      
      <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-[#0F0F12] to-transparent sm:hidden" />
      <div className="absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-black/35 to-transparent" />
    </div>
  )
}
