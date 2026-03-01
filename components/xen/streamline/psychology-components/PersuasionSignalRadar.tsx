import { Megaphone } from "lucide-react"
import { clamp, formatSecondsToTimeLabel } from "./psychology-timeline-utils"

export type PersuasionNarrativeInterval = {
  start: number
  end: number
  narrative: string
  dominantSignal: "Authority" | "Urgency" | "Social Proof" | "Certainty" | "Scarcity" | "None"
  intensity: number
}

export interface PersuasionSignalsData {
  authority: number
  urgency: number
  socialProof: number
  certainty: number
  scarcity: number
}

export interface PersuasionNarrativeData {
  interval_seconds: 2 | 5
  persuasionScore: number
  dominantSignal: "Authority" | "Urgency" | "Social Proof" | "Certainty" | "Scarcity" | "None"
  intervals: PersuasionNarrativeInterval[]
}

interface PersuasionSignalRadarProps {
  data?: PersuasionNarrativeData
  onSeek?: (seconds: number) => void
}

export default function PersuasionSignalRadar({
  data,
  onSeek,
}: PersuasionSignalRadarProps) {
  const safeData: PersuasionNarrativeData = data ?? {
    interval_seconds: 5,
    persuasionScore: 0,
    dominantSignal: "None",
    intervals: [],
  }

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Persuasion Influence Mapping</h3>
          <p className="text-xs text-zinc-400">Dominant influence narrative by interval</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-1.5">
          <Megaphone className="h-4 w-4 text-sky-300" />
          <span className="text-sm font-semibold text-sky-200">{clamp(safeData.persuasionScore, 0, 100)}</span>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Overall Persuasion Score</p>
          <p className="text-sm font-semibold text-white">{clamp(safeData.persuasionScore, 0, 100)}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
          <p className="text-xs text-zinc-400">Dominant Influence Type</p>
          <p className="text-sm font-semibold text-white">{safeData.dominantSignal}</p>
        </div>
      </div>

      <div className="space-y-3">
        {safeData.intervals.length === 0 ? (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
            <p className="text-sm leading-relaxed text-zinc-300">
              No persuasion narrative intervals generated yet for this selection.
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
                  isHigh ? "shadow-[0_0_24px_rgba(56,189,248,0.2)]" : "",
                ].join(" ")}
              >
                <p className="mb-1 text-xs font-medium text-sky-300">
                  {formatSecondsToTimeLabel(interval.start)} - {formatSecondsToTimeLabel(interval.end)}
                </p>
                <p className="mb-2 text-[11px] text-zinc-400">Dominant: {interval.dominantSignal}</p>
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
