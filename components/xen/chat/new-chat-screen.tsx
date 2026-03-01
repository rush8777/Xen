"use client"

import { useEffect, useState } from "react"
import {
  Paperclip,
  Command,
  Navigation,
  Image,
  Settings,
  X,
} from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

interface ApiProject {
  id: number
  name: string
  video_url?: string | null
  thumbnail_url?: string | null
  created_at?: string
}

export type SelectedChatProject = ApiProject

const getThumbnailUrl = (videoUrl?: string | null) => {
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
}

interface NewChatScreenProps {
  onStartChat: (message: string, selectedProject?: SelectedChatProject | null) => void
}

const NewChatScreen = ({ onStartChat }: NewChatScreenProps) => {
  const [input, setInput] = useState("")
  const [projects, setProjects] = useState<ApiProject[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [selectedProject, setSelectedProject] = useState<ApiProject | null>(null)

  const handleStartChat = () => {
    if (input.trim()) {
      onStartChat(input, selectedProject)
      setInput("")
    }
  }

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/projects?limit=12`, { cache: "no-store" })
        if (!res.ok) {
          setProjects([])
          return
        }
        const data = (await res.json()) as ApiProject[]
        const sorted = [...(data || [])].sort((a, b) => {
          const aTime = new Date(a.created_at || 0).getTime()
          const bTime = new Date(b.created_at || 0).getTime()
          return bTime - aTime
        })
        setProjects(sorted)
      } catch {
        setProjects([])
      } finally {
        setLoadingProjects(false)
      }
    }

    loadProjects()
  }, [])

  return (
    <div className="min-h-screen bg-[#0F0F12] flex flex-col items-center justify-between px-6 py-12">
      <div className="w-full max-w-4xl flex flex-col items-start gap-8">
        <div>
          <h1 className="text-white text-3xl font-bold leading-tight tracking-tight">
            Hi, Gustavo
          </h1>
          <h2 className="text-white text-3xl font-bold leading-tight tracking-tight">
            What can{" "}
            <span className="text-blue-400">I help you</span>{" "}
            with?
          </h2>
          <p className="text-zinc-500 text-xs mt-2.5 leading-relaxed">
            Choose a prompt below or write your own to start chatting with Orbita GPT.
          </p>
        </div>

        <div className="w-full rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 overflow-hidden">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or make a request..."
            rows={2}
            className="w-full bg-transparent text-white placeholder-zinc-500 text-xs px-4 pt-3.5 pb-2 resize-none outline-none leading-relaxed"
          />
          {selectedProject && (
            <div className="px-4 pb-2">
              <div className="inline-flex items-center gap-2 rounded-xl bg-zinc-900/80 border border-zinc-800 px-2.5 py-2">
                <div className="w-10 h-10 rounded-md overflow-hidden bg-zinc-800 flex items-center justify-center">
                  {(selectedProject.thumbnail_url || getThumbnailUrl(selectedProject.video_url)) ? (
                    <img
                      src={selectedProject.thumbnail_url || getThumbnailUrl(selectedProject.video_url)}
                      alt={selectedProject.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Image className="w-4 h-4 text-zinc-600" />
                  )}
                </div>
                <div className="min-w-0">
                  <p className="text-zinc-100 text-xs leading-tight truncate max-w-[220px]">{selectedProject.name}</p>
                  <p className="text-zinc-400 text-[10px] leading-tight">Selected video</p>
                </div>
                <button
                  type="button"
                  className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedProject(null)}
                  className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
              <button className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all text-[11px] font-medium">
                <Paperclip className="w-3 h-3" />
                <span>Attach</span>
              </button>
              <button className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800/50 transition-all">
                <Command className="w-3 h-3" />
              </button>
            </div>
            <button
              onClick={handleStartChat}
              className={`p-2 rounded-lg transition-all ${
                input.trim()
                  ? "bg-purple-600 hover:bg-purple-700 text-white"
                  : "bg-zinc-800/50 text-zinc-600 cursor-not-allowed"
              }`}
            >
              <Navigation className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="w-full space-y-2 pt-1">
          <div className="flex items-center justify-between">
            <p className="text-xs text-zinc-400">Created Projects</p>
            {!loadingProjects && <p className="text-[11px] text-zinc-500">{projects.length} total</p>}
          </div>

          {loadingProjects ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/50 animate-pulse"
                >
                  <div className="aspect-[16/9] bg-zinc-800/80" />
                  <div className="px-2 py-2 space-y-1">
                    <div className="h-2 w-5/6 bg-zinc-800 rounded" />
                    <div className="h-2 w-1/2 bg-zinc-800 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : projects.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-4 text-center">
              <p className="text-xs text-zinc-400">No projects yet. Create one to see video cards here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {projects.map((project) => {
                const thumbnail = project.thumbnail_url || getThumbnailUrl(project.video_url)
                return (
                  <button
                    key={project.id}
                    type="button"
                    onClick={() => {
                      setSelectedProject(project)
                    }}
                    className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/50 text-left hover:border-zinc-700 transition-colors"
                  >
                    <div className="aspect-[16/9] overflow-hidden bg-zinc-900">
                      {thumbnail ? (
                        <img
                          src={thumbnail}
                          alt={project.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-zinc-800 to-zinc-900">
                          <Image className="w-5 h-5 text-zinc-600" />
                        </div>
                      )}
                    </div>
                    <div className="px-2 py-2">
                      <p className="text-[10px] leading-snug text-zinc-200 line-clamp-2">{project.name}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <footer className="flex items-center gap-2 text-zinc-600 text-[10px] mt-12">
        <span>2024 Orbita GPT</span>
        <span>-</span>
        <button className="hover:text-zinc-400 transition-colors">Privacy Policy</button>
        <span>-</span>
        <button className="hover:text-zinc-400 transition-colors">Support</button>
      </footer>
    </div>
  )
}

export default NewChatScreen
