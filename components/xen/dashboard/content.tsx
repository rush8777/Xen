"use client"

import { ArrowRight, Filter, ArrowUpDown, Link2, MessageCircle, X, ChevronDown, Play, Image, FileText, Film, Users, MoreHorizontal, Trash2, Lightbulb } from "lucide-react"
import { useState, useRef, useEffect, useCallback } from "react"
import CreateProjectModal from "@/components/xen/create-project"
import { Card, CardContent } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { useGlobalLoader } from "@/components/xen/main/layout"
// Icons for chat model (local React SVG components)
import FacebookIcon from "./icons/FacebookIcon"
import InstagramIcon from "./icons/InstagramIcon"
import YoutubeIcon from "./icons/YoutubeIcon"
import TiktokIcon from "./icons/TiktokIcon"

interface Course {
  id: number
  label: string
  description: string
  icon: React.FC<{ className?: string }>
  gradient: string
  accentColor: string
}

const initLoadingStates = [
  { text: "Initializing video analysis" },
  { text: "Downloading video" },
  { text: "Extracting comments" },
  { text: "Running Gemini analysis" },
  { text: "Creating project" },
  { text: "Opening Streamline" },
]

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

type ApiProject = {
  id: number
  name: string
  category?: string | null
  description?: string | null
  video_url?: string | null
  priority?: string | null
  progress: number
  status: string
}

type DashboardProject = {
  id: string
  title: string
  description: string
  priority: string
  category: string
  thumbnailUrl?: string
  context: number
  progressColor: string
  team: string[]
  links: number
  comments: number
  column: string
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

export default function CoursePage() {
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)
  const [selectedContentType, setSelectedContentType] = useState<string | null>(null)
  const filterRef = useRef<HTMLDivElement>(null)
  const [projects, setProjects] = useState<DashboardProject[]>([])
  const { setLoading, setStep, setLoadingStates } = useGlobalLoader()

  const handleInitializingChange = useCallback(
    (loading: boolean) => {
      setLoadingStates(initLoadingStates)
      setLoading(loading)
      if (!loading) {
        setStep(0)
      }
    },
    [setLoading, setLoadingStates, setStep]
  )

  const handleProgressChange = useCallback(
    (step: number) => setStep(step),
    [setStep]
  )

  const handleDeleteProject = useCallback(async (id: string) => {
    const ok = window.confirm("Are you sure you want to delete this project?")
    if (!ok) return

    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${encodeURIComponent(id)}`, {
        method: "DELETE",
      })
      if (!res.ok && !res.status.toString().startsWith("2")) {
        throw new Error(`Failed to delete project (${res.status})`)
      }
      setProjects((prev) => prev.filter((p) => p.id !== id))
    } catch (e) {
      console.error("Failed to delete project:", e)
      alert("Failed to delete project. Please try again.")
    }
  }, [])

  const platforms = ["Facebook", "Instagram", "Tiktok", "Youtube"]
  const contentTypes = ["Video", "Image", "Post"]

  const normalizeCategory = useCallback((category?: string | null) => {
      const c = (category || "").toLowerCase()
      if (c === "youtube") return "Youtube"
      if (c === "facebook") return "Facebook"
      if (c === "instagram") return "Instagram"
      if (c === "tiktok") return "Tiktok"
      return category || "Youtube"
  }, [])

  const mapColumn = useCallback((status: string) => {
      const s = (status || "").toLowerCase()
      if (s === "draft") return "todo"
      if (s === "in_progress") return "progress"
      if (s === "review") return "review"
      if (s === "completed" || s === "done") return "done"
      return "todo"
  }, [])

  const mapProgressColor = useCallback((progress: number) => {
      if (progress >= 80) return "bg-green-500"
      if (progress >= 50) return "bg-blue-600"
      if (progress >= 20) return "bg-amber-500"
      return "bg-red-500"
  }, [])

  const getThumbnailUrl = useCallback((videoUrl?: string | null) => {
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
  }, [])

  const loadProjects = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects?limit=100`, {
        cache: "no-store",
      })
      if (!res.ok) {
        console.error("Failed to load projects:", res.status, res.statusText)
        setProjects([])
        return
      }
      const data = (await res.json()) as ApiProject[]
      const mapped = (data || []).map((p) => {
        const progress = typeof p.progress === "number" ? p.progress : 0
        const priority = p.priority || "Video"
        const category = normalizeCategory(p.category)
        const thumbnailUrl = getThumbnailUrl(p.video_url)
        return {
          id: String(p.id),
          title: p.name,
          description: p.description || "",
          priority,
          category,
          thumbnailUrl,
          context: progress,
          progressColor: mapProgressColor(progress),
          team: ["👤"],
          links: 0,
          comments: 0,
          column: mapColumn(p.status),
        }
      })
      setProjects(mapped)
    } catch (e) {
      console.error("Failed to load projects:", e)
      setProjects([])
    }
  }, [mapColumn, mapProgressColor, normalizeCategory, getThumbnailUrl])

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
      document.removeEventListener("visibilitychange", onVisibility)
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

  const filteredTasks = projects.filter((task) => {
    const matchesPlatform = !selectedPlatform || task.category === selectedPlatform
    const matchesContentType = !selectedContentType || task.priority === selectedContentType
    return matchesPlatform && matchesContentType
  })

  const activeFilterCount = (selectedPlatform ? 1 : 0) + (selectedContentType ? 1 : 0)

  const courses: Course[] = [
    { 
      id: 1, 
      label: "Videos", 
      description: "Create engaging video content with AI-powered editing",
      icon: Play, 
      gradient: "from-emerald-500/20 to-teal-500/20",
      accentColor: "emerald"
    },
    { 
      id: 2, 
      label: "Posts", 
      description: "Generate compelling social media posts instantly",
      icon: FileText, 
      gradient: "from-blue-500/20 to-cyan-500/20",
      accentColor: "cyan"
    },
    { 
      id: 3, 
      label: "Comments", 
      description: "Analyze and respond to comments intelligently",
      icon: MessageCircle, 
      gradient: "from-purple-500/20 to-pink-500/20",
      accentColor: "purple"
    },
    { 
      id: 4, 
      label: "IdeaGen", 
      description: "Discover creative ideas for your next campaign",
      icon: Lightbulb, 
      gradient: "from-amber-500/20 to-orange-500/20",
      accentColor: "amber"
    }
  ]

  const getAccentColorClass = (color: string) => {
    const colors: Record<string, string> = {
      emerald: "text-emerald-400 group-hover:text-emerald-300",
      cyan: "text-cyan-400 group-hover:text-cyan-300",
      purple: "text-purple-400 group-hover:text-purple-300",
      amber: "text-amber-400 group-hover:text-amber-300"
    }
    return colors[color] || colors.emerald
  }

  const handleCourseClick = (course: Course) => {
    console.log('handleCourseClick called with course:', course)
    setSelectedCourse(course)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedCourse(null)
  }

