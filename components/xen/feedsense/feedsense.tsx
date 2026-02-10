"use client"

import React from "react"
import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  MessageCircle,
  FileText,
  Search,
  Scissors,
  Megaphone,
  Cpu,
  Calendar,
  Clock,
  Sun,
  Moon,
  Heart,
  Share2,
  MessageSquare,
  Eye,
  TrendingUp,
  Users,
  Hash,
  AtSign,
} from "lucide-react"
import { cn } from "@/lib/utils"
import FloatingVideoChat from "@/components/xen/floating-chat-bar"

const toptabs = [
  { id: "overview", label: "Post Overview", icon: MessageCircle },
  { id: "analytics", label: "Analytics", icon: Search },
  { id: "comments", label: "Comments Analysis", icon: MessageSquare },
  { id: "editor", label: "Content Editor", icon: Scissors },
  { id: "optimizer", label: "AI Optimizer", icon: Megaphone, badge: "Agent" },
  { id: "insights", label: "Audience Insights", icon: Cpu, badge: "Agent" },
]

const currentPost = {
  platform: "LinkedIn",
  platformIcon: "💼",
  author: "Sarah Chen",
  authorTitle: "Product Marketing Manager",
  postedDate: "2024-02-05",
  postedTime: "14:32",
  content: `🚀 Excited to share that our team just launched the new sustainability dashboard!

After 6 months of research and development, we're helping companies track their carbon footprint in real-time. The response from our beta users has been incredible - 40% reduction in manual reporting time.

Big shoutout to the engineering team for making this happen. What sustainability metrics do you track at your company?

#SustainabilityTech #ProductLaunch #ClimateAction`,
  metrics: {
    impressions: "2,847",
    engagements: "342",
    engagementRate: "12.0%",
    shares: "89",
    comments: "47",
    likes: "206",
  },
  thumbnail: "/images/design-mode/post-preview.png"
}

const insights = {
  summary:
    "Sarah Chen announced the launch of a sustainability dashboard product, highlighting 6 months of development and strong beta user results. The post uses authentic storytelling, team recognition, and audience engagement tactics to maximize reach within the B2B sustainability tech space.",
  contentCharacteristics: {
    tone: "Professional, Authentic, Celebratory",
    contentType: "Product Launch Announcement",
    engagementStrategy: "Question CTA + Team Mention",
    sentimentScore: 78,
    wordCount: 87,
    readingTime: "30 sec"
  },
  performanceAnalysis: [
    "Engagement rate 3.2x above account average, driven by authentic storytelling and specific metrics",
    "Question CTA generated 47 comments with high-quality responses from target audience",
    "Hashtag strategy reached 1,200+ users in sustainability tech community",
    "Team mention drove internal sharing, expanding reach by 40%"
  ],
  recommendations: [
    "Post performed well 2-4pm EST - replicate timing for similar content",
    "Consider follow-up post with customer testimonials to maintain momentum",
    "Emoji usage (rocket) correlated with 22% higher engagement",
    "Question format generated quality discussions - use in future posts"
  ],
  contentTags: ["Product Launch", "B2B", "Sustainability", "Team Culture", "Engagement"]
}

