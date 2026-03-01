"use client"

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { formatSecondsToTimeLabel } from "./psychology-timeline-utils"

type CurvePoint = { time: number; value: number }

export interface TensionReleaseData {
  tensionCurve: CurvePoint[]
  releaseCurve: CurvePoint[]
  totalCycles: number
  avgBuildDuration: number
  unresolvedCount: number
}

interface TensionReleaseDynamicsChartProps {
  data?: TensionReleaseData
  currentTimeSeconds?: number
}

export default function TensionReleaseDynamicsChart({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
}: TensionReleaseDynamicsChartProps) {
  const safeData: TensionReleaseData = data ?? {
    tensionCurve: [{ time: 0, value: 0 }],
    releaseCurve: [{ time: 0, value: 0 }],
    totalCycles: 0,
    avgBuildDuration: 0,
    unresolvedCount: 0,
  }

  const combined = safeData.tensionCurve.map((point, idx) => ({
    time: point.time,
    timeLabel: formatSecondsToTimeLabel(point.time),
    tension: point.value,
    release: safeData.releaseCurve[idx]?.value ?? 0,
  }))

  const activeTimeLabel = Number.isFinite(currentTimeSeconds)
    ? formatSecondsToTimeLabel(Number(currentTimeSeconds || 0))
    : null

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Tension & Release Dynamics</h3>
        <p className="text-xs text-zinc-400">Dual-curve view of build and payoff behavior</p>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={combined} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <YAxis domain={[0, 100]} stroke="#71717a" tick={{ fill: "#71717a", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#111217", border: "1px solid #27272a", borderRadius: 8 }}
              labelStyle={{ color: "#e4e4e7", fontSize: 12 }}
            />
            <Legend />
            {activeTimeLabel && <ReferenceLine x={activeTimeLabel} stroke="#a855f7" strokeDasharray="4 4" />}
            <Line type="monotone" dataKey="tension" stroke="#f59e0b" strokeWidth={2.4} dot={false} name="Tension" />
            <Line type="monotone" dataKey="release" stroke="#22c55e" strokeWidth={2.4} dot={false} name="Release" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Tension Cycles</p>
          <p className="text-sm font-semibold text-white">{safeData.totalCycles}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Avg Build Duration</p>
          <p className="text-sm font-semibold text-white">{safeData.avgBuildDuration}s</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Unresolved Tension</p>
          <p className="text-sm font-semibold text-white">{safeData.unresolvedCount}</p>
        </div>
      </div>
    </div>
  )
}
