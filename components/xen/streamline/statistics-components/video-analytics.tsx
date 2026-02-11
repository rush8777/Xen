"use client"

import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import EmotionalIntensityChart from "./emotional-anal"
import {
  AgeDistribution,
  GenderDistribution,
  TopLocations,
  AudienceInterests,
} from "./audience-demographics"
import VideoMetricsGrid from "./VideoMetricsGrid"
import SentimentPulseChart from "./SentimentPulseChart"
import EmotionRadarChart from "./EmotionRadarChart"
import TopComments from "./TopComments"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

type StatisticsStatus = "not_started" | "pending" | "completed" | "failed"

type ProjectStatisticsPayload = {
  version?: number
  video_metrics_grid?: any
  sentiment_pulse?: any
  emotion_radar?: any
  emotional_intensity_timeline?: any
  audience_demographics?: {
    age_distribution?: any
    gender_distribution?: any
    top_locations?: any
    audience_interests?: any
  }
  top_comments?: any
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

export default function VideoAnalytics() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get("projectId")

  const [status, setStatus] = useState<StatisticsStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)

  const [stats, setStats] = useState<ProjectStatisticsPayload | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)

  const [loading, setLoading] = useState(false)

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
  }, [projectId])

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
        <div className="text-white font-semibold mb-1">Statistics not generated yet</div>
        <div className="text-xs text-zinc-400">
          Generate statistics for this project, then return to this tab.
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

  return (
    <div className="space-y-6">
      <VideoMetricsGrid data={stats?.video_metrics_grid} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentPulseChart data={stats?.sentiment_pulse} />
        <EmotionRadarChart data={stats?.emotion_radar} />
      </div>

      <EmotionalIntensityChart data={stats?.emotional_intensity_timeline} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgeDistribution data={stats?.audience_demographics?.age_distribution} />
        <GenderDistribution data={stats?.audience_demographics?.gender_distribution} />
        <TopLocations data={stats?.audience_demographics?.top_locations} />
        <AudienceInterests data={stats?.audience_demographics?.audience_interests} />
      </div>

      <TopComments comments={stats?.top_comments} />
    </div>
  )
}

