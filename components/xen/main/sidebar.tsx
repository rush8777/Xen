"use client"

import React, { useState, useEffect, useCallback } from "react"

import {
  BarChart2,
  Building2,
  Folder,
  Users2,
  Boxes,
  MessagesSquare,
  Video,
  Settings,
  HelpCircle,
  Menu,
  ChevronLeft,
  ChevronDown,
} from "lucide-react"

import { Home } from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import { useSidebarContext } from "./layout"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

interface ApiProject {
  id: number
  name: string
  category?: string | null
  description?: string | null
  video_url?: string | null
  priority?: string | null
  progress: number
  status: string
  created_at: string
  updated_at: string
}

interface RecentChat {
  id: string
  name: string
  platform: string
  updatedAt: string
}

export default function Sidebar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isRecentsOpen, setIsRecentsOpen] = useState(true)
  const { isSidebarExpanded, setIsSidebarExpanded } = useSidebarContext()
  const [recentChats, setRecentChats] = useState<RecentChat[]>([])
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

  const loadRecentProjects = useCallback(async () => {
    try {
      setIsLoading(true)
      const res = await fetch(`${API_BASE_URL}/api/projects?limit=5`, {
        cache: "no-store",
      })
      if (!res.ok) {
        console.error("Failed to load recent projects:", res.status, res.statusText)
        setRecentChats([])
        return
      }
      const data = (await res.json()) as ApiProject[]
      const mapped: RecentChat[] = (data || []).map((p) => ({
        id: String(p.id),
        name: p.name,
        platform: normalizeCategory(p.category),
        updatedAt: formatTimeAgo(p.updated_at),
      }))
      setRecentChats(mapped)
    } catch (e) {
      console.error("Failed to load recent projects:", e)
      setRecentChats([])
    } finally {
      setIsLoading(false)
    }
  }, [formatTimeAgo, normalizeCategory])

  useEffect(() => {
    loadRecentProjects()
  }, [loadRecentProjects])

  useEffect(() => {
    const onFocus = () => loadRecentProjects()
    const onVisibility = () => {
      if (document.visibilityState === "visible") loadRecentProjects()
    }
    window.addEventListener("focus", onFocus)
    document.addEventListener("visibilitychange", onVisibility)
    return () => {
      window.removeEventListener("focus", onFocus)
      document.removeEventListener("visibilitychange", onVisibility)
    }
  }, [loadRecentProjects])

  function handleNavigation() {
    setIsMobileMenuOpen(false)
  }

  function NavItem({
    href,
    icon: Icon,
    children,
  }: {
    href: string
    icon: any
    children: React.ReactNode
  }) {
    return (
      <Link
        href={href}
        onClick={handleNavigation}
        className={`flex items-center rounded-md transition-colors text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-[#1F1F23] ${
          isSidebarExpanded ? "px-2 py-1 justify-start" : "px-2 py-1 justify-center"
        }`}
        title={isSidebarExpanded ? "" : children?.toString()}
      >
        <Icon className="h-3.5 w-3.5 flex-shrink-0" />
        {isSidebarExpanded && <span className="ml-2 text-xs">{children}</span>}
      </Link>
    )
  }

  function RecentChatItem({ chat }: { chat: typeof recentChats[0] }) {
    return (
      <Link
        href={`/chat/${chat.id}`}
        onClick={handleNavigation}
        className={`flex items-center gap-2 rounded-md transition-colors text-gray-400 dark:text-gray-400 hover:text-gray-100 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-[#1F1F23] ${
          isSidebarExpanded ? "px-2 py-1.5" : "px-2 py-1.5 justify-center"
        }`}
        title={chat.name}
      >
        {isSidebarExpanded && (
          <span className="text-xs truncate flex-1">{chat.name}</span>
        )}
      </Link>
    )
  }

  return (
    <>
      <button
        type="button"
        className="lg:hidden fixed top-4 left-4 z-[70] p-2 rounded-lg bg-white dark:bg-[#0F0F12] shadow-md"
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      >
        <Menu className="h-5 w-5 text-gray-600 dark:text-gray-300" />
      </button>
      <nav
        className={`
                fixed inset-y-0 left-0 z-[70] bg-white dark:bg-[#0F0F12] transform transition-all duration-200 ease-in-out
                lg:translate-x-0 lg:static border-r border-gray-200 dark:border-[#1F1F23]
                ${isMobileMenuOpen ? "translate-x-0 w-56" : "-translate-x-full w-56"}
                ${isSidebarExpanded ? "lg:w-56" : "lg:w-16"}
            `}
      >
        <div className="h-full flex flex-col">
          <div className={`flex items-center justify-between border-b border-gray-200 dark:border-[#1F1F23] ${isSidebarExpanded ? "h-12 px-4" : "h-12 px-2"}`}>
            {isSidebarExpanded && (
              <Link
                href="/dashboard"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <Image
                  src="/images/logo.png"
                  alt="Logo"
                  width={100}
                  height={32}
                  className="flex-shrink-0 rounded-lg"
                />
                
              </Link>
            )}
            {!isSidebarExpanded && (
              <Image
                src="/images/logo.png"
                alt="Logo"
                width={28}
                height={28}
                className="flex-shrink-0 mx-auto rounded-lg"
              />
            )}
            <button
              onClick={() => setIsSidebarExpanded(!isSidebarExpanded)}
              className="p-1 hover:bg-gray-100 dark:hover:bg-[#1F1F23] rounded-md transition-colors text-gray-600 dark:text-gray-400 hidden lg:flex flex-shrink-0"
            >
              <ChevronLeft className={`h-3.5 w-3.5 transition-transform ${!isSidebarExpanded ? "rotate-180" : ""}`} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-3">
            <div className={`space-y-4 ${isSidebarExpanded ? "px-3" : "px-2"}`}>
              <div>
                {isSidebarExpanded && (
                  <div className="px-2 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Overview
                  </div>
                )}
                <div className={`space-y-0.5 ${!isSidebarExpanded ? "space-y-3" : ""}`}>
                  <NavItem href="/dashboard" icon={Home}>
                    Home
                  </NavItem>
                  <NavItem href="/library" icon={Building2}>
                    Library
                  </NavItem>
                  <NavItem href="/project" icon={Folder}>
                    Projects
                  </NavItem>
                  <NavItem href="/connections" icon={Boxes}>
                    Connections
                  </NavItem>
                  
                </div>
              </div>

              {/* Recents Section */}
              <div>
                {isSidebarExpanded ? (
                  <button
                    onClick={() => setIsRecentsOpen(!isRecentsOpen)}
                    className="w-full flex items-center justify-between px-2 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                  >
                    <span>Recents</span>
                    <ChevronDown
                      className={`h-3 w-3 transition-transform ${
                        !isRecentsOpen ? "-rotate-90" : ""
                      }`}
                    />
                  </button>
                ) : null}
                {isRecentsOpen && (
                  <div className={`space-y-0.5 ${!isSidebarExpanded ? "space-y-3" : ""}`}>
                    {isLoading ? (
                      <div className="px-2 py-1.5">
                        <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                      </div>
                    ) : (
                      recentChats.map((chat) => (
                        <RecentChatItem key={chat.id} chat={chat} />
                      ))
                    )}
                  </div>
                )}
              </div>


            </div>
          </div>

          <div className={`border-t border-gray-200 dark:border-[#1F1F23] ${isSidebarExpanded ? "px-3 py-3" : "px-2 py-3"}`}>
            <div className={`space-y-0.5 ${!isSidebarExpanded ? "space-y-3" : ""}`}>
              <NavItem href="#" icon={Settings}>
                Settings
              </NavItem>
              <NavItem href="#" icon={HelpCircle}>
                Help
              </NavItem>
            </div>
          </div>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-[65] lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  )
}
