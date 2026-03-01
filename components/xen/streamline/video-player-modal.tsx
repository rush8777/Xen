"use client"

import React, { useEffect, useMemo, useRef, useState } from "react"
import {
  X,
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  Volume2,
  VolumeX,
  ExternalLink,
} from "lucide-react"

const PLATFORM_COLORS: Record<string, string> = {
  youtube: "#FF0000",
  facebook: "#1877F2",
  instagram: "#E1306C",
  twitter: "#1DA1F2",
  tiktok: "#69C9D0",
  vimeo: "#1AB7EA",
  twitch: "#9146FF",
  dailymotion: "#0066DC",
  rumble: "#85C742",
  streamable: "#00B2FF",
  loom: "#625DF5",
  wistia: "#54BBFF",
  direct: "#22c55e",
  unknown: "#71717a",
}

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
  type: EmbedType
  embedUrl?: string
  originalUrl: string
  label: string
  supportsAutoplay: boolean
}

function qs(url: URL, key: string) {
  return url.searchParams.get(key) ?? ""
}

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

  const params = new URLSearchParams({ autoplay: "1", rel: "0", modestbranding: "1" })
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
  const isVideo = (host === "facebook.com" && url.pathname.includes("/videos/")) || host === "fb.watch"
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
  const isMedia = url.pathname.startsWith("/p/") || url.pathname.startsWith("/reel/") || url.pathname.startsWith("/tv/")
  if (!isMedia) return null
  const shortcode = url.pathname.split("/").filter(Boolean)[1]
  if (!shortcode) return null
  return {
    platform: "instagram",
    type: "iframe",
    embedUrl: `https://www.instagram.com/p/${shortcode}/embed/`,
    originalUrl: url.href,
    label: "Instagram",
    supportsAutoplay: false,
  }
}

