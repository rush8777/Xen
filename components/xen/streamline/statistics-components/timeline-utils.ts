export type TimelinePointBase = {
  time: string
}

export const parseTimeLabelToSeconds = (time: string): number => {
  const raw = String(time || "").trim()
  if (!raw) return -1

  const parts = raw.split(":").map((part) => Number(part))
  if (parts.some((n) => Number.isNaN(n) || n < 0)) return -1

  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2]
  }
  if (parts.length === 2) {
    return parts[0] * 60 + parts[1]
  }
  return -1
}

export const formatSecondsToTimeLabel = (seconds: number): string => {
  const total = Math.max(0, Math.floor(seconds || 0))
  const hh = Math.floor(total / 3600)
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60

  if (hh > 0) return `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
}

export const getVisibleTimelineData = <T extends TimelinePointBase>(
  data: T[],
  currentTimeSeconds: number
): T[] => {
  if (!Array.isArray(data) || data.length === 0) return []
  const safeTime = Number.isFinite(currentTimeSeconds) ? Math.max(0, currentTimeSeconds) : 0
  return data.filter((item) => parseTimeLabelToSeconds(item.time) <= safeTime)
}

export const getNearestTimelineLabel = <T extends TimelinePointBase>(
  data: T[],
  currentTimeSeconds: number
): string | null => {
  if (!Array.isArray(data) || data.length === 0) return null
  const safeTime = Number.isFinite(currentTimeSeconds) ? Math.max(0, currentTimeSeconds) : 0
  let nearest: { label: string; distance: number } | null = null

  for (const point of data) {
    const seconds = parseTimeLabelToSeconds(point.time)
    if (seconds < 0) continue
    const distance = Math.abs(seconds - safeTime)
    if (!nearest || distance < nearest.distance) {
      nearest = { label: point.time, distance }
    }
  }

  return nearest?.label ?? null
}

export const getTimelineMaxSeconds = (...datasets: Array<TimelinePointBase[] | undefined>): number => {
  let max = 0
  for (const dataset of datasets) {
    if (!Array.isArray(dataset)) continue
    for (const point of dataset) {
      const seconds = parseTimeLabelToSeconds(point.time)
      if (seconds > max) max = seconds
    }
  }
  return max
}
