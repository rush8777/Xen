"use client"

import { X, Upload, FolderOpen, ChevronDown } from "lucide-react"

import React, { useState, useEffect, useRef, DragEvent, useCallback, ChangeEvent } from "react"

import { useRouter } from "next/navigation"

import { MultiStepLoader } from "@/components/ui/multi-step-loader"

import { useSidebarContext } from "./main/layout"



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
  const [modalSize, setModalSize] = useState<'max-w-sm' | 'max-w-md' | 'max-w-2xl' | 'max-w-3xl' | 'max-w-4xl'>('max-w-md')
  const [videos, setVideos] = useState<LibraryVideo[]>([])
  const [filteredVideos, setFilteredVideos] = useState<LibraryVideo[]>([])
  const [videosLoading, setVideosLoading] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState<LibraryVideo | null>(null)
  const { isSidebarExpanded } = useSidebarContext()
  const [isPlatformDropdownOpen, setIsPlatformDropdownOpen] = useState(false)
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
          // Keep loader visible across navigation; Streamline page will turn it off on mount.
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
          platform: item.platform || platform, // Use API platform or selected platform
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

  const handlePlatformSelect = (platform: string) => {
    setSelectedPlatform(platform)
    setIsPlatformDropdownOpen(false)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isPlatformDropdownOpen) {
        const target = event.target as Element
        if (!target.closest('.platform-dropdown')) {
          setIsPlatformDropdownOpen(false)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isPlatformDropdownOpen])

  // Handle sidebar resize and modal sizing
  useEffect(() => {
    const updateModalSize = () => {
      // Get actual sidebar width from CSS variables or use estimates
      const sidebarWidth = isSidebarExpanded ? 224 : 64 // More accurate sidebar widths (w-56 = 14rem = 224px, w-16 = 4rem = 64px)
      const padding = 32 // Account for modal padding
      const availableWidth = window.innerWidth - sidebarWidth - padding
      
      console.log('Sidebar state:', { isSidebarExpanded, sidebarWidth, availableWidth, windowWidth: window.innerWidth })
      
      // Set modal size based on available width
      if (availableWidth < 640) {
        setModalSize('max-w-sm')
      } else if (availableWidth < 768) {
        setModalSize('max-w-md')
      } else if (availableWidth < 1024) {
        setModalSize('max-w-2xl')
      } else if (availableWidth < 1280) {
        setModalSize('max-w-3xl')
      } else {
        setModalSize('max-w-4xl')
      }
    }

    updateModalSize()
    window.addEventListener('resize', updateModalSize)
    
    // Also update when sidebar state changes
    const timer = setTimeout(updateModalSize, 100) // Small delay for CSS transition
    
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
    
    // Start initialization
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
    } finally {
      // keep initializing true; polling effect will stop it when completed/failed
    }
  }



  const handleSaveDraft = () => {

    console.log("Draft saved:", formData)

    // Add your draft save logic here

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

      {/* Modal - Always show import content */}

      <div className={`relative w-full max-h-[85vh] p-3 rounded-lg bg-white dark:bg-zinc-900/70 border border-zinc-100 dark:border-zinc-800 shadow-sm backdrop-blur-xl flex flex-col transition-all duration-500 ease-in-out ${modalSize} z-10 transform will-change-auto animate-in zoom-in-95 duration-500`} style={{
        transition: 'all 0.5s cubic-bezier(0.4, 0.0, 0.2, 1)',
      }}>

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

        {/* Header */}

        <div className="flex items-start justify-between p-4 pb-2 flex-shrink-0 transition-all duration-300 ease-in-out">

          <div className="flex items-start gap-2.5 transition-all duration-300 ease-in-out">

            <div className="p-1.5 bg-[#3A3A3E] rounded-lg transition-all duration-300 ease-in-out hover:bg-[#4A4A4E] hover:scale-105 transform">

              <FolderOpen className="w-4 h-4 text-white transition-colors duration-300" />

            </div>

            <div className="flex-1 transition-all duration-300 ease-in-out">

              <h2 className="text-lg font-bold text-white mb-0.5 transition-all duration-300 ease-in-out">

                Create New {course?.label || 'Project'}

              </h2>

              <p className="text-[11px] text-gray-400 transition-all duration-300 ease-in-out">

                Create a project to structure your team's workflow.

              </p>

            </div>

          </div>

          {/* Close Button - Top Right */}

          <button

            type="button"

            onClick={onClose}

            className="p-1.5 hover:bg-[#4A4A4E] rounded-lg transition-all duration-300 ease-in-out hover:scale-110 transform"

          >

            <X className="w-4 h-4 text-gray-400 hover:text-white transition-all duration-300 ease-in-out" />

          </button>

        </div>



        {/* Form */}

        <div className="flex flex-col flex-1 min-h-0">

          {/* Project Name & Category - Fixed */}

          <div className="px-4 pb-3 flex-shrink-0">

            <div className="grid grid-cols-2 gap-2">

              <div>

                <label className="block text-[11px] font-medium text-white mb-1">

                  Project name<span className="text-red-500">*</span>

                </label>

                <input

                  type="text"

                  placeholder="Type here"

                  value={formData.projectName}

                  onChange={(e) => setFormData({ ...formData, projectName: e.target.value })}

                  className="w-full px-2.5 py-1.5 text-xs bg-[#3A3A3E] border border-[#4A4A4E] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all duration-300 ease-in-out hover:border-[#5A5A5E]"

                  required

                />

              </div>

              <div>

                <label className="block text-[11px] font-medium text-white mb-1">

                  Project category<span className="text-red-500">*</span>

                </label>

                <div className="relative">

                  <select

                    value={formData.category}

                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}

                    className="w-full px-2.5 py-1.5 text-xs bg-[#3A3A3E] border border-[#4A4A4E] rounded-lg text-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all duration-300 ease-in-out appearance-none cursor-pointer hover:border-[#5A5A5E]"

                    required

                  >

                    <option value="">Choose category</option>

                    <option value="UI/UX Design">UI/UX Design</option>

                    <option value="Branding">Branding</option>

                    <option value="Front End">Front End</option>

                    <option value="Marketing">Marketing</option>

                    <option value="Photography">Photography</option>

                  </select>

                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />

                </div>

              </div>

            </div>

          </div>



          {/* Scrollable Content Area */}

          <form id="project-form" onSubmit={handleSubmit} className="px-4 space-y-3 flex-1 overflow-y-auto min-h-0">

            {/* Import Content - Always show */}

            <div className="flex flex-col h-full -mx-4 animate-in fade-in slide-in-from-left-5 duration-300">

              {/* Header - Fixed */}

              <div className="flex-shrink-0 px-4 pb-3">

                <label className="block text-[11px] font-medium text-white mb-0.5">

                  Import from Library

                </label>

                <p className="text-[10px] text-gray-400">

                  Select videos from your content library to import. {filteredVideos.length} videos found

                </p>

              </div>
              
              {/* Filter Bar */}

              <div className="flex-shrink-0 px-4 pb-3">

                <div className="flex items-center gap-2">

                  <div className="relative platform-dropdown">
                    <button 
                      type="button"
                      onClick={() => setIsPlatformDropdownOpen(!isPlatformDropdownOpen)}
                      className="px-2.5 py-1.5 text-[10px] bg-[#35353A] border border-[#4A4A4E] rounded-lg text-white hover:bg-[#3A3A3E] transition-all duration-300 ease-in-out flex items-center gap-1.5 hover:scale-105 transform hover:border-[#5A5A5E]"
                    >
                      {selectedPlatform}
                      <ChevronDown className="w-3 h-3 transition-transform duration-300" />
                    </button>

                    {/* Dropdown Menu */}
                    {isPlatformDropdownOpen && (
                      <div className="absolute top-full left-0 mt-1 w-40 bg-[#35353A] border border-[#4A4A4E] rounded-lg shadow-lg z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                        {platforms.map((platform) => (
                          <button
                            key={platform}
                            type="button"
                            onClick={() => handlePlatformSelect(platform)}
                            className="w-full px-3 py-2 text-[10px] text-left text-white hover:bg-[#4A4A4E] transition-all duration-200 ease-in-out first:rounded-t-lg last:rounded-b-lg hover:translate-x-1 transform"
                          >
                            {platform}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <button 
                    type="button"
                    className="px-2.5 py-1.5 text-[10px] bg-[#35353A] border border-[#4A4A4E] rounded-lg text-white hover:bg-[#3A3A3E] transition-all duration-300 ease-in-out flex items-center gap-1.5 hover:scale-105 transform hover:border-[#5A5A5E]"
                  >
                    Filters
                  </button>
                </div>
              </div>
              
              {/* Video Grid - Scrollable */}

              <div className="flex-1 overflow-y-auto px-4 pb-2">

                <div className="grid grid-cols-4 gap-3">

                  {videosLoading && (
                    <div className="col-span-4 text-center text-xs text-gray-400 py-6">
                      Loading your videos...
                    </div>
                  )}

                  {!videosLoading && filteredVideos.length === 0 && (
                    <div className="col-span-4 text-center text-xs text-gray-400 py-6">
                      No videos found for {selectedPlatform}
                    </div>
                  )}

                  {!videosLoading && filteredVideos.map((video, index) => (
                    <div 
                      key={video.id || index}
                      className={
                        "group cursor-pointer animate-in fade-in zoom-in-95 duration-500 " +
                        (selectedVideo?.id === video.id ? "ring-2 ring-purple-500 rounded-lg" : "")
                      }
                      style={{ animationDelay: `${index * 50}ms` }}
                      onClick={() => setSelectedVideo(video)}
                    >
                      {/* Thumbnail */}

                      <div className="relative aspect-video rounded-lg overflow-hidden mb-1.5 bg-[#3A3A3E] transition-all duration-300 ease-in-out group-hover:shadow-lg group-hover:shadow-purple-500/20">

                        <img 
                          src={video.thumbnail} 
                          alt={video.title}
                          className="w-full h-full object-cover transition-all duration-500 ease-out group-hover:scale-110"
                        />

                        {/* Duration Badge */}

                        <div className="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 bg-black/80 rounded text-[9px] text-white font-semibold transition-all duration-300 group-hover:bg-black/90">

                          {video.durationText}

                        </div>

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
                       

                      {/* Video Info */}

                      <div className="space-y-0.5 transition-all duration-300 group-hover:translate-y-0.5">

                        <h3 className="text-[11px] text-white font-medium line-clamp-2 leading-tight transition-all duration-300 group-hover:text-purple-400">

                          {video.title}

                        </h3>

                        <p className="text-[9px] text-gray-400 transition-all duration-300 group-hover:text-gray-300">

                          {video.channel} • {video.viewsText} • {video.timeText}

                        </p>

                        <p className="text-[8px] text-gray-500 transition-all duration-300 group-hover:text-gray-400">

                          {video.statsText}

                        </p>

                      </div>

                    </div>
                  ))}
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 pt-2 border-t border-zinc-800 flex-shrink-0 transition-all duration-300 ease-in-out">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white hover:bg-[#4A4A4E] rounded-lg transition-all duration-300 ease-in-out hover:scale-105 transform"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="project-form"
            disabled={!selectedVideo?.url}
            className="px-4 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-all duration-300 ease-in-out flex items-center gap-1.5 hover:scale-105 transform disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            Create Project
          </button>
        </div>
      </div>
    </div>
  )
}
