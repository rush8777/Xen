"use client"

import type { ReactNode } from "react"
import Sidebar from "./sidebar"
import { useTheme } from "next-themes"
import { useEffect, useState, createContext, useContext, useMemo } from "react"
import { MultiStepLoader } from "@/components/ui/multi-step-loader"
import { usePathname } from "next/navigation"
import CourseCreator from "@/components/CourseCreator"

interface LayoutProps {
  children: ReactNode
}

interface SidebarContextType {
  isSidebarExpanded: boolean
  setIsSidebarExpanded: (expanded: boolean) => void
}

type LoadingState = { text: string }

interface GlobalLoaderContextType {
  loading: boolean
  step: number
  loadingStates: LoadingState[]
  setLoading: (loading: boolean) => void
  setStep: (step: number) => void
  setLoadingStates: (states: LoadingState[]) => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

const GlobalLoaderContext = createContext<GlobalLoaderContextType | undefined>(undefined)

export const useSidebarContext = () => {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebarContext must be used within Layout")
  }
  return context
}

export const useGlobalLoader = () => {
  const context = useContext(GlobalLoaderContext)
  if (!context) {
    throw new Error("useGlobalLoader must be used within Layout")
  }
  return context
}

export default function Layout({ children }: LayoutProps) {
  const { theme } = useTheme()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true)

  const [globalLoading, setGlobalLoading] = useState(false)
  const [globalStep, setGlobalStep] = useState(0)
  const [globalLoadingStates, setGlobalLoadingStates] = useState<LoadingState[]>([
    { text: "Initializing video analysis" },
    { text: "Downloading video" },
    { text: "Extracting comments" },
    { text: "Uploading video for overview" },
    { text: "Generating overview" },
    { text: "Opening Streamline" },
  ])

  const [showSurvey, setShowSurvey] = useState(false)

  const globalLoaderValue = useMemo<GlobalLoaderContextType>(
    () => ({
      loading: globalLoading,
      step: globalStep,
      loadingStates: globalLoadingStates,
      setLoading: setGlobalLoading,
      setStep: setGlobalStep,
      setLoadingStates: setGlobalLoadingStates,
    }),
    [globalLoading, globalStep, globalLoadingStates]
  )

  useEffect(() => {
    if (!globalLoading) return

    const message = "A process is still running. If you leave now, the current processing will be terminated. Continue?"

    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = message
      return message
    }

    const onClickCapture = (e: MouseEvent) => {
      const target = e.target as Element | null
      if (!target) return

      const anchor = target.closest("a[href]") as HTMLAnchorElement | null
      if (!anchor) return

      if (anchor.target === "_blank") return
      const href = anchor.getAttribute("href")
      if (!href) return
      if (href.startsWith("#")) return
      if (href.startsWith("mailto:") || href.startsWith("tel:")) return

      const ok = window.confirm(message)
      if (!ok) {
        e.preventDefault()
        e.stopPropagation()
      }
    }

    const onPopState = () => {
      const ok = window.confirm(message)
      if (!ok) {
        window.history.pushState(null, "", pathname)
      }
    }

    window.addEventListener("beforeunload", onBeforeUnload)
    document.addEventListener("click", onClickCapture, true)
    window.addEventListener("popstate", onPopState)

    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload)
      document.removeEventListener("click", onClickCapture, true)
      window.removeEventListener("popstate", onPopState)
    }
  }, [globalLoading, pathname])

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    if (!pathname?.startsWith("/dashboard")) {
      setShowSurvey(false)
      return
    }

    try {
      const completed = window.localStorage.getItem("xen:welcomeSurveyCompleted")
      setShowSurvey(!completed)
    } catch {
      setShowSurvey(true)
    }
  }, [mounted, pathname])

  if (!mounted) {
    return null
  }

  return (
    <SidebarContext.Provider value={{ isSidebarExpanded, setIsSidebarExpanded }}>
      <GlobalLoaderContext.Provider value={globalLoaderValue}>
        <div className={`min-h-screen ${theme === "dark" ? "dark" : ""}`}>
          <Sidebar />
          <main
            className={`relative min-h-screen p-6 bg-white dark:bg-[#0F0F12] transition-all duration-300 ease-in-out ${
              isSidebarExpanded ? "ml-60" : "ml-16"
            } ${globalLoading || showSurvey ? "overflow-hidden" : "overflow-auto"}`}
          >
            {children}
          </main>

          {showSurvey && !globalLoading && (
            <div className="fixed inset-0 z-50 isolate">
              <div
                className="absolute inset-0 z-0 bg-black/40 backdrop-blur-md pointer-events-auto"
                onClick={() => {
                  setShowSurvey(false)
                }}
              />
              <div className="absolute inset-0 z-10 flex items-center justify-center p-4 pointer-events-none">
                <div className="w-full max-w-6xl pointer-events-auto">
                  <CourseCreator
                    variant="overlay"
                    onComplete={() => {
                      try {
                        window.localStorage.setItem("xen:welcomeSurveyCompleted", "1")
                      } catch {}
                      setShowSurvey(false)
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {globalLoading && (
            <div className="fixed inset-0 z-50">
              <MultiStepLoader
                loadingStates={globalLoadingStates}
                loading={globalLoading}
                duration={1200}
                loop={true}
                value={globalStep}
                overlay="fixed"
              />
            </div>
          )}
        </div>
      </GlobalLoaderContext.Provider>
    </SidebarContext.Provider>
  )
}
