"use client"

import React, { useState, useEffect, useCallback, useMemo } from "react"

import {
  LayoutDashboard,
  FolderOpen,
  Link2,
  MessageSquare,
  Settings,
  HelpCircle,
  Search,
  Plus,
  ChevronDown,
  Clock,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react"

import Link from "next/link"
import Image from "next/image"
import { useSidebarContext } from "./layout"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

interface ApiRecentChat {
  id: number
  project_id: number
  project_name: string
  project_category?: string | null
  name: string
  platform?: string | null
  updated_at: string
  last_message_at?: string | null
}

interface RecentChat {
  id: string
  heading: string
  projectName: string
  platform: string
  updatedAt: string
}

export default function Sidebar() {
  const [isRecentsOpen, setIsRecentsOpen] = useState(true)
  const { isSidebarExpanded, setIsSidebarExpanded } = useSidebarContext()
  const [recentChats, setRecentChats] = useState<RecentChat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")

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

  const loadRecentChats = useCallback(async () => {
    try {
      setIsLoading(true)
      const res = await fetch(`${API_BASE_URL}/api/recent-chats?limit=8`, {
        cache: "no-store",
      })
      if (!res.ok) {
        console.error("Failed to load recent chats:", res.status, res.statusText)
        setRecentChats([])
        return
      }
      const data = (await res.json()) as ApiRecentChat[]
      const mapped: RecentChat[] = (data || []).map((c) => ({
        id: String(c.id),
        heading: c.name,
        projectName: c.project_name,
        platform: normalizeCategory(c.project_category),
        updatedAt: formatTimeAgo(c.last_message_at || c.updated_at),
      }))
      setRecentChats(mapped)
    } catch (e) {
      console.error("Failed to load recent chats:", e)
      setRecentChats([])
    } finally {
      setIsLoading(false)
    }
  }, [formatTimeAgo, normalizeCategory])

  const filteredRecentChats = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) return recentChats
    return recentChats.filter(
      (c) =>
        c.heading.toLowerCase().includes(query) ||
        c.projectName.toLowerCase().includes(query) ||
        c.platform.toLowerCase().includes(query)
    )
  }, [recentChats, searchQuery])

  useEffect(() => {
    loadRecentChats()
  }, [loadRecentChats])

  useEffect(() => {
    const onFocus = () => loadRecentChats()
    const onVisibility = () => {
      if (document.visibilityState === "visible") loadRecentChats()
    }
    window.addEventListener("focus", onFocus)
    document.addEventListener("visibilitychange", onVisibility)
    return () => {
      window.removeEventListener("focus", onFocus)
      document.removeEventListener("visibilitychange", onVisibility)
    }
  }, [loadRecentChats])

  function NavItem({
    href,
    icon: Icon,
    children,
    badge,
  }: {
    href: string
    icon: any
    children: React.ReactNode
    badge?: string
  }) {
    return (
      <Link
        href={href}
        className={`group flex items-center gap-1 rounded-lg transition-all duration-200 ${
          isSidebarExpanded 
            ? "px-2 py-2 hover:bg-white/5" 
            : "px-2 py-2 justify-center hover:bg-white/5"
        }`}
      >
        <Icon className="h-3 w-3 text-zinc-400 group-hover:text-white transition-colors" />
        {isSidebarExpanded && (
          <span className="text-xs font-medium text-zinc-300 group-hover:text-white transition-colors flex-1">
            {children}
          </span>
        )}
        {isSidebarExpanded && badge && (
          <span className="px-1 py-0.5 text-[10px] font-semibold bg-zinc-800 text-zinc-300 rounded-full">
            {badge}
          </span>
        )}
      </Link>
    )
  }

  function RecentChatItem({ chat }: { chat: typeof recentChats[0] }) {
    return (
      <Link
        href={`/chat?chatId=${encodeURIComponent(chat.id)}`}
        className={`group flex items-center gap-2 rounded-lg transition-all duration-200 ${
          isSidebarExpanded 
            ? "px-2 py-1.5 hover:bg-white/5" 
            : "px-2 py-1.5 justify-center hover:bg-white/5"
        }`}
        title={chat.heading}
      >
        <div className="h-1 w-1 rounded-full bg-zinc-600 flex-shrink-0" />
        {isSidebarExpanded && (
          <div className="flex-1 min-w-0">
            <p className="text-xs text-zinc-400 group-hover:text-white truncate transition-colors">
              {chat.heading}
            </p>
            <p className="text-[10px] text-zinc-600 mt-0.5 truncate">
              {chat.projectName} • {chat.updatedAt}
            </p>
          </div>
        )}
      </Link>
    )
  }

  return (
    <aside
      className={`fixed left-0 top-0 bottom-0 bg-zinc-950 border-r border-zinc-800/50 transition-all duration-300 ease-in-out z-40 flex flex-col ${
        isSidebarExpanded ? "w-60" : "w-16"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-10 px-2 border-b border-zinc-800/50">
        {isSidebarExpanded ? (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-5 w-5 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-xs">SC</span>
            </div>
            <div>
              <h2 className="text-xs font-semibold text-white">SocialCraft</h2>
              <p className="text-[10px] text-zinc-500">Dashboard</p>
            </div>
          </Link>
        ) : (
          <div className="h-5 w-5 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto">
            <span className="text-white font-bold text-xs">SC</span>
          </div>
        )}
        
        {isSidebarExpanded && (
          <button
            onClick={() => setIsSidebarExpanded(false)}
            className="p-1 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white"
          >
            <PanelLeftClose className="h-2.5 w-2.5" />
          </button>
        )}
      </div>

      {/* Search Bar */}
      {isSidebarExpanded && (
        <div className="px-3 py-2 border-b border-zinc-800/50">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-500" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-7 pr-2 py-1 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-300 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            />
          </div>
        </div>
      )}

      {/* Expand Button (collapsed state) */}
      {!isSidebarExpanded && (
        <div className="px-3 py-2 border-b border-zinc-800/50">
          <button
            onClick={() => setIsSidebarExpanded(true)}
            className="w-full p-1.5 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white"
          >
            <PanelLeft className="h-3.5 w-3.5 mx-auto" />
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-2">
        <div className="px-1.5 space-y-3">
          {/* Main Navigation */}
          <div className="space-y-1">
            {isSidebarExpanded && (
              <h3 className="px-2 mb-1 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
                Main Menu
              </h3>
            )}
            <NavItem href="/dashboard" icon={LayoutDashboard}>
              Dashboard
            </NavItem>
            <NavItem href="/library" icon={FolderOpen}>
              Library
            </NavItem>
            <NavItem href="/project" icon={MessageSquare} badge="3">
              Projects
            </NavItem>
            <NavItem href="/connections" icon={Link2}>
              Connections
            </NavItem>
          </div>

          {/* Recents Section */}
          <div className="space-y-1">
            {isSidebarExpanded ? (
              <button
                onClick={() => setIsRecentsOpen(!isRecentsOpen)}
                className="w-full flex items-center justify-between px-2 mb-1 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider hover:text-zinc-400 transition-colors"
              >
                <span className="flex items-center gap-1.5">
                  <Clock className="h-2.5 w-2.5" />
                  Recent
                </span>
                <ChevronDown
                  className={`h-3 w-3 transition-transform duration-200 ${
                    !isRecentsOpen ? "-rotate-90" : ""
                  }`}
                />
              </button>
            ) : (
              <div className="px-2 mb-1">
                <Clock className="h-3 w-3 text-zinc-500 mx-auto" />
              </div>
            )}

            {isRecentsOpen && (
              <div className="space-y-0.5">
                {isLoading ? (
                  <>
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="px-2 py-1">
                        <div className="h-2.5 bg-zinc-800/50 rounded animate-pulse"></div>
                      </div>
                    ))}
                  </>
                ) : filteredRecentChats.length > 0 ? (
                  filteredRecentChats.map((chat) => (
                    <RecentChatItem key={chat.id} chat={chat} />
                  ))
                ) : (
                  isSidebarExpanded && (
                    <p className="px-2 py-1 text-[10px] text-zinc-600">No recent chats</p>
                  )
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Project Button */}
      {isSidebarExpanded && (
        <div className="px-3 py-2 border-t border-zinc-800/50">
          <button className="w-full flex items-center justify-center gap-1 px-2 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg font-medium text-xs transition-all shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30">
            <Plus className="h-3 w-3" />
            New Project
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="px-2 py-1.5 border-t border-zinc-800/50 space-y-1">
        <NavItem href="#" icon={Settings}>
          Settings
        </NavItem>
        <NavItem href="#" icon={HelpCircle}>
          Help & Support
        </NavItem>
      </div>

      {/* User Profile */}
      {isSidebarExpanded && (
        <div className="px-3 py-2 border-t border-zinc-800/50">
          <div className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-zinc-800/50 transition-colors cursor-pointer">
            <div className="h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white font-semibold text-xs">JD</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">John Doe</p>
              <p className="text-[10px] text-zinc-500 truncate">john@example.com</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
