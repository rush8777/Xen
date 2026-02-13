"use client"

import { X, Grid3x3, Plus } from "lucide-react"

import React, { useState, useEffect, useRef, DragEvent, useCallback, ChangeEvent } from "react"

import { useRouter } from "next/navigation"

import { MultiStepLoader } from "@/components/ui/multi-step-loader"

import { cn } from "@/lib/utils"

import { useSidebarContext } from "./main/layout"

import Masonry from "react-masonry-css"



const toptabs = [

  { id: "import", label: "Import"},

  { id: "link", label: "Link"},

  { id: "local", label: "Local"}

] as const

const initLoadingStates = [
  { text: "Initializing video analysis" },
  { text: "Downloading video" },
  { text: "Extracting comments" },
  { text: "Running Gemini analysis" },
  { text: "Creating project" },
  { text: "Opening Streamline" },
]



interface Course {

  id: number

  label: string

  icon: React.ComponentType<{ className?: string }>

  gradient: string

}



interface CreateProjectModalProps {

  isOpen: boolean

  onClose: () => void

  course?: Course | null

  onInitializingChange?: (isInitializing: boolean) => void

  useGlobalLoader?: boolean

  onProgressChange?: (step: number, text: string) => void

}



interface FormData {

  projectName: string

  category: string

  startDate: string

  endDate: string

  description: string

  documents: File[]
}

