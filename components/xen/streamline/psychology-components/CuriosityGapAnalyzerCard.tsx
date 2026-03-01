import { Brain } from "lucide-react"
import { clamp, formatSecondsToTimeLabel } from "./psychology-timeline-utils"

export type CuriosityNarrativeInterval = {
  start: number
  end: number
  narrative: string
  intensity: number
}

export interface CuriosityGapData {
  interval_seconds: 2 | 5
  curiosityScore: number
  totalOpenLoops: number
  avgLoopDuration: number
  intervals: CuriosityNarrativeInterval[]
}

interface CuriosityGapAnalyzerCardProps {
  data?: CuriosityGapData
  onSeek?: (seconds: number) => void
}

export default function CuriosityGapAnalyzerCard({
  data,
  onSeek,
}: CuriosityGapAnalyzerCardProps) {
  const safeData: CuriosityGapData = data ?? {
    interval_seconds: 5,
    curiosityScore: 0,
    totalOpenLoops: 0,
    avgLoopDuration: 0,
    intervals: [],
  }

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Curiosity Architecture</h3>
          <p className="text-xs text-zinc-400">Interval narrative intelligence</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1.5">
          <Brain className="h-4 w-4 text-purple-300" />
          <span className="text-sm font-semibold text-purple-200">{clamp(safeData.curiosityScore, 0, 100)}</span>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Curiosity Score</p>
          <p className="text-sm font-semibold text-white">{clamp(safeData.curiosityScore, 0, 100)}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Total Open Loops</p>
          <p className="text-sm font-semibold text-white">{Math.max(0, safeData.totalOpenLoops)}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Average Loop Duration</p>
          <p className="text-sm font-semibold text-white">{Math.max(0, safeData.avgLoopDuration)}s</p>
        </div>
      </div>

      <div className="space-y-3">
        {safeData.intervals.length === 0 ? (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
            <p className="text-sm leading-relaxed text-zinc-300">
              No narrative intervals generated yet for this selection.
            </p>
          </div>
        ) : (
          safeData.intervals.map((interval, idx) => {
            const intensity = clamp(interval.intensity, 0, 100)
            const isHigh = intensity >= 70
            return (
              <button
                key={`${interval.start}-${interval.end}-${idx}`}
                type="button"
                onClick={() => onSeek?.(interval.start)}
                className={[
                  "w-full rounded-lg border p-4 text-left transition-all",
                  "border-zinc-800 bg-zinc-900/70 hover:border-zinc-700",
                  isHigh ? "shadow-[0_0_24px_rgba(168,85,247,0.22)]" : "",
                ].join(" ")}
              >
                <p className="mb-2 text-xs font-medium text-purple-300">
                  {formatSecondsToTimeLabel(interval.start)} - {formatSecondsToTimeLabel(interval.end)}
                </p>
                <p className="text-sm leading-7 text-zinc-200">{interval.narrative}</p>
              </button>
            )
          })
        )}
      </div>

      <p className="mt-4 text-[11px] text-zinc-500">
        Generated using Gemini video context and structured psychological extraction.
      </p>
    </div>
  )
}
