import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

export interface EmotionRadarPoint {
  subject: string
  value: number
}

const emotionConfig = {
  value: { label: "Sentiment Level", color: "hsl(262 80% 50%)" },
}

export default function EmotionRadarChart({ data }: { data?: EmotionRadarPoint[] }) {
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
        <RadarChart data={data}>
          <PolarGrid className="stroke-zinc-200 dark:stroke-zinc-800" />
          <PolarAngleAxis dataKey="subject" className="text-xs" />
          <PolarRadiusAxis angle={90} domain={[0, 100]} className="text-xs" />
          <Radar
            name="Sentiment"
            dataKey="value"
            stroke="var(--color-A)"
            fill="var(--color-A)"
            fillOpacity={0.6}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
        </RadarChart>
      </ChartContainer>
    </div>
  )
}


