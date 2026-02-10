import { cn } from "@/lib/utils"
import { TrendingUp, AlertCircle, MessageCircle, HelpCircle } from "lucide-react"

export interface VideoMetricsGridData {
  net_sentiment_score: number
  net_sentiment_delta_vs_last: number
  engagement_velocity_comments_per_hour: number
  toxicity_alert_bots_detected: number
  question_density_percent: number
}

function formatDelta(delta: number) {
  const sign = delta > 0 ? "+" : ""
  return `${sign}${delta}%`
}

export default function VideoMetricsGrid({ data }: { data?: VideoMetricsGridData }) {
  const fallback: VideoMetricsGridData = {
    net_sentiment_score: 0,
    net_sentiment_delta_vs_last: 0,
    engagement_velocity_comments_per_hour: 0,
    toxicity_alert_bots_detected: 0,
    question_density_percent: 0,
  }

  const safeData = data ?? fallback

  const delta = Number.isFinite(safeData.net_sentiment_delta_vs_last)
    ? safeData.net_sentiment_delta_vs_last
    : 0
  const deltaIsPositive = delta >= 0
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Net Sentiment Score */}
      <div
        className={cn(
          "p-4 rounded-lg",
          "bg-white dark:bg-zinc-900/70",
          "border border-zinc-100 dark:border-zinc-800",
          "shadow-sm backdrop-blur-xl",
        )}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Net Sentiment Score</p>
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              {Math.round(safeData.net_sentiment_score)}%
            </h3>
          </div>
          <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
            <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
        <p
          className={cn(
            "text-xs",
            deltaIsPositive
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-red-600 dark:text-red-400",
          )}
        >
          {formatDelta(delta)} vs last video
        </p>
      </div>

      {/* Engagement Velocity */}
      <div
        className={cn(
          "p-4 rounded-lg",
          "bg-white dark:bg-zinc-900/70",
          "border border-zinc-100 dark:border-zinc-800",
          "shadow-sm backdrop-blur-xl",
        )}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Engagement Velocity</p>
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              {Math.round(safeData.engagement_velocity_comments_per_hour)}
            </h3>
          </div>
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <MessageCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">comments/hr</p>
      </div>

      {/* Toxicity Alert */}
      <div
        className={cn(
          "p-4 rounded-lg",
          "bg-white dark:bg-zinc-900/70",
          "border border-zinc-100 dark:border-zinc-800",
          "shadow-sm backdrop-blur-xl",
        )}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Toxicity Alert</p>
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              {Math.round(safeData.toxicity_alert_bots_detected)}
            </h3>
          </div>
          <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
          </div>
        </div>
        <p className="text-xs text-red-600 dark:text-red-400">Bots Detected</p>
      </div>

      {/* Question Density */}
      <div
        className={cn(
          "p-4 rounded-lg",
          "bg-white dark:bg-zinc-900/70",
          "border border-zinc-100 dark:border-zinc-800",
          "shadow-sm backdrop-blur-xl",
        )}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Question Density</p>
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              {Math.round(safeData.question_density_percent)}%
            </h3>
          </div>
          <div className="p-2 rounded-lg bg-yellow-100 dark:bg-yellow-900/30">
            <HelpCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">of comments</p>
      </div>
    </div>
  )
}


