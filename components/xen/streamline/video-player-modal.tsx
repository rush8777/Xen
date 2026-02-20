"use client"

import React, { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import {
  X,
  ChevronLeft,
  ChevronRight,
  Download,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Settings,
  ChevronDown,
  ExternalLink,
} from "lucide-react"

/* ─── Platform badge colours ─── */
const PLATFORM_COLORS: Record<string, string> = {
  youtube:     "#FF0000",
  facebook:    "#1877F2",
  instagram:   "#E1306C",
  twitter:     "#1DA1F2",
  tiktok:      "#69C9D0",
  vimeo:       "#1AB7EA",
  twitch:      "#9146FF",
  dailymotion: "#0066DC",
  rumble:      "#85C742",
  streamable:  "#00B2FF",
  loom:        "#625DF5",
  wistia:      "#54BBFF",
  direct:      "#22c55e",
  unknown:     "#71717a",
}

/* ─── Platform SVG logos (inline, no external deps) ─── */
const PlatformIcon = ({ platform }: { platform: string }) => {
  const color = PLATFORM_COLORS[platform] ?? "#71717a"
  return (
    <span
      className="inline-flex items-center justify-center w-4 h-4 rounded-sm text-[9px] font-black text-white flex-shrink-0"
      style={{ background: color }}
    >
      {platform[0].toUpperCase()}
    </span>
  )
}

/* ─── Video embed resolver ─── */
export type VideoPlatform =
  | "youtube"
  | "facebook"
  | "instagram"
  | "twitter"
  | "tiktok"
  | "vimeo"
  | "twitch"
  | "dailymotion"
  | "rumble"
  | "streamable"
  | "loom"
  | "wistia"
  | "direct"
  | "unknown"

export type EmbedType = "iframe" | "native" | "unsupported"

export type VideoEmbedInfo = {
  platform: VideoPlatform
  /** "iframe"      → render <iframe src={embedUrl} />
   *  "native"      → render <video src={originalUrl} />
   *  "unsupported" → show a "cannot embed" message with a link
   */
  type: EmbedType
  /** Ready-to-use embed URL (only set when type === "iframe") */
  embedUrl?: string
  /** Original URL (always set) */
  originalUrl: string
  /** Human-readable platform name */
  label: string
  /** Whether platform supports autoplay via embed params */
  supportsAutoplay: boolean
}

/* ─── helpers ─── */

function qs(url: URL, key: string) {
  return url.searchParams.get(key) ?? ""
}

/* ─── resolvers ─── */

function resolveYouTube(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  let videoId = ""

  if (host === "youtu.be") {
    videoId = url.pathname.slice(1).split("/")[0]
  } else if (host === "youtube.com" || host === "m.youtube.com") {
    if (url.pathname.startsWith("/watch")) {
      videoId = qs(url, "v")
    } else if (url.pathname.startsWith("/shorts/") || url.pathname.startsWith("/live/")) {
      videoId = url.pathname.split("/")[2]
    } else if (url.pathname.startsWith("/embed/")) {
      videoId = url.pathname.split("/")[2]
    }
  }

  if (!videoId) return null

  const params = new URLSearchParams({
    autoplay: "1",
    rel: "0",
    modestbranding: "1",
  })

  return {
    platform: "youtube",
    type: "iframe",
    embedUrl: `https://www.youtube.com/embed/${videoId}?${params}`,
    originalUrl: url.href,
    label: "YouTube",
    supportsAutoplay: true,
  }
}

function resolveFacebook(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  const isVideo =
    (host === "facebook.com" && url.pathname.includes("/videos/")) ||
    host === "fb.watch"

  if (!isVideo) return null

  const encoded = encodeURIComponent(url.href)
  return {
    platform: "facebook",
    type: "iframe",
    embedUrl: `https://www.facebook.com/plugins/video.php?href=${encoded}&show_text=false&autoplay=true&mute=0`,
    originalUrl: url.href,
    label: "Facebook",
    supportsAutoplay: true,
  }
}

function resolveInstagram(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "instagram.com") return null

  const isMedia =
    url.pathname.startsWith("/p/") ||
    url.pathname.startsWith("/reel/") ||
    url.pathname.startsWith("/tv/")

  if (!isMedia) return null

  // Extract shortcode: /p/<shortcode>/ or /reel/<shortcode>/
  const shortcode = url.pathname.split("/").filter(Boolean)[1]
  if (!shortcode) return null

  return {
    platform: "instagram",
    type: "iframe",
    embedUrl: `https://www.instagram.com/p/${shortcode}/embed/`,
    originalUrl: url.href,
    label: "Instagram",
    supportsAutoplay: false, // Instagram embeds do not autoplay
  }
}