export default function PostAnalysis() {
  const [isDark, setIsDark] = useState(true)
  const [activeTopTab, setActiveTopTab] = useState("overview")

  return (
    <div className={cn("min-h-screen py-6 px-4")}>
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="mb-8 space-y-4">
          {activeTopTab === "overview" ? (
            <>
              <div className="flex items-center justify-between">
                <h1 className={cn("text-2xl font-bold", isDark ? "text-white" : "text-gray-900")}>
                  LinkedIn Post // Campaign Q1
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
                </div>
              </div>

              <div className={cn("flex items-center gap-4 text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>{currentPost.postedDate}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <span>{currentPost.postedTime}</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <div className={cn(
                "flex items-center gap-4 px-4 py-3 rounded-xl",
                isDark ? "bg-zinc-900/50 border border-zinc-800" : "bg-white border border-gray-200"
              )}>
                {/* Post Preview Thumbnail */}
                <div className={cn(
                  "relative w-32 h-20 rounded-lg overflow-hidden flex-shrink-0",
                  isDark ? "bg-zinc-800" : "bg-gray-100"
                )}>
                  <div className="w-full h-full flex items-center justify-center text-3xl">
                    {currentPost.platformIcon}
                  </div>
                </div>

                {/* Post Info */}
                <div className="flex flex-col gap-1">
                  <h2 className={cn("text-base font-semibold", isDark ? "text-white" : "text-gray-900")}>
                    {currentPost.platform} Post
                  </h2>
                  <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-600")}>
                    by {currentPost.author} • {currentPost.postedDate}
                  </p>
                  <button
                    className={cn(
                      "text-xs text-left hover:underline w-fit",
                      isDark ? "text-zinc-500 hover:text-zinc-400" : "text-gray-500 hover:text-gray-600"
                    )}
                  >
                    View Original Post
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

        {/* Main Content - Overview Tab */}
        {activeTopTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Left & Center - Post Preview */}
            <div className="lg:col-span-3 space-y-6">

              {/* Post Display Card */}
              <Card className={cn("overflow-hidden", isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <CardContent className="p-6">
                  
                  {/* Post Header */}
                  <div className="flex items-center gap-3 mb-4 pb-4 border-b border-zinc-800">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-2xl flex-shrink-0">
                      {currentPost.platformIcon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className={cn("text-base font-semibold mb-0.5", isDark ? "text-white" : "text-gray-900")}>
                        {currentPost.author}
                      </h3>
                      <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                        {currentPost.authorTitle}
                      </p>
                      <p className={cn("text-xs mt-0.5", isDark ? "text-zinc-500" : "text-gray-400")}>
                        Posted on {currentPost.platform} • {currentPost.postedDate} • Public
                      </p>
                    </div>
                  </div>

                  {/* Post Content */}
                  <div className="space-y-4">
                    <div className={cn(
                      "rounded-lg p-5",
                      isDark ? "bg-zinc-950/50" : "bg-gray-50"
                    )}>
                      <p className={cn(
                        "text-sm leading-relaxed whitespace-pre-line",
                        isDark ? "text-zinc-200" : "text-gray-700"
                      )}>
                        {currentPost.content}
                      </p>
                    </div>

                    {/* Post Image Placeholder */}
                    <div className={cn(
                      "w-full h-64 rounded-lg flex items-center justify-center text-5xl",
                      isDark ? "bg-zinc-800" : "bg-gray-200"
                    )}>
                      📊
                    </div>
                  </div>

                </CardContent>
              </Card>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                  <CardContent className="pt-6 text-center">
                    <Eye className={cn("h-5 w-5 mx-auto mb-2", isDark ? "text-zinc-400" : "text-gray-400")} />
                    <div className={cn("text-2xl font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>
                      {currentPost.metrics.impressions}
                    </div>
                    <div className={cn("text-xs uppercase tracking-wider", isDark ? "text-zinc-500" : "text-gray-500")}>
                      Impressions
                    </div>
                  </CardContent>
                </Card>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                  <CardContent className="pt-6 text-center">
                    <TrendingUp className={cn("h-5 w-5 mx-auto mb-2", isDark ? "text-zinc-400" : "text-gray-400")} />
                    <div className={cn("text-2xl font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>
                      {currentPost.metrics.engagements}
                    </div>
                    <div className={cn("text-xs uppercase tracking-wider", isDark ? "text-zinc-500" : "text-gray-500")}>
                      Engagements
                    </div>
                  </CardContent>
                </Card>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                  <CardContent className="pt-6 text-center">
                    <Users className={cn("h-5 w-5 mx-auto mb-2", isDark ? "text-zinc-400" : "text-gray-400")} />
                    <div className={cn("text-2xl font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>
                      {currentPost.metrics.engagementRate}
                    </div>
                    <div className={cn("text-xs uppercase tracking-wider", isDark ? "text-zinc-500" : "text-gray-500")}>
                      Eng. Rate
                    </div>
                  </CardContent>
                </Card>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                  <CardContent className="pt-6 text-center">
                    <Share2 className={cn("h-5 w-5 mx-auto mb-2", isDark ? "text-zinc-400" : "text-gray-400")} />
                    <div className={cn("text-2xl font-bold mb-1", isDark ? "text-white" : "text-gray-900")}>
                      {currentPost.metrics.shares}
                    </div>
                    <div className={cn("text-xs uppercase tracking-wider", isDark ? "text-zinc-500" : "text-gray-500")}>
                      Shares
                    </div>
                  </CardContent>
                </Card>
              </div>

            </div>

            {/* Right Sidebar - Insights */}
            <div className="lg:col-span-2 space-y-6">

              {/* Summary Card */}
              <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-white")}>
                <CardContent className="pt-6">
                  <h2 className={cn("text-sm font-semibold mb-3", isDark ? "text-white" : "text-gray-900")}>
                    Summary
                  </h2>
                  <p className={cn("text-sm leading-relaxed", isDark ? "text-zinc-300" : "text-gray-600")}>
                    {insights.summary}
                  </p>
                </CardContent>
              </Card>

              {/* Content Insights */}
              <div className="space-y-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                  Content Insights
                </h3>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-gray-50")}>
                  <CardContent className="pt-6 space-y-6">

                    <div>
                      <h4 className={cn("text-xs font-semibold mb-2 uppercase tracking-wider", isDark ? "text-zinc-400" : "text-gray-500")}>
                        Tone & Voice
                      </h4>
                      <p className={cn("text-sm", isDark ? "text-white" : "text-gray-900")}>
                        {insights.contentCharacteristics.tone}
                      </p>
                    </div>

                    <div>
                      <h4 className={cn("text-xs font-semibold mb-2 uppercase tracking-wider", isDark ? "text-zinc-400" : "text-gray-500")}>
                        Content Type
                      </h4>
                      <p className={cn("text-sm", isDark ? "text-white" : "text-gray-900")}>
                        {insights.contentCharacteristics.contentType}
                      </p>
                    </div>

                    <div>
                      <h4 className={cn("text-xs font-semibold mb-2 uppercase tracking-wider", isDark ? "text-zinc-400" : "text-gray-500")}>
                        Engagement Strategy
                      </h4>
                      <p className={cn("text-sm", isDark ? "text-white" : "text-gray-900")}>
                        {insights.contentCharacteristics.engagementStrategy}
                      </p>
                    </div>

                    <div>
                      <h4 className={cn("text-xs font-semibold mb-2 uppercase tracking-wider", isDark ? "text-zinc-400" : "text-gray-500")}>
                        Sentiment Score
                      </h4>
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <div className={cn("h-2 rounded-full overflow-hidden", isDark ? "bg-zinc-800" : "bg-gray-200")}>
                            <div 
                              className="h-full bg-gradient-to-r from-purple-600 to-pink-600 rounded-full"
                              style={{ width: `${insights.contentCharacteristics.sentimentScore}%` }}
                            />
                          </div>
                        </div>
                        <span className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                          {insights.contentCharacteristics.sentimentScore}%
                        </span>
                      </div>
                    </div>

                  </CardContent>
                </Card>
              </div>

              {/* Performance Analysis */}
              <div className="space-y-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                  Performance Analysis
                </h3>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-gray-50")}>
                  <CardContent className="pt-6">
                    <ul className="space-y-3">
                      {insights.performanceAnalysis.map((item, idx) => (
                        <li key={idx} className={cn("text-xs flex gap-2", isDark ? "text-zinc-300" : "text-gray-600")}>
                          <span className={cn("flex-shrink-0 mt-1", isDark ? "text-purple-400" : "text-purple-500")}>•</span>
                          <span className="leading-relaxed">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* Recommendations */}
              <div className="space-y-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                  Recommendations
                </h3>

                <Card className={cn(isDark ? "border-zinc-800 bg-zinc-900/50" : "border-gray-200 bg-gray-50")}>
                  <CardContent className="pt-6">
                    <ul className="space-y-3">
                      {insights.recommendations.map((item, idx) => (
                        <li key={idx} className={cn("text-xs flex gap-2", isDark ? "text-zinc-300" : "text-gray-600")}>
                          <span className={cn("flex-shrink-0 mt-1", isDark ? "text-purple-400" : "text-purple-500")}>•</span>
                          <span className="leading-relaxed">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* Content Tags */}
              <div className="space-y-4">
                <h3 className={cn("text-sm font-semibold", isDark ? "text-white" : "text-gray-900")}>
                  Content Tags
                </h3>

                <div className="flex flex-wrap gap-2">
                  {insights.contentTags.map((tag, idx) => (
                    <span
                      key={idx}
                      className={cn(
                        "px-3 py-1.5 rounded-md text-xs font-medium",
                        isDark 
                          ? "bg-zinc-800 text-zinc-300 border border-zinc-700" 
                          : "bg-gray-100 text-gray-700 border border-gray-200"
                      )}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Analytics Tab Placeholder */}
        {activeTopTab === "analytics" && (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <Search className={cn("h-12 w-12 mx-auto mb-4", isDark ? "text-zinc-600" : "text-gray-300")} />
              <h3 className={cn("text-lg font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>
                Analytics Coming Soon
              </h3>
              <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                Detailed analytics and performance metrics will be available here
              </p>
            </div>
          </div>
        )}

        {/* Other Tabs Placeholders */}
        {(activeTopTab === "comments" || activeTopTab === "editor" || activeTopTab === "optimizer" || activeTopTab === "insights") && (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className={cn("text-6xl mb-4")}>
                {activeTopTab === "comments" && "💬"}
                {activeTopTab === "editor" && "✂️"}
                {activeTopTab === "optimizer" && "📣"}
                {activeTopTab === "insights" && "🎯"}
              </div>
              <h3 className={cn("text-lg font-semibold mb-2", isDark ? "text-white" : "text-gray-900")}>
                {activeTopTab === "comments" && "Comments Analysis"}
                {activeTopTab === "editor" && "Content Editor"}
                {activeTopTab === "optimizer" && "AI Optimizer"}
                {activeTopTab === "insights" && "Audience Insights"}
              </h3>
              <p className={cn("text-sm", isDark ? "text-zinc-400" : "text-gray-500")}>
                This feature is coming soon
              </p>
            </div>
          </div>
        )}

      </div>

      {activeTopTab === "overview" && (
        <FloatingVideoChat
          initialMessages={[
            {
              id: 1,
              text: "What made this post perform so well?",
              isUser: true,
            },
            {
              id: 2,
              text: "The combination of authentic storytelling, specific metrics (40% reduction), team recognition, and a question CTA drove 3.2x higher engagement than average.",
              isUser: false,
            },
          ]}
        />
      )}
    </div>
  )
}