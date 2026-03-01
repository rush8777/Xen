import { useMemo } from "react"
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { parseTimeLabelToSeconds } from "./timeline-utils"

export interface EmotionRadarPoint {
  subject: string
  value: number
  time?: string
}

const emotionConfig = {
  value: { label: "Sentiment Level", color: "hsl(262 80% 50%)" },
}

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

type NormalizedRadarPoint = {
  subject: string
  value: number
  visible: number
}

export default function EmotionRadarChart({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
  durationSeconds = 0,
}: {
  data?: EmotionRadarPoint[]
  currentTimeSeconds?: number
  durationSeconds?: number
}) {
  const hasData = Array.isArray(data) && data.length > 0

  if (!hasData) {
    return (
      <div
        className="p-6 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100 
                   dark:border-zinc-800 shadow-sm backdrop-blur-xl flex flex-col justify-between"
      >
        <div>
          <div className="mb-2">
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Emotion Radar</h3>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Not enough audience signal yet to derive reliable emotional attributes from comments.
          </p>
        </div>
        <p className="mt-6 text-xs text-zinc-400 dark:text-zinc-500">
          When more comments are available, this radar will highlight patterns like hype, skepticism, curiosity,
          and support around your video.
        </p>
      </div>
    )
  }

  const normalizedData = useMemo<NormalizedRadarPoint[]>(() => {
    if (!Array.isArray(data) || data.length === 0) return []

    const safeTime = Number.isFinite(currentTimeSeconds) ? Math.max(0, currentTimeSeconds) : Number.POSITIVE_INFINITY
    const hasTimeline = data.some((item) => typeof item?.time === "string" && parseTimeLabelToSeconds(item.time) >= 0)

    if (!hasTimeline) {
      const grouped = new Map<string, number>()
      for (const point of data) {
        const subject = String(point?.subject || "").trim()
        if (!subject) continue
        const value = clamp(Number(point?.value || 0), 0, 100)
        const prev = grouped.get(subject) ?? value
        grouped.set(subject, Math.max(prev, value))
      }

      const groupedEntries = Array.from(grouped.entries())
      if (groupedEntries.length === 0) return []

      const hasClock = Number.isFinite(safeTime) && durationSeconds > 0
      const progress = hasClock ? clamp(safeTime / durationSeconds, 0, 1) : 1
      const revealEdge = progress * groupedEntries.length

      return groupedEntries.map(([subject, value], index) => {
        const distanceFromEdge = revealEdge - index
        const visible = clamp(distanceFromEdge, 0.2, 1)
        return {
          subject,
          // Grow the radar area as the timeline advances.
          value: Math.round(value * visible),
          visible,
        }
      })
    }

    const pointsWithTime = data
      .map((point) => ({
        subject: String(point?.subject || "").trim(),
        value: clamp(Number(point?.value || 0), 0, 100),
        second: parseTimeLabelToSeconds(String(point?.time || "")),
      }))
      .filter((point) => point.subject && point.second >= 0)
      .sort((a, b) => a.second - b.second)

    const latestBySubject = new Map<string, { value: number; second: number }>()
    for (const point of pointsWithTime) {
      if (point.second <= safeTime) latestBySubject.set(point.subject, { value: point.value, second: point.second })
    }

    const visibilityWindowSeconds = 12
    const allSubjects = Array.from(new Set(pointsWithTime.map((p) => p.subject)))
    return allSubjects
      .map((subject) => {
        const current = latestBySubject.get(subject)
        if (!current) return null
        const distance = safeTime - current.second
        const visible = clamp(1 - distance / visibilityWindowSeconds, 0.18, 1)
        return {
          subject,
          value: current.value,
          visible,
        }
      })
      .filter((point): point is NormalizedRadarPoint => Boolean(point))
  }, [data, currentTimeSeconds, durationSeconds])

  const axisOpacityBySubject = useMemo(() => {
    const map = new Map<string, number>()
    for (const point of normalizedData) map.set(point.subject, point.visible)
    return map
  }, [normalizedData])

  return (
    <div
      className="p-6 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100 
                 dark:border-zinc-800 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Emotion Radar</h3>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          Emotional attributes detected in comments
        </p>
      </div>
      <ChartContainer config={emotionConfig} className="h-72 w-full">
        <RadarChart data={normalizedData}>
          <PolarGrid className="stroke-zinc-200 dark:stroke-zinc-800" />
          <PolarAngleAxis
            dataKey="subject"
            className="text-xs"
            tick={(props: any) => {
              const { x, y, payload } = props
              const subject = String(payload?.value || "")
              const opacity = axisOpacityBySubject.get(subject) ?? 1
              return (
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill="currentColor"
                  style={{
                    opacity,
                    transition: "opacity 260ms ease, transform 260ms ease",
                    transform: opacity > 0.7 ? "scale(1)" : "scale(0.96)",
                    transformOrigin: `${x}px ${y}px`,
                  }}
                  className="fill-zinc-500 dark:fill-zinc-300"
                >
                  {subject}
                </text>
              )
            }}
          />
          <PolarRadiusAxis angle={90} domain={[0, 100]} className="text-xs" />
          <Radar
            name="Sentiment"
            dataKey="value"
            stroke="var(--color-value)"
            fill="var(--color-value)"
            fillOpacity={0.42}
            animationDuration={260}
            animationEasing="ease-out"
          />
          <ChartTooltip content={<ChartTooltipContent />} />
        </RadarChart>
      </ChartContainer>
    </div>
  )
}