function resolveTwitter(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "twitter.com" && host !== "x.com") return null

  // Pattern: /<user>/status/<tweetId>
  const parts = url.pathname.split("/").filter(Boolean)
  const statusIdx = parts.indexOf("status")
  if (statusIdx === -1 || !parts[statusIdx + 1]) return null

  const tweetId = parts[statusIdx + 1]

  return {
    platform: "twitter",
    type: "iframe",
    embedUrl: `https://platform.twitter.com/embed/Tweet.html?id=${tweetId}&theme=dark`,
    originalUrl: url.href,
    label: "X (Twitter)",
    supportsAutoplay: false,
  }
}

function resolveTikTok(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "tiktok.com") return null

  // Pattern: /@<user>/video/<videoId>
  const match = url.pathname.match(/\/video\/(\d+)/)
  if (!match) return null

  const videoId = match[1]
  return {
    platform: "tiktok",
    type: "iframe",
    embedUrl: `https://www.tiktok.com/embed/v2/${videoId}`,
    originalUrl: url.href,
    label: "TikTok",
    supportsAutoplay: false,
  }
}

function resolveVimeo(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "vimeo.com" && host !== "player.vimeo.com") return null

  // Standard: /123456789  or  /video/123456789
  const match = url.pathname.match(/\/(?:video\/)?(\d+)/)
  if (!match) return null

  const videoId = match[1]
  const params = new URLSearchParams({ autoplay: "1", color: "ffffff" })
  return {
    platform: "vimeo",
    type: "iframe",
    embedUrl: `https://player.vimeo.com/video/${videoId}?${params}`,
    originalUrl: url.href,
    label: "Vimeo",
    supportsAutoplay: true,
  }
}

function resolveTwitch(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "twitch.tv" && host !== "clips.twitch.tv") return null

  const parent = typeof window !== "undefined" ? window.location.hostname : "localhost"
  const parts = url.pathname.split("/").filter(Boolean)

  // VOD: /videos/<id>
  if (parts[0] === "videos" && parts[1]) {
    const params = new URLSearchParams({ video: parts[1], parent, autoplay: "true" })
    return {
      platform: "twitch",
      type: "iframe",
      embedUrl: `https://player.twitch.tv/?${params}`,
      originalUrl: url.href,
      label: "Twitch VOD",
      supportsAutoplay: true,
    }
  }

  // Clip: clips.twitch.tv/<slug> or twitch.tv/<channel>/clip/<slug>
  if (host === "clips.twitch.tv" || (parts[1] === "clip" && parts[2])) {
    const slug = host === "clips.twitch.tv" ? parts[0] : parts[2]
    const params = new URLSearchParams({ clip: slug, parent, autoplay: "true" })
    return {
      platform: "twitch",
      type: "iframe",
      embedUrl: `https://clips.twitch.tv/embed?${params}`,
      originalUrl: url.href,
      label: "Twitch Clip",
      supportsAutoplay: true,
    }
  }

  // Live channel: /channelName
  if (parts.length === 1) {
    const params = new URLSearchParams({ channel: parts[0], parent, autoplay: "true" })
    return {
      platform: "twitch",
      type: "iframe",
      embedUrl: `https://player.twitch.tv/?${params}`,
      originalUrl: url.href,
      label: "Twitch Live",
      supportsAutoplay: true,
    }
  }

  return null
}

