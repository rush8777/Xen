"use client"

import { useEffect, useState } from "react"
import { Search, Zap, CheckCircle2, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

interface AppConnection {
  id: string
  name: string
  description: string
  icon: string
  color: string
  connected: boolean
  contactPerson?: string
}

const statusConfig = {
  connected: {
    icon: CheckCircle2,
    textClass: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-100 dark:bg-emerald-900/30",
    dotColor: "bg-emerald-500",
    label: "CONNECTED",
  },
  disconnected: {
    icon: Circle,
    textClass: "text-zinc-600 dark:text-zinc-400",
    bg: "bg-zinc-100 dark:bg-zinc-900/30",
    dotColor: "bg-zinc-400",
    label: "DISCONNECTED",
  },
}

export default function Connections() {
  const [apps, setApps] = useState<AppConnection[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedApp, setSelectedApp] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [connectingAppId, setConnectingAppId] = useState<string | null>(null)

  const readErrorBody = async (res: Response) => {
    try {
      const text = await res.text()
      return text
    } catch {
      return ""
    }
  }

  const backendBaseUrl =
    process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000"

  useEffect(() => {
    const fetchConnections = async () => {
      try {
        setIsLoading(true)
        const res = await fetch(`${backendBaseUrl}/api/connections`, {
          credentials: "include",
        })
        if (!res.ok) {
          const body = await readErrorBody(res)
          throw new Error(
            `Failed to load connections (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`
          )
        }
        const data: AppConnection[] = await res.json()
        setApps(data)
      } catch (error) {
        console.error(error)
        alert(error instanceof Error ? error.message : String(error))
      } finally {
        setIsLoading(false)
      }
    }

    fetchConnections()
  }, [backendBaseUrl])

  const handleConnect = async (appId: string, isConnected: boolean) => {
    try {
      if (isConnected) {
        await handleDisconnect(appId)
        return
      }

      setConnectingAppId(appId)
      const res = await fetch(`${backendBaseUrl}/oauth/${appId}/authorize`, {
        credentials: "include",
      })
      if (!res.ok) {
        const body = await readErrorBody(res)
        throw new Error(
          `Failed to start OAuth flow (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`
        )
      }
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        throw new Error("OAuth authorize did not return a redirect url")
      }
    } catch (error) {
      console.error(error)
      alert(error instanceof Error ? error.message : String(error))
    } finally {
      setConnectingAppId(null)
    }
  }

  const handleDisconnect = async (appId: string) => {
    try {
      const res = await fetch(
        `${backendBaseUrl}/api/connections/${appId}/disconnect`,
        {
          method: "POST",
          credentials: "include",
        }
      )
      if (!res.ok) {
        const body = await readErrorBody(res)
        throw new Error(
          `Failed to disconnect (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`
        )
      }
      setApps(
        apps.map((app) =>
          app.id === appId ? { ...app, connected: false } : app
        )
      )
    } catch (error) {
      console.error(error)
      alert(error instanceof Error ? error.message : String(error))
    }
  }

  const filteredApps = apps.filter(
    (app) =>
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-white">
              Integrations
            </h1>
            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-300">
              {apps.length}
            </span>
          </div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Search through the comprehensive directory of Integrations
          </p>
        </div>

        {/* Search Bar and Sorting */}
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-400 dark:text-zinc-600" />
            <input
              type="text"
              placeholder="Search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                "w-full pl-9 pr-4 py-2 text-sm",
                "rounded-lg",
                "border border-zinc-200 dark:border-zinc-800",
                "bg-white dark:bg-zinc-900/70",
                "text-zinc-900 dark:text-white",
                "placeholder-zinc-500 dark:placeholder-zinc-400",
                "focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600",
                "transition-all duration-200"
              )}
            />
          </div>
          <button className="px-3 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
            ⚙️ Sorting
          </button>
        </div>

        {/* Apps Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredApps.map((app) => {
            const status = app.connected ? "connected" : "disconnected"
            const statusInfo = statusConfig[status]
            const isSelected = selectedApp === app.id

            return (
              <button
                key={app.id}
                onClick={() => setSelectedApp(isSelected ? null : app.id)}
                className={cn(
                  "flex flex-col",
                  "w-full p-4",
                  "rounded-xl",
                  "border transition-all duration-200",
                  "hover:shadow-md",
                  "text-left",
                  isSelected
                    ? "border-zinc-400 dark:border-zinc-600 bg-zinc-50 dark:bg-zinc-800/50 shadow-md"
                    : "border-zinc-100 dark:border-zinc-800 bg-white dark:bg-zinc-900/70 hover:border-zinc-200 dark:hover:border-zinc-700"
                )}
              >
                {/* Icon and Status Badge */}
                <div className="flex items-start justify-between mb-3">
                  <div
                    className={cn(
                      "rounded-lg p-2.5 flex items-center justify-center text-2xl w-10 h-10 flex-shrink-0",
                      app.color
                    )}
                  >
                    {app.icon}
                  </div>
                  <div
                    className={cn(
                      "px-2 py-1 rounded-full flex items-center gap-1",
                      statusInfo.bg,
                      statusInfo.textClass
                    )}
                  >
                    {statusInfo.dotColor === "bg-emerald-500" ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <Circle className="w-3.5 h-3.5" />
                    )}
                    <span className="text-xs font-medium">{statusInfo.label}</span>
                  </div>
                </div>

                {/* App Name */}
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-1">
                  {app.name}
                </h3>

                {/* Description */}
                <p className="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2 mb-3 flex-grow">
                  {app.description}
                </p>

                {/* Contact Person */}
                {app.contactPerson && (
                  <div className="flex items-center gap-2 mb-3 pb-3 border-t border-zinc-100 dark:border-zinc-800 pt-3">
                    <div className="w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-xs font-medium text-zinc-600 dark:text-zinc-400">
                      {app.contactPerson.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-zinc-600 dark:text-zinc-400">
                        {app.contactPerson}
                      </p>
                    </div>
                  </div>
                )}

                {/* Action Button */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleConnect(app.id, app.connected)
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.stopPropagation()
                      handleConnect(app.id, app.connected)
                    }
                  }}
                  className={cn(
                    "w-full py-2 px-3 text-xs font-medium rounded-lg",
                    "transition-all duration-200 cursor-pointer",
                    "focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2",
                    app.connected
                      ? "text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                      : "text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700",
                    connectingAppId === app.id &&
                      "opacity-60 cursor-not-allowed"
                  )}
                >
                  {app.connected
                    ? "DISCONNECT"
                    : connectingAppId === app.id
                      ? "CONNECTING..."
                      : "CONNECT"}
                </div>
              </button>
            )
          })}
        </div>

        {/* Empty State */}
        {!isLoading && filteredApps.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Zap className="h-12 w-12 text-zinc-400 dark:text-zinc-600 mb-4" />
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              No apps found matching your search
            </p>
          </div>
        )}
      </div>
  )
}
