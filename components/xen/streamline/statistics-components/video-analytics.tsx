"use client"

import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Pause, Play } from "lucide-react"
import EmotionalIntensityChart from "./emotional-anal"
import VideoMetricsGrid from "./VideoMetricsGrid"
import SentimentPulseChart from "./SentimentPulseChart"
import EmotionRadarChart from "./EmotionRadarChart"
import EngagementTrendCurve from "./EngagementTrendCurve"
import { formatSecondsToTimeLabel, getTimelineMaxSeconds } from "./timeline-utils"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

type StatisticsStatus = "not_started" | "pending" | "completed" | "failed"

type ProjectStatisticsPayload = {
  version?: number
  video_metrics_grid?: any
  sentiment_pulse?: any
  emotion_radar?: any
  emotional_intensity_timeline?: any
  engagement_trend_curve?: any
  source?: {
    video_duration_seconds?: number | null
  }
}

type ProjectStatisticsResponse = {
  project_id: number
  stats: ProjectStatisticsPayload
  generated_at: string
  version: number
  status: string
}

type ProjectStatisticsStatusResponse = {
  project_id: number
  status: StatisticsStatus
  generated_at: string | null
  version: number | null
  error: string | null
}

type VideoAnalyticsProps = {
  currentTimeSeconds?: number | null
  durationSeconds?: number | null
  isExternalClockActive?: boolean
  onSeekTimeline?: (seconds: number) => void
}