function resolveDailymotion(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "dailymotion.com" && host !== "dai.ly") return null

  let videoId = ""
  if (host === "dai.ly") {
    videoId = url.pathname.slice(1)
  } else {
    const match = url.pathname.match(/\/video\/([a-zA-Z0-9]+)/)
    if (match) videoId = match[1]
  }

  if (!videoId) return null

  const params = new URLSearchParams({ autoplay: "1", mute: "0" })
  return {
    platform: "dailymotion",
    type: "iframe",
    embedUrl: `https://www.dailymotion.com/embed/video/${videoId}?${params}`,
    originalUrl: url.href,
    label: "Dailymotion",
    supportsAutoplay: true,
  }
}

function resolveRumble(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "rumble.com") return null

  // Already an embed URL
  if (url.pathname.startsWith("/embed/")) {
    return {
      platform: "rumble",
      type: "iframe",
      embedUrl: url.href,
      originalUrl: url.href,
      label: "Rumble",
      supportsAutoplay: true,
    }
  }

  // Public video page: /v<id>-<slug>.html
  const match = url.pathname.match(/\/(v[a-zA-Z0-9]+)/)
  if (match) {
    return {
      platform: "rumble",
      type: "iframe",
      embedUrl: `https://rumble.com/embed/${match[1]}/`,
      originalUrl: url.href,
      label: "Rumble",
      supportsAutoplay: true,
    }
  }

  return null
}

function resolveStreamable(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "streamable.com") return null

  const code = url.pathname.split("/").filter(Boolean)[0]
  if (!code) return null

  return {
    platform: "streamable",
    type: "iframe",
    embedUrl: `https://streamable.com/e/${code}?autoplay=1`,
    originalUrl: url.href,
    label: "Streamable",
    supportsAutoplay: true,
  }
}

function resolveLoom(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "loom.com") return null

  const match = url.pathname.match(/\/share\/([a-f0-9]+)/)
  if (!match) return null

  return {
    platform: "loom",
    type: "iframe",
    embedUrl: `https://www.loom.com/embed/${match[1]}?autoplay=1`,
    originalUrl: url.href,
    label: "Loom",
    supportsAutoplay: true,
  }
}

function resolveWistia(url: URL): VideoEmbedInfo | null {
  const host = url.hostname
  const isWistia = host.endsWith("wistia.com") || host.endsWith("wi.st")
  if (!isWistia) return null

  // fast.wistia.com/embed/medias/<id>.jsonp  or  *.wistia.com/medias/<id>
  const match = url.pathname.match(/\/(?:embed\/)?medias\/([a-zA-Z0-9]+)/)
  if (!match) return null

  return {
    platform: "wistia",
    type: "iframe",
    embedUrl: `https://fast.wistia.com/embed/medias/${match[1]}`,
    originalUrl: url.href,
    label: "Wistia",
    supportsAutoplay: true,
  }
}

function resolveDirectVideo(urlStr: string): VideoEmbedInfo | null {
  const directExts = [".mp4", ".webm", ".ogg", ".mov", ".m4v"]
  const lower = urlStr.toLowerCase().split("?")[0]
  if (directExts.some(ext => lower.endsWith(ext))) {
    return {
      platform: "direct",
      type: "native",
      originalUrl: urlStr,
      label: "Direct Video",
      supportsAutoplay: true,
    }
  }
  return null
}

/* ─── main export ─── */

/**
 * Given any video URL string, returns a VideoEmbedInfo describing
 * how to render it inside the player modal.
 */
