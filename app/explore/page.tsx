"use client"

import React, { useState } from "react"
import Masonry from "react-masonry-css"
import { Grid3x3, Plus, Edit, MoreVertical } from "lucide-react"
import { cn } from "@/lib/utils"

// Platform filter buttons
const platformFilters = [
  "Saved",
  "Planned",
  "Published",
  "All Platforms",
  "Instagram",
  "Facebook",
  "Youtube",
  "LinkedIn",
  "TikTok",
]

// Collection cards data
const collections = [
  { title: "Facebook Collection", date: "Jan 2025", thumbnail: "/api/placeholder/100/100" },
  { title: "Instagram Collection", date: "Jan 2025", thumbnail: "/api/placeholder/100/100" },
  { title: "LinkedIn Collection", date: "Jan 2025", thumbnail: "/api/placeholder/100/100" },
  { title: "TikTok Collection", date: "Jan 2025", thumbnail: "/api/placeholder/100/100" },
]

// Post content data
const posts = [
  {
    id: 1,
    platform: "Facebook",
    platformIcon: "📘",
    type: "Post",
    title: "Emerging Trends in Pilates",
    description: "Big changes start with small, intentional steps. At Kately Mann Nutrition, we're here to help you take control of you Bi...",
    image: "/api/placeholder/400/450",
    hasOverlay: true,
    overlayBadge: "PILATES UPDATE",
    overlayTitle: "Emerging Trends in Pilates for 2023 Fitness Goals",
    overlayText: "2023 is shaping up to be a pivotal year for Pilates, with an increasing focus on holistic wellness and community engagement. Innovations in online platforms are making classes more accessible and personalized than ever before.",
    bgColor: "bg-pink-200",
  },
  {
    id: 2,
    platform: "Instagram",
    platformIcon: "📷",
    type: "Post",
    title: "Stay Motivated and Feel Great",
    description: "Big changes start with small, intentional steps. At Kately Mann Nutrition, we're here to help you take control of you Bi...",
    image: null,
    content: {
      subtitle: "SHARE IN THE COMMENTS!",
      mainText: "WHAT'S YOUR FAVORITE WAY TO MOVE AND FEEL GREAT?",
    },
    bgColor: "bg-zinc-900",
    textWhite: true,
  },
  {
    id: 3,
    platform: "Facebook",
    platformIcon: "📘",
    type: "Post",
    title: "Never go a day without a 5 meal plan",
    description: "Big changes start with small, intentional steps. At Kately Mann Nutrition, we're here to help you take control of you Bi...",
    image: "/api/placeholder/400/450",
    hasOverlay: true,
    overlayTitle: "Breathe",
    overlayText: "Transform your body, elevate your spirit—wellness starts with a single breath.",
    bgColor: "bg-blue-200",
  },
  {
    id: 4,
    platform: "Facebook",
    platformIcon: "📘",
    type: "Post",
    title: "The North Coach",
    description: "Helping you succeed",
    image: "/api/placeholder/400/500",
    content: {
      mainText: "THE NORTH COACH",
      subtitle: "HELPING YOU SUCCEED",
    },
    bgColor: "bg-pink-100",
    textColor: "text-amber-900",
  },
  {
    id: 5,
    platform: "Instagram",
    platformIcon: "📷",
    type: "Post",
    title: "Myth vs Reality",
    description: "Pilates myths debunked",
    image: null,
    content: {
      badge: "East River Pilates",
      subtitle: "Pilates Myths vs. Facts",
      mainText: "Myth vs Reality",
      points: [
        { label: "MYTH", text: "Pilates is only for dancers and athletes.\nPilates will bulk up my muscles too much.\nYou need to be flexible to do Pilates." },
        { label: "Reality", text: "Pilates helps all.\nPilates improves flexibility for everyone!" },
      ],
    },
    bgColor: "bg-zinc-900",
    textWhite: true,
  },
  {
    id: 6,
    platform: "Facebook",
    platformIcon: "📘",
    type: "Post",
    title: "Business Coach Testimonial",
    description: "Jessica Miller testimonial",
    image: null,
    content: {
      badge: "BUSINESS COACH",
      quote: "Working with her has been a game changer for our business.",
      author: "JESSICA MILLER",
      authorImage: "/api/placeholder/120/120",
    },
    bgColor: "bg-zinc-900",
    textWhite: true,
  },
]

const breakpointColumns = {
  default: 3,
  1100: 3,
  700: 2,
  500: 1,
}

