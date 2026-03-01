"use client"

import React, { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { useGlobalLoader } from "@/components/xen/main/layout"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  MessageCircle,
  FileText,
  Search,
  Brain,
  Play,
  Volume2,
  Clock,
  Star,
  Users,
  Settings2,
  Calendar,
  Sun,
  Moon,
  ChevronDown,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import VideoAnalytics from "@/components/xen/streamline/statistics-components/video-analytics"
import FloatingVideoChat from "@/components/xen/floating-chat-bar"
import PsychologicalPersuasionAnalytics from "@/components/xen/streamline/psychology-components/psychological-persuasion-analytics"

import VideoPlayerModal from "@/components/xen/streamline/video-player-modal"
import KeyMomentsTimeline, { type KeyMoment } from "@/components/xen/streamline/statistics-components/KeyMomentsTimeline"

type ProjectOverview = {
  project_id: number
  blog_markdown: string
  summary: string
  insights: {
    situation?: string
    pain?: string[]
    impact?: string[]
    critical_event?: string
    decision?: string
    [key: string]: any
  }
  generated_at: string | null
  version: number
  status: "not_started" | "pending" | "completed" | "failed" | string
}

type VectorStatus = {
  project_id: number
  status: "not_started" | "pending" | "completed" | "failed" | string
  started_at: string | null
  completed_at: string | null
  error: string | null
}

type FeatureId = "clips" | "subtitles" | "chapters" | "moments"
type FeatureStatus = "not_started" | "loading" | "processing" | "completed" | "error"
type FeatureState = {
  status: FeatureStatus
  progress: number
  error: string | null
  updated_at: string | null
}

type ContentFeatureStatusResponse = {
  project_id: number
  features: Record<FeatureId, FeatureState>
  started_at: string | null
  completed_at: string | null
}

type TranscriptPassageResponse = {
  project_id: number
  source: "premium_transcript_table" | "content_feature_subtitles" | "none" | string
  passage: string
  segments: Array<{
    start_time_seconds: number
    end_time_seconds: number
    text: string
  }>
}

type ChapterSubchapter = {
  id: string
  title: string
  start_time_seconds: number
  end_time_seconds: number
  duration_seconds: number
  summary: string
}

type StructuralChapter = {
  id: string
  title: string
  start_time_seconds: number
  end_time_seconds: number
  duration_seconds: number
  summary: string
  psychological_intent?: string
  chapter_type?: string
  subchapters?: ChapterSubchapter[]
}

const Skeleton = ({ className }: { className?: string }) => {
  return <div className={cn("animate-pulse rounded-md", className)} />
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

const getThumbnailUrl = (videoUrl?: string | null) => {
  if (!videoUrl) return undefined
  try {
    const u = new URL(videoUrl)
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
}

type TopTab = {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

const toptabs: TopTab[] = [
  { id: "overview", label: "Video Overview", icon: MessageCircle },
  { id: "statistics", label: "Statistics", icon: Search },
  { id: "transcription", label: "Video Transcription", icon: FileText },
  { id: "psychology", label: "Psychological & Persuasion", icon: Brain },
  { id: "subtitles", label: "Subtitles", icon: Volume2 },
  { id: "chapters", label: "Chapters", icon: Clock },
  { id: "moments", label: "Key Moments", icon: Star },
]

const tabs = [
  { id: "transcript", label: "Transcript" },
  { id: "speakers", label: "Speakers" },
  { id: "meeting", label: "Meeting" },
]

const chatMessages = [
  {
    id: 1,
    author: "Ashley Lawson",
    avatar: "AL",
    time: "0:18",
    message: "Hey Dylan, great to meet you!",
  },
  {
    id: 2,
    author: "Dylan Parker",
    avatar: "DP",
    time: "0:25",
    message:
      "Hey Ashley, thanks for reaching out to us at Basepoint! Can you tell me a bit more about GreenLeaf and what you're hoping to get out of our platform?",
  },
  {
    id: 3,
    author: "Ashley Lawson",
    avatar: "AL",
    time: "0:37",
    message:
      "Of course! So I'm Ashley, I lead GTM at GreenLeaf. We're building an AI-powered climate tech platform and just raised a Series A last month. We're looking for a CRM with integration and automation capabilities to accelerate our growth. I'll let Simon describe our use case in a little more depth.",
  },
  {
    id: 4,
    author: "Simon Mitchell",
    avatar: "SM",
    time: "1:04",
    message:
      "Yes, so at the moment we're largely relying on spreadsheets to track our prospect and customer information. It's a lot of manual data entry, and everyone has their own system for working with the data. It's resulting in a lot of inconsistencies with prospect follow-ups, meaning we're missing some really good opportunities.",
  },
]

const insights = {
  summary:
    "Ashley Lawson met with Dylan Parker to learn more about Basepoint. The GreenLeaf team is facing a number of inefficiencies due to their reliance on manual data entry and tools. They're looking for a scalable CRM with automation and integration functionality to accelerate their growth.",
  situation:
    "Ashley Lawson is the GTM Manager at GreenLeaf, a rapidly scaling tech startup that raised a Series A. The team currently uses spreadsheets to track prospect and customer information, which are poorly integrated with their other tools. They rely on manual processes for data management and follow-ups, which are creating bottlenecks.",
  pain: [
    "Disconnected tools are leading to data silos and loss of key information.",
    "Manual processes are resulting in inconsistent follow-ups and lost deals, while reducing time available for strategic growth initiatives.",
  ],
  impact: [
    "Urgent need for repeatable, optimized workflows to support rapid growth.",
    "Establishing a single source of truth their customer and product data is crucial for alignment between teams.",
    "Building out a comprehensive GTM motion is important to help the team scale.",
  ],
  criticalEvent:
    "GreenLeaf's next board meeting is in early June, and they're aiming to present a comprehensive summary of improvements to their GTM strategy by then. The team needs to have a new system fully implemented by the end of April.",
  decision:
    "Annual budget is approximately $10,000. Must-have features include strong integrations, automation capabilities, and Ashley appears to be the lead on this initiative and is overseeing a range of stakeholders.",
}

const currentProject = {
  name: "GreenLeaf Project",
  lastModified: "2023-10-01",
  duration: "28:14",
  videoLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  platform: "YouTube",
  thumbnail: getThumbnailUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ") || "/images/design-mode/Screenshot%202025-05-08%20133020(1).png"
}
const DEFAULT_VIDEO_TITLE = "GreenLeaf // Basepoint"

const featureLoadingSteps: Record<FeatureId, string[]> = {
  clips: [
    "Analyzing full video structure for key moments...",
    "Detecting insights, decisions, and emotional peaks",
    "Generating contextual justifications for each moment",
    "Validating timestamps and impact levels",
  ],
  subtitles: [
    "Using existing transcript from chat analysis",
    "Optimizing text for subtitle formatting",
    "Generating translations (if requested)",
    "Creating export formats (SRT, VTT)",
    "Applying style customizations",
  ],
  chapters: [
    "Analyzing content flow and topics",
    "Identifying natural break points",
    "Creating meaningful chapter titles",
    "Selecting representative thumbnails",
  ],
  moments: [
    "Detecting emotional highlights",
    "Finding critical insights and information",
    "Scoring moments by importance",
    "Organizing highlights by category",
  ],
}

const defaultFeatureState: FeatureState = {
  status: "not_started",
  progress: 0,
  error: null,
  updated_at: null,
}

const defaultFeatureMap: Record<FeatureId, FeatureState> = {
  clips: { ...defaultFeatureState },
  subtitles: { ...defaultFeatureState },
  chapters: { ...defaultFeatureState },
  moments: { ...defaultFeatureState },
}

const formatSeconds = (seconds: number) => {
  const s = Math.max(0, Math.floor(seconds || 0))
  const hh = Math.floor(s / 3600)
  const mm = Math.floor((s % 3600) / 60)
  const ss = s % 60
  if (hh > 0) return `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
}
const normalizeKeyMoment = (item: any, index: number): KeyMoment => {
  const title = String(item?.title || item?.label || `Moment ${index + 1}`).trim()
  const category = String(item?.category || item?.moment_type || "critical_insight")
  const impact = String(item?.impact_level || "").toLowerCase()
  const start = Math.max(0, Number(item?.start_time_seconds || 0))
  const end = Math.max(start + 1, Number(item?.end_time_seconds || start + 1))
  return {
    id: String(item?.id || item?.clip_id || `moment_${index + 1}`),
    title,
    category,
    impact_level: impact || undefined,
    start_time_seconds: start,
    end_time_seconds: end,
    duration_seconds: Number(item?.duration_seconds || end - start),
    justification: String(item?.justification || item?.rationale || item?.why_this_is_strong || "").trim(),
    context: String(item?.context || "").trim(),
    key_quote: String(item?.key_quote || "").trim(),
  }
}

const normalizeSubchapter = (item: any, chapterIndex: number, subIndex: number, chapterStart: number, chapterEnd: number): ChapterSubchapter => {
  const toSafeInt = (value: any, fallback: number) => {
    const numeric = Number(value)
    return Number.isFinite(numeric) ? Math.floor(numeric) : fallback
  }
  const fallbackStart = chapterStart
  const fallbackEnd = Math.max(chapterStart + 1, chapterEnd)
  const start = Math.max(chapterStart, toSafeInt(item?.start_time_seconds, fallbackStart))
  const end = Math.min(chapterEnd, Math.max(start + 1, toSafeInt(item?.end_time_seconds, fallbackEnd)))
  return {
    id: String(item?.id || `chapter_${chapterIndex + 1}_sub_${subIndex + 1}`),
    title: String(item?.title || `Subchapter ${subIndex + 1}`).trim(),
    start_time_seconds: start,
    end_time_seconds: end,
    duration_seconds: Math.max(1, Number(item?.duration_seconds || end - start)),
    summary: String(item?.summary || "Subchapter details are not available yet.").trim(),
  }
}

const normalizeStructuralChapter = (item: any, index: number): StructuralChapter => {
  const toSafeInt = (value: any, fallback: number) => {
    const numeric = Number(value)
    return Number.isFinite(numeric) ? Math.floor(numeric) : fallback
  }
  const title = String(item?.title || `Chapter ${index + 1}`).trim()
  const start = Math.max(0, toSafeInt(item?.start_time_seconds, 0))
  const end = Math.max(start + 1, toSafeInt(item?.end_time_seconds, start + 1))
  const subchapters = Array.isArray(item?.subchapters)
    ? item.subchapters.map((sub: any, subIndex: number) => normalizeSubchapter(sub, index, subIndex, start, end))
    : []

  return {
    id: String(item?.id || `chapter_${index + 1}`),
    title,
    start_time_seconds: start,
    end_time_seconds: end,
    duration_seconds: Math.max(1, toSafeInt(item?.duration_seconds, end - start)),
    summary: String(item?.summary || "Core section with key ideas and takeaways.").trim(),
    psychological_intent: String(item?.psychological_intent || "other").trim(),
    chapter_type: String(item?.chapter_type || "Education").trim(),
    subchapters,
  }
}

function StreamlineSkeleton({ isDark }: { isDark: boolean }) {
  const base = isDark ? "bg-zinc-800/60" : "bg-gray-200"
  const card = isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white"

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className={cn("h-7 w-56", base)} />
          <div className="flex items-center gap-2">
            <Skeleton className={cn("h-8 w-10 rounded", base)} />
            <Skeleton className={cn("h-8 w-10 rounded-lg", base)} />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Skeleton className={cn("h-4 w-28", base)} />
          <Skeleton className={cn("h-4 w-24", base)} />
        </div>
      </div>

      <div className="flex justify-center">
        <div className={cn("inline-flex items-center gap-1.5 p-1 rounded-lg", isDark ? "bg-transparent" : "bg-gray-100")}>
          <Skeleton className={cn("h-9 w-32 rounded-md", base)} />
          <Skeleton className={cn("h-9 w-28 rounded-md", base)} />
          <Skeleton className={cn("h-9 w-40 rounded-md", base)} />
          <Skeleton className={cn("h-9 w-32 rounded-md", base)} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <Card className={cn("overflow-hidden", card)}>
            <div className="aspect-video">
              <Skeleton className={cn("h-full w-full rounded-none", base)} />
            </div>
          </Card>

          <div className={cn("flex items-center gap-6 px-0 border-b", isDark ? "border-zinc-800" : "border-gray-200")}>
            <Skeleton className={cn("h-5 w-20", base)} />
            <Skeleton className={cn("h-5 w-20", base)} />
            <Skeleton className={cn("h-5 w-20", base)} />
          </div>

          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="flex gap-4">
                <Skeleton className={cn("h-10 w-10 rounded-full", base)} />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <Skeleton className={cn("h-4 w-32", base)} />
                    <Skeleton className={cn("h-3 w-12", base)} />
                  </div>
                  <Skeleton className={cn("h-3 w-full", base)} />
                  <Skeleton className={cn("h-3 w-5/6", base)} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <Card className={cn(card)}>
            <CardContent className="pt-6 space-y-3">
              <Skeleton className={cn("h-4 w-24", base)} />
              <Skeleton className={cn("h-3 w-full", base)} />
              <Skeleton className={cn("h-3 w-11/12", base)} />
              <Skeleton className={cn("h-3 w-10/12", base)} />
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Skeleton className={cn("h-4 w-20", base)} />
            <Card className={cn(card)}>
              <CardContent className="pt-6 space-y-6">
                <div className="space-y-2">
                  <Skeleton className={cn("h-4 w-28", base)} />
                  <Skeleton className={cn("h-3 w-full", base)} />
                  <Skeleton className={cn("h-3 w-10/12", base)} />
                </div>
                <div className="space-y-2">
                  <Skeleton className={cn("h-4 w-16", base)} />
                  <Skeleton className={cn("h-3 w-full", base)} />
                  <Skeleton className={cn("h-3 w-11/12", base)} />
                </div>
                <div className="space-y-2">
                  <Skeleton className={cn("h-4 w-20", base)} />
                  <Skeleton className={cn("h-3 w-full", base)} />
                  <Skeleton className={cn("h-3 w-9/12", base)} />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Streamline() {
  const { setLoading, setStep } = useGlobalLoader()

  useEffect(() => {
    setLoading(false)
    setStep(0)
  }, [setLoading, setStep])

  const searchParams = useSearchParams()
  const projectId = searchParams.get("projectId")
  const forwardedVideoUrl = searchParams.get("videoUrl")
  const [resolvedVideoLink, setResolvedVideoLink] = useState<string>(forwardedVideoUrl || currentProject.videoLink)
  const [projectThumbnailUrl, setProjectThumbnailUrl] = useState<string | null>(null)
  const [dynamicThumbnail, setDynamicThumbnail] = useState<string>(
    getThumbnailUrl(forwardedVideoUrl || currentProject.videoLink) || currentProject.thumbnail
  )
  const [videoTitle, setVideoTitle] = useState<string>(DEFAULT_VIDEO_TITLE)
  const [projectCreatedDate, setProjectCreatedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [isProjectLoading, setIsProjectLoading] = useState<boolean>(!!projectId)

  // Update dynamic thumbnail when video link changes
  useEffect(() => {
    const newThumbnail = projectThumbnailUrl || getThumbnailUrl(resolvedVideoLink) || currentProject.thumbnail
    setDynamicThumbnail(newThumbnail)
  }, [resolvedVideoLink, projectThumbnailUrl])

  // Function to fetch YouTube video title
  const fetchYouTubeTitle = async (videoUrl: string): Promise<string> => {
    try {
      const url = new URL(videoUrl)
      let videoId = ''

      if (url.hostname === 'youtu.be') {
        videoId = url.pathname.replace('/', '').trim()
      } else if (url.hostname.includes('youtube.com')) {
        videoId = url.searchParams.get('v') || ''
      }

      if (!videoId) return DEFAULT_VIDEO_TITLE

      // Use YouTube oEmbed API to get video title
      const oEmbedUrl = `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`
      const response = await fetch(oEmbedUrl)

      if (response.ok) {
        const data = await response.json()
        return data.title || DEFAULT_VIDEO_TITLE
      }
    } catch (error) {
      console.error('Error fetching YouTube title:', error)
    }

    return DEFAULT_VIDEO_TITLE
  }

  // Update video title when video link changes
  useEffect(() => {
    const updateTitle = async () => {
      if (projectId) return
      if (resolvedVideoLink && resolvedVideoLink !== currentProject.videoLink) {
        const title = await fetchYouTubeTitle(resolvedVideoLink)
        setVideoTitle(title)
      }
    }

    updateTitle()
  }, [resolvedVideoLink, projectId])

  // Update project creation date when new project is initiated
  useEffect(() => {
    if (projectId || forwardedVideoUrl) {
      setProjectCreatedDate(new Date().toISOString().split('T')[0])
    }
  }, [projectId, forwardedVideoUrl])

  const [projectOverview, setProjectOverview] = useState<ProjectOverview | null>(null)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [isOverviewLoading, setIsOverviewLoading] = useState<boolean>(false)
  const [vectorStatus, setVectorStatus] = useState<VectorStatus | null>(null)
  const [vectorStatusError, setVectorStatusError] = useState<string | null>(null)
  const vectorTriggerRequested = React.useRef(false)

  useEffect(() => {
    const run = async () => {
      if (!projectId) {
        setIsProjectLoading(false)
        setResolvedVideoLink(forwardedVideoUrl || currentProject.videoLink)
        setProjectThumbnailUrl(null)
        setVideoTitle(DEFAULT_VIDEO_TITLE)
        setProjectOverview(null)
        setOverviewError(null)
        setIsOverviewLoading(false)
        return
      }

      try {
        setIsProjectLoading(true)
        const res = await fetch(`${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}`, {
          cache: "no-store",
        })
        if (!res.ok) {
          setResolvedVideoLink(forwardedVideoUrl || currentProject.videoLink)
          return
        }
        const p = await res.json()
        const projectName = typeof p?.name === "string" && p.name.trim().length > 0 ? p.name.trim() : ""
        if (projectName) {
          setVideoTitle(projectName)
        }
        const nextUrl = typeof p?.video_url === "string" && p.video_url.length > 0
          ? p.video_url
          : (forwardedVideoUrl || currentProject.videoLink)
        setResolvedVideoLink(nextUrl)
        const fetchedThumbnail = typeof p?.thumbnail_url === "string" && p.thumbnail_url.trim().length > 0
          ? p.thumbnail_url.trim()
          : ""
        if (fetchedThumbnail) {
          setProjectThumbnailUrl(fetchedThumbnail)
        } else {
          setProjectThumbnailUrl(null)
          try {
            const thumbRes = await fetch(
              `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/thumbnail/ensure`,
              { method: "POST" }
            )
            if (thumbRes.ok) {
              const thumbData = await thumbRes.json()
              const ensuredThumb = typeof thumbData?.thumbnail_url === "string" && thumbData.thumbnail_url.trim().length > 0
                ? thumbData.thumbnail_url.trim()
                : ""
              if (ensuredThumb) {
                setProjectThumbnailUrl(ensuredThumb)
              }
            }
          } catch {}
        }
        if (typeof p?.created_at === "string" && p.created_at.trim().length > 0) {
          const created = new Date(p.created_at)
          if (!Number.isNaN(created.getTime())) {
            setProjectCreatedDate(created.toISOString().split("T")[0])
          }
        }
        if (typeof p?.video_duration_seconds === "number" && p.video_duration_seconds > 0) {
          setVideoDurationSeconds(p.video_duration_seconds)
        }
      } catch {
        setResolvedVideoLink(forwardedVideoUrl || currentProject.videoLink)
      } finally {
        setIsProjectLoading(false)
      }
    }

    run()
  }, [projectId, forwardedVideoUrl])

  useEffect(() => {
    if (!projectId) return

    let cancelled = false
    let pollTimer: ReturnType<typeof setTimeout> | null = null

    const fetchOverview = async () => {
      if (cancelled) return
      setIsOverviewLoading(true)
      setOverviewError(null)
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/overview`,
          { cache: "no-store" }
        )
        if (!res.ok) {
          throw new Error(`Failed to load overview (${res.status})`)
        }
        const data = (await res.json()) as ProjectOverview
        if (cancelled) return
        setProjectOverview(data)

        if (data?.status === "pending" || data?.status === "not_started") {
          pollTimer = setTimeout(fetchOverview, 2000)
        }
      } catch (e: any) {
        if (cancelled) return
        setOverviewError(e?.message || "Failed to load overview")
      } finally {
        if (!cancelled) setIsOverviewLoading(false)
      }
    }

    fetchOverview()

    return () => {
      cancelled = true
      if (pollTimer) clearTimeout(pollTimer)
    }
  }, [projectId])

  useEffect(() => {
    if (!projectId) {
      setVectorStatus(null)
      setVectorStatusError(null)
      return
    }

    let cancelled = false
    let pollTimer: ReturnType<typeof setTimeout> | null = null

    const fetchVectorStatus = async () => {
      if (cancelled) return
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/vector-status`,
          { cache: "no-store" }
        )
        if (!res.ok) {
          throw new Error(`Failed to load vector status (${res.status})`)
        }
        const data = (await res.json()) as VectorStatus
        if (cancelled) return
        setVectorStatus(data)
        setVectorStatusError(null)

        if (data?.status === "pending" || data?.status === "not_started") {
          pollTimer = setTimeout(fetchVectorStatus, 3000)
        }
      } catch (e: any) {
        if (cancelled) return
        setVectorStatusError(e?.message || "Failed to load vector status")
      }
    }

    fetchVectorStatus()

    return () => {
      cancelled = true
      if (pollTimer) clearTimeout(pollTimer)
    }
  }, [projectId])

  useEffect(() => {
    vectorTriggerRequested.current = false
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    if (vectorTriggerRequested.current) return
    if (projectOverview?.status !== "completed") return
    if (vectorStatus?.status !== "not_started") return

    const triggerVectorGeneration = async () => {
      try {
        vectorTriggerRequested.current = true
        await fetch(
          `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/generate-vector-data`,
          { method: "POST" }
        )
      } catch {
        vectorTriggerRequested.current = false
      }
    }

    triggerVectorGeneration()
  }, [projectId, projectOverview?.status, vectorStatus?.status])

  const [isDark, setIsDark] = useState(true)
  const [activeTab, setActiveTab] = useState("transcript")
  const [activeTopTab, setActiveTopTab] = useState("overview")
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false)
  const [selectedMomentId, setSelectedMomentId] = useState<string | number | null>(null)
  const [selectedMomentStartSeconds, setSelectedMomentStartSeconds] = useState(0)
  const [playbackTimeSeconds, setPlaybackTimeSeconds] = useState<number | null>(null)
  const [videoDurationSeconds, setVideoDurationSeconds] = useState<number>(0)
  const [editorMessages, setEditorMessages] = useState([
    { id: 1, content: "Hi! I'm your AI video editor assistant. How can I help you edit this video today?", isUser: false },
  ])
  const [contentFeatureStatus, setContentFeatureStatus] = useState<Record<FeatureId, FeatureState>>(defaultFeatureMap)
  const [contentFeatureData, setContentFeatureData] = useState<Record<FeatureId, any>>({
    clips: null,
    subtitles: null,
    chapters: null,
    moments: null,
  })
  const [selectedLanguage, setSelectedLanguage] = useState("en")
  const [subtitleStyle, setSubtitleStyle] = useState("default")
  const [exportFormat, setExportFormat] = useState<"srt" | "vtt">("srt")
  const [contentFeatureError, setContentFeatureError] = useState<string | null>(null)
  const [transcriptPassage, setTranscriptPassage] = useState<TranscriptPassageResponse | null>(null)
  const [isTranscriptPassageLoading, setIsTranscriptPassageLoading] = useState(false)
  const [expandedChapterIds, setExpandedChapterIds] = useState<Set<string>>(new Set())

  const placeholderMarkdown = `# Taxing Laughter: The Joke Tax Chronicles\n\nOnce upon a time, in a far-off land, there was a very lazy king who spent all day lounging on his throne. One day, his advisors came to him with a problem: the kingdom was running out of money.\n`

  const blogMarkdown = (projectOverview?.blog_markdown || "").trim() || placeholderMarkdown

  const { blogTitle, blogBodyMarkdown } = React.useMemo(() => {
    const md = blogMarkdown.trim()
    const h1Match = md.match(/^#\s+(.+)\s*\n+/)
    if (!h1Match) {
      return { blogTitle: "", blogBodyMarkdown: md }
    }
    const title = h1Match[1].trim()
    const body = md.slice(h1Match[0].length).trimStart()
    return { blogTitle: title, blogBodyMarkdown: body }
  }, [blogMarkdown])

  const markdownComponents = React.useMemo(() => {
    return {
      h1: (props: any) => (
        <h1
          {...props}
          className={cn(
            "scroll-m-20 text-4xl font-extrabold tracking-tight text-balance",
            isDark ? "text-white" : "text-gray-900",
            props?.className
          )}
        />
      ),
      h2: (props: any) => (
        <h2
          {...props}
          className={cn(
            "mt-10 scroll-m-20 border-b pb-2 text-2xl font-semibold tracking-tight first:mt-0",
            isDark ? "text-white border-zinc-800" : "text-gray-900 border-gray-200",
            props?.className
          )}
        />
      ),
      h3: (props: any) => (
        <h3
          {...props}
          className={cn(
            "mt-8 scroll-m-20 text-xl font-semibold tracking-tight",
            isDark ? "text-white" : "text-gray-900",
            props?.className
          )}
        />
      ),
      p: (props: any) => (
        <p
          {...props}
          className={cn(
            "leading-7 [&:not(:first-child)]:mt-6",
            isDark ? "text-zinc-300" : "text-gray-600",
            props?.className
          )}
        />
      ),
      a: (props: any) => (
        <a
          {...props}
          className={cn(
            "font-medium underline underline-offset-4",
            isDark ? "text-purple-400 hover:text-purple-300" : "text-purple-600 hover:text-purple-700",
            props?.className
          )}
          target={props?.target || "_blank"}
          rel={props?.rel || "noopener noreferrer"}
        />
      ),
      blockquote: (props: any) => (
        <blockquote
          {...props}
          className={cn(
            "mt-6 border-l-2 pl-6 italic",
            isDark ? "border-zinc-700 text-zinc-400" : "border-gray-300 text-gray-600",
            props?.className
          )}
        />
      ),
      ul: (props: any) => (
        <ul
          {...props}
          className={cn(
            "my-6 ml-6 list-disc [&>li]:mt-2",
            isDark ? "text-zinc-300" : "text-gray-600",
            props?.className
          )}
        />
      ),
      ol: (props: any) => (
        <ol
          {...props}
          className={cn(
            "my-6 ml-6 list-decimal [&>li]:mt-2",
            isDark ? "text-zinc-300" : "text-gray-600",
            props?.className
          )}
        />
      ),
      hr: (props: any) => (
        <hr
          {...props}
          className={cn(
            "my-8",
            isDark ? "border-zinc-800" : "border-gray-200",
            props?.className
          )}
        />
      ),
      table: (props: any) => (
        <div className="my-6 w-full overflow-x-auto">
          <table
            {...props}
            className={cn(
              "w-full text-sm",
              isDark ? "text-zinc-300" : "text-gray-700",
              props?.className
            )}
          />
        </div>
      ),
      thead: (props: any) => (
        <thead
          {...props}
          className={cn(
            isDark ? "border-b border-zinc-800" : "border-b border-gray-200",
            props?.className
          )}
        />
      ),
      th: (props: any) => (
        <th
          {...props}
          className={cn(
            "px-3 py-2 text-left font-semibold",
            isDark ? "text-white" : "text-gray-900",
            props?.className
          )}
        />
      ),
      td: (props: any) => (
        <td
          {...props}
          className={cn(
            "px-3 py-2 align-top",
            isDark ? "border-b border-zinc-800" : "border-b border-gray-200",
            props?.className
          )}
        />
      ),
      code: (props: any) => (
        <code
          {...props}
          className={cn(
            "rounded px-1.5 py-0.5 font-mono text-[0.85em]",
            isDark ? "bg-zinc-800 text-zinc-100" : "bg-gray-100 text-gray-900",
            props?.className
          )}
        />
      ),
      pre: (props: any) => (
        <pre
          {...props}
          className={cn(
            "my-6 overflow-x-auto rounded-lg p-4",
            isDark ? "bg-zinc-900 border border-zinc-800" : "bg-gray-50 border border-gray-200",
            props?.className
          )}
        />
      ),
    }
  }, [isDark])

  const vectorStatusLabel = React.useMemo(() => {
    if (!vectorStatus?.status) return null
    switch (vectorStatus.status) {
      case "completed":
        return "Vector index ready"
      case "failed":
        return "Vector index failed"
      case "pending":
        return "Building vector index"
      case "not_started":
        return "Vector index queued"
      default:
        return `Vector index: ${vectorStatus.status}`
    }
  }, [vectorStatus])

  const handleSendMessage = (message: string) => {
    // Add user message
    setEditorMessages(prev => [...prev, { id: Date.now(), content: message, isUser: true }])

    // Simulate AI response
    setTimeout(() => {
      setEditorMessages(prev => [...prev, {
        id: Date.now() + 1,
        content: "I understand you want to edit the video. I can help you with trimming, adding captions, extracting clips, and more. What would you like to do?",
        isUser: false
      }])
    }, 1000)
  }

  const fetchContentFeatureStatus = React.useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/content-features/status`,
        { cache: "no-store" }
      )
      if (!res.ok) throw new Error(`Failed to load content feature status (${res.status})`)
      const data = (await res.json()) as ContentFeatureStatusResponse
      setContentFeatureStatus(data.features || defaultFeatureMap)
      setContentFeatureError(null)
      return data.features || defaultFeatureMap
    } catch (e: any) {
      setContentFeatureError(e?.message || "Failed to load content feature status")
      return null
    }
  }, [projectId])

  const triggerContentFeatureGeneration = React.useCallback(async (force = false) => {
    if (!projectId) return
    try {
      await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/content-features/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force }),
        }
      )
    } catch (e) {
      // keep non-blocking UX
    }
  }, [projectId])

  const loadFeaturePayload = React.useCallback(async (featureId: FeatureId) => {
    if (!projectId) return
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/content-features/${featureId}`,
        { cache: "no-store" }
      )
      if (!res.ok) return
      const data = await res.json()
      setContentFeatureData((prev) => ({ ...prev, [featureId]: data?.payload || null }))
    } catch {
      // no-op
    }
  }, [projectId])

  const handleExportSubtitles = React.useCallback(async () => {
    if (!projectId) return
    const res = await fetch(
      `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/content-features/subtitles/export`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: exportFormat, language: selectedLanguage }),
      }
    )
    if (!res.ok) return
    const data = await res.json()
    const blob = new Blob([data.content], { type: data.mime_type || "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = data.filename || `subtitles.${exportFormat}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }, [projectId, exportFormat, selectedLanguage])

  const fetchTranscriptPassage = React.useCallback(async () => {
    if (!projectId) return
    setIsTranscriptPassageLoading(true)
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/transcript-passage`,
        { cache: "no-store" }
      )
      if (!res.ok) return
      const data = (await res.json()) as TranscriptPassageResponse
      setTranscriptPassage(data)
    } catch {
      // no-op
    } finally {
      setIsTranscriptPassageLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    if (projectOverview?.status !== "completed") return
    triggerContentFeatureGeneration(false)
  }, [projectId, projectOverview?.status, triggerContentFeatureGeneration])

  useEffect(() => {
    if (!projectId) return
    if (projectOverview?.status !== "completed") return
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | null = null

    const poll = async () => {
      if (cancelled) return
      const state = await fetchContentFeatureStatus()
      if (!state) {
        timer = setTimeout(poll, 2500)
        return
      }
      const values = Object.values(state || {})
      const done = values.length > 0 && values.every((v) => v.status === "completed" || v.status === "error")
      if (!done) timer = setTimeout(poll, 2500)
    }

    poll()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [projectId, projectOverview?.status, fetchContentFeatureStatus])

  useEffect(() => {
    const featureTabs: FeatureId[] = ["clips", "subtitles", "chapters", "moments"]
    for (const featureId of featureTabs) {
      if (contentFeatureStatus[featureId]?.status === "completed" && !contentFeatureData[featureId]) {
        loadFeaturePayload(featureId)
      }
    }
  }, [contentFeatureStatus, contentFeatureData, loadFeaturePayload])

  useEffect(() => {
    if (activeTopTab !== "subtitles") return
    fetchTranscriptPassage()
  }, [activeTopTab, fetchTranscriptPassage])

  const featureTabIds: FeatureId[] = ["subtitles", "chapters", "moments"]
  const activeFeatureId = (featureTabIds.includes(activeTopTab as FeatureId) ? activeTopTab : null) as FeatureId | null
  const activeFeatureState = activeFeatureId ? contentFeatureStatus[activeFeatureId] : null
  const chapters = React.useMemo<StructuralChapter[]>(() => {
    const raw = contentFeatureData.chapters?.chapters
    if (!Array.isArray(raw)) return []
    return raw
      .map((item: any, index: number) => normalizeStructuralChapter(item, index))
      .sort((a: StructuralChapter, b: StructuralChapter) => {
        if (a.start_time_seconds !== b.start_time_seconds) return a.start_time_seconds - b.start_time_seconds
        return a.end_time_seconds - b.end_time_seconds
      })
  }, [contentFeatureData.chapters])
  const totalChapters = Number(contentFeatureData.chapters?.totalChapters)
  const resolvedTotalChapters = Number.isFinite(totalChapters) && totalChapters > 0 ? Math.floor(totalChapters) : chapters.length
  const chapterTotalDurationSeconds = React.useMemo(() => {
    const fromVideo = Math.max(0, Math.floor(videoDurationSeconds || 0))
    const fromChapters = chapters.reduce((maxEnd: number, chapter: StructuralChapter) => Math.max(maxEnd, chapter.end_time_seconds), 0)
    return Math.max(fromVideo, fromChapters)
  }, [videoDurationSeconds, chapters])
  const keyMoments = React.useMemo<KeyMoment[]>(() => {
    const clipMoments = contentFeatureData.clips?.key_moments
    if (Array.isArray(clipMoments) && clipMoments.length > 0) {
      return clipMoments.map((item: any, index: number) => normalizeKeyMoment(item, index))
    }
    const legacyMoments = contentFeatureData.moments?.moments
    if (Array.isArray(legacyMoments) && legacyMoments.length > 0) {
      return legacyMoments.map((item: any, index: number) => normalizeKeyMoment(item, index))
    }
    return []
  }, [contentFeatureData.clips, contentFeatureData.moments])

  useEffect(() => {
    setExpandedChapterIds(new Set())
  }, [contentFeatureData.chapters])
  useEffect(() => {
    if (keyMoments.length === 0) {
      setSelectedMomentId(null)
      setSelectedMomentStartSeconds(0)
      setPlaybackTimeSeconds(null)
      return
    }
    const existing = keyMoments.find((moment) => moment.id === selectedMomentId)
    if (!existing) {
      setSelectedMomentId(keyMoments[0].id)
      setSelectedMomentStartSeconds(keyMoments[0].start_time_seconds)
    }
  }, [keyMoments, selectedMomentId])

  useEffect(() => {
    if (!isVideoModalOpen) {
      setPlaybackTimeSeconds(null)
    }
  }, [isVideoModalOpen])

  const renderFeatureStatusPanel = (featureId: FeatureId) => {
    const state = contentFeatureStatus[featureId] || defaultFeatureState
    const steps = featureLoadingSteps[featureId]
    const currentStepIdx = Math.min(steps.length - 1, Math.floor((state.progress || 0) / Math.max(1, Math.floor(100 / steps.length))))
    return (
      <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
        <CardContent className="pt-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>Processing {featureId}</h3>
            <span className={cn("text-xs", isDark ? "text-zinc-400" : "text-gray-500")}>
              {state.status} • {state.progress}%
            </span>
          </div>
          <div className={cn("h-2 rounded-full overflow-hidden", isDark ? "bg-zinc-800" : "bg-gray-200")}>
            <div
              className={cn("h-full transition-all duration-500", state.status === "error" ? "bg-red-500" : "bg-blue-500")}
              style={{ width: `${Math.max(0, Math.min(100, state.progress || 0))}%` }}
            />
          </div>
          <div className="space-y-2">
            {steps.map((step, idx) => (
              <div key={step} className={cn("text-xs", idx <= currentStepIdx ? (isDark ? "text-zinc-200" : "text-gray-700") : (isDark ? "text-zinc-500" : "text-gray-400"))}>
                {step}
              </div>
            ))}
          </div>
          {state.error && (
            <div className={cn("text-xs", isDark ? "text-red-300" : "text-red-600")}>{state.error}</div>
          )}
          {state.status === "error" && (
            <button
              onClick={() => triggerContentFeatureGeneration(true)}
              className={cn(
                "px-3 py-1.5 text-xs rounded-md border",
                isDark ? "border-zinc-700 text-zinc-200 hover:bg-zinc-800" : "border-gray-300 text-gray-700 hover:bg-gray-50"
              )}
            >
              Retry Generation
            </button>
          )}
        </CardContent>
      </Card>
    )
  }

  const renderFeatureContent = () => {
    if (!activeFeatureId || !activeFeatureState) return null
    if (activeFeatureState.status !== "completed") {
      return (
        <div className="space-y-4">
          {contentFeatureError && (
            <div className={cn("text-xs", isDark ? "text-red-300" : "text-red-600")}>{contentFeatureError}</div>
          )}
          {renderFeatureStatusPanel(activeFeatureId)}
        </div>
      )
    }

    if (activeFeatureId === "subtitles") {
      const subtitles = contentFeatureData.subtitles?.segments || []
      const fallbackPassage = subtitles
        .map((s: any) => {
          if (Array.isArray(s?.lines) && s.lines.length > 0) {
            return s.lines.map((line: any) => String(line || "").trim()).filter(Boolean).join(" ")
          }
          return String(s?.text || "").trim()
        })
        .filter(Boolean)
        .join("\n\n")

      const transcriptText = (transcriptPassage?.passage || "").trim() || fallbackPassage || ""

      return (
        <div className="space-y-4">
          <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
            <CardContent className="pt-5 flex flex-wrap items-center gap-3">
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className={cn("px-2 py-1 text-xs rounded border", isDark ? "bg-zinc-900 border-zinc-700 text-zinc-200" : "bg-white border-gray-300 text-gray-700")}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
              <select
                value={subtitleStyle}
                onChange={(e) => setSubtitleStyle(e.target.value)}
                className={cn("px-2 py-1 text-xs rounded border", isDark ? "bg-zinc-900 border-zinc-700 text-zinc-200" : "bg-white border-gray-300 text-gray-700")}
              >
                <option value="default">Default</option>
                <option value="contrast">High Contrast</option>
                <option value="minimal">Minimal</option>
              </select>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat((e.target.value as "srt" | "vtt"))}
                className={cn("px-2 py-1 text-xs rounded border", isDark ? "bg-zinc-900 border-zinc-700 text-zinc-200" : "bg-white border-gray-300 text-gray-700")}
              >
                <option value="srt">SRT</option>
                <option value="vtt">VTT</option>
              </select>
              <button
                onClick={handleExportSubtitles}
                className={cn("px-3 py-1.5 text-xs rounded border", isDark ? "border-zinc-700 text-zinc-100 hover:bg-zinc-800" : "border-gray-300 text-gray-700 hover:bg-gray-50")}
              >
                Export
              </button>
            </CardContent>
          </Card>
          <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
            <CardContent className="pt-5 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-zinc-100" : "text-gray-900")}>
                  Full Transcript Passage
                </h3>
                <span className={cn("text-[11px]", isDark ? "text-zinc-400" : "text-gray-500")}>
                  Source: {transcriptPassage?.source || "content_feature_subtitles"}
                </span>
              </div>
              {isTranscriptPassageLoading ? (
                <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>Loading transcript passage...</p>
              ) : transcriptText ? (
                <div className={cn("max-h-[65vh] overflow-y-auto pr-1", isDark ? "text-zinc-100" : "text-gray-800")}>
                  <p className="text-sm leading-7 whitespace-pre-wrap">{transcriptText}</p>
                </div>
              ) : (
                <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                  No transcript passage is available yet.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )
    }

    if (activeFeatureId === "chapters") {
      const allExpanded = chapters.length > 0 && chapters.every((chapter) => expandedChapterIds.has(chapter.id))
      return (
        <div className="space-y-4">
          <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
            <CardContent className="pt-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                  <div className={cn("rounded-md px-3 py-2", isDark ? "bg-zinc-800/80 text-zinc-200" : "bg-gray-100 text-gray-700")}>
                    <span className={cn("block text-[11px]", isDark ? "text-zinc-400" : "text-gray-500")}>Total Chapters</span>
                    <span className="text-sm font-semibold">{resolvedTotalChapters}</span>
                  </div>
                  <div className={cn("rounded-md px-3 py-2", isDark ? "bg-zinc-800/80 text-zinc-200" : "bg-gray-100 text-gray-700")}>
                    <span className={cn("block text-[11px]", isDark ? "text-zinc-400" : "text-gray-500")}>Total Duration</span>
                    <span className="text-sm font-semibold">{formatSeconds(chapterTotalDurationSeconds)}</span>
                  </div>
                  <div className={cn("rounded-md px-3 py-2", isDark ? "bg-zinc-800/80 text-zinc-200" : "bg-gray-100 text-gray-700")}>
                    <span className={cn("block text-[11px]", isDark ? "text-zinc-400" : "text-gray-500")}>Rendered Cards</span>
                    <span className="text-sm font-semibold">{chapters.length}</span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (allExpanded) {
                      setExpandedChapterIds(new Set())
                      return
                    }
                    setExpandedChapterIds(new Set(chapters.map((chapter) => chapter.id)))
                  }}
                  className={cn(
                    "px-3 py-1.5 text-xs rounded-md border",
                    isDark ? "border-zinc-700 text-zinc-200 hover:bg-zinc-800" : "border-gray-300 text-gray-700 hover:bg-gray-50"
                  )}
                >
                  {allExpanded ? "Collapse All" : "Expand All"}
                </button>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-3">
            {chapters.length === 0 ? (
              <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
                <CardContent className="pt-5">
                  <p className={cn("text-sm", isDark ? "text-zinc-300" : "text-gray-700")}>
                    {contentFeatureData.chapters?.skip_reason || "No chapters generated yet."}
                  </p>
                </CardContent>
              </Card>
            ) : chapters.map((chapter: StructuralChapter) => {
              const chapterId = chapter.id
              const isExpanded = expandedChapterIds.has(chapterId)
              const intent = String(chapter.psychological_intent || "other")
              const intentClass = intent === "build_tension"
                ? (isDark ? "bg-amber-500/20 text-amber-200 ring-1 ring-amber-400/30" : "bg-amber-100 text-amber-700 ring-1 ring-amber-300")
                : intent === "deliver_proof"
                  ? (isDark ? "bg-blue-500/20 text-blue-200 ring-1 ring-blue-400/30" : "bg-blue-100 text-blue-700 ring-1 ring-blue-300")
                  : intent === "escalate"
                    ? (isDark ? "bg-rose-500/20 text-rose-200 ring-1 ring-rose-400/30" : "bg-rose-100 text-rose-700 ring-1 ring-rose-300")
                    : intent === "cta"
                      ? (isDark ? "bg-green-500/20 text-green-200 ring-1 ring-green-400/30" : "bg-green-100 text-green-700 ring-1 ring-green-300")
                      : (isDark ? "bg-purple-500/20 text-purple-200 ring-1 ring-purple-400/30" : "bg-purple-100 text-purple-700 ring-1 ring-purple-300")

              return (
                <Card key={chapter.id} className={cn("overflow-hidden", isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
                  <CardContent className="pt-4 pb-4">
                    <button
                      onClick={() =>
                        setExpandedChapterIds((prev) => {
                          const next = new Set(prev)
                          if (next.has(chapterId)) next.delete(chapterId)
                          else next.add(chapterId)
                          return next
                        })
                      }
                      className={cn("w-full text-left")}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <h3 className={cn("text-base font-semibold", isDark ? "text-white" : "text-gray-900")}>
                              {chapter.title}
                            </h3>
                            <span className={cn("text-[10px] px-2 py-0.5 rounded-full", intentClass)}>
                              {intent.replaceAll("_", " ")}
                            </span>
                            <span className={cn("text-[10px] px-2 py-0.5 rounded-full", isDark ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700")}>
                              {chapter.chapter_type || "Education"}
                            </span>
                          </div>
                          <button
                            onClick={(event) => {
                              event.stopPropagation()
                              setSelectedMomentStartSeconds(chapter.start_time_seconds)
                              setPlaybackTimeSeconds(chapter.start_time_seconds)
                              setIsVideoModalOpen(true)
                            }}
                            className={cn(
                              "text-xs rounded px-1.5 py-0.5 border",
                              isDark ? "border-zinc-700 text-zinc-300 hover:bg-zinc-800" : "border-gray-300 text-gray-600 hover:bg-gray-100"
                            )}
                          >
                            {formatSeconds(chapter.start_time_seconds)} - {formatSeconds(chapter.end_time_seconds)}
                          </button>
                          <p className={cn("text-sm leading-6 pr-2", isDark ? "text-zinc-300" : "text-gray-700")}>
                            {chapter.summary}
                          </p>
                        </div>
                        <div className={cn("mt-1 shrink-0", isDark ? "text-zinc-400" : "text-gray-500")}>
                          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </div>
                      </div>
                    </button>

                    <div
                      className={cn(
                        "overflow-hidden transition-all duration-300 ease-in-out",
                        isExpanded ? "max-h-[800px] opacity-100 mt-4" : "max-h-0 opacity-0 mt-0"
                      )}
                    >
                      <div className={cn("ml-1 pl-4 space-y-2 border-l", isDark ? "border-zinc-700" : "border-gray-200")}>
                        {(chapter.subchapters || []).map((subchapter: ChapterSubchapter) => (
                          <div
                            key={subchapter.id}
                            className={cn("rounded-lg p-3", isDark ? "bg-zinc-900/80" : "bg-gray-50")}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="space-y-1">
                                <p className={cn("text-xs font-semibold", isDark ? "text-zinc-100" : "text-gray-900")}>
                                  {subchapter.title}
                                </p>
                                <p className={cn("text-xs leading-5", isDark ? "text-zinc-300" : "text-gray-700")}>
                                  {subchapter.summary}
                                </p>
                              </div>
                              <button
                                onClick={() => {
                                  setSelectedMomentStartSeconds(subchapter.start_time_seconds)
                                  setPlaybackTimeSeconds(subchapter.start_time_seconds)
                                  setIsVideoModalOpen(true)
                                }}
                                className={cn(
                                  "text-[11px] rounded px-1.5 py-0.5 border whitespace-nowrap",
                                  isDark ? "border-zinc-700 text-zinc-300 hover:bg-zinc-800" : "border-gray-300 text-gray-600 hover:bg-gray-100"
                                )}
                              >
                                {formatSeconds(subchapter.start_time_seconds)} - {formatSeconds(subchapter.end_time_seconds)}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )
    }

    const moments = contentFeatureData.moments?.moments || []
    return (
      <div className="grid gap-3">
        {moments.map((moment: any) => (
          <Card key={moment.id} className={cn(isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
            <CardContent className="pt-5 space-y-2">
              <div className="flex items-center justify-between gap-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>{moment.label}</h3>
                <span className={cn("text-[10px] px-2 py-0.5 rounded", isDark ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700")}>{moment.category}</span>
              </div>
              <p className={cn("text-xs", isDark ? "text-zinc-400" : "text-gray-500")}>
                {formatSeconds(moment.start_time_seconds)} - {formatSeconds(moment.end_time_seconds)} • Score {moment.importance_score}
              </p>
              <p className={cn("text-xs", isDark ? "text-zinc-300" : "text-gray-700")}>{moment.rationale}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen py-6 px-4")}>
      <div className="max-w-7xl mx-auto">

        {isProjectLoading ? (
          <StreamlineSkeleton isDark={isDark} />
        ) : (

          <>

        {/* Header */}
        <div className="mb-8 space-y-4">
          {activeTopTab === "overview" ? (
            // Original header for statistics tab
            <>
              <div className="flex items-center justify-between">
                <h1 className={cn("text-2xl font-bold", isDark ? "text-white" : "text-gray-900")}>
                  {videoTitle}
                </h1>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsDark(!isDark)}
                    className={cn(
                      "p-1.5 rounded-lg transition-colors",
                      isDark
                        ? "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300"
                        : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
                    )}
                  >
                    {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className={cn("flex items-center gap-4 text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>{projectCreatedDate}</span>
                </div>
                {vectorStatusLabel && (
                  <div className="flex items-center gap-1">
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full",
                        vectorStatus?.status === "completed"
                          ? "bg-green-500"
                          : vectorStatus?.status === "failed"
                            ? "bg-red-500"
                            : "bg-amber-500"
                      )}
                    />
                    <span>{vectorStatusLabel}</span>
                  </div>
                )}
              </div>

              {vectorStatusError && (
                <div className={cn("text-xs mt-2", isDark ? "text-red-300" : "text-red-600")}>
                  {vectorStatusError}
                </div>
              )}
            </>
          ) : (
            // Video info card for all other tabs
            <div className="flex items-center justify-between">
              <div className={cn(
                "flex items-center gap-4 px-4 py-3 rounded-xl",
                isDark ? "bg-zinc-900/50 border border-zinc-800" : "bg-white border border-gray-200"
              )}>
                {/* Video Thumbnail */}
                <div className="relative w-32 h-20 rounded-lg overflow-hidden flex-shrink-0 bg-black">
                  <img
                    src={dynamicThumbnail}
                    alt="Video thumbnail"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to placeholder if thumbnail fails
                      const target = e.target as HTMLImageElement
                      target.src = "/images/design-mode/Screenshot%202025-05-08%20133020(1).png"
                    }}
                  />

                </div>

                {/* Video Info */}
                <div className="flex flex-col gap-1">
                  <h2 className={cn("text-base font-semibold", isDark ? "text-white" : "text-gray-900")}>
                    {videoTitle}
                  </h2>
                  <a
                    href={resolvedVideoLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      "text-sm hover:underline",
                      isDark ? "text-zinc-400 hover:text-zinc-300" : "text-gray-600 hover:text-gray-700"
                    )}
                  >
                    {resolvedVideoLink}
                  </a>
                  <button
                    className={cn(
                      "text-xs text-left hover:underline w-fit",
                      isDark ? "text-zinc-500 hover:text-zinc-400" : "text-gray-500 hover:text-gray-600"
                    )}
                  >
                    Rename
                  </button>
                </div>
              </div>

              {/* Right side: star + theme toggle */}
              <div className="flex items-center gap-2">
                <button
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded transition-colors",
                    isDark
                      ? "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                      : "bg-gray-100 border border-gray-200 text-gray-500 hover:bg-gray-200"
                  )}
                >
                  ★
                </button>

                <button
                  onClick={() => setIsDark(!isDark)}
                  className={cn(
                    "p-1.5 rounded-lg transition-colors",
                    isDark
                      ? "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300"
                      : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
                  )}
                >
                  {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 flex justify-center">
          <div className={cn("inline-flex items-center gap-1.5 p-1 rounded-lg", isDark ? "bg-transparent" : "bg-gray-100")}>
            {toptabs.map((toptab) => {
              const Icon = toptab.icon
              const isActive = activeTopTab === toptab.id
              return (
                <button
                  key={toptab.id}
                  onClick={() => setActiveTopTab(toptab.id)}
                  className={cn(
                    "px-3 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap",
                    isActive
                      ? isDark
                        ? "bg-zinc-800 text-white shadow-lg"
                        : "bg-white text-gray-900 shadow"
                      : isDark
                        ? "text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50"
                        : "text-gray-500 hover:text-gray-700 hover:bg-gray-200"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {toptab.label}
                  {toptab.badge && (
                    <span className={cn(
                      "ml-0.5 px-1.5 py-0.5 text-[10px] rounded-md font-semibold",
                      isDark ? "bg-purple-500/30 text-purple-300" : "bg-purple-100 text-purple-600"
                    )}>
                      {toptab.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Main Content */}
        {activeTopTab === "statistics" ? (
          <div className="lg:col-span-5">
            <VideoAnalytics
              currentTimeSeconds={playbackTimeSeconds}
              durationSeconds={videoDurationSeconds}
              isExternalClockActive={playbackTimeSeconds !== null}
              onSeekTimeline={(seconds: number) => {
                setSelectedMomentStartSeconds(seconds)
                setPlaybackTimeSeconds(seconds)
                setIsVideoModalOpen(true)
              }}
            />
          </div>
        ) : activeTopTab === "psychology" ? (
          <div className="lg:col-span-5">
            <PsychologicalPersuasionAnalytics
              currentTimeSeconds={playbackTimeSeconds}
              durationSeconds={videoDurationSeconds}
              onSeekTimeline={(seconds: number) => {
                setSelectedMomentStartSeconds(seconds)
                setPlaybackTimeSeconds(seconds)
                setIsVideoModalOpen(true)
              }}
            />
          </div>
        ) : activeFeatureId === "moments" ? (
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 items-start">
            <div className="xl:col-span-4 space-y-5">
              <Card className={cn("overflow-hidden", isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <div className="mx-auto w-full max-w-4xl p-3">
                  <div
                    className="aspect-video bg-black relative group cursor-pointer rounded-lg overflow-hidden"
                    onClick={() => setIsVideoModalOpen(true)}
                  >
                    <img
                      src={dynamicThumbnail}
                      alt={`${currentProject.name} thumbnail`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = "/images/design-mode/Screenshot%202025-05-08%20133020(1).png"
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
                      <button className="p-3 rounded-full bg-white/20 hover:bg-white/30 text-white">
                        <Play className="h-6 w-6" />
                      </button>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black via-black/50 to-transparent">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-xs text-zinc-400">09:18</span>
                        <div className="flex-1 h-1 bg-zinc-700 rounded-full overflow-hidden">
                          <div className="h-full w-1/3 bg-purple-600" />
                        </div>
                        <span className="text-xs text-zinc-400">{formatSeconds(videoDurationSeconds)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button className="p-1 hover:bg-white/10 rounded text-white">
                          <Play className="h-4 w-4" />
                        </button>
                        <button className="p-1 hover:bg-white/10 rounded text-white">
                          <Volume2 className="h-4 w-4" />
                        </button>
                        <button className="p-1 hover:bg-white/10 rounded text-white ml-auto">
                          <Settings2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
              <Card className={cn("overflow-visible", isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <CardContent className="pt-6 pb-5">
                  <h3 className={cn("text-sm font-semibold mb-4", isDark ? "text-white" : "text-gray-900")}>
                    Key Moments
                  </h3>
                  <KeyMomentsTimeline
                    moments={keyMoments}
                    selectedMomentId={selectedMomentId}
                    totalDurationSeconds={videoDurationSeconds}
                    currentTimeSeconds={playbackTimeSeconds ?? selectedMomentStartSeconds}
                    isDark={isDark}
                    onMomentSelect={(moment: KeyMoment) => {
                      setSelectedMomentId(moment.id)
                    }}
                    onSeek={(seconds: number) => {
                      setSelectedMomentStartSeconds(seconds)
                      setIsVideoModalOpen(true)
                    }}
                  />
                </CardContent>
              </Card>
            </div>
            <div className="xl:col-span-1">
              <Card className={cn("px-2", isDark ? "border-zinc-800 bg-zinc-900/60" : "border-gray-200 bg-white")}>
                <CardContent className="pt-5">
                  <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                    Extracted Key Moments
                  </h3>
                  <p className={cn("text-xs mt-1 mb-3", isDark ? "text-zinc-400" : "text-gray-500")}>
                    {keyMoments.length} highlights
                  </p>
                  <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
                    {keyMoments.length === 0 ? (
                      <div className={cn("rounded-lg border p-3", isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-gray-50")}>
                        <p className={cn("text-xs", isDark ? "text-zinc-300" : "text-gray-700")}>
                          {contentFeatureData.clips?.skip_reason || contentFeatureData.moments?.skip_reason || "No key moments generated yet."}
                        </p>
                      </div>
                    ) : (
                      keyMoments.map((moment: KeyMoment) => (
                        <button
                          key={moment.id}
                          onClick={() => {
                            setSelectedMomentId(moment.id)
                            setSelectedMomentStartSeconds(moment.start_time_seconds)
                            setIsVideoModalOpen(true)
                          }}
                          className={cn(
                            "w-full text-left rounded-lg border p-2.5",
                            selectedMomentId === moment.id
                              ? (isDark ? "border-zinc-500 bg-zinc-800/60" : "border-gray-300 bg-white")
                              : (isDark ? "border-zinc-800 bg-zinc-900/40" : "border-gray-200 bg-gray-50")
                          )}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className={cn("text-xs font-medium line-clamp-2", isDark ? "text-zinc-100" : "text-gray-800")}>
                              {moment.title}
                            </p>
                            <span className={cn("text-[10px] whitespace-nowrap", isDark ? "text-zinc-500" : "text-gray-500")}>
                              {formatSeconds(moment.start_time_seconds)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={cn("text-[10px] px-1.5 py-0.5 rounded", isDark ? "bg-zinc-800 text-zinc-300" : "bg-gray-200 text-gray-700")}>
                              {moment.category}
                            </span>
                            {moment.impact_level && (
                              <span className={cn("text-[10px] px-1.5 py-0.5 rounded", isDark ? "bg-blue-500/20 text-blue-300" : "bg-blue-100 text-blue-700")}>
                                {moment.impact_level}
                              </span>
                            )}
                          </div>
                          <p className={cn("text-[11px] mt-1 line-clamp-2", isDark ? "text-zinc-400" : "text-gray-600")}>
                            {moment.justification}
                          </p>
                        </button>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : activeFeatureId ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-gray-900")}>
                {toptabs.find((t) => t.id === activeFeatureId)?.label}
              </h2>
              <span className={cn("text-xs", isDark ? "text-zinc-400" : "text-gray-500")}>
                {(contentFeatureStatus[activeFeatureId]?.status || "not_started").toUpperCase()}
              </span>
            </div>
            {renderFeatureContent()}
          </div>
        ) : (
          /* Original Video Chat View */
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Left & Center */}
            <div className="lg:col-span-3 space-y-6">

              {/* Video Player */}
              <Card className={cn("overflow-hidden", isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <div
                  className="aspect-video bg-black relative group cursor-pointer"
                  onClick={() => setIsVideoModalOpen(true)}
                >
                  <img
                    src={dynamicThumbnail}
                    alt={`${currentProject.name} thumbnail`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to placeholder if thumbnail fails
                      const target = e.target as HTMLImageElement
                      target.src = "/images/design-mode/Screenshot%202025-05-08%20133020(1).png"
                    }}
                  />
                  {/* Hover play overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
                    <button className="p-3 rounded-full bg-white/20 hover:bg-white/30 text-white">
                      <Play className="h-6 w-6" />
                    </button>
                  </div>
                  {/* Controls bar */}
                  <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black via-black/50 to-transparent">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-xs text-zinc-400">09:18</span>
                      <div className="flex-1 h-1 bg-zinc-700 rounded-full overflow-hidden">
                        <div className="h-full w-1/3 bg-purple-600" />
                      </div>
                      <span className="text-xs text-zinc-400">{formatSeconds(videoDurationSeconds)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-1 hover:bg-white/10 rounded text-white">
                        <Play className="h-4 w-4" />
                      </button>
                      <button className="p-1 hover:bg-white/10 rounded text-white">
                        <Volume2 className="h-4 w-4" />
                      </button>
                      <button className="p-1 hover:bg-white/10 rounded text-white ml-auto">
                        <Settings2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Lower Tabs */}
              <div className={cn("flex items-center gap-6 px-0 border-b", isDark ? "border-zinc-800" : "border-gray-200")}>
                {/* Tabs removed */}
              </div>

              {/* Typography Content */}
              <div>
                {blogTitle && (
                  <h1 className={cn("scroll-m-20 text-4xl font-extrabold tracking-tight text-balance", isDark ? "text-white" : "text-gray-900")}>
                    {blogTitle}
                  </h1>
                )}

                <div className={cn("mt-6 max-w-3xl", isDark ? "text-zinc-300" : "text-gray-600")}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {blogBodyMarkdown}
                  </ReactMarkdown>
                </div>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="lg:col-span-2 space-y-6">

              {/* Summary Card */}
              <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <CardContent className="pt-6">
                  <h2 className={cn("text-sm font-semibold mb-3", isDark ? "text-white" : "text-gray-900")}>
                    {(projectOverview?.summary || insights.summary) && "Summary"}
                  </h2>
                  <p className={cn("text-sm leading-relaxed", isDark ? "text-zinc-300" : "text-gray-600")}>
                    {projectOverview?.summary || insights.summary}
                  </p>
                </CardContent>
              </Card>

              {/* Insights */}
              <div className="space-y-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>Insights</h3>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-gray-50")}>
                  <CardContent className="pt-6 space-y-6">

                    {overviewError && (
                      <div className={cn("text-xs", isDark ? "text-red-300" : "text-red-600")}>
                        {overviewError}
                      </div>
                    )}

                    {isOverviewLoading && !projectOverview && (
                      <div className={cn("text-xs", isDark ? "text-zinc-400" : "text-gray-500")}>
                        Loading overview...
                      </div>
                    )}

                    <div>
                      <h4 className={cn("text-sm font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>Situation</h4>
                      <p className={cn("text-xs leading-relaxed", isDark ? "text-zinc-300" : "text-gray-600")}>
                        {projectOverview?.insights?.situation || insights.situation}
                      </p>
                    </div>

                    <div>
                      <h4 className={cn("text-sm font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>Pain</h4>
                      <ul className="space-y-2">
                        {(projectOverview?.insights?.pain || insights.pain).map((item: string, idx: number) => (
                          <li key={idx} className={cn("text-xs flex gap-2", isDark ? "text-zinc-300" : "text-gray-600")}>
                            <span className={cn("flex-shrink-0", isDark ? "text-purple-400" : "text-purple-500")}>•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className={cn("text-sm font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>Impact</h4>
                      <ul className="space-y-2">
                        {(projectOverview?.insights?.impact || insights.impact).map((item: string, idx: number) => (
                          <li key={idx} className={cn("text-xs flex gap-2", isDark ? "text-zinc-300" : "text-gray-600")}>
                            <span className={cn("flex-shrink-0", isDark ? "text-purple-400" : "text-purple-500")}>•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className={cn("text-sm font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>Critical Event</h4>
                      <p className={cn("text-xs leading-relaxed", isDark ? "text-zinc-300" : "text-gray-600")}>
                        {projectOverview?.insights?.critical_event || insights.criticalEvent}
                      </p>
                    </div>

                    <div>
                      <h4 className={cn("text-sm font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>Decision</h4>
                      <p className={cn("text-xs leading-relaxed", isDark ? "text-zinc-300" : "text-gray-600")}>
                        {projectOverview?.insights?.decision || insights.decision}
                      </p>
                    </div>

                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}

        <FloatingVideoChat
          projectId={projectId}
          initialMessages={[
            {
              id: 1,
              content: "What were main pain points discussed in this meeting?",
              isUser: true,
            },
            {
              id: 2,
              content: "Disconnected tools, manual processes, and inconsistent follow-ups.",
              isUser: false,
            },
          ]}
        />

        {/* Video Player Modal */}
        <VideoPlayerModal
          open={isVideoModalOpen}
          onClose={() => setIsVideoModalOpen(false)}
          title={videoTitle}
          src={resolvedVideoLink}
          startAtSeconds={selectedMomentStartSeconds}
          onPlaybackTimeChange={(seconds) => setPlaybackTimeSeconds(seconds)}
          poster={dynamicThumbnail}
        />
          </>
        )}
      </div>
    </div>
  )
}

