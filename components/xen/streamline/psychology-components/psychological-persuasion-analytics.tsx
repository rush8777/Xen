"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useSearchParams } from "next/navigation"
import CuriosityGapAnalyzerCard, { type CuriosityGapData } from "./CuriosityGapAnalyzerCard"
import EmotionalArcMappingChart, { type EmotionalArcData } from "./EmotionalArcMappingChart"
import TensionReleaseDynamicsChart, { type TensionReleaseData } from "./TensionReleaseDynamicsChart"
import PersuasionSignalRadar, {
  type PersuasionNarrativeData,
  type PersuasionSignalsData,
} from "./PersuasionSignalRadar"
import CognitiveLoadIndexCard, { type CognitiveLoadData } from "./CognitiveLoadIndexCard"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export type PsychologyStatus = "not_started" | "pending" | "completed" | "failed"

type LegacyCuriosityData = {
  curiosityScore: number
  spikes: Array<{ time: number; intensity: number }>
  openLoops: Array<{ time: number; text: string }>
  closedLoops: Array<{ time: number; text: string }>
}

export interface ProjectPsychologyPayload {
  curiosity: LegacyCuriosityData
  curiosity_narrative: CuriosityGapData
  emotional_arc: EmotionalArcData
  tension_release: TensionReleaseData
  persuasion_signals: PersuasionSignalsData
  persuasion_narrative: PersuasionNarrativeData
  cognitive_load: CognitiveLoadData
  source?: Record<string, any>
}

type ProjectPsychologyResponse = {
  project_id: number
  psychology: ProjectPsychologyPayload
  generated_at: string
  version: number
  status: string
}

type PsychologyStatusResponse = {
  project_id: number
  status: PsychologyStatus
  generated_at: string | null
  version: number | null
  error: string | null
}

const fallbackPsychologyPayload: ProjectPsychologyPayload = {
  curiosity: {
    curiosityScore: 66,
    spikes: [
      { time: 8, intensity: 74 },
      { time: 34, intensity: 80 },
      { time: 71, intensity: 67 },
    ],
    openLoops: [
      { time: 6, text: "Sets unresolved promise about final outcome." },
      { time: 33, text: "Introduces second uncertainty to extend retention." },
    ],
    closedLoops: [
      { time: 52, text: "Resolves first promise with concrete takeaway." },
      { time: 89, text: "Closes final loop with explicit payoff." },
    ],
  },
  curiosity_narrative: {
    interval_seconds: 5,
    curiosityScore: 66,
    totalOpenLoops: 4,
    avgLoopDuration: 18,
    intervals: [
      {
        start: 0,
        end: 5,
        intensity: 72,
        narrative:
          "The opening introduces a process claim while withholding operational detail. This creates an unresolved information gap that prompts expectation of a near-term reveal. Curiosity remains elevated because the framing signals relevance but defers the concrete mechanism viewers are waiting to understand.",
      },
      {
        start: 5,
        end: 10,
        intensity: 78,
        narrative:
          "Language reinforces uncertainty by adding a second implied promise without closing the first thread. Anticipation compounds as viewers track multiple pending outcomes. The segment sustains attention through controlled incompleteness, preserving forward momentum while postponing explicit procedural clarification.",
      },
    ],
  },
  emotional_arc: {
    emotionalTimeline: [
      { time: 0, intensity: 32 },
      { time: 20, intensity: 47 },
      { time: 40, intensity: 68 },
      { time: 60, intensity: 82 },
      { time: 80, intensity: 43 },
      { time: 100, intensity: 58 },
    ],
    highestPeak: { time: 60, value: 82 },
    strongestDrop: { time: 80, value: 43 },
    volatilityScore: 64,
  },
  tension_release: {
    tensionCurve: [
      { time: 0, value: 24 },
      { time: 20, value: 40 },
      { time: 40, value: 58 },
      { time: 60, value: 76 },
      { time: 80, value: 44 },
      { time: 100, value: 31 },
    ],
    releaseCurve: [
      { time: 0, value: 10 },
      { time: 20, value: 14 },
      { time: 40, value: 32 },
      { time: 60, value: 58 },
      { time: 80, value: 81 },
      { time: 100, value: 67 },
    ],
    totalCycles: 3,
    avgBuildDuration: 18,
    unresolvedCount: 1,
  },
  persuasion_signals: {
    authority: 71,
    urgency: 52,
    socialProof: 48,
    certainty: 66,
    scarcity: 39,
  },
  persuasion_narrative: {
    interval_seconds: 5,
    persuasionScore: 64,
    dominantSignal: "Authority",
    intervals: [
      {
        start: 0,
        end: 5,
        dominantSignal: "Authority",
        intensity: 68,
        narrative:
          "The segment foregrounds authority through confident declarative phrasing and implied expertise. Influence is framed as trust in execution quality rather than emotional urgency. This can reduce viewer hesitation by positioning the speaker as a credible source before evidentiary detail is fully disclosed.",
      },
      {
        start: 5,
        end: 10,
        dominantSignal: "Certainty",
        intensity: 74,
        narrative:
          "Certainty cues become dominant as statements narrow ambiguity and present outcomes as predictable. The persuasion frame shifts toward decisiveness, encouraging cognitive ease for the audience. Psychological impact is likely strongest among viewers seeking clear direction over exploratory or probabilistic interpretation.",
      },
    ],
  },
  cognitive_load: {
    cognitiveScore: 58,
    densityTimeline: [
      { time: 0, density: 34 },
      { time: 20, density: 41 },
      { time: 40, density: 57 },
      { time: 60, density: 69 },
      { time: 80, density: 81 },
      { time: 100, density: 62 },
    ],
    overloadDetected: true,
  },
}