function resolveTwitter(url: URL): VideoEmbedInfo | null {
  const host = url.hostname.replace("www.", "")
  if (host !== "twitter.com" && host !== "x.com") return null
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
  if (directExts.some((ext) => lower.endsWith(ext))) {
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

export function resolveVideoEmbed(rawUrl: string): VideoEmbedInfo {
  const trimmed = rawUrl.trim()
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

export function isEmbeddable(url: string): boolean {
  return resolveVideoEmbed(url).type !== "unsupported"
}

export function getPlatformLabel(url: string): string {
  return resolveVideoEmbed(url).label
}

type Server = { id: string; label: string }
const DEFAULT_SERVERS: Server[] = [
  { id: "myth-16", label: "16 Myth" },
  { id: "myth-17", label: "17 Myth" },
  { id: "nova-1", label: "1 Nova" },
  { id: "nova-2", label: "2 Nova" },
]

type Props = {
  open: boolean
  onClose: () => void
  title?: string
  onPrev?: () => void
  onNext?: () => void
  src?: string
  startAtSeconds?: number
  onPlaybackTimeChange?: (seconds: number) => void
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
  startAtSeconds = 0,
  onPlaybackTimeChange,
  poster,
  servers = DEFAULT_SERVERS,
  activeServerId,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const trackRef = useRef<HTMLDivElement>(null)
  const animRef = useRef<number | null>(null)
  const overlayRef = useRef<HTMLDivElement>(null)

  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(30)
  const [volume, setVolume] = useState(0.8)
  const [isMuted, setIsMuted] = useState(false)
  const [tooltip, setTooltip] = useState<{ x: number; time: number; label: string | null; color: string } | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isHoveringTrack, setIsHoveringTrack] = useState(false)

  const embedInfo: VideoEmbedInfo | null = src ? resolveVideoEmbed(src) : null
  const isNative = embedInfo?.type === "native"
  const isIframe = embedInfo?.type === "iframe"
  const isUnknown = !embedInfo || embedInfo.type === "unsupported"
  const startSeconds = Math.max(0, Math.floor(startAtSeconds || 0))
  const embedUrlWithStart = embedInfo ? withStartAt(embedInfo, startSeconds) : undefined
  const effectiveServer = activeServerId ?? servers[0]?.id ?? ""

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : ""
    return () => {
      document.body.style.overflow = ""
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
      if (e.key === " ") {
        e.preventDefault()
        togglePlay()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    setCurrentTime(startSeconds)
    onPlaybackTimeChange?.(startSeconds)
  }, [open, startSeconds, onPlaybackTimeChange])

  useEffect(() => {
    if (!open || !isNative || !src) return
    const v = videoRef.current
    if (!v) return
    const apply = () => {
      v.currentTime = startSeconds
      v.volume = isMuted ? 0 : volume
      v.muted = isMuted
      setCurrentTime(startSeconds)
    }
    if (v.readyState >= 1) {
      apply()
      return
    }
    v.addEventListener("loadedmetadata", apply, { once: true })
    return () => v.removeEventListener("loadedmetadata", apply)
  }, [open, isNative, src, startSeconds, volume, isMuted])

  useEffect(() => {
    if (!open || isNative) return
    if (!isPlaying) {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      animRef.current = null
      return
    }
    const tick = () => {
      setCurrentTime((prev) => {
        const next = prev + 0.05
        if (next >= duration) {
          setIsPlaying(false)
          onPlaybackTimeChange?.(duration)
          return duration
        }
        onPlaybackTimeChange?.(next)
        return next
      })
      animRef.current = requestAnimationFrame(tick)
    }
    animRef.current = requestAnimationFrame(tick)
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      animRef.current = null
    }
  }, [open, isNative, isPlaying, duration, onPlaybackTimeChange])

  const sections = useMemo(() => {
    const labels = ["Cold Open", "Act I", "Ad Break", "Act II", "Credits"]
    const colors = ["#a78bfa", "#34d399", "#fbbf24", "#f87171", "#60a5fa"]
    const d = Math.max(30, Math.floor(duration || 30))
    const part = d / labels.length
    return labels.map((label, idx) => ({
      label,
      start: Math.floor(idx * part),
      end: idx === labels.length - 1 ? d : Math.floor((idx + 1) * part),
      color: colors[idx],
    }))
  }, [duration])

  const activeSection = useMemo(
    () => sections.find((s) => currentTime >= s.start && currentTime < s.end) || null,
    [sections, currentTime]
  )

  const progress = Math.max(0, Math.min(100, (currentTime / Math.max(1, duration)) * 100))

  if (!open) return null

  const formatTime = (t: number) => {
    if (!t || Number.isNaN(t)) return "0:00"
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60).toString().padStart(2, "0")
    return `${m}:${s}`
  }

  const togglePlay = () => {
    if (isNative) {
      const v = videoRef.current
      if (!v) return
      if (v.paused) {
        v.play()
        setIsPlaying(true)
      } else {
        v.pause()
        setIsPlaying(false)
      }
      return
    }
    setIsPlaying((p) => !p)
  }

  const toggleMute = () => {
    const next = !isMuted
    setIsMuted(next)
    const v = videoRef.current
    if (v) v.muted = next
  }

  const handleTimeUpdate = () => {
    const v = videoRef.current
    if (!v) return
    setCurrentTime(v.currentTime)
    if (Number.isFinite(v.duration) && v.duration > 0) setDuration(v.duration)
    setIsPlaying(!v.paused)
    onPlaybackTimeChange?.(v.currentTime)
  }

  const getTimeFromEvent = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackRef.current) return 0
    const rect = trackRef.current.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    return ratio * duration
  }

  const skipTo = (t: number) => {
    const next = Math.max(0, Math.min(duration, t))
    setCurrentTime(next)
    onPlaybackTimeChange?.(next)
    if (isNative && videoRef.current) videoRef.current.currentTime = next
  }

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    skipTo(getTimeFromEvent(e))
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackRef.current) return
    const rect = trackRef.current.getBoundingClientRect()
    const t = getTimeFromEvent(e)
    const sec = sections.find((s) => t >= s.start && t < s.end)
    setTooltip({ x: e.clientX - rect.left, time: t, label: sec?.label || null, color: sec?.color || "#fff" })
    if (isDragging) skipTo(t)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseFloat(e.target.value)
    setVolume(v)
    setIsMuted(v === 0)
    if (videoRef.current) {
      videoRef.current.volume = v
      videoRef.current.muted = v === 0
    }
  }

  return (
    <div ref={overlayRef} className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" style={{ minHeight: "100vh", padding: 24 }} onClick={(e) => { if (e.target === overlayRef.current) onClose() }}>
      <div className="w-[min(920px,92vw)] overflow-hidden rounded-2xl border border-[#1e1e3a] bg-[#0d0d1a] font-mono shadow-[0_40px_80px_#00000088]">
        <div className="flex items-center justify-between border-b border-[#1a1a2e] px-5 py-3">
          <div className="flex items-center gap-2">
            <button onClick={onPrev} disabled={!onPrev} className="rounded p-1 text-zinc-500 hover:text-zinc-300 disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button>
            <span className="h-2 w-2 rounded-full bg-violet-400 shadow-[0_0_8px_#a78bfa]" />
            <span className="text-xs font-semibold tracking-wider text-violet-200">{title}</span>
            {embedInfo && <span className="text-[10px] text-zinc-500">via {embedInfo.label}</span>}
            <button onClick={onNext} disabled={!onNext} className="rounded p-1 text-zinc-500 hover:text-zinc-300 disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button>
          </div>
          <div className="flex items-center gap-1">
            {src && <a href={src} target="_blank" rel="noopener noreferrer" className="rounded p-1 text-zinc-500 hover:text-zinc-300"><ExternalLink className="h-4 w-4" /></a>}
            <button onClick={onClose} className="rounded p-1 text-zinc-500 hover:text-zinc-300"><X className="h-4 w-4" /></button>
          </div>
        </div>

        <div className="relative aspect-video overflow-hidden bg-[#0a0a16]">
          {isIframe && embedUrlWithStart && (
            <iframe key={`${embedUrlWithStart}:${effectiveServer}`} src={embedUrlWithStart} className="absolute inset-0 h-full w-full border-0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen title={title} />
          )}
          {isNative && src && (
            <video ref={videoRef} src={src} poster={poster} className="absolute inset-0 h-full w-full object-cover" onTimeUpdate={handleTimeUpdate} onLoadedMetadata={() => setDuration(videoRef.current?.duration || 30)} onEnded={() => setIsPlaying(false)} />
          )}
          {(isUnknown || !src) && <div className="absolute inset-0 flex items-center justify-center text-zinc-500">Unsupported source</div>}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.04),transparent_65%)]" />
          <div className="pointer-events-none absolute inset-0" style={{ backgroundColor: activeSection?.color || "#1e1e2e", opacity: isPlaying ? 0.12 : 0.06 }} />
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3">
            <button onClick={togglePlay} className="flex h-16 w-16 items-center justify-center rounded-full border border-white/25 bg-black/40 text-white backdrop-blur">{isPlaying ? <Pause className="h-7 w-7" /> : <Play className="h-7 w-7" />}</button>
            {activeSection && <span className="rounded-full px-3 py-1 text-[11px] font-semibold text-black" style={{ backgroundColor: activeSection.color }}>{activeSection.label}</span>}
          </div>
        </div>

        <div className="px-5 pb-4 pt-2">
          <div ref={trackRef} onClick={handleSeek} onMouseMove={handleMouseMove} onMouseLeave={() => { setTooltip(null); setIsHoveringTrack(false) }} onMouseEnter={() => setIsHoveringTrack(true)} onMouseDown={(e) => { setIsDragging(true); handleSeek(e) }} onMouseUp={() => setIsDragging(false)} className="relative py-2">
            {tooltip && (
              <div className="pointer-events-none absolute bottom-[calc(100%+6px)] z-10 -translate-x-1/2 rounded-md border bg-[#111122] px-2.5 py-1 text-[11px] text-zinc-200" style={{ left: tooltip.x, borderColor: tooltip.color }}>
                {tooltip.label && <span className="mr-1 font-bold" style={{ color: tooltip.color }}>{tooltip.label}</span>}
                {formatTime(tooltip.time)}
              </div>
            )}
            <div className="relative overflow-hidden rounded bg-[#1a1a2e]" style={{ height: isHoveringTrack ? 8 : 5 }}>
              <div className="absolute left-0 top-0 h-full bg-[#2a2a4a]" style={{ width: `${progress}%` }} />
              {sections.map((s, i) => (
                <div key={i} className="absolute top-0 h-full" style={{ left: `${(s.start / duration) * 100}%`, width: `${((s.end - s.start) / duration) * 100}%`, backgroundColor: s.color, opacity: activeSection?.label === s.label ? 0.95 : 0.55 }} />
              ))}
              {sections.slice(0, -1).map((s, i) => (
                <div key={`gap-${i}`} className="absolute top-[-2px] bottom-[-2px] w-[2px] bg-[#0d0d1a]" style={{ left: `${(s.end / duration) * 100}%` }} />
              ))}
              <div className="pointer-events-none absolute top-1/2 z-10 -translate-y-1/2 rounded-full" style={{ left: `${progress}%`, width: isHoveringTrack ? 14 : 10, height: isHoveringTrack ? 14 : 10, transform: "translate(-50%, -50%)", backgroundColor: activeSection?.color || "#fff", boxShadow: `0 0 8px ${(activeSection?.color || "#fff")}88` }} />
            </div>
          </div>

          <div className="mt-1 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button onClick={() => skipTo(currentTime - 10)} className="rounded px-1 text-xs text-zinc-500 hover:text-zinc-300">-10</button>
              <button onClick={togglePlay} className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-black">{isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}</button>
              <button onClick={() => skipTo(currentTime + 10)} className="rounded px-1 text-xs text-zinc-500 hover:text-zinc-300">+10</button>
              <span className="text-xs"><span style={{ color: activeSection?.color || "#e0e0ff" }}>{formatTime(currentTime)}</span><span className="text-zinc-600"> / </span><span className="text-zinc-500">{formatTime(duration)}</span></span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={toggleMute} className="rounded p-1 text-zinc-500 hover:text-zinc-300">{(isMuted || volume === 0) ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}</button>
              <input type="range" min="0" max="1" step="0.02" value={isMuted ? 0 : volume} onChange={handleVolumeChange} className="w-20 accent-violet-400" />
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {sections.map((s, i) => (
              <button key={i} onClick={() => { skipTo(s.start); setIsPlaying(true) }} className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px]" style={{ borderColor: activeSection?.label === s.label ? s.color : "transparent", backgroundColor: activeSection?.label === s.label ? `${s.color}18` : "transparent" }}>
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                <span style={{ color: activeSection?.label === s.label ? s.color : "#777" }}>{s.label}</span>
                <span className="text-zinc-500">{formatTime(s.start)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function withStartAt(embed: VideoEmbedInfo, startAtSeconds: number): string | undefined {
  if (!embed.embedUrl) return embed.embedUrl
  if (startAtSeconds <= 0) return embed.embedUrl
  try {
    const url = new URL(embed.embedUrl)
    if (embed.platform === "youtube") {
      url.searchParams.set("start", String(startAtSeconds))
      return url.toString()
    }
    if (embed.platform === "vimeo") {
      url.searchParams.set("t", `${startAtSeconds}s`)
      return url.toString()
    }
    if (embed.platform === "dailymotion") {
      url.searchParams.set("start", String(startAtSeconds))
      return url.toString()
    }
    return embed.embedUrl
  } catch {
    return embed.embedUrl
  }
}
