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
  Scissors,
  Megaphone,
  Cpu,
  Play,
  Volume2,
  Clock,
  Users,
  Settings2,
  Calendar,
  Sun,
  Moon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import VideoAnalytics from "@/components/xen/streamline/statistics-components/video-analytics"
import FloatingVideoChat from "@/components/xen/floating-chat-bar"
import ChatMessage from "@/components/xen/chat/chatmassegeui"
import ChatInput from "@/components/xen/chat/chatinputui"
import EmotionalIntensityGraph from "@/components/xen/streamline/statistics-components/emotional-anal"
import VideoPlayerModal from "@/components/xen/streamline/video-player-modal"

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

const toptabs = [
  { id: "overview", label: "Video Overview", icon: MessageCircle },
  { id: "statistics", label: "Statistics", icon: Search },
  { id: "transcription", label: "Video Transcription", icon: FileText },
  { id: "editor", label: "Video Editor", icon: Scissors },
  { id: "marketer", label: "Video Marketer", icon: Megaphone, badge: "Agent" },
  { id: "hardware", label: "AI Hardware", icon: Cpu, badge: "Agent" },
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
  const [dynamicThumbnail, setDynamicThumbnail] = useState<string>(
    getThumbnailUrl(forwardedVideoUrl || currentProject.videoLink) || currentProject.thumbnail
  )
  const [videoTitle, setVideoTitle] = useState<string>("GreenLeaf // Basepoint")
  const [projectCreatedDate, setProjectCreatedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [isProjectLoading, setIsProjectLoading] = useState<boolean>(!!projectId)

  // Update dynamic thumbnail when video link changes
  useEffect(() => {
    const newThumbnail = getThumbnailUrl(resolvedVideoLink) || currentProject.thumbnail
    setDynamicThumbnail(newThumbnail)
  }, [resolvedVideoLink])

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
      
      if (!videoId) return "GreenLeaf // Basepoint"
      
      // Use YouTube oEmbed API to get video title
      const oEmbedUrl = `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`
      const response = await fetch(oEmbedUrl)
      
      if (response.ok) {
        const data = await response.json()
        return data.title || "GreenLeaf // Basepoint"
      }
    } catch (error) {
      console.error('Error fetching YouTube title:', error)
    }
    
    return "GreenLeaf // Basepoint"
  }

  // Update video title when video link changes
  useEffect(() => {
    const updateTitle = async () => {
      if (resolvedVideoLink && resolvedVideoLink !== currentProject.videoLink) {
        const title = await fetchYouTubeTitle(resolvedVideoLink)
        setVideoTitle(title)
      }
    }
    
    updateTitle()
  }, [resolvedVideoLink])

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
        const nextUrl = typeof p?.video_url === "string" && p.video_url.length > 0
          ? p.video_url
          : (forwardedVideoUrl || currentProject.videoLink)
        setResolvedVideoLink(nextUrl)
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
  const [editorMessages, setEditorMessages] = useState([
    { id: 1, content: "Hi! I'm your AI video editor assistant. How can I help you edit this video today?", isUser: false },
  ])

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
                    Video
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
            <VideoAnalytics />
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
                      <span className="text-xs text-zinc-400">28:14</span>
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

        {activeTopTab !== "editor" && (
          <FloatingVideoChat
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
        )}

        {/* Video Player Modal */}
        <VideoPlayerModal
          open={isVideoModalOpen}
          onClose={() => setIsVideoModalOpen(false)}
          title={currentProject.name}
          src={resolvedVideoLink}
          poster={dynamicThumbnail}
        />
          </>
        )}
      </div>
    </div>
  )
}