type PsychologyAnalyticsProps = {
  currentTimeSeconds?: number | null
  durationSeconds?: number | null
  onSeekTimeline?: (seconds: number) => void
}

export default function PsychologicalPersuasionAnalytics({
  currentTimeSeconds,
  durationSeconds,
  onSeekTimeline,
}: PsychologyAnalyticsProps) {
  const searchParams = useSearchParams()
  const projectId = searchParams.get("projectId")

  const [status, setStatus] = useState<PsychologyStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [payload, setPayload] = useState<ProjectPsychologyPayload | null>(null)
  const [loadingPayload, setLoadingPayload] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [intervalSeconds, setIntervalSeconds] = useState<2 | 5>(5)
  const triggerRequested = useRef(false)

  const statusUrl = useMemo(() => {
    if (!projectId) return null
    return `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/psychology/status`
  }, [projectId])

  const dataUrl = useMemo(() => {
    if (!projectId) return null
    return `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/psychology?interval_seconds=${intervalSeconds}`
  }, [projectId, intervalSeconds])

  const regenerateUrl = useMemo(() => {
    if (!projectId) return null
    return `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/psychology/regenerate`
  }, [projectId])

  const fetchStatus = async () => {
    if (!statusUrl) return
    try {
      const res = await fetch(statusUrl, { cache: "no-store" })
      const json = (await res.json()) as PsychologyStatusResponse
      if (!res.ok) {
        setStatus(null)
        setStatusError((json as any)?.detail || `Failed to fetch psychology status (${res.status})`)
        return
      }
      setStatus(json.status)
      setStatusError(json.error || null)
    } catch (e: any) {
      setStatus(null)
      setStatusError(e?.message || "Failed to fetch psychology status")
    }
  }

  const fetchPayload = async () => {
    if (!dataUrl) return
    setLoadingPayload(true)
    try {
      const res = await fetch(dataUrl, { cache: "no-store" })
      const json = (await res.json()) as ProjectPsychologyResponse
      if (!res.ok) {
        setPayload(null)
        const detail = (json as any)?.detail || ""
        if (res.status === 400 && String(detail).includes("Variant not generated")) {
          setStatus("pending")
          setStatusError(null)
          await triggerGeneration(intervalSeconds)
          return
        }
        setStatusError((json as any)?.detail || `Failed to fetch psychology payload (${res.status})`)
        return
      }
      setPayload(json.psychology)
      setStatusError(null)
    } catch (e: any) {
      setPayload(null)
      setStatusError(e?.message || "Failed to fetch psychology payload")
    } finally {
      setLoadingPayload(false)
    }
  }

  const triggerGeneration = async (selectedIntervalSeconds?: 2 | 5) => {
    if (!regenerateUrl || regenerating) return
    const nextInterval = selectedIntervalSeconds || intervalSeconds
    setRegenerating(true)
    try {
      const res = await fetch(regenerateUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval_seconds: nextInterval }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail || `Failed to trigger psychology generation (${res.status})`)
      }
      setStatus("pending")
      setStatusError(null)
    } catch (e: any) {
      setStatusError(e?.message || "Failed to trigger psychology generation")
    } finally {
      setRegenerating(false)
    }
  }

  useEffect(() => {
    setStatus(null)
    setStatusError(null)
    setPayload(null)
    setLoadingPayload(false)
    setRegenerating(false)
    triggerRequested.current = false
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | null = null

    const poll = async () => {
      if (cancelled) return
      await fetchStatus()
      if (cancelled) return
      timer = setTimeout(poll, 2500)
    }

    poll()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [projectId, statusUrl])

  useEffect(() => {
    if (!projectId) return
    if (status !== "not_started") return
    if (triggerRequested.current) return
    triggerRequested.current = true
    triggerGeneration()
  }, [projectId, status])

  useEffect(() => {
    if (status !== "completed") return
    fetchPayload()
  }, [status, dataUrl])

  if (!projectId) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        Select a project to view psychology analytics.
      </div>
    )
  }

  if (status === "failed") {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Psychological analysis failed</div>
        <div className="text-xs text-zinc-400 mb-4">{statusError || "Unknown error"}</div>
        <button
          type="button"
          onClick={() => {
            void triggerGeneration()
          }}
          disabled={regenerating}
          className="px-3 py-1.5 rounded-md text-xs bg-white text-black disabled:opacity-60"
        >
          {regenerating ? "Retrying..." : "Retry Generation"}
        </button>
      </div>
    )
  }

  if (status === "not_started") {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Psychology analysis not generated yet</div>
        <div className="text-xs text-zinc-400 mb-4">
          Generate psychological and persuasion analytics for this project.
        </div>
        <button
          type="button"
          onClick={() => {
            void triggerGeneration()
          }}
          disabled={regenerating}
          className="px-3 py-1.5 rounded-md text-xs bg-white text-black disabled:opacity-60"
        >
          {regenerating ? "Generating..." : "Generate Analysis"}
        </button>
      </div>
    )
  }

  if (status === "pending" || status === null || loadingPayload) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Generating psychology analytics...</div>
        <div className="text-xs text-zinc-400">
          This tab updates automatically when processing finishes.
        </div>
      </div>
    )
  }

  const safePayload = payload ?? fallbackPsychologyPayload
  const safeCurrentTime = Number(currentTimeSeconds || 0)
  const safeCuriosityNarrative = safePayload.curiosity_narrative
  const safePersuasionNarrative = safePayload.persuasion_narrative

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300">Narrative interval mode</h3>
        <div className="inline-flex rounded-md border border-zinc-700 bg-zinc-900/70 p-0.5">
          {[2, 5].map((step) => {
            const active = intervalSeconds === step
            return (
              <button
                key={step}
                type="button"
                onClick={() => {
                  const selected = step as 2 | 5
                  setIntervalSeconds(selected)
                  setPayload(null)
                }}
                className={[
                  "px-3 py-1 text-xs rounded",
                  active ? "bg-zinc-100 text-black" : "text-zinc-300 hover:bg-zinc-800",
                ].join(" ")}
              >
                {step}s
              </button>
            )
          })}
        </div>
      </div>

      <CuriosityGapAnalyzerCard
        data={safeCuriosityNarrative}
        onSeek={onSeekTimeline}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <EmotionalArcMappingChart
          data={safePayload.emotional_arc}
          currentTimeSeconds={safeCurrentTime}
          onSeek={onSeekTimeline}
        />
        <TensionReleaseDynamicsChart
          data={safePayload.tension_release}
          currentTimeSeconds={safeCurrentTime}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <PersuasionSignalRadar
          data={safePersuasionNarrative}
          onSeek={onSeekTimeline}
        />
        <CognitiveLoadIndexCard
          data={safePayload.cognitive_load}
          currentTimeSeconds={safeCurrentTime}
        />
      </div>
    </div>
  )
}
