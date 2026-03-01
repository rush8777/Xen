"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { AlertTriangle } from "lucide-react"
import { clamp, formatSecondsToTimeLabel } from "./psychology-timeline-utils"

type DensityPoint = { time: number; density: number }

export interface CognitiveLoadData {
  cognitiveScore: number
  densityTimeline: DensityPoint[]
  overloadDetected: boolean
}

interface CognitiveLoadIndexCardProps {
  data?: CognitiveLoadData
  currentTimeSeconds?: number
}

export default function CognitiveLoadIndexCard({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
}: CognitiveLoadIndexCardProps) {
  const safeData: CognitiveLoadData = data ?? {
    cognitiveScore: 0,
    densityTimeline: [{ time: 0, density: 0 }],
    overloadDetected: false,
  }
  const chartData = safeData.densityTimeline.map((point) => ({
    timeLabel: formatSecondsToTimeLabel(point.time),
    density: clamp(point.density, 0, 100),
  }))
  const activeTimeLabel = Number.isFinite(currentTimeSeconds)
    ? formatSecondsToTimeLabel(Number(currentTimeSeconds || 0))
    : null

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">Cognitive Load Index</h3>
          <p className="text-xs text-zinc-400">Information density and processing pressure</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-white">{clamp(safeData.cognitiveScore, 0, 100)}</p>
          <p className="text-[11px] text-zinc-400">/ 100</p>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
            <defs>
              <linearGradient id="densityFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <YAxis domain={[0, 100]} stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#111217", border: "1px solid #27272a", borderRadius: 8 }}
              labelStyle={{ color: "#e4e4e7", fontSize: 12 }}
            />
            {activeTimeLabel && <ReferenceLine x={activeTimeLabel} stroke="#a855f7" strokeDasharray="4 4" />}
            <ReferenceLine y={75} stroke="#f97316" strokeDasharray="3 3" />
            <Area type="monotone" dataKey="density" stroke="#22d3ee" fillOpacity={1} fill="url(#densityFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {safeData.overloadDetected && (
        <div className="mt-4 inline-flex items-center gap-2 rounded-md border border-orange-500/30 bg-orange-500/10 px-2.5 py-1.5">
          <AlertTriangle className="h-4 w-4 text-orange-300" />
          <span className="text-xs text-orange-200">Cognitive overload risk detected</span>
        </div>
      )}
    </div>
  )
}
