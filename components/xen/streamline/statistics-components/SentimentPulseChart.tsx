import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const sentimentData = [
  { time: "0:00", positive: 85, negative: 15 },
  { time: "1:00", positive: 78, negative: 22 },
  { time: "2:00", positive: 82, negative: 18 },
  { time: "3:00", positive: 88, negative: 12 },
  { time: "4:00", positive: 91, negative: 9 },
  { time: "5:00", positive: 89, negative: 11 },
  { time: "6:00", positive: 84, negative: 16 },
  { time: "7:00", positive: 87, negative: 13 },
  { time: "8:00", positive: 86, negative: 14 },
  { time: "9:00", positive: 90, negative: 10 },
  { time: "10:00", positive: 92, negative: 8 },
]

const sentimentConfig = {
  positive: { label: "Positive", color: "hsl(142 72% 29%)" },
  negative: { label: "Negative", color: "hsl(0 84% 60%)" },
}

export default function SentimentPulseChart() {
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
        <LineChart data={sentimentData}>
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-zinc-200 dark:stroke-zinc-800"
          />
          <XAxis dataKey="time" className="text-xs" />
          <YAxis className="text-xs" />
          <ChartTooltip content={<ChartTooltipContent />} />
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


