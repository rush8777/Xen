"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import TeachCanvasKit from "@/components/teach-canvas-kit-component/TeachCanvasKit"
import type { CourseSlides } from "@/components/teach-canvas-kit-component/data/courseData"
import SonosTypoCourse from "@/components/teach-canvas-kit-component/SonosTypoCourse"
import PixelBrutalistCourse from "@/components/teach-canvas-kit-component/PixelBrutalistCourse"

type CourseTemplateId = "default" | "sonos_typo" | "pixel_brutalist"

export default function CoursePage() {
  const searchParams = useSearchParams()
  const courseKey = searchParams.get("courseKey")
  const [courseData, setCourseData] = useState<CourseSlides | null>(null)
  const [courseTemplate, setCourseTemplate] = useState<CourseTemplateId>("default")

  const storageKey = useMemo(() => {
    if (!courseKey) return null
    return `xen:course:${courseKey}`
  }, [courseKey])

  useEffect(() => {
    if (!storageKey) {
      setCourseData(null)
      return
    }
    try {
      const raw = window.sessionStorage.getItem(storageKey)
      if (!raw) {
        setCourseData(null)
        return
      }
      const parsed = JSON.parse(raw) as
        | CourseSlides
        | { courseData?: CourseSlides; template?: CourseTemplateId }

      const wrappedData =
        parsed && typeof parsed === "object" && "courseData" in parsed
          ? parsed.courseData
          : (parsed as CourseSlides)
      const wrappedTemplate =
        parsed && typeof parsed === "object" && "template" in parsed
          ? parsed.template
          : "default"

      if (!wrappedData) {
        setCourseData(null)
        return
      }

      if (
        typeof wrappedData.courseTitle === "string" &&
        Array.isArray(wrappedData.slides) &&
        wrappedData.slides.length > 0
      ) {
        setCourseData(wrappedData)
        setCourseTemplate(
          wrappedTemplate === "sonos_typo" || wrappedTemplate === "pixel_brutalist"
            ? wrappedTemplate
            : "default"
        )
      } else {
        setCourseData(null)
      }
    } catch {
      setCourseData(null)
    }
  }, [storageKey])

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#070A10]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl animate-pulse" />
        <div className="absolute right-0 top-1/4 h-96 w-96 rounded-full bg-indigo-500/15 blur-3xl animate-[spin_28s_linear_infinite]" />
        <div className="absolute bottom-[-120px] left-1/3 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl animate-pulse" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.06),transparent_45%)]" />
      </div>

      <div className="relative z-10 flex h-full flex-col">
        <Link
          href="/chat"
          className="absolute right-3 top-1/2 z-20 -translate-y-1/2 rounded-md border border-zinc-600 bg-zinc-900/80 px-2.5 py-1.5 text-[11px] font-medium text-zinc-200 transition-colors hover:bg-zinc-800"
        >
          Back
        </Link>

        <div className="flex-1 p-0">
          {courseData ? (
            <div className="h-full overflow-hidden border border-white/10 bg-black/30 shadow-[0_25px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl">
              {courseTemplate === "sonos_typo" ? (
                <SonosTypoCourse courseData={courseData as any} className="h-full" />
              ) : courseTemplate === "pixel_brutalist" ? (
                <PixelBrutalistCourse courseData={courseData as any} className="h-full" />
              ) : (
                <TeachCanvasKit courseData={courseData} className="h-full" />
              )}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center border border-dashed border-zinc-700/80 bg-black/30">
              <div className="max-w-md text-center">
                <h2 className="text-lg font-semibold text-zinc-100">Course unavailable</h2>
                <p className="mt-2 text-sm text-zinc-400">
                  We could not find this generated course in the current session. Generate it again from chat.
                </p>
                <Link
                  href="/chat"
                  className="mt-5 inline-flex rounded-lg border border-zinc-600 bg-zinc-900 px-4 py-2 text-xs font-semibold text-zinc-200 transition-colors hover:bg-zinc-800"
                >
                  Return to chat
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
