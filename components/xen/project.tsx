"use client"

import { Search, Plus, Link2, MessageCircle, Filter, ArrowUpDown, X, ChevronDown, Image, MoreHorizontal, Trash2 } from "lucide-react"
import { useState, useRef, useEffect, useCallback } from "react"
import Layout from "@/components/xen/main/layout"
import { Card, CardContent } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import Link from "next/link"

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

const getThumbnailUrl = (videoUrl?: string | null) => {
  if (!videoUrl) return undefined
  try {
    const u = new URL(videoUrl)

    // YouTube
    if (u.hostname.includes("youtube.com") || u.hostname.includes("youtu.be")) {
      const id = u.hostname.includes("youtu.be")
        ? u.pathname.replace("/", "")
        : u.searchParams.get("v")
      if (id) return `https://img.youtube.com/vi/${id}/hqdefault.jpg`
    }

    // TikTok (no stable public thumbnail without API)
    if (u.hostname.includes("tiktok.com")) {
      return undefined
    }

    // Instagram / Facebook (often blocked by CORS / requires auth)
    if (u.hostname.includes("instagram.com") || u.hostname.includes("facebook.com")) {
      return undefined
    }

    return undefined
  } catch {
    return undefined
  }
}

interface Project {
  id: number
  title: string
  description: string
  priority: string
  category: string
  progress: number
  progressColor: string
  status: string
  thumbnailUrl?: string
}

const getProgressColor = (progress: number) => {
  if (progress >= 75) return "bg-green-500"
  if (progress >= 50) return "bg-blue-600"
  if (progress >= 25) return "bg-orange-500"
  return "bg-red-500"
}

const normalizeCategory = (category?: string | null) => {
  const c = (category || "").toLowerCase()
  if (c === "youtube") return "Youtube"
  if (c === "facebook") return "Facebook"
  if (c === "instagram") return "Instagram"
  if (c === "tiktok") return "Tiktok"
  return category || "Youtube"
}

const normalizePriority = (priority?: string | null) => {
  const p = (priority || "").toLowerCase()
  if (p === "video") return "Video"
  if (p === "image") return "Image"
  if (p === "post") return "Post"
  return "Video" // Default priority
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case "Video":
      return "bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400"
    case "Image":
      return "bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400"
    case "Post":
      return "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400"
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400"
  }
}

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    Facebook: "bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
    Instagram: "bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400",
    Tiktok: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400",
    Youtube: "bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400",
  }
  return colors[category] || "bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400"
}