export default function Explore() {
  const [activeFilter, setActiveFilter] = useState("All Platforms")

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Explore</h1>
              <p className="text-zinc-400 text-sm">
                This is where your content lives. Discover what's ready to post, spark new ideas and keep your strategy moving forward.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
                <Grid3x3 className="w-4 h-4" />
                Action Hub
              </button>
              <button className="px-4 py-2 bg-white hover:bg-gray-100 text-black rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
                <Plus className="w-4 h-4" />
                Generate
              </button>
            </div>
          </div>
        </div>

        {/* Platform Filters */}
        <div className="mb-8 flex items-center gap-2 flex-wrap">
          {platformFilters.map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-all",
                activeFilter === filter
                  ? "bg-white text-black"
                  : "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
              )}
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Collections Scroll */}
        <div className="mb-8 overflow-x-auto pb-4 -mx-6 px-6">
          <div className="flex gap-4 min-w-max">
            {collections.map((collection, idx) => (
              <div
                key={idx}
                className="relative w-64 h-32 rounded-2xl overflow-hidden bg-zinc-800 border border-zinc-700 hover:border-zinc-600 transition-colors cursor-pointer group"
              >
                <div className="absolute inset-0 flex">
                  <div className="w-1/3 bg-zinc-700"></div>
                  <div className="w-1/3 bg-zinc-600"></div>
                  <div className="w-1/3 bg-zinc-500"></div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <h3 className="text-white font-semibold text-sm mb-1">
                    {collection.title}
                  </h3>
                  <p className="text-zinc-400 text-xs">{collection.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Masonry Grid */}
        <Masonry
          breakpointCols={breakpointColumns}
          className="flex -ml-6 w-auto"
          columnClassName="pl-6 bg-clip-padding"
        >
          {posts.map((post) => (
            <div key={post.id} className="mb-6">
              {/* Post Card */}
              <div className="rounded-2xl overflow-hidden bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all">
                
                {/* Image or Content Area */}
                {post.image ? (
                  <div className="relative">
                    <img
                      src={post.image}
                      alt={post.title}
                      className="w-full h-auto object-cover"
                    />
                    {post.hasOverlay && (
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-6">
                        <div className="w-full bg-white rounded-lg p-4">
                          {post.overlayBadge && (
                            <span className="inline-block px-2 py-1 bg-black text-white text-[10px] font-bold uppercase mb-2">
                              {post.overlayBadge}
                            </span>
                          )}
                          <h3 className="text-black font-bold text-lg mb-2">
                            {post.overlayTitle}
                          </h3>
                          {post.overlayText && (
                            <p className="text-zinc-700 text-xs leading-relaxed">
                              {post.overlayText}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className={cn("p-8 min-h-[400px] flex flex-col justify-center items-center", post.bgColor)}>
                    {post.content?.badge && (
                      <span className="inline-block px-3 py-1 bg-white text-black text-xs font-bold uppercase mb-4 rounded">
                        {post.content.badge}
                      </span>
                    )}
                    
                    {post.content?.subtitle && (
                      <p className={cn("text-xs font-semibold mb-4 tracking-wider", post.textWhite ? "text-white" : "text-zinc-700")}>
                        {post.content.subtitle}
                      </p>
                    )}
                    
                    {post.content?.mainText && (
                      <h2 className={cn(
                        "font-bold text-center mb-6",
                        post.id === 2 ? "text-4xl" : "text-5xl",
                        post.textWhite ? "text-white" : post.textColor || "text-amber-900"
                      )}>
                        {post.content.mainText}
                      </h2>
                    )}

                    {post.id === 2 && (
                      <div className="w-16 h-1 bg-white rounded-full"></div>
                    )}

                    {post.content?.points && (
                      <div className="w-full space-y-4 mt-4">
                        {post.content.points.map((point, idx) => (
                          <div key={idx} className="space-y-2">
                            <span className="inline-block px-3 py-1 border border-zinc-600 rounded-full text-xs text-white">
                              {point.label}
                            </span>
                            <p className="text-white text-sm leading-relaxed whitespace-pre-line">
                              {point.text}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}

                    {post.content?.quote && (
                      <div className="text-center">
                        <p className="text-3xl font-serif text-white mb-8 leading-relaxed">
                          "{post.content.quote}"
                        </p>
                        {post.content.authorImage && (
                          <div className="flex flex-col items-center">
                            <div className="w-24 h-24 rounded-full overflow-hidden mb-4 border-4 border-white">
                              <img src={post.content.authorImage} alt={post.content.author} className="w-full h-full object-cover" />
                            </div>
                            <p className="text-white font-bold text-sm tracking-wider">
                              {post.content.author}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {post.content?.authorImage && post.id === 4 && (
                      <div className="mt-6">
                        <img src="/api/placeholder/300/300" alt="Coach" className="w-full rounded-lg" />
                      </div>
                    )}
                  </div>
                )}

                {/* Post Meta Information */}
                <div className="p-4 bg-zinc-900">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{post.platformIcon}</span>
                    <span className="text-sm font-medium text-white">{post.platform}</span>
                    <span className="text-zinc-600">•</span>
                    <span className="text-sm text-zinc-400">{post.type}</span>
                  </div>
                  
                  <h3 className="font-semibold text-white mb-1">{post.title}</h3>
                  <p className="text-sm text-zinc-400 line-clamp-2 mb-4">
                    {post.description}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    <button className="flex-1 px-4 py-2 bg-white hover:bg-gray-100 text-black rounded-lg text-sm font-medium transition-colors">
                      Smart Schedule
                    </button>
                    <button className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg text-sm font-medium transition-colors">
                      Post Now
                    </button>
                    <button className="p-2 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg transition-colors">
                      <Edit className="w-4 h-4" />
                    </button>
                    <button className="p-2 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg transition-colors">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Masonry>
      </div>

      <style jsx global>{`
        .masonry-grid {
          display: flex;
          margin-left: -24px;
          width: auto;
        }
        .masonry-grid_column {
          padding-left: 24px;
          background-clip: padding-box;
        }
      `}</style>
    </div>
  )
}