export default function VideoAnalytics({
  currentTimeSeconds,
  durationSeconds,
  isExternalClockActive,
  onSeekTimeline,
}: VideoAnalyticsProps) {
  const searchParams = useSearchParams()
  const projectId = searchParams.get("projectId")

  const [status, setStatus] = useState<StatisticsStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)

  const [stats, setStats] = useState<ProjectStatisticsPayload | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)

  const [loading, setLoading] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [syntheticTimeSeconds, setSyntheticTimeSeconds] = useState(0)
  const [syntheticPlaying, setSyntheticPlaying] = useState(false)

  const handleRegenerateStats = async () => {
    if (!projectId || regenerating) return

    setRegenerating(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/statistics/regenerate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to start statistics generation')
      }

      // Refresh status to trigger polling
      if (statusUrl) {
        const statusRes = await fetch(statusUrl, { cache: "no-store" })
        if (statusRes.ok) {
          const statusJson = await statusRes.json()
          setStatus(statusJson.status)
        }
      }
    } catch (error) {
      console.error('Failed to regenerate statistics:', error)
    } finally {
      setRegenerating(false)
    }
  }

  const statusUrl = useMemo(() => {
    if (!projectId) return null
    return `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/statistics/status`
  }, [projectId])

  const statsUrl = useMemo(() => {
    if (!projectId) return null
    return `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/statistics`
  }, [projectId])

  useEffect(() => {
    setStatus(null)
    setStatusError(null)
    setStats(null)
    setStatsError(null)
    setLoading(false)
    setSyntheticPlaying(false)
    setSyntheticTimeSeconds(0)
  }, [projectId])

  const inferredTimelineDuration = useMemo(
    () =>
      getTimelineMaxSeconds(
        stats?.sentiment_pulse,
        stats?.emotional_intensity_timeline,
        stats?.engagement_trend_curve
      ),
    [stats]
  )

  const statsDurationSeconds = useMemo(() => {
    const value = stats?.source?.video_duration_seconds
    return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : 0
  }, [stats])

  const timelineDuration = useMemo(() => {
    if (durationSeconds && durationSeconds > 0) return durationSeconds
    if (statsDurationSeconds > 0) return statsDurationSeconds
    if (inferredTimelineDuration > 0) return inferredTimelineDuration
    return 0
  }, [durationSeconds, statsDurationSeconds, inferredTimelineDuration])

  const externalClockEnabled = Boolean(isExternalClockActive && currentTimeSeconds !== null && currentTimeSeconds !== undefined)
  const activeTimelineTime = externalClockEnabled
    ? Number(currentTimeSeconds || 0)
    : syntheticTimeSeconds

  useEffect(() => {
    if (!externalClockEnabled) return
    setSyntheticTimeSeconds(Math.max(0, Number(currentTimeSeconds || 0)))
  }, [externalClockEnabled, currentTimeSeconds])

  useEffect(() => {
    if (externalClockEnabled) return
    if (!syntheticPlaying) return
    if (!timelineDuration || timelineDuration <= 0) return

    const intervalId = setInterval(() => {
      setSyntheticTimeSeconds((prev) => {
        const next = prev + 0.25
        if (next >= timelineDuration) {
          setSyntheticPlaying(false)
          return timelineDuration
        }
        return next
      })
    }, 250)

    return () => clearInterval(intervalId)
  }, [externalClockEnabled, syntheticPlaying, timelineDuration])

  useEffect(() => {
    let cancelled = false
    let intervalId: any = null

    const fetchStatus = async () => {
      if (!statusUrl) return
      try {
        const res = await fetch(statusUrl, { cache: "no-store" })
        const json = (await res.json()) as ProjectStatisticsStatusResponse

        if (cancelled) return

        if (!res.ok) {
          setStatus(null)
          setStatusError(typeof (json as any)?.detail === "string" ? (json as any).detail : `Failed to fetch status (${res.status})`)
          return
        }

        setStatus(json.status)
        setStatusError(json.error)
      } catch (e: any) {
        if (cancelled) return
        setStatus(null)
        setStatusError(e?.message || "Failed to fetch status")
      }
    }

    const fetchStats = async () => {
      if (!statsUrl) return
      setLoading(true)
      try {
        const res = await fetch(statsUrl, { cache: "no-store" })
        const json = (await res.json()) as ProjectStatisticsResponse

        if (cancelled) return

        if (!res.ok) {
          setStats(null)
          setStatsError(typeof (json as any)?.detail === "string" ? (json as any).detail : `Failed to fetch statistics (${res.status})`)
          return
        }

        setStats(json.stats)
        setStatsError(null)
      } catch (e: any) {
        if (cancelled) return
        setStats(null)
        setStatsError(e?.message || "Failed to fetch statistics")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    const run = async () => {
      if (!projectId) return

      await fetchStatus()
      if (cancelled) return

      if (status === "completed") {
        await fetchStats()
        return
      }

      intervalId = setInterval(async () => {
        await fetchStatus()
      }, 2500)
    }

    run()

    return () => {
      cancelled = true
      if (intervalId) clearInterval(intervalId)
    }
  }, [projectId, statusUrl, statsUrl, status])

  useEffect(() => {
    if (status !== "completed") return
    if (!statsUrl) return
    if (stats) return

    let cancelled = false

    const run = async () => {
      try {
        setLoading(true)
        const res = await fetch(statsUrl, { cache: "no-store" })
        const json = (await res.json()) as ProjectStatisticsResponse
        if (cancelled) return

        if (!res.ok) {
          setStats(null)
          setStatsError(typeof (json as any)?.detail === "string" ? (json as any).detail : `Failed to fetch statistics (${res.status})`)
          return
        }

        setStats(json.stats)
        setStatsError(null)
      } catch (e: any) {
        if (cancelled) return
        setStats(null)
        setStatsError(e?.message || "Failed to fetch statistics")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    run()

    return () => {
      cancelled = true
    }
  }, [status, statsUrl, stats])

  if (!projectId) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        Select a project to view statistics.
      </div>
    )
  }

  if (status === "failed") {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Statistics generation failed</div>
        <div className="text-xs text-zinc-400">{statusError || "Unknown error"}</div>
      </div>
    )
  }

  if (status === "not_started") {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-semibold mb-1">Statistics not generated yet</div>
            <div className="text-xs text-zinc-400">
              Click below to generate detailed video analytics for this project.
            </div>
          </div>
          <button
            onClick={handleRegenerateStats}
            disabled={regenerating}
            className="px-4 py-2 bg-white hover:bg-gray-100 text-black rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {regenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Statistics'
            )}
          </button>
        </div>
      </div>
    )
  }

  if (status === "pending" || loading) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Generating statistics…</div>
        <div className="text-xs text-zinc-400">
          This tab will update automatically once the backend finishes.
        </div>
      </div>
    )
  }

  if (statsError) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800 text-zinc-300">
        <div className="text-white font-semibold mb-1">Could not load statistics</div>
        <div className="text-xs text-zinc-400">{statsError}</div>
      </div>
    )
  }

  const handleTimelineSeek = (nextValue: number) => {
    const clamped = Math.max(0, Math.min(nextValue, timelineDuration || nextValue))
    setSyntheticTimeSeconds(clamped)
    if (externalClockEnabled && onSeekTimeline) {
      onSeekTimeline(clamped)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-100 dark:border-zinc-800 bg-white dark:bg-zinc-900/70 shadow-sm backdrop-blur-xl p-4">
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              {externalClockEnabled ? "Synced to video playback" : "Synthetic timeline playback"}
            </p>
            <button
              type="button"
              onClick={() => {
                if (externalClockEnabled) return
                setSyntheticPlaying((prev) => !prev)
              }}
              disabled={externalClockEnabled || timelineDuration <= 0}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {syntheticPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              {syntheticPlaying ? "Pause" : "Play"}
            </button>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(1, Math.floor(timelineDuration || 1))}
            value={Math.max(0, Math.floor(activeTimelineTime || 0))}
            onChange={(e) => handleTimelineSeek(Number(e.target.value))}
            className="w-full accent-purple-600"
          />
          <div className="flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400">
            <span>{formatSecondsToTimeLabel(activeTimelineTime || 0)}</span>
            <span>{formatSecondsToTimeLabel(timelineDuration || 0)}</span>
          </div>
        </div>
      </div>

      <VideoMetricsGrid data={stats?.video_metrics_grid} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentPulseChart
          data={stats?.sentiment_pulse}
          currentTimeSeconds={activeTimelineTime}
        />
        <EmotionRadarChart
          data={stats?.emotion_radar}
          currentTimeSeconds={activeTimelineTime}
          durationSeconds={timelineDuration}
        />
      </div>

      <EmotionalIntensityChart
        data={stats?.emotional_intensity_timeline}
        currentTimeSeconds={activeTimelineTime}
      />

      <EngagementTrendCurve
        data={stats?.engagement_trend_curve}
        currentTimeSeconds={activeTimelineTime}
      />
    </div>
  )
}
