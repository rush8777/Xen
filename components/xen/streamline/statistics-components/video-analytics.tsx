"use client"

import EmotionalIntensityChart from "./emotional-anal"
import {
  AgeDistribution,
  GenderDistribution,
  TopLocations,
  AudienceInterests,
} from "./audience-demographics"
import VideoMetricsGrid from "./VideoMetricsGrid"
import SentimentPulseChart from "./SentimentPulseChart"
import EmotionRadarChart from "./EmotionRadarChart"
import TopComments from "./TopComments"

const emotionalData = [
  { time: "00:00", intensity: 45, emotion: "neutral" },
  { time: "00:05", intensity: 32, emotion: "neutral" },
  { time: "00:10", intensity: 68, emotion: "surprise" },
  { time: "00:15", intensity: 91, emotion: "excitement" },
  { time: "00:20", intensity: 40, emotion: "calm" },
  { time: "00:25", intensity: 55, emotion: "interest" },
  { time: "00:30", intensity: 78, emotion: "joy" },
  { time: "00:35", intensity: 23, emotion: "sadness" },
  { time: "00:40", intensity: 62, emotion: "surprise" },
  { time: "00:45", intensity: 85, emotion: "excitement" },
  { time: "00:50", intensity: 48, emotion: "neutral" },
  { time: "00:55", intensity: 70, emotion: "interest" },
  { time: "01:00", intensity: 38, emotion: "calm" },
]

export default function VideoAnalytics() {
  return (
    <div className="space-y-6">
      <VideoMetricsGrid />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentPulseChart />
        <EmotionRadarChart />
      </div>

      <EmotionalIntensityChart data={emotionalData} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgeDistribution />
        <GenderDistribution />
        <TopLocations />
        <AudienceInterests />
      </div>

      <TopComments />
    </div>
  )
}

