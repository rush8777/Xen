"use client"

import React, { useEffect, useMemo, useRef, useState } from "react"
import { cn } from "@/lib/utils"

export interface KeyMoment {
  id: string | number
  title: string
  category?: string
  impact_level?: "high" | "medium" | "low" | string
  start_time_seconds: number
  end_time_seconds: number
  duration_seconds?: number
  justification?: string
  context?: string
  key_quote?: string
}

export interface KeyMomentsTimelineProps {
  moments: KeyMoment[]
  totalDurationSeconds: number
  currentTimeSeconds?: number
  isDark?: boolean
  selectedMomentId?: string | number | null
  onMomentSelect?: (moment: KeyMoment) => void
  onSeek?: (seconds: number) => void
}

const SEGMENT_COLORS = [
  { bg: "bg-violet-500", ring: "ring-violet-400", hex: "#8b5cf6" },
  { bg: "bg-sky-500", ring: "ring-sky-400", hex: "#0ea5e9" },
  { bg: "bg-emerald-500", ring: "ring-emerald-400", hex: "#10b981" },
  { bg: "bg-amber-500", ring: "ring-amber-400", hex: "#f59e0b" },
  { bg: "bg-rose-500", ring: "ring-rose-400", hex: "#f43f5e" },
  { bg: "bg-fuchsia-500", ring: "ring-fuchsia-400", hex: "#d946ef" },
  { bg: "bg-teal-500", ring: "ring-teal-400", hex: "#14b8a6" },
  { bg: "bg-orange-500", ring: "ring-orange-400", hex: "#f97316" },
]

function formatTime(seconds: number) {
  const total = Math.max(0, Math.floor(seconds || 0))
  const hh = Math.floor(total / 3600)
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60
  if (hh > 0) return `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
}

function impactChipClass(isDark: boolean, impact?: string) {
  if (impact === "high") return isDark ? "bg-red-500/20 text-red-300" : "bg-red-100 text-red-700"
  if (impact === "medium") return isDark ? "bg-amber-500/20 text-amber-300" : "bg-amber-100 text-amber-700"
  return isDark ? "bg-sky-500/20 text-sky-300" : "bg-sky-100 text-sky-700"
}

export default function KeyMomentsTimeline({
  moments,
  totalDurationSeconds,
  currentTimeSeconds = 0,
  isDark = true,
  selectedMomentId,
  onMomentSelect,
  onSeek,
}: KeyMomentsTimelineProps) {
  const [localSelectedId, setLocalSelectedId] = useState<string | number | null>(null)
  const [hoveredId, setHoveredId] = useState<string | number | null>(null)
  const [tooltipX, setTooltipX] = useState(-1)
  const [tooltipTime, setTooltipTime] = useState(0)
  const trackRef = useRef<HTMLDivElement>(null)

  const total = Math.max(1, totalDurationSeconds || 1)

  useEffect(() => {
    if (selectedMomentId !== undefined) {
      setLocalSelectedId(selectedMomentId)
      return
    }
    setLocalSelectedId(moments[0]?.id ?? null)
  }, [selectedMomentId, moments])

  const activeMoment = useMemo(() => {
    return (
      moments.find((m) => m.id === localSelectedId) ??
      moments.find((m) => currentTimeSeconds >= m.start_time_seconds && currentTimeSeconds <= m.end_time_seconds) ??
      moments[0] ??
      null
    )
  }, [moments, localSelectedId, currentTimeSeconds])

  const playheadPct = Math.min(100, (currentTimeSeconds / total) * 100)

  return (
    <div className="space-y-3">
      <div
        ref={trackRef}
        className={cn(
          "relative h-9 rounded-xl overflow-visible cursor-crosshair select-none group",
          "bg-white dark:bg-zinc-900/70 border border-zinc-100 dark:border-zinc-800 shadow-sm backdrop-blur-xl"
        )}
        onMouseMove={(e) => {
          if (!trackRef.current) return
          const rect = trackRef.current.getBoundingClientRect()
          const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
          setTooltipX(pct * 100)
          setTooltipTime(pct * total)
        }}
        onMouseLeave={() => setTooltipX(-1)}
        onClick={(e) => {
          if (!trackRef.current) return
          const rect = trackRef.current.getBoundingClientRect()
          const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
          onSeek?.(pct * total)
        }}
      >
        {moments.map((moment, idx) => {
          const color = SEGMENT_COLORS[idx % SEGMENT_COLORS.length]
          const left = (moment.start_time_seconds / total) * 100
          const width = Math.max(0.4, ((moment.end_time_seconds - moment.start_time_seconds) / total) * 100)
          const isSelected = activeMoment?.id === moment.id
          const isHovered = hoveredId === moment.id
          return (
            <button
              key={moment.id}
              title={moment.title}
              style={{ left: `${left}%`, width: `${width}%` }}
              className={cn(
                "absolute inset-y-0 rounded-sm transition-all duration-150 focus:outline-none",
                color.bg,
                isSelected
                  ? `opacity-100 ring-2 ring-offset-1 ring-offset-transparent ${color.ring}`
                  : isHovered
                    ? "opacity-90"
                    : "opacity-60 hover:opacity-80"
              )}
              onMouseEnter={() => setHoveredId(moment.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={(e) => {
                e.stopPropagation()
                setLocalSelectedId(moment.id)
                onMomentSelect?.(moment)
                onSeek?.(moment.start_time_seconds)
              }}
            />
          )
        })}

        <div className="absolute top-0 bottom-0 w-0.5 z-20 pointer-events-none" style={{ left: `${playheadPct}%` }}>
          <div className={cn("w-full h-full", isDark ? "bg-white/90" : "bg-gray-900/80")} />
          <div
            className={cn(
              "absolute -top-1 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full border-2",
              isDark ? "bg-white border-zinc-900" : "bg-gray-900 border-white"
            )}
          />
        </div>

        {tooltipX >= 0 && (
          <div
            className={cn(
              "absolute -top-8 z-30 px-2 py-0.5 rounded text-[11px] font-mono whitespace-nowrap pointer-events-none -translate-x-1/2",
              isDark ? "bg-zinc-700 text-zinc-100" : "bg-gray-800 text-white"
            )}
            style={{ left: `${tooltipX}%` }}
          >
            {formatTime(tooltipTime)}
          </div>
        )}
      </div>

      {activeMoment && (
        <div className="mt-2 rounded-xl border px-4 py-3 bg-white dark:bg-zinc-900/70 border-zinc-100 dark:border-zinc-800 shadow-sm backdrop-blur-xl">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{
                  background: SEGMENT_COLORS[Math.max(0, moments.findIndex((m) => m.id === activeMoment.id)) % SEGMENT_COLORS.length].hex,
                }}
              />
              <p className={cn("text-sm font-semibold truncate", isDark ? "text-zinc-100" : "text-gray-900")}>{activeMoment.title}</p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 text-[11px] font-mono">
              {activeMoment.category && (
                <span className={cn("px-2 py-0.5 rounded-full", isDark ? "bg-zinc-800 text-zinc-300" : "bg-gray-200 text-gray-700")}>
                  {activeMoment.category}
                </span>
              )}
              {activeMoment.impact_level && (
                <span className={cn("px-2 py-0.5 rounded-full", impactChipClass(isDark, activeMoment.impact_level))}>
                  {activeMoment.impact_level}
                </span>
              )}
              <span className={isDark ? "text-zinc-500" : "text-gray-500"}>
                {formatTime(activeMoment.start_time_seconds)} - {formatTime(activeMoment.end_time_seconds)}
              </span>
            </div>
          </div>

          <p className={cn("text-xs leading-relaxed", isDark ? "text-zinc-300" : "text-gray-700")}>
            {activeMoment.justification || "No justification provided for this moment."}
          </p>
          <p className={cn("text-[11px] mt-2", isDark ? "text-zinc-400" : "text-gray-600")}>
            <span className="font-medium">Context:</span> {activeMoment.context || "No context provided."}
          </p>
          <p className={cn("text-[11px] mt-1", isDark ? "text-zinc-400" : "text-gray-600")}>
            <span className="font-medium">Key quote:</span> {activeMoment.key_quote || "No key quote captured."}
          </p>
        </div>
      )}
    </div>
  )
}