export function resolveVideoEmbed(rawUrl: string): VideoEmbedInfo {
  const trimmed = rawUrl.trim()

  // Try direct video first (no URL parsing needed)
  const direct = resolveDirectVideo(trimmed)
  if (direct) return direct

  let url: URL
  try {
    url = new URL(trimmed)
  } catch {
    return {
      platform: "unknown",
      type: "unsupported",
      originalUrl: trimmed,
      label: "Unknown",
      supportsAutoplay: false,
    }
  }

  const resolvers = [
    resolveYouTube,
    resolveFacebook,
    resolveInstagram,
    resolveTwitter,
    resolveTikTok,
    resolveVimeo,
    resolveTwitch,
    resolveDailymotion,
    resolveRumble,
    resolveStreamable,
    resolveLoom,
    resolveWistia,
  ]

  for (const resolve of resolvers) {
    const result = resolve(url)
    if (result) return result
  }

  return {
    platform: "unknown",
    type: "unsupported",
    originalUrl: trimmed,
    label: "Unknown",
    supportsAutoplay: false,
  }
}

/**
 * Quick helper – returns true if URL is from a known embeddable platform.
 */
export function isEmbeddable(url: string): boolean {
  return resolveVideoEmbed(url).type !== "unsupported"
}

/**
 * Returns a human-readable platform label for a URL.
 */
export function getPlatformLabel(url: string): string {
  return resolveVideoEmbed(url).label
}

type Server = { id: string; label: string }
const DEFAULT_SERVERS: Server[] = [
  { id: "myth-16", label: "16 Myth" },
  { id: "myth-17", label: "17 Myth" },
  { id: "nova-1",  label: "1 Nova"  },
  { id: "nova-2",  label: "2 Nova"  },
]

type Props = {
  open: boolean
  onClose: () => void
  title?: string
  onPrev?: () => void
  onNext?: () => void
  /**
   * Video URL — any supported platform URL or direct mp4/webm link.
   * The modal auto-detects the platform and renders the right embed.
   */
  src?: string
  /** Fallback poster image for native video or placeholder */
  poster?: string
  servers?: Server[]
  activeServerId?: string
  onServerChange?: (id: string) => void
}

