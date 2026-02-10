import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const emotionData = [
  { subject: "Hype", A: 92 },
  { subject: "Skepticism", A: 45 },
  { subject: "Humor", A: 78 },
  { subject: "Anger", A: 12 },
  { subject: "Curiosity", A: 88 },
  { subject: "Trust", A: 76 },
]

const emotionConfig = {
  A: { label: "Sentiment Level", color: "hsl(262 80% 50%)" },
}

export default function EmotionRadarChart() {
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
        <RadarChart data={emotionData}>
          <PolarGrid className="stroke-zinc-200 dark:stroke-zinc-800" />
          <PolarAngleAxis dataKey="subject" className="text-xs" />
          <PolarRadiusAxis angle={90} domain={[0, 100]} className="text-xs" />
          <Radar
            name="Sentiment"
            dataKey="A"
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