interface LibraryVideo {
  id: number | string
  title: string
  channel: string
  viewsText: string
  timeText: string
  durationText: string
  statsText: string
  thumbnail: string
  platform: string
  url: string
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

// Masonry breakpoint configuration
const breakpointColumns = {
  default: 4,
  1100: 4,
  900: 3,
  600: 2,
}

// CreateProjectModal component
export default function CreateProjectModal({
  isOpen,
  onClose,
  course,
  onInitializingChange,
  useGlobalLoader,
  onProgressChange,
}: CreateProjectModalProps) {
  console.log('CreateProjectModal rendering, isOpen:', isOpen)

  const router = useRouter()
  
  const [formData, setFormData] = useState<FormData>({
    projectName: "",
    category: course?.label || "",
    startDate: "",
    endDate: "",
    description: "",
    documents: []
  })

  const [isDragging, setIsDragging] = useState(false)
  const [modalSize, setModalSize] = useState<'max-w-sm' | 'max-w-md' | 'max-w-2xl' | 'max-w-3xl' | 'max-w-4xl' | 'max-w-6xl'>('max-w-6xl')
  const [videos, setVideos] = useState<LibraryVideo[]>([])
  const [filteredVideos, setFilteredVideos] = useState<LibraryVideo[]>([])
  const [videosLoading, setVideosLoading] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState<LibraryVideo | null>(null)
  const { isSidebarExpanded } = useSidebarContext()
  const [activeFilter, setActiveFilter] = useState("All Platforms")
  const [selectedPlatform, setSelectedPlatform] = useState("youtube")

  // Initialization states
  const [isInitializing, setIsInitializing] = useState(false)
  const [initError, setInitError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const [progressStep, setProgressStep] = useState(0)
  const [progressText, setProgressText] = useState(initLoadingStates[0]?.text || "Initializing video analysis")

  useEffect(() => {
    onInitializingChange?.(isInitializing)
  }, [isInitializing, onInitializingChange])

  useEffect(() => {
    onProgressChange?.(progressStep, progressText)
  }, [progressStep, progressText, onProgressChange])

  useEffect(() => {
    if (!isInitializing || !jobId) return

    let stopped = false
    const interval = setInterval(async () => {
      if (stopped) return
      try {
        const res = await fetch(`${API_BASE_URL}/api/analysis/progress/${encodeURIComponent(jobId)}`, {
          cache: "no-store",
        })
        if (!res.ok) return
        const data = await res.json()

        const step = typeof data?.step === "number" ? data.step : 0
        const text = typeof data?.text === "string" ? data.text : "Initializing video analysis"
        setProgressStep(step)
        setProgressText(text)

        if (data?.status === "failed") {
          setInitError(data?.error || "Initialization failed")
          setIsInitializing(false)
          clearInterval(interval)
          return
        }

        if (data?.status === "completed") {
          clearInterval(interval)
          if (data?.project_id) {
            router.push(`/streamline?projectId=${encodeURIComponent(String(data.project_id))}`)
          }
          setJobId(null)
        }
      } catch {
        // ignore transient polling errors
      }
    }, 1000)

    return () => {
      stopped = true
      clearInterval(interval)
    }
  }, [API_BASE_URL, isInitializing, jobId, router])

  const platforms = ["youtube", "facebook", "instagram", "tiktok", "twitter", "linkedin"]

  const platformFilters = [
    "All Platforms",
    "Instagram",
    "Facebook",
    "Youtube",
    "LinkedIn",
    "TikTok",
  ]

  const filterToPlatform = useCallback((filter: string) => {
    switch (filter) {
      case "Instagram":
        return "instagram"
      case "Facebook":
        return "facebook"
      case "Youtube":
        return "youtube"
      case "LinkedIn":
        return "linkedin"
      case "TikTok":
        return "tiktok"
      case "All Platforms":
      default:
        return "youtube"
    }
  }, [])

  const loadVideosForPlatform = useCallback(async (platform: string) => {
    setVideosLoading(true)
    try {
      const url = `${API_BASE_URL}/api/videos?live=true&page_size=24&platform=${platform.toLowerCase()}`
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch videos: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      
      const mapped: LibraryVideo[] = (data.items || []).map((item: any, index: number) => {
        const fallbackId = typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `video-${index}-${Date.now()}`

        const mappedVideo = {
          id: item.id ?? item.platform_video_id ?? fallbackId,
          title: item.title,
          channel: item.channel || item.channel_title || 'Unknown',
          viewsText: item.views_text || (item.view_count ? `${item.view_count} views` : ''),
          timeText: item.published_time_text || item.timeText || '',
          durationText: item.duration_text || item.durationText || '',
          statsText: item.stats_text || '',
          thumbnail: item.thumbnail || item.thumbnail_url || 'https://via.placeholder.com/400x225?text=Video',
          platform: item.platform || platform,
          url: item.url || '',
        }
        
        return mappedVideo
      })
      
      setVideos(mapped)
      setFilteredVideos(mapped)
      setSelectedVideo(null)
    } catch (error) {
      setVideos([])
      setFilteredVideos([])
      setSelectedVideo(null)
    } finally {
      setVideosLoading(false)
    }
  }, [API_BASE_URL])

  const handleFilterSelect = useCallback((filter: string) => {
    setActiveFilter(filter)
    setSelectedPlatform(filterToPlatform(filter))
  }, [filterToPlatform])

  // Handle sidebar resize and modal sizing
  useEffect(() => {
    const updateModalSize = () => {
      const sidebarWidth = isSidebarExpanded ? 224 : 64
      const padding = 32
      const availableWidth = window.innerWidth - sidebarWidth - padding
      
      console.log('Sidebar state:', { isSidebarExpanded, sidebarWidth, availableWidth, windowWidth: window.innerWidth })
      
      if (availableWidth < 640) {
        setModalSize('max-w-sm')
      } else if (availableWidth < 768) {
        setModalSize('max-w-md')
      } else if (availableWidth < 1024) {
        setModalSize('max-w-2xl')
      } else if (availableWidth < 1280) {
        setModalSize('max-w-3xl')
      } else if (availableWidth < 1536) {
        setModalSize('max-w-4xl')
      } else {
        setModalSize('max-w-6xl')
      }
    }

    updateModalSize()
    window.addEventListener('resize', updateModalSize)
    
    const timer = setTimeout(updateModalSize, 100)
    
    return () => {
      window.removeEventListener('resize', updateModalSize)
      clearTimeout(timer)
    }
  }, [isSidebarExpanded])

  useEffect(() => {
    if (!isOpen) return
    if (!selectedPlatform) return
    loadVideosForPlatform(selectedPlatform)
  }, [isOpen, selectedPlatform, loadVideosForPlatform])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedVideo?.url) {
      return
    }
    
    setIsInitializing(true)
    setInitError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze-from-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: selectedVideo.url,
          project_name: formData.projectName || "Streamline Project"
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to initialize video analysis')
      }

