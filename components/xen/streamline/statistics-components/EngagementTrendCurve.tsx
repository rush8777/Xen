import { CartesianGrid, Line, YAxis, XAxis, Area, ComposedChart, ReferenceLine } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { getNearestTimelineLabel, getVisibleTimelineData } from "./timeline-utils"

export interface EngagementTrendPoint {
  time: string
  engagement: number
  speech_energy: number
  pace: number
  key_moment_boost: number
}

const chartConfig = {
  engagement: { label: "Engagement", color: "hsl(262 80% 56%)" },
  speech_energy: { label: "Speech Energy", color: "hsl(187 85% 43%)" },
  pace_normalized: { label: "Pace (normalized)", color: "hsl(35 92% 53%)" },
  key_moment_boost: { label: "Key Moment Boost", color: "hsl(142 70% 40%)" },
}

const normalizePace = (pace: number) => {
  const min = 60
  const max = 220
  const clamped = Math.min(max, Math.max(min, Number.isFinite(pace) ? pace : min))
  return Math.round(((clamped - min) / (max - min)) * 100)
}

export default function EngagementTrendCurve({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
}: {
  data?: EngagementTrendPoint[]
  currentTimeSeconds?: number
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
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Engagement Trend Curve</h3>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Not enough timeline signal yet to map engagement progression.
          </p>
        </div>
        <p className="mt-6 text-xs text-zinc-400 dark:text-zinc-500">
          Once statistics are generated, this chart will combine speech energy, pace, and key moments over time.
        </p>
      </div>
    )
  }

  const normalizedData = (data || []).map((point) => ({
    ...point,
    pace_normalized: normalizePace(point.pace),
  }))
  const visibleData = getVisibleTimelineData(normalizedData, currentTimeSeconds)
  const activeLabel = getNearestTimelineLabel(normalizedData, currentTimeSeconds)

  return (
    <div
      className="p-6 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100
                 dark:border-zinc-800 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Engagement Trend Curve</h3>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          Unified engagement from speech energy, pace, and key moments
        </p>
      </div>

      <ChartContainer config={chartConfig} className="h-72 w-full">
        <ComposedChart data={visibleData}>
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-zinc-200 dark:stroke-zinc-800"
          />
          <XAxis dataKey="time" className="text-xs" />
          <YAxis domain={[0, 100]} className="text-xs" />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value, name, item) => {
                  if (name === "pace_normalized") {
                    return (
                      <span className="font-mono tabular-nums">
                        {item?.payload?.pace ?? 0} wpm
                      </span>
                    )
                  }
                  return <span className="font-mono tabular-nums">{Number(value).toLocaleString()}</span>
                }}
              />
            }
          />
          {activeLabel && (
            <ReferenceLine x={activeLabel} stroke="hsl(262 80% 56%)" strokeDasharray="4 4" />
          )}

          <Area
            type="monotone"
            dataKey="key_moment_boost"
            fill="var(--color-key_moment_boost)"
            stroke="var(--color-key_moment_boost)"
            fillOpacity={0.1}
            strokeOpacity={0.35}
            strokeWidth={1.5}
          />
          <Line
            type="monotone"
            dataKey="engagement"
            stroke="var(--color-engagement)"
            strokeWidth={2.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="speech_energy"
            stroke="var(--color-speech_energy)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="pace_normalized"
            stroke="var(--color-pace_normalized)"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
          />
        </ComposedChart>
      </ChartContainer>
    </div>
  )
}
