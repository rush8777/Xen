"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Activity } from "lucide-react"
import { clamp, formatSecondsToTimeLabel } from "./psychology-timeline-utils"

type TimelinePoint = { time: number; intensity: number }

export interface EmotionalArcData {
  emotionalTimeline: TimelinePoint[]
  highestPeak: { time: number; value: number }
  strongestDrop: { time: number; value: number }
  volatilityScore: number
}

interface EmotionalArcMappingChartProps {
  data?: EmotionalArcData
  currentTimeSeconds?: number
  onSeek?: (seconds: number) => void
}

export default function EmotionalArcMappingChart({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
  onSeek,
}: EmotionalArcMappingChartProps) {
  const safeData: EmotionalArcData = data ?? {
    emotionalTimeline: [{ time: 0, intensity: 0 }],
    highestPeak: { time: 0, value: 0 },
    strongestDrop: { time: 0, value: 0 },
    volatilityScore: 0,
  }

  const chartData = safeData.emotionalTimeline.map((point) => ({
    ...point,
    timeLabel: formatSecondsToTimeLabel(point.time),
  }))
  const activeTimeLabel = Number.isFinite(currentTimeSeconds)
    ? formatSecondsToTimeLabel(Number(currentTimeSeconds || 0))
    : null

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-5 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">Emotional Arc Mapping</h3>
          <p className="text-xs text-zinc-400">Intensity shifts and volatility over time</p>
        </div>
        <div className="inline-flex items-center gap-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs text-blue-200">
          <Activity className="h-3.5 w-3.5" />
          Volatility {clamp(safeData.volatilityScore, 0, 100)}
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <YAxis domain={[0, 100]} stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#111217", border: "1px solid #27272a", borderRadius: 8 }}
              labelStyle={{ color: "#e4e4e7", fontSize: 12 }}
              formatter={(value: any) => [value, "Intensity"]}
            />
            {activeTimeLabel && <ReferenceLine x={activeTimeLabel} stroke="#a855f7" strokeDasharray="4 4" />}
            <Line type="monotone" dataKey="intensity" stroke="#a855f7" strokeWidth={2.5} dot={false} />
            <ReferenceDot
              x={formatSecondsToTimeLabel(safeData.highestPeak.time)}
              y={clamp(safeData.highestPeak.value, 0, 100)}
              fill="#22c55e"
              stroke="#86efac"
              strokeWidth={2}
              r={5}
            />
            <ReferenceDot
              x={formatSecondsToTimeLabel(safeData.strongestDrop.time)}
              y={clamp(safeData.strongestDrop.value, 0, 100)}
              fill="#ef4444"
              stroke="#fca5a5"
              strokeWidth={2}
              r={5}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onSeek?.(safeData.highestPeak.time)}
          className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-left"
        >
          <p className="text-xs font-medium text-emerald-300">Highest Peak</p>
          <p className="text-sm text-white">{clamp(safeData.highestPeak.value, 0, 100)}</p>
          <p className="text-[11px] text-zinc-300">{formatSecondsToTimeLabel(safeData.highestPeak.time)}</p>
        </button>
        <button
          type="button"
          onClick={() => onSeek?.(safeData.strongestDrop.time)}
          className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-left"
        >
          <p className="text-xs font-medium text-rose-300">Strongest Drop</p>
          <p className="text-sm text-white">{clamp(safeData.strongestDrop.value, 0, 100)}</p>
          <p className="text-[11px] text-zinc-300">{formatSecondsToTimeLabel(safeData.strongestDrop.time)}</p>
        </button>
      </div>
    </div>
  )
}