      const data = await response.json()
      setJobId(data.job_id)
      console.log('yt-dlp initialized, job_id:', data.job_id)

      setProgressStep(0)
      setProgressText(initLoadingStates[0]?.text || "Initializing video analysis")
      onClose()
    } catch (err: any) {
      console.error('yt-dlp initialization error:', err)
      setInitError(err.message || 'Failed to initialize video')
      setIsInitializing(false)
    }
  }



  const handleSaveDraft = () => {

    console.log("Draft saved:", formData)

    onClose()

  }



  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {

    e.preventDefault()

    setIsDragging(true)

  }



  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {

    e.preventDefault()

    setIsDragging(false)

  }



  const handleDrop = (e: DragEvent<HTMLDivElement>) => {

    e.preventDefault()

    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)

    setFormData({ ...formData, documents: [...formData.documents, ...files] })

  }



  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {

    if (e.target.files) {

      const files = Array.from(e.target.files) as File[]

      setFormData({ ...formData, documents: [...formData.documents, ...files] })

    }

  }

  const removeFile = (index: number) => {
    const newDocuments = formData.documents.filter((_, i) => i !== index)
    setFormData({ ...formData, documents: newDocuments })
  }

  if (!isOpen) return null

  return (

    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ease-in-out ${isSidebarExpanded ? 'lg:pl-60' : 'lg:pl-20'}`}>

      {/* Backdrop */}

      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-all duration-300 ease-in-out animate-in fade-in duration-300"
        onClick={onClose}
      />

      {/* Modal Content (Explore UI) */}

      <div
        className="relative w-[95%] max-w-[1300px] h-[90vh] bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-800 overflow-hidden z-10"
        style={{ transition: 'all 0.5s cubic-bezier(0.4, 0.0, 0.2, 1)' }}
      >

        {/* Initialization Overlay */}
        {!useGlobalLoader && isInitializing && (
          <MultiStepLoader loadingStates={initLoadingStates} loading={isInitializing} duration={1200} loop={true} />
        )}

        {/* Error Overlay */}
        {initError && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-lg">
            <div className="bg-[#2A2A2E] border border-red-800 rounded-xl p-6 max-w-sm mx-4 text-center">
              <div className="h-8 w-8 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <X className="h-5 w-5 text-red-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">Initialization Failed</h3>
              <p className="text-gray-400 text-sm mb-4">{initError}</p>
              <button
                type="button"
                onClick={() => setInitError(null)}
                className="px-4 py-2 text-sm font-medium text-white bg-[#4A4A4E] hover:bg-[#5A5A5E] rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        <form id="project-form" onSubmit={handleSubmit} className="h-full max-h-[85vh] overflow-hidden">
          <div className="max-w-[1400px] mx-auto px-4 py-4">
            {/* Header (Explore 1:1) */}
            <div className="mb-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h1 className="text-2xl font-bold text-white mb-1">Explore</h1>
                  <p className="text-zinc-400 text-xs">
                    This is where your content lives. Discover what's ready to post, spark new ideas and keep your strategy moving forward.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="px-3 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                  >
                    <Grid3x3 className="w-3 h-3" />
                    Action Hub
                  </button>
                  <button
                    type="submit"
                    disabled={!selectedVideo?.url}
                    className="px-3 py-1 bg-white hover:bg-gray-100 text-black rounded-lg text-xs font-medium flex items-center gap-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="w-3 h-3" />
                    Create Project
                  </button>
                </div>
              </div>
            </div>

            {/* Platform Filters (Explore 1:1) */}
            <div className="mb-4 flex items-center gap-1 flex-wrap">
              {platformFilters.map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => handleFilterSelect(filter)}
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium transition-all",
                    activeFilter === filter
                      ? "bg-white text-black"
                      : "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
                  )}
                >
                  {filter}
                </button>
              ))}
            </div>

            {/* Masonry Video Grid */}
            <div className="overflow-y-auto pr-1" style={{ maxHeight: "calc(85vh - 140px)" }}>
              {videosLoading && (
                <div className="text-center text-xs text-gray-400 py-6">
                  Loading your videos...
                </div>
              )}

              {!videosLoading && filteredVideos.length === 0 && (
                <div className="text-center text-xs text-gray-400 py-6">
                  No videos found for {selectedPlatform}
                </div>
              )}

              {!videosLoading && filteredVideos.length > 0 && (
                <Masonry
                  breakpointCols={breakpointColumns}
                  className="flex -ml-4 w-auto"
                  columnClassName="pl-4 bg-clip-padding"
                >
                  {filteredVideos.map((video, index) => (
                    <div
                      key={video.id || index}
                      className="mb-4"
                    >
                      <div
                        className={cn(
                          "group cursor-pointer animate-in fade-in zoom-in-95 duration-500 rounded-2xl overflow-hidden bg-zinc-900 border transition-all",
                          selectedVideo?.id === video.id 
                            ? "ring-2 ring-purple-500 border-purple-500" 
                            : "border-zinc-800 hover:border-zinc-700"
                        )}
                        style={{ animationDelay: `${index * 50}ms` }}
                        onClick={() => setSelectedVideo(video)}
                      >
                        {/* Video Thumbnail */}
                        <div className="relative w-full bg-[#3A3A3E] transition-all duration-300 ease-in-out group-hover:shadow-lg group-hover:shadow-purple-500/20">
                          <img
                            src={video.thumbnail}
                            alt={video.title}
                            className="w-full h-auto object-cover transition-all duration-500 ease-out group-hover:scale-105"
                            loading="lazy"
                          />

                          {/* Duration Badge */}
                          {video.durationText && (
                            <div className="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 bg-black/80 rounded text-[9px] text-white font-semibold transition-all duration-300 group-hover:bg-black/90">
                              {video.durationText}
                            </div>
                          )}

                          {/* Hover Overlay */}
                          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 ease-out flex items-center justify-center">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                setSelectedVideo(video)
                              }}
                              className="px-3 py-1.5 bg-white text-black text-[10px] font-semibold rounded-md hover:bg-gray-100 transition-all duration-300 transform translate-y-3 group-hover:translate-y-0 opacity-0 group-hover:opacity-100 hover:scale-105"
                            >
                              Select
                            </button>
                          </div>
                        </div>

                        {/* Post Meta Information */}
                        <div className="p-3 bg-zinc-900">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium text-white capitalize">{video.platform}</span>
                            <span className="text-zinc-600">•</span>
                            <span className="text-xs text-zinc-400">Post</span>
                          </div>
                          
                          <h3 className="font-semibold text-white mb-1 text-sm line-clamp-2">{video.title}</h3>
                          <p className="text-xs text-zinc-400 line-clamp-2 mb-3">
                            {video.channel} • {video.viewsText} • {video.timeText}
                          </p>

                          {/* Action Buttons */}
                          <div className="flex items-center gap-1">
                            <button 
                              type="button"
                              className="flex-1 px-3 py-1 bg-white hover:bg-gray-100 text-black rounded-lg text-xs font-medium transition-colors"
                            >
                              Smart Schedule
                            </button>
                            <button 
                              type="button"
                              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg text-xs font-medium transition-colors"
                            >
                              Post Now
                            </button>
                            <button 
                              type="button"
                              className="p-1 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg transition-colors"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                              </svg>
                            </button>
                            <button 
                              type="button"
                              className="p-1 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 rounded-lg transition-colors"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </Masonry>
              )}
            </div>
          </div>
        </form>
      </div>

      {/* Global Masonry Styles */}
      <style jsx global>{`
        .masonry-grid {
          display: flex;
          margin-left: -16px;
          width: auto;
        }
        .masonry-grid_column {
          padding-left: 16px;
          background-clip: padding-box;
        }
      `}</style>
    </div>
  )
}