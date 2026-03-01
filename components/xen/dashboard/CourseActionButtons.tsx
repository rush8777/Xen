"use client"

import { Sparkles, Zap, Upload, ChevronDown } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import CreateProjectModal from "@/components/xen/create-project"
import { cn } from "@/lib/utils"

// Drop-in replacement for the course cards grid section in CoursePage
// Place this where the courses.map(...) grid used to be

interface CourseActionButtonsProps {
  onInitializingChange: (loading: boolean) => void
  onProgressChange: (step: number) => void
  onImportPreviewChange?: (preview: UrlImportPreview | null) => void
}

export interface UrlImportPreview {
  url: string
  heading: string
  thumbnailUrl?: string
  platform?: string
}

export default function CourseActionButtons({
  onInitializingChange,
  onProgressChange,
  onImportPreviewChange,
}: CourseActionButtonsProps) {
  const router = useRouter()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [showUrlInput, setShowUrlInput] = useState(false)
  const [customUrl, setCustomUrl] = useState("")
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isSubmittingUrl, setIsSubmittingUrl] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

  const closeImportMenu = (clearPreview = true) => {
    setImportOpen(false)
    setShowUrlInput(false)
    setUrlError(null)
    if (clearPreview) {
      onImportPreviewChange?.(null)
    }
  }

  const getClientThumbnailFromUrl = useCallback((rawUrl: string) => {
    try {
      const u = new URL(rawUrl)
      const host = u.hostname.toLowerCase()
      if (host === "youtu.be") {
        const id = u.pathname.replace("/", "").trim()
        return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : undefined
      }
      if (host.endsWith("youtube.com")) {
        const id = u.searchParams.get("v")
        return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : undefined
      }
    } catch {
      return undefined
    }
    return undefined
  }, [])

  const fetchPreviewFromUrl = useCallback(async (rawUrl: string) => {
    const trimmed = rawUrl.trim()
    if (!trimmed) {
      onImportPreviewChange?.(null)
      return
    }

    try {
      new URL(trimmed)
    } catch {
      onImportPreviewChange?.(null)
      return
    }
    const clientThumbnailUrl = getClientThumbnailFromUrl(trimmed)

    try {
      const res = await fetch(
        `${API_BASE_URL}/api/video/preview?url=${encodeURIComponent(trimmed)}`
      )
      if (!res.ok) {
        onImportPreviewChange?.({
          url: trimmed,
          heading: "Video preview",
          thumbnailUrl: clientThumbnailUrl,
        })
        return
      }

      const data = await res.json()
      const heading = typeof data?.heading === "string" && data.heading.trim()
        ? data.heading.trim()
        : "Video preview"
      const thumbnailUrl =
        typeof data?.thumbnail_url === "string" && data.thumbnail_url.trim()
          ? data.thumbnail_url
          : undefined

      onImportPreviewChange?.({
        url: trimmed,
        heading,
        thumbnailUrl: thumbnailUrl || clientThumbnailUrl,
        platform: typeof data?.platform === "string" ? data.platform : undefined,
      })
    } catch {
      onImportPreviewChange?.({
        url: trimmed,
        heading: "Video preview",
        thumbnailUrl: clientThumbnailUrl,
      })
    }
  }, [API_BASE_URL, getClientThumbnailFromUrl, onImportPreviewChange])

  useEffect(() => {
    if (!importOpen || !showUrlInput) return
    const timer = setTimeout(() => {
      fetchPreviewFromUrl(customUrl)
    }, 450)
    return () => clearTimeout(timer)
  }, [customUrl, fetchPreviewFromUrl, importOpen, showUrlInput])

  useEffect(() => {
    return () => onImportPreviewChange?.(null)
  }, [onImportPreviewChange])

  useEffect(() => {
    if (!jobId) return

    let stopped = false
    const interval = setInterval(async () => {
      if (stopped) return
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/analysis/progress/${encodeURIComponent(jobId)}`,
          { cache: "no-store" }
        )
        if (!res.ok) return

        const data = await res.json()
        const step = typeof data?.step === "number" ? data.step : 0
        onProgressChange(step)

        if (data?.status === "failed") {
          setUrlError(data?.error || "Initialization failed")
          onInitializingChange(false)
          setJobId(null)
          clearInterval(interval)
          return
        }

        if (data?.status === "completed") {
          onInitializingChange(false)
          setJobId(null)
          clearInterval(interval)
          if (data?.project_id) {
            router.push(`/streamline?projectId=${encodeURIComponent(String(data.project_id))}`)
          }
          return
        }

      } catch {
        // Ignore transient polling errors
      }
    }, 1000)

    return () => {
      stopped = true
      clearInterval(interval)
    }
  }, [API_BASE_URL, jobId, onInitializingChange, onProgressChange, router])

  const handleAnalyzeFromUrl = async () => {
    const trimmed = customUrl.trim()
    if (!trimmed) {
      setUrlError("Please enter a video URL.")
      return
    }

    try {
      new URL(trimmed)
    } catch {
      setUrlError("Please enter a valid URL.")
      return
    }

    setUrlError(null)
    setIsSubmittingUrl(true)
    onImportPreviewChange?.({
      url: trimmed,
      heading: "Importing video...",
    })
    void fetchPreviewFromUrl(trimmed)
    onInitializingChange(true)
    onProgressChange(0)

    try {
      const duplicateCheckResponse = await fetch(
        `${API_BASE_URL}/api/video/check-duplicate?url=${encodeURIComponent(trimmed)}`
      )
      const duplicateData = await duplicateCheckResponse.json()

      if (duplicateData.exists) {
        onInitializingChange(false)
        onImportPreviewChange?.(null)
        router.push(`/streamline?projectId=${duplicateData.project_id}`)
        closeImportMenu(false)
        return
      }
    } catch {
      // proceed with analyze request if duplicate check fails
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze-from-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: trimmed,
          project_name: "Streamline Project",
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to initialize video analysis")
      }

      const data = await response.json()
      setJobId(data.job_id)
      closeImportMenu(false)
      setCustomUrl("")
    } catch (err: any) {
      setUrlError(err?.message || "Failed to initialize video analysis")
      onInitializingChange(false)
    } finally {
      setIsSubmittingUrl(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2.5">

        {/* Button 1: Create new (primary) */}
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className={cn(
            "group relative flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200",
            "bg-gradient-to-br from-zinc-700 via-zinc-800 to-zinc-900",
            "border border-zinc-600/60 hover:border-zinc-500/80",
            "text-white shadow-lg shadow-black/40",
            "hover:shadow-zinc-700/30 hover:scale-[1.02] active:scale-[0.98]"
          )}
        >
          {/* inner glow on hover */}
          <span className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />

          {/* AI spark icon */}
          <span className="flex items-center justify-center w-4 h-4 rounded-full bg-gradient-to-br from-blue-400 to-violet-500 shadow-sm shadow-violet-500/50">
            <Sparkles className="h-2.5 w-2.5 text-white" />
          </span>

          <span className="relative">+ Create new</span>

          {/* AI badge */}
          <span className="px-1.5 py-0.5 text-[9px] font-bold rounded uppercase tracking-wider bg-gradient-to-r from-blue-500/30 to-violet-500/30 border border-blue-500/40 text-blue-300">
            AI
          </span>
        </button>

        {/* Button 2: New gamma (ghost) */}
        <button
          type="button"
          className={cn(
            "flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200",
            "border border-zinc-700 text-zinc-300",
            "hover:border-zinc-500 hover:text-white hover:bg-zinc-800/60",
            "active:scale-[0.98]"
          )}
        >
          <Zap className="h-3.5 w-3.5" />
          + New gamma
        </button>

        {/* Button 3: Import (ghost + dropdown) */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              if (importOpen) {
                closeImportMenu()
              } else {
                setImportOpen(true)
              }
            }}
            className={cn(
              "relative z-10 flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 import-special",
              "border border-cyan-500/60 text-cyan-100 bg-cyan-500/10",
              "hover:border-zinc-500 hover:text-white hover:bg-zinc-800/60",
              "active:scale-[0.98]"
            )}
          >
            <Upload className="h-3.5 w-3.5" />
            Import
            <ChevronDown className={cn("h-3 w-3 transition-transform duration-200", importOpen && "rotate-180")} />
          </button>

          {importOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => closeImportMenu()} />
              <div className="absolute left-0 mt-2 w-64 z-20 rounded-xl border border-zinc-700/80 bg-zinc-900 p-1 shadow-2xl shadow-black/60">
                {!showUrlInput ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setShowUrlInput(true)}
                      className="w-full text-left px-3 py-2 text-xs rounded-lg text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
                    >
                      From URL
                    </button>
                    {["From file", "From Google Drive"].map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => closeImportMenu()}
                        className="w-full text-left px-3 py-2 text-xs rounded-lg text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
                      >
                        {item}
                      </button>
                    ))}
                  </>
                ) : (
                  <div className="p-2 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-medium text-zinc-300">Import from URL</span>
                      <button
                        type="button"
                        onClick={() => {
                          setShowUrlInput(false)
                          setUrlError(null)
                          onImportPreviewChange?.(null)
                        }}
                        className="text-[10px] text-zinc-400 hover:text-zinc-200"
                      >
                        Back
                      </button>
                    </div>
                    <input
                      type="url"
                      value={customUrl}
                      onChange={(e) => {
                        setCustomUrl(e.target.value)
                        if (urlError) setUrlError(null)
                      }}
                      placeholder="https://..."
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                    />
                    {urlError && <p className="text-[10px] text-red-400">{urlError}</p>}
                    <button
                      type="button"
                      onClick={handleAnalyzeFromUrl}
                      disabled={isSubmittingUrl}
                      className="w-full rounded-lg bg-zinc-100 px-2 py-1.5 text-xs font-medium text-zinc-900 hover:bg-white disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {isSubmittingUrl ? "Initializing..." : "Analyze"}
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Modal wired to your existing CreateProjectModal */}
      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        course={null}
        onInitializingChange={onInitializingChange}
        useGlobalLoader={true}
        onProgressChange={onProgressChange}
      />
      <style jsx>{`
        .import-special {
          animation: import-special-pulse 3s ease-in-out infinite;
          box-shadow:
            0 0 0 0 rgba(34, 211, 238, 0.2),
            0 0 12px rgba(34, 211, 238, 0.1);
        }

        .import-special:hover {
          animation-play-state: paused;
          transform: scale(1.02);
        }

        @keyframes import-special-pulse {
          0%,
          100% {
            transform: scale(1);
            box-shadow:
              0 0 0 0 rgba(34, 211, 238, 0.15),
              0 0 8px rgba(34, 211, 238, 0.08);
          }
          50% {
            transform: scale(1.02);
            box-shadow:
              0 0 0 4px rgba(34, 211, 238, 0),
              0 0 16px rgba(34, 211, 238, 0.2);
          }
        }
      `}</style>
    </>
  )
}

