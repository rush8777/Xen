import { ThumbsUp } from "lucide-react"
import { cn } from "@/lib/utils"

export type TopCommentIntent = "positive" | "criticism" | "question"

export interface TopComment {
  id: string
  author: string
  avatar: string
  content: string
  likes: number
  intent: TopCommentIntent
}

export default function TopComments({ comments = [] }: { comments?: TopComment[] }) {
  return (
    <div
      className={cn(
        "p-6 rounded-lg",
        "bg-white dark:bg-zinc-900/70",
        "border border-zinc-100 dark:border-zinc-800",
        "shadow-sm backdrop-blur-xl",
      )}
    >
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">Top Comments</h3>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          Most impactful comments from your audience
        </p>
      </div>
      <div className="space-y-3">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className={cn(
              "p-4 rounded-lg",
              "bg-zinc-50 dark:bg-zinc-800/50",
              "border border-zinc-100 dark:border-zinc-700",
              "hover:bg-zinc-100 dark:hover:bg-zinc-800",
              "transition-colors duration-200",
            )}
          >
            <div className="flex gap-3">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0",
                  "bg-zinc-200 dark:bg-zinc-700 text-sm font-medium",
                  "text-zinc-900 dark:text-white",
                )}
              >
                {comment.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium text-zinc-900 dark:text-white">
                    {comment.author}
                  </h4>
                  <div
                    className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-medium",
                      comment.intent === "positive" &&
                        "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
                      comment.intent === "criticism" &&
                        "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300",
                      comment.intent === "question" &&
                        "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
                    )}
                  >
                    {comment.intent === "positive" && "Positive"}
                    {comment.intent === "criticism" && "Criticism"}
                    {comment.intent === "question" && "Question"}
                  </div>
                </div>
                <p className="text-sm text-zinc-700 dark:text-zinc-300 mb-2 line-clamp-2">
                  {comment.content}
                </p>
                <div className="flex items-center gap-4 text-xs text-zinc-600 dark:text-zinc-400">
                  <button className="flex items-center gap-1 hover:text-zinc-900 dark:hover:text-white transition-colors">
                    <ThumbsUp className="w-3.5 h-3.5" />
                    {comment.likes.toLocaleString()}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


