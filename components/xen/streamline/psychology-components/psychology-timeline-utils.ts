export const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

export const formatSecondsToTimeLabel = (seconds: number): string => {
  const total = Math.max(0, Math.floor(seconds || 0))
  const hh = Math.floor(total / 3600)
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60

  if (hh > 0) return `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
}

export const getNearestTime = (
  points: Array<{ time: number }>,
  currentTimeSeconds: number,
): number | null => {
  if (!Array.isArray(points) || points.length === 0) return null
  const safeCurrent = Number.isFinite(currentTimeSeconds) ? Math.max(0, currentTimeSeconds) : 0
  let nearest = points[0].time
  let nearestDistance = Math.abs(points[0].time - safeCurrent)
  for (const point of points) {
    const distance = Math.abs(point.time - safeCurrent)
    if (distance < nearestDistance) {
      nearest = point.time
      nearestDistance = distance
    }
  }
  return nearest
}
