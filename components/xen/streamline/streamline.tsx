"use client"

import React from "react"
import { useState, useEffect } from "react"
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

const Skeleton = ({ className }: { className?: string }) => {
  return <div className={cn("animate-pulse rounded-md", className)} />
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

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
  thumbnail: "/images/design-mode/Screenshot%202025-05-08%20133020(1).png"
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
  const [isProjectLoading, setIsProjectLoading] = useState<boolean>(!!projectId)

  const [projectOverview, setProjectOverview] = useState<ProjectOverview | null>(null)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [isOverviewLoading, setIsOverviewLoading] = useState<boolean>(false)

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

  const [isDark, setIsDark] = useState(true)
  const [activeTab, setActiveTab] = useState("transcript")
  const [activeTopTab, setActiveTopTab] = useState("overview")
  const [editorMessages, setEditorMessages] = useState([
    { id: 1, content: "Hi! I'm your AI video editor assistant. How can I help you edit this video today?", isUser: false },
  ])

  const placeholderMarkdown = `# Taxing Laughter: The Joke Tax Chronicles\n\nOnce upon a time, in a far-off land, there was a very lazy king who spent all day lounging on his throne. One day, his advisors came to him with a problem: the kingdom was running out of money.\n\n## The King's Plan\n\nThe king thought long and hard, and finally came up with a brilliant plan: he would tax the jokes in the kingdom.\n\n> "After all," he said, "everyone enjoys a good joke, so it's only fair that they should pay for the privilege."\n\n### The Joke Tax\n\nThe king's subjects were not amused. They grumbled and complained, but the king was firm:\n\n- 1st level of puns: 5 gold coins\n- 2nd level of jokes: 10 gold coins\n- 3rd level of one-liners : 20 gold coins\n\nAs a result, people stopped telling jokes, and the kingdom fell into a gloom. But there was one person who refused to let the king's foolishness get him down: a court jester named Jokester.\n\n### Jokester's Revolt\n\nJokester began sneaking into the castle in the middle of the night and leaving jokes all over the place: under the king's pillow, in his soup, even in the royal toilet. The king was furious, but he couldn't seem to stop Jokester.\n\nAnd then, one day, the people of the kingdom discovered that the jokes left by Jokester were so funny that they couldn't help but laugh. And once they started laughing, they couldn't stop.\n`

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
                      GreenLeaf // Basepoint
                    </h1>

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
          </>
        )}
      </div>
    </div>
  )
}