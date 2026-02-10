"use client"

import { Search } from "lucide-react"
import { useState, useRef, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

interface ApiProject {
  id: number
  user_id: number
  name: string
  category?: string | null
  description?: string | null
  video_url?: string | null
  video_id?: number | null
  priority?: string | null
  progress: number
  status: string
  job_id?: string | null
  analysis_file_path?: string | null
  gemini_file_uri?: string | null
  start_date?: string | null
  end_date?: string | null
  created_at: string
  updated_at: string
}

interface Chat {
  id: string
  name: string
  platform?: string
  updatedAt: string
}

// Platform icons definition
const platformIcons: Record<string, React.FC<{ className?: string }>> = {
  Facebook: () => (
    <div className="w-4 h-4 rounded-full bg-[#1877F2] flex items-center justify-center flex-shrink-0">
      <svg className="w-2.5 h-2.5" viewBox="0 0 24 24" fill="white">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
      </svg>
    </div>
  ),
  Instagram: () => (
    <div className="w-4 h-4 rounded-lg bg-gradient-to-tr from-[#FCAF45] via-[#E1306C] to-[#833AB4] flex items-center justify-center flex-shrink-0">
      <svg className="w-2.5 h-2.5" viewBox="0 0 24 24" fill="white">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
      </svg>
    </div>
  ),
  Youtube: () => (
    <div className="w-4 h-4 rounded bg-[#FF0000] flex items-center justify-center flex-shrink-0">
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="white">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
      </svg>
    </div>
  ),
}

// ChatRow component - exact copy from "My Chats Section"
function ChatRow({ chat, index }: { chat: any; index: number }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const PlatformIcon = chat.platform ? platformIcons[chat.platform] : null

  return (
    <div className="group hover:bg-gray-50 dark:hover:bg-[#2F2F37]/50 transition-colors">
      <div className="px-6 py-3 flex items-center justify-between gap-4">
        {/* Left - Chat Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {chat.name}
          </h3>
        </div>
        {/* PlatformIcon */}
        <div className="w-24 flex justify-center flex-shrink-0">
          {PlatformIcon ? <PlatformIcon /> : <div className="w-4" />}
        </div>

        {/* Right - Platform, Time, Status, Menu */}
        <div className="flex items-center gap-3 flex-shrink-0">

          {/* Time */}
          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
            {chat.updatedAt}
          </span>

          {/* Status Dot */}
          <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"></div>

          {/* Three Dots Menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 hover:bg-gray-200 dark:hover:bg-[#2F2F37] rounded-lg transition-colors"
            >
              <div className="flex items-center gap-0.5">
                <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-gray-400"></div>
                <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-gray-400"></div>
                <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-gray-400"></div>
              </div>
            </button>

            {/* Dropdown Menu */}
            {isMenuOpen && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2F2F37] rounded-lg shadow-lg shadow-black/10 dark:shadow-black/30 py-1 z-50">
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#2F2F37] transition-colors">
                  Share
                </button>
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#2F2F37] transition-colors">
                  Move...
                </button>
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#2F2F37] transition-colors">
                  Add to Favorites
                </button>
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#2F2F37] transition-colors">
                  Rename
                </button>
                <div className="border-t border-gray-200 dark:border-[#2F2F37] my-1"></div>
                <button className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-[#2F2F37] transition-colors">
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LibraryPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const filterRef = useRef<HTMLDivElement>(null)
  const [chats, setChats] = useState<Chat[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const formatTimeAgo = useCallback((dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) {
      return `${diffDays}d ago`
    } else if (diffHours > 0) {
      return `${diffHours}h ago`
    } else {
      return "Just now"
    }
  }, [])

  const normalizeCategory = useCallback((category?: string | null) => {
    const c = (category || "").toLowerCase()
    if (c === "youtube") return "Youtube"
    if (c === "facebook") return "Facebook"
    if (c === "instagram") return "Instagram"
    if (c === "tiktok") return "Tiktok"
    return category || "Youtube"
  }, [])

  const loadProjects = useCallback(async () => {
    try {
      setIsLoading(true)
      const res = await fetch(`${API_BASE_URL}/api/projects?limit=100`, {
        cache: "no-store",
      })
      if (!res.ok) {
        console.error("Failed to load projects:", res.status, res.statusText)
        setChats([])
        return
      }
      const data = (await res.json()) as ApiProject[]
      const mapped: Chat[] = (data || []).map((p) => ({
        id: String(p.id),
        name: p.name,
        platform: normalizeCategory(p.category),
        updatedAt: formatTimeAgo(p.updated_at),
      }))
      setChats(mapped)
    } catch (e) {
      console.error("Failed to load projects:", e)
      setChats([])
    } finally {
      setIsLoading(false)
    }
  }, [formatTimeAgo, normalizeCategory])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  useEffect(() => {
    const onFocus = () => loadProjects()
    const onVisibility = () => {
      if (document.visibilityState === "visible") loadProjects()
    }
    window.addEventListener("focus", onFocus)
    document.addEventListener("visibilitychange", onVisibility)
    return () => {
      window.removeEventListener("focus", onFocus)
      window.removeEventListener("visibilitychange", onVisibility)
    }
  }, [loadProjects])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setIsFilterOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const filteredChats = chats.filter((chat) =>
    chat.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (chat.platform && chat.platform.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="min-h-screen bg-black dark:bg-[#0F0F12] text-white">
        {/* Header */}
        <div className="px-6 py-6 border-b border-gray-800 dark:border-[#2F2F37]">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-semibold text-zinc-900 dark:text-white">
                Library
              </h1>
              <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-300">
                {isLoading ? "Loading..." : chats.length}
              </span>
            </div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Search through the comprehensive directory of Projects
            </p>
          </div>

          {/* Search Bar and Sorting */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-400 dark:text-zinc-600" />
              <input
                type="text"
                placeholder="Search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={cn(
                  "w-full pl-9 pr-4 py-2 text-sm",
                  "rounded-lg",
                  "border border-zinc-200 dark:border-zinc-800",
                  "bg-white dark:bg-zinc-900/70",
                  "text-zinc-900 dark:text-white",
                  "placeholder-zinc-500 dark:placeholder-zinc-400",
                  "focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600",
                  "transition-all duration-200"
                )}
              />
            </div>
            <button className="px-3 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
              ⚙️ Filter
            </button>
          </div>
        </div>

        {/* Chat List */}
        <div>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="px-6 py-3 flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="w-3/4 h-4 bg-gray-700 rounded animate-pulse"></div>
                  </div>
                  <div className="w-24 flex justify-center">
                    <div className="w-4 h-4 bg-gray-700 rounded animate-pulse"></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-3 bg-gray-700 rounded animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-700 rounded-full animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            filteredChats.map((chat, index) => (
              <ChatRow key={chat.id} chat={chat} index={index} />
            ))
          )}
        </div>

        {/* Empty State */}
        {filteredChats.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-[#1F1F23] flex items-center justify-center mb-4">
              <Search className="w-8 h-8 text-gray-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-300 mb-1">No chats found</h3>
            <p className="text-sm text-gray-500">Try adjusting your search query</p>
          </div>
        )}
      </div>
  )
}