// Platform icons definition (put this outside any component, at the top of your file)
const platformIcons: Record<string, React.FC<{ className?: string }>> = {
  Facebook: ({ className }) => <FacebookIcon className={className || "w-4 h-4"} />,
  Instagram: ({ className }) => <InstagramIcon className={className || "w-4 h-4"} />,
  Youtube: ({ className }) => <YoutubeIcon className={className || "w-4 h-4"} />,
  Tiktok: ({ className }) => <TiktokIcon className={className || "w-4 h-4"} />,
}

// ChatRow component
function ChatRow({ project, index }: { project: any; index: number }) {
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

  const PlatformIcon = platformIcons[project.category] || (() => <div className="w-4 h-4 rounded-full bg-gray-500 flex-shrink-0" />)

  return (
    <div className="group hover:bg-gray-50 dark:hover:bg-[#2F2F37]/50 transition-colors">
      <div className="px-6 py-3 flex items-center">
        {/* Left - Chat Info */}
        <div className="w-48 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {project.title.replace(/\.\.$/, '')}
          </h3>
        </div>

        {/* Middle - Platform Icon + Project Name (Centered) */}
        <div className="flex-1 flex justify-center items-center gap-2 flex-shrink-0">
          <PlatformIcon />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
            Project #{project.id}
          </span>
        </div>

        {/* Right - Time, Status, Menu */}
        <div className="flex items-center gap-3 flex-shrink-0 w-48 justify-end">
          {/* Time */}
          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
            {index === 0 ? "20h ago" : index === 1 ? "5d ago" : "29d ago"}
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

  return (
    <div className="space-y-8 min-h-screen bg-gray-50 dark:bg-[#0F0F12] p-6">
      {/* Course Banner */}
      <div className="rounded-2xl p-8 text-white flex items-center justify-between overflow-hidden relative h-48 border border-gray-300">
        <img
          src="/images/icons/banner_overlay.png"
          alt="Course Banner"
          className="absolute top-0 right-0 h-full w-auto"
        />
        <div className="relative z-10">
          <p className="text-sm font-semibold tracking-widest text-purple-200 mb-2">ONLINE COURSE</p>
          <h1 className="text-4xl font-bold mb-6">Sharpen Your Skills with<br />Professional Online Courses</h1>
          <button className="bg-black hover:bg-gray-800 transition-colors text-white rounded-full px-6 py-3 font-semibold flex items-center gap-2">
            Join Now
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Course Cards - NEW DESIGN */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {courses.map((course) => {
          const Icon = course.icon
          return (
            <button
              key={course.id}
              onClick={() => handleCourseClick(course)}
              className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#1a1a1a] to-[#0f0f0f] border border-white/5 hover:border-white/10 transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/50"
            >
              {/* Gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${course.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              
              {/* Noise texture overlay */}
              <div className="absolute inset-0 opacity-[0.015] mix-blend-overlay">
                <div className="w-full h-full" style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'repeat'
                }} />
              </div>
              {/* Content */}
              <div className="relative p-4 flex flex-col items-start h-full min-h-[150px]">
                {/* Text content */}
                <div className="mb-4 space-y-2">
                  <h3 className="text-lg font-semibold text-white group-hover:text-white/90">
                    {course.label}
                  </h3>
                  <p className="text-xs text-gray-400 leading-relaxed group-hover:text-gray-300">
                    {course.description}
                  </p>
                </div>

                {/* Learn more link */}
                <div className="flex items-center justify-center gap-2 text-xs font-medium">
                  <span className={getAccentColorClass(course.accentColor)}>
                    Learn more
                  </span>
                  <svg 
                    className={`w-4 h-4 ${getAccentColorClass(course.accentColor)} transition-transform group-hover:translate-x-1`}
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>

                {/* Large icon container - takes up bottom portion */}
                <div className="w-full flex justify-end mt-auto mb-2">
                  <div className="relative">
                    {/* Glow effect */}
                    <div className={`absolute inset-0 ${getAccentColorClass(course.accentColor)} opacity-20 blur-xl rounded-full scale-150`} />
                    
                    {/* Icon */}
                    <div className="relative group-hover:bg-white/10">
                      {course.label === "Videos" ? (
                        <img
                          src="/images/icons/video_icon.png"
                          alt="Videos"
                          className="w-16 h-16"
                        />
                      ) : course.label === "Posts" ? (
                        <img
                          src="/images/icons/learn_icon.png"
                          alt="Posts"
                          className="w-16 h-16"
                        />
                      ) : course.label === "Comments" ? (
                        <img
                          src="/images/icons/comment_icon.png"
                          alt="Comments"
                          className="w-16 h-16"
                        />
                      ) : course.label === "IdeaGen" ? (
                        <img
                          src="/images/icons/bulb.png"
                          alt="IdeaGen"
                          className="w-16 h-20"
                        />
                      ) : (
                        <Icon className={`w-12 h-12 ${getAccentColorClass(course.accentColor)}`} />
                      )}
                    </div>
                  </div>
                </div>

                {/* Bottom gradient line */}
                <div className={`absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r ${course.gradient} opacity-50`} />
              </div>

              {/* Bottom gradient line */}
              <div className={`absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r ${course.gradient} opacity-50`} />
            </button>
          )
        })}
      </div>

      {/* Projects Section - MINIMALIST CARDS */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-400 dark:text-gray-500">Recent Projects</h2>
          <Link href="/project" className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium flex items-center gap-1">
            View All
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Minimalist Project Cards - 4 columns horizontal layout */}
        {filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <img
              src="/images/icons/Recent_project_empty.png"
              alt="No recent projects"
              className="w-50 h-40 object-cover rounded-lg mb-4 opacity-50"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400">No recent projects</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {filteredTasks.slice(0, 4).map((project) => (
              <Link
                key={project.id}
                href={`/streamline?projectId=${encodeURIComponent(project.id)}`}
                className="group block"
              >
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
                          <Image className="w-16 h-16 object-cover text-gray-500" />
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
                        {project.id === "1" ? "7d ago" : project.id === "2" ? "55d ago" : "60d ago"}
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
                            handleDeleteProject(project.id)
                          }}
                          className="text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete project
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* My Chats Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-400 dark:text-gray-500">My Chats</h2>
          <Link href="/library" className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium flex items-center gap-1">
            View All
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="flex justify-center">
          <div className="w-full max-w-4xl">
            {filteredTasks.slice(0, 5).map((project, index) => (
              <ChatRow key={project.id} project={project} index={index} />
            ))}
          </div>
        </div>
      </div>

      {/* Create Project Modal */}
      <CreateProjectModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        course={selectedCourse}
        onInitializingChange={handleInitializingChange}
        useGlobalLoader={true}
        onProgressChange={handleProgressChange}
      />
    </div>
  )
}