import { cn } from "@/lib/utils"
import { TrendingUp, AlertCircle, MessageCircle, HelpCircle } from "lucide-react"

export default function VideoMetricsGrid() {
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
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">82%</h3>
          </div>
          <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
            <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
        <p className="text-xs text-emerald-600 dark:text-emerald-400">+5% vs last video</p>
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
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">450</h3>
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
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">3</h3>
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
            <h3 className="text-2xl font-semibold text-zinc-900 dark:text-white">12%</h3>
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