export default function VideoPlayerModal({
  open,
  onClose,
  title = "Video",
  onPrev,
  onNext,
  src,
  poster,
  servers = DEFAULT_SERVERS,
  activeServerId,
  onServerChange,
}: Props) {
  /* ── native video state (only used for direct/mp4) ── */
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying,    setIsPlaying]    = useState(false)
  const [isMuted,      setIsMuted]      = useState(false)
  const [progress,     setProgress]     = useState(0)
  const [duration,     setDuration]     = useState(0)
  const [currentTime,  setCurrentTime]  = useState(0)
  const [showControls, setShowControls] = useState(true)

  /* ── server dropdown ── */
  const [serverDropdownOpen, setServerDropdownOpen] = useState(false)
  const [selectedServer, setSelectedServer] = useState(
    activeServerId ?? servers[0]?.id ?? ""
  )

  /* ── collapse video area ── */
  const [collapsed, setCollapsed] = useState(false)

  const controlsTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const overlayRef    = useRef<HTMLDivElement>(null)

  /* ── resolve embed info whenever src changes ── */
  const embedInfo: VideoEmbedInfo | null = src ? resolveVideoEmbed(src) : null
  const isNative   = embedInfo?.type === "native"
  const isIframe   = embedInfo?.type === "iframe"
  const isUnknown  = !embedInfo || embedInfo.type === "unsupported"

  /* ── lock body scroll ── */
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : ""
    return () => { document.body.style.overflow = "" }
  }, [open])

  /* ── keyboard shortcuts ── */
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
      if (e.key === " " && isNative) { e.preventDefault(); togglePlay() }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, isPlaying, isNative])

  /* ── auto-hide controls ── */
  const resetControlsTimer = () => {
    setShowControls(true)
    if (controlsTimer.current) clearTimeout(controlsTimer.current)
    controlsTimer.current = setTimeout(() => setShowControls(false), 3000)
  }
  useEffect(() => {
    if (open) resetControlsTimer()
    return () => { if (controlsTimer.current) clearTimeout(controlsTimer.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  if (!open) return null

  /* ── native video helpers ── */
  const togglePlay = () => {
    const v = videoRef.current
    if (!v) return
    if (v.paused) { v.play(); setIsPlaying(true) }
    else          { v.pause(); setIsPlaying(false) }
  }
  const toggleMute = () => {
    const v = videoRef.current
    if (!v) return
    v.muted = !v.muted
    setIsMuted(v.muted)
  }
  const handleTimeUpdate = () => {
    const v = videoRef.current
    if (!v) return
    setCurrentTime(v.currentTime)
    setProgress(v.duration ? (v.currentTime / v.duration) * 100 : 0)
  }
  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const v = videoRef.current
    if (!v || !v.duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    v.currentTime = ((e.clientX - rect.left) / rect.width) * v.duration
  }
  const fmt = (s: number) => {
    if (!isFinite(s)) return "0:00"
    const m   = Math.floor(s / 60)
    const sec = Math.floor(s % 60).toString().padStart(2, "0")
    return `${m}:${sec}` 
  }

  const handleServerSelect = (id: string) => {
    setSelectedServer(id)
    setServerDropdownOpen(false)
    onServerChange?.(id)
  }
  const selectedServerLabel = servers.find(s => s.id === selectedServer)?.label ?? "Server"

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose()
  }

  /* ─────────────────── render ─────────────────── */
  return (
    <div
      ref={overlayRef}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      style={{ animation: "vpm-fadeIn 150ms ease" }}
    >
      <style>{`
        @keyframes vpm-fadeIn  { from{opacity:0} to{opacity:1} }
        @keyframes vpm-slideUp { from{opacity:0;transform:translateY(24px) scale(.97)} to{opacity:1;transform:translateY(0) scale(1)} }
      `}</style>

      {/* ── Modal shell ── */}
      <div
        className="relative flex flex-col w-[92vw] max-w-5xl rounded-2xl overflow-hidden shadow-2xl"
        style={{ background: "#0a0a0a", animation: "vpm-slideUp 200ms ease", maxHeight: "90vh" }}
        onMouseMove={resetControlsTimer}
      >
        {/* ══ TOP BAR ══ */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#111111] border-b border-white/5 flex-shrink-0">
          {/* Left: nav + title + platform badge */}
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={onPrev}
              disabled={!onPrev}
              className="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-default transition-colors flex-shrink-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>

            {embedInfo && (
              <PlatformIcon platform={embedInfo.platform} />
            )}

            <span className="text-sm font-medium text-white tracking-wide select-none truncate">
              {title}
            </span>

            {embedInfo && (
              <span className="hidden sm:inline text-[10px] text-zinc-500 flex-shrink-0">
                via {embedInfo.label}
              </span>
            )}

            <button
              onClick={onNext}
              disabled={!onNext}
              className="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-default transition-colors flex-shrink-0"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Right: hint + server + download + close */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {isIframe && (
              <span className="hidden md:block text-xs text-zinc-500 select-none">
                Video not loading? Try changing server →
              </span>
            )}

            {/* Server dropdown (only shown for iframe embeds) */}
            {isIframe && (
              <div className="relative">
                <button
                  onClick={() => setServerDropdownOpen(v => !v)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1e1e1e] border border-white/10 text-xs text-white hover:bg-[#2a2a2a] transition-colors"
                >
                  <span className="text-zinc-400 text-[10px] mr-0.5">▣</span>
                  {selectedServerLabel}
                  <ChevronDown className="h-3 w-3 text-zinc-400 ml-0.5" />
                </button>

                {serverDropdownOpen && (
                  <div className="absolute right-0 top-full mt-1 w-36 rounded-lg bg-[#1a1a1a] border border-white/10 shadow-xl z-10 overflow-hidden">
                    {servers.map(s => (
                      <button
                        key={s.id}
                        onClick={() => handleServerSelect(s.id)}
                        className={cn(
                          "w-full text-left px-3 py-2 text-xs transition-colors",
                          s.id === selectedServer
                            ? "bg-white/10 text-white"
                            : "text-zinc-400 hover:bg-white/5 hover:text-white"
                        )}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Open original in new tab */}
            {src && (
              <a
                href={src}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                title="Open original"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}

            {/* Download (native only) */}
            {isNative && src && (
              <a
                href={src}
                download
                className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <Download className="h-4 w-4" />
              </a>
            )}

            {/* Close */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* ══ VIDEO AREA ══ */}
        <div
          className={cn(
            "relative bg-black transition-all duration-300 flex-shrink-0",
            collapsed ? "h-0 overflow-hidden" : "aspect-video"
          )}
        >

          {/* ── iframe embed (YouTube, Facebook, Vimeo, etc.) ── */}
          {isIframe && embedInfo?.embedUrl && (
            <iframe
              key={embedInfo.embedUrl}
              src={embedInfo.embedUrl}
              className="w-full h-full border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
              title={title}
            />
          )}

          {/* ── native <video> (direct mp4/webm) ── */}
          {isNative && src && (
            <div className="w-full h-full" onClick={togglePlay} style={{ cursor: "pointer" }}>
              <video
                ref={videoRef}
                src={src}
                poster={poster}
                className="w-full h-full object-contain"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={() => setDuration(videoRef.current?.duration ?? 0)}
                onEnded={() => setIsPlaying(false)}
              />

              {/* Native controls overlay */}
              <div
                className={cn(
                  "absolute inset-0 flex flex-col justify-end transition-opacity duration-300",
                  showControls ? "opacity-100" : "opacity-0"
                )}
                onClick={e => e.stopPropagation()}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                <div className="relative px-4 pb-4 space-y-2">
                  {/* Scrubber */}
                  <div
                    className="w-full h-1 bg-white/20 rounded-full cursor-pointer group"
                    onClick={handleSeek}
                  >
                    <div
                      className="h-full bg-white rounded-full relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                  {/* Buttons */}
                  <div className="flex items-center gap-3">
                    <button onClick={togglePlay} className="text-white hover:text-zinc-300 transition-colors">
                      {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </button>
                    <button onClick={toggleMute} className="text-white hover:text-zinc-300 transition-colors">
                      {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                    </button>
                    <span className="text-xs text-zinc-400 select-none tabular-nums">
                      {fmt(currentTime)} / {fmt(duration)}
                    </span>
                    <div className="flex-1" />
                    <button className="text-white hover:text-zinc-300 transition-colors">
                      <Settings className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => videoRef.current?.requestFullscreen()}
                      className="text-white hover:text-zinc-300 transition-colors"
                    >
                      <Maximize2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Unsupported / no source ── */}
          {(isUnknown || !src) && (
            <div className="w-full h-full flex flex-col items-center justify-center gap-4 select-none px-6 text-center">
              {poster ? (
                <img src={poster} alt="Poster" className="absolute inset-0 w-full h-full object-cover opacity-20" />
              ) : null}
              <div className="relative z-10 space-y-2">
                <p className="text-zinc-400 text-sm">
                  {!src
                    ? "No video source provided."
                    : "This URL cannot be embedded directly."}
                </p>
                {src && (
                  <a
                    href={src}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
                  >
                    Open in new tab <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(v => !v)}
            className="absolute top-3 right-3 p-1.5 rounded-lg bg-black/50 text-zinc-300 hover:text-white hover:bg-black/70 transition-all z-10"
          >
            <ChevronDown className={cn("h-4 w-4 transition-transform duration-200", collapsed && "rotate-180")} />
          </button>
        </div>

        {/* ── Platform info footer (shown for iframe embeds) ── */}
        {isIframe && embedInfo && (
          <div className="flex items-center gap-2 px-4 py-2 bg-[#111111] border-t border-white/5 flex-shrink-0">
            <PlatformIcon platform={embedInfo.platform} />
            <span className="text-[11px] text-zinc-500">
              Embedded from <span className="text-zinc-400">{embedInfo.label}</span>
              {!embedInfo.supportsAutoplay && (
                <span className="ml-2 text-zinc-600">· Autoplay not supported on this platform</span>
              )}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
