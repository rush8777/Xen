"use client"

import React from "react"
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Users, MapPin, Tag, TrendingUp } from "lucide-react"

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0]
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg p-3">
        <p className="text-xs font-semibold text-white mb-1">
          {data.payload.label || data.name}
        </p>
        <p className="text-xs text-zinc-400">
          <span className="font-semibold text-purple-400">{data.value}%</span>
        </p>
      </div>
    )
  }
  return null
}

const renderCustomLabel = (entry: any) => `${entry.value}%`

// ========================================
// 1. AGE DISTRIBUTION COMPONENT
// ========================================
interface AgeDistributionPoint {
  label: string
  value: number
}

interface AgeDistributionProps {
  data?: AgeDistributionPoint[]
}

export function AgeDistribution({ 
  data = [
    { label: "13–17", value: 8 },
    { label: "18–24", value: 38 },
    { label: "25–34", value: 42 },
    { label: "35–44", value: 14 },
    { label: "45+", value: 6 },
  ]
}: AgeDistributionProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
        <div className="mb-2">
          <h3 className="text-lg font-semibold text-white mb-1">Age Distribution</h3>
        </div>
        <p className="text-xs text-zinc-400">
          Not enough audience data yet to estimate age distribution for this video.
        </p>
      </div>
    )
  }

  const primaryAge = data.reduce((max, group) => 
    group.value > max.value ? group : max
  )

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-1">Age Distribution</h3>
        <p className="text-xs text-zinc-400">
          Age groups based on engagement patterns and comment analysis
        </p>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
            <XAxis
              type="number"
              stroke="#71717a"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#27272a" }}
              domain={[0, 50]}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis
              type="category"
              dataKey="label"
              stroke="#71717a"
              tick={{ fill: "#71717a", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "#27272a" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="value"
              fill="#6366f1"
              radius={[0, 8, 8, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
        <p className="text-xs text-indigo-400">
          <TrendingUp className="w-3 h-3 inline mr-1" />
          Your primary audience is{" "}
          <span className="font-semibold">{primaryAge.label}</span>
          {" "}with <span className="font-semibold">{primaryAge.value}%</span>
        </p>
      </div>
    </div>
  )
}

// ========================================
// 2. GENDER DISTRIBUTION COMPONENT
// ========================================
interface GenderDistributionPoint {
  label: string
  value: number
}

interface GenderDistributionProps {
  data?: GenderDistributionPoint[]
}

const GENDER_COLORS: Record<string, string> = {
  "Male": "#3b82f6",
  "Female": "#ec4899",
  "Other / Unknown": "#8b5cf6",
}

export function GenderDistribution({ 
  data = [
    { label: "Male", value: 62 },
    { label: "Female", value: 34 },
    { label: "Other / Unknown", value: 4 },
  ]
}: GenderDistributionProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
        <div className="mb-2">
          <h3 className="text-lg font-semibold text-white mb-1">Gender Distribution</h3>
        </div>
        <p className="text-xs text-zinc-400">
          Not enough audience data yet to show gender distribution.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-1">Gender Distribution</h3>
        <p className="text-xs text-zinc-400">
          Inferred from engagement patterns and user interactions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        <div className="h-80 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
                label={renderCustomLabel}
                labelLine={false}
                animationDuration={1000}
                animationEasing="ease-out"
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={GENDER_COLORS[entry.label] || "#8b5cf6"}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-3">
          {data.map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 border border-zinc-700"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: GENDER_COLORS[item.label] || "#8b5cf6" }}
                />
                <span className="text-sm font-medium text-white">{item.label}</span>
              </div>
              <span className="text-sm font-semibold text-purple-400">{item.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ========================================
// 3. TOP LOCATIONS COMPONENT
// ========================================
interface TopLocationPoint {
  label: string
  value: number
}

interface TopLocationsProps {
  data?: TopLocationPoint[]
}

export function TopLocations({ 
  data = [
    { label: "India", value: 28 },
    { label: "USA", value: 22 },
    { label: "UK", value: 11 },
    { label: "Canada", value: 9 },
    { label: "Australia", value: 7 },
    { label: "Germany", value: 5 },
    { label: "Others", value: 18 },
  ]
}: TopLocationsProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="w-4 h-4 text-emerald-400" />
            <h3 className="text-lg font-semibold text-white">Top Locations</h3>
          </div>
        </div>
        <p className="text-xs text-zinc-400">
          Not enough geographic data yet to rank top locations for this audience.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <MapPin className="w-4 h-4 text-emerald-400" />
          <h3 className="text-lg font-semibold text-white">Top Locations</h3>
        </div>
        <p className="text-xs text-zinc-400">
          Geographic distribution of your audience based on engagement data
        </p>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="label"
              stroke="#71717a"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#27272a" }}
            />
            <YAxis
              stroke="#71717a"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#27272a" }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="value"
              fill="#10b981"
              radius={[8, 8, 0, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {data.slice(0, 4).map((location, index) => (
          <div
            key={location.label}
            className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700"
          >
            <p className="text-xs text-zinc-400 mb-1">#{index + 1}</p>
            <p className="text-sm font-semibold text-white">{location.label}</p>
            <p className="text-xs text-emerald-400 font-medium">{location.value}%</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ========================================
// 4. AUDIENCE INTERESTS COMPONENT
// ========================================
interface AudienceInterestsProps {
  data?: string[]
}

export function AudienceInterests({ 
  data = [
    "Tech",
    "AI Tools",
    "Startups",
    "Content Creation",
    "Productivity",
    "Design",
    "Marketing",
    "SaaS",
  ]
}: AudienceInterestsProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-1">
            <Tag className="w-4 h-4 text-pink-400" />
            <h3 className="text-lg font-semibold text-white">Audience Interests</h3>
          </div>
        </div>
        <p className="text-xs text-zinc-400">
          Not enough engagement signal yet to infer audience interests for this project.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border p-6 bg-zinc-900/50 border-zinc-800">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <Tag className="w-4 h-4 text-pink-400" />
          <h3 className="text-lg font-semibold text-white">Audience Interests</h3>
        </div>
        <p className="text-xs text-zinc-400">
          Topics and themes your audience engages with most
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {data.map((interest, index) => (
          <div
            key={interest}
            className="px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 hover:border-purple-400/40 transition-all duration-300 cursor-pointer group"
            style={{
              animationDelay: `${index * 50}ms`,
              animation: "fadeIn 0.5s ease-out forwards",
            }}
          >
            <span className="text-sm font-medium text-purple-300 group-hover:text-purple-200 transition-colors">
              {interest}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
        <p className="text-xs text-purple-400">
          💡 <span className="font-semibold">Content Strategy Tip:</span> Create more content
          around these topics to maximize engagement with your existing audience
        </p>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