function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: number) => void }) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    if (isDeleting) return
    const ok = window.confirm(`Are you sure you want to delete "${project.title}"?`)
    if (!ok) return

    setIsDeleting(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}`, {
        method: "DELETE",
      })
      if (!res.ok && !res.status.toString().startsWith("2")) {
        throw new Error(`Failed to delete project (${res.status})`)
      }
      onDelete(project.id)
    } catch (e) {
      console.error("Failed to delete project:", e)
      alert("Failed to delete project. Please try again.")
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* Card with Image */}
      <div className="relative bg-[#1a1a1a] dark:bg-[#1a1a1a] rounded-xl overflow-hidden border border-gray-800 dark:border-gray-800 hover:border-gray-700 dark:hover:border-gray-700 transition-all">
        {/* Floating Badges on Image - Top Left */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
          <span className={cn("px-2 py-1 rounded-md text-xs font-medium backdrop-blur-sm", getPriorityColor(project.priority))}>
            {project.priority}
          </span>
          <span className={cn("px-2 py-1 rounded-md text-xs font-medium backdrop-blur-sm", getCategoryColor(project.category))}>
            {project.category}
          </span>
        </div>

        {/* Project Thumbnail - Full Width */}
        <div className="w-full aspect-video bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center overflow-hidden">
          {project.thumbnailUrl ? (
            <img
              src={project.thumbnailUrl}
              alt={project.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-16 h-16 bg-gray-700/50 rounded-lg flex items-center justify-center">
              <Image className="w-8 h-8 text-gray-500" />
            </div>
          )}
        </div>
      </div>

      {/* Text Content Outside Card */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 space-y-1">
          {/* Title */}
          <h3 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
            {project.title}
          </h3>

          {/* Time Stamp */}
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {project.id === 1 ? "7d ago" : project.id === 2 ? "55d ago" : "60d ago"}
          </p>
        </div>

        {/* Three Dots Menu - Bottom Right */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="p-1 hover:bg-gray-200 dark:hover:bg-[#2F2F37] rounded transition-colors"
              onClick={(e) => e.stopPropagation()}
              type="button"
            >
              <MoreHorizontal className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={4} className="w-40">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                handleDelete()
              }}
              className="text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400"
              disabled={isDeleting}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {isDeleting ? "Deleting..." : "Delete project"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)
  const [selectedContentType, setSelectedContentType] = useState<string | null>(null)
  const filterRef = useRef<HTMLDivElement>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const handleDeleteProject = useCallback((id: number) => {
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }, [])

  const platforms = ["Facebook", "Instagram", "Tiktok", "Youtube"]
  const contentTypes = ["Video", "Image", "Post"]

  const loadProjects = useCallback(async () => {
    try {
      setIsLoading(true)
      const res = await fetch(`${API_BASE_URL}/api/projects?limit=100`, {
        cache: "no-store",
      })
      if (!res.ok) {
        console.error("Failed to load projects:", res.status, res.statusText)
        setProjects([])
        return
      }
      const data = (await res.json()) as ApiProject[]
      const mapped: Project[] = (data || []).map((p) => ({
        id: p.id,
        title: p.name,
        description: p.description || "No description available",
        priority: normalizePriority(p.priority),
        category: normalizeCategory(p.category),
        progress: p.progress,
        progressColor: getProgressColor(p.progress),
        status: p.status,
        thumbnailUrl: getThumbnailUrl(p.video_url),
      }))
      setProjects(mapped)
    } catch (e) {
      console.error("Failed to load projects:", e)
      setProjects([])
    } finally {
      setIsLoading(false)
    }
  }, [])

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

  const filteredProjects = projects.filter((project) => {
    const matchesSearch = project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.id.toString().toLowerCase().includes(searchQuery.toLowerCase())
    const matchesPlatform = !selectedPlatform || project.category === selectedPlatform
    const matchesContentType = !selectedContentType || project.priority === selectedContentType
    return matchesSearch && matchesPlatform && matchesContentType
  })

  const activeFilterCount = (selectedPlatform ? 1 : 0) + (selectedContentType ? 1 : 0)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setIsFilterOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0F0F12] p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              Projects
            </h1>
            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-300">
              {projects.length}
            </span>
          </div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Search through the comprehensive directory of Projects
          </p>
        </div>

        {/* Search Bar and Sorting */}
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
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
          <div className="flex items-center gap-3">
            <div className="relative" ref={filterRef}>
              <button
                onClick={() => setIsFilterOpen(!isFilterOpen)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
                  activeFilterCount > 0
                    ? "bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300"
                    : "bg-white dark:bg-[#1F1F23] border-gray-200 dark:border-[#2F2F37] hover:bg-gray-50 dark:hover:bg-[#2F2F37] text-gray-700 dark:text-gray-300"
                )}
              >
                <Filter className="w-4 h-4" />
                Filter
                {activeFilterCount > 0 && (
                  <span className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full bg-purple-600 text-white text-xs font-bold">
                    {activeFilterCount}
                  </span>
                )}
                <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", isFilterOpen && "rotate-180")} />
              </button>

              {isFilterOpen && (
                <div className="absolute top-full right-0 mt-2 w-64 bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2F2F37] rounded-xl shadow-lg shadow-black/10 dark:shadow-black/30 z-50 p-4 space-y-4">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Filters</span>
                    {activeFilterCount > 0 && (
                      <button
                        onClick={() => { setSelectedPlatform(null); setSelectedContentType(null) }}
                        className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium transition-colors"
                      >
                        <X className="w-3 h-3" />
                        Clear all
                      </button>
                    )}
                  </div>

                  {/* Platform */}
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Platform</p>
                    <div className="flex flex-wrap gap-1.5">
                      {platforms.map((platform) => (
                        <button
                          key={platform}
                          onClick={() => setSelectedPlatform(selectedPlatform === platform ? null : platform)}
                          className={cn(
                            "px-3 py-1 rounded-full text-xs font-medium transition-all",
                            selectedPlatform === platform
                              ? getCategoryColor(platform) + " ring-2 ring-offset-1 dark:ring-offset-[#1F1F23] ring-current"
                              : "bg-gray-100 dark:bg-[#2F2F37] text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-[#3F3F47]"
                          )}
                        >
                          {platform}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Divider */}
                  <hr className="border-gray-200 dark:border-[#2F2F37]" />

                  {/* Content Type */}
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Content Type</p>
                    <div className="flex flex-wrap gap-1.5">
                      {contentTypes.map((type) => (
                        <button
                          key={type}
                          onClick={() => setSelectedContentType(selectedContentType === type ? null : type)}
                          className={cn(
                            "px-3 py-1 rounded-full text-xs font-medium transition-all",
                            selectedContentType === type
                              ? getPriorityColor(type) + " ring-2 ring-offset-1 dark:ring-offset-[#1F1F23] ring-current"
                              : "bg-gray-100 dark:bg-[#2F2F37] text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-[#3F3F47]"
                          )}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2F2F37] hover:bg-gray-50 dark:hover:bg-[#2F2F37] text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors">
              <ArrowUpDown className="w-4 h-4" />
              Sort
            </button>
          </div>
        </div>

        {/* Projects Grid - Using exact 4-column layout from original code */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <Card key={i} className="border border-gray-200 dark:border-[#2F2F37] bg-white dark:bg-[#1F1F23]">
                <CardContent className="p-3 space-y-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className="w-12 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                    <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                  </div>
                  <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
                  <div className="w-3/4 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                  <div className="space-y-1.5">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredProjects.map((project) => (
              <Link
                key={project.id}
                href={`/streamline?projectId=${encodeURIComponent(String(project.id))}`}
                className="block"
              >
                <ProjectCard project={project} onDelete={handleDeleteProject} />
              </Link>
            ))}
          </div>
        )}

        {/* Empty State */}
        {filteredProjects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-gray-200 dark:bg-[#1F1F23] flex items-center justify-center mb-4">
              <Search className="w-8 h-8 text-gray-400 dark:text-gray-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-1">No projects found</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Try adjusting your search query</p>
          </div>
        )}
      </div>
  )
}
