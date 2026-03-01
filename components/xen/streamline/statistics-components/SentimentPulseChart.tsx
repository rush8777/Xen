import { LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { getNearestTimelineLabel, getVisibleTimelineData } from "./timeline-utils"

export interface SentimentPoint {
  time: string
  positive: number
  negative: number
}

const sentimentConfig = {
  positive: { label: "Positive", color: "hsl(142 72% 29%)" },
  negative: { label: "Negative", color: "hsl(0 84% 60%)" },
}

export default function SentimentPulseChart({
  data,
  currentTimeSeconds = Number.POSITIVE_INFINITY,
}: {
  data?: SentimentPoint[]
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
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Sentiment Pulse</h3>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Not enough comment data yet to calculate sentiment over time.
          </p>
        </div>
        <p className="mt-6 text-xs text-zinc-400 dark:text-zinc-500">
          Once statistics are generated for this project, you&apos;ll see how positive vs. negative sentiment
          evolves across the video.
        </p>
      </div>
    )
  }

  const visibleData = getVisibleTimelineData(data || [], currentTimeSeconds)
  const activeLabel = getNearestTimelineLabel(data || [], currentTimeSeconds)

  return (
    <div
      className="p-6 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100 
                 dark:border-zinc-800 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Sentiment Pulse</h3>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          Positive vs. Negative sentiment over video duration
        </p>
      </div>
      <ChartContainer config={sentimentConfig} className="h-72 w-full">
        <LineChart data={visibleData}>
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-zinc-200 dark:stroke-zinc-800"
          />
          <XAxis dataKey="time" className="text-xs" />
          <YAxis className="text-xs" />
          <ChartTooltip content={<ChartTooltipContent />} />
          {activeLabel && (
            <ReferenceLine x={activeLabel} stroke="hsl(262 80% 56%)" strokeDasharray="4 4" />
          )}
          <Line
            type="monotone"
            dataKey="positive"
            stroke="var(--color-positive)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="negative"
            stroke="var(--color-negative)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ChartContainer>
    </div>
  )
}

