"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Image, X } from "lucide-react"
import ChatInput from "./chatinputui"
import ChatMessage from "./chatmassegeui"
import { useSidebarContext } from "../main/layout"
import { TopBar } from "./chatmassegeui"
import NewChatScreen from "./new-chat-screen"
import type { SelectedChatProject } from "./new-chat-screen"
import CourseClarificationWindow from "./course-clarification-window"
import type { CourseSlides } from "@/components/teach-canvas-kit-component/data/courseData"
type CoursePayload =
  | CourseSlides
  | {
      brand?: { name?: string }
      slides?: any[]
      courseTitle?: string
    }

interface Message {
  id: string
  type: "message" | "divider"
  kind?: "text" | "course"
  content: string
  isUser?: boolean
  isStreaming?: boolean
  timestamp: Date
  projectName?: string
  ragActive?: boolean
  contextChunksUsed?: number
  courseData?: CoursePayload | null
  courseSummary?: string | null
  courseTemplate?: CourseTemplateId
}

interface CourseClarificationQuestion {
  id: string
  label: string
  input_type: "single_choice" | "multi_choice" | "short_text" | "long_text" | "number"
  options?: string[]
  max_select?: number
  placeholder?: string
  required?: boolean
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
const CHOICE_SEP = " || "
type CourseTemplateId = "default" | "sonos_typo" | "pixel_brutalist" | "brand_guides"
const isCourseTemplateId = (value: unknown): value is CourseTemplateId =>
  value === "sonos_typo"
const COURSE_PAYLOAD_PREFIX = "[[COURSE_PAYLOAD_V1:"
const COURSE_PAYLOAD_SUFFIX = "]]"
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

const ChatContainer = () => {
  const { isSidebarExpanded } = useSidebarContext()
  const [isChatActive, setIsChatActive] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [chatId, setChatId] = useState<number | null>(null)
  const [ragActive, setRagActive] = useState(false)
  const [contextOpen, setContextOpen] = useState(false)
  const [contextChunks, setContextChunks] = useState<string[]>([])
  const [activeProjectName, setActiveProjectName] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<SelectedChatProject | null>(null)
  const [courseClarificationQuestions, setCourseClarificationQuestions] = useState<CourseClarificationQuestion[]>([])
  const [courseClarificationValues, setCourseClarificationValues] = useState<Record<string, string>>({})
  const [courseClarificationIndex, setCourseClarificationIndex] = useState(0)
  const router = useRouter()
  const searchParams = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const projectIdParam = searchParams.get("projectId")
  const resolvedProjectId =
    projectIdParam && Number.isFinite(Number(projectIdParam))
      ? Number(projectIdParam)
      : null

  const isValidCourseData = (value: unknown): value is CoursePayload => {
    if (!value || typeof value !== "object") return false
    const payload = value as CoursePayload
    const hasSlides = Array.isArray((payload as any).slides) && (payload as any).slides.length > 0
    if (!hasSlides) return false
    const hasCourseTitle = typeof (payload as any).courseTitle === "string" && (payload as any).courseTitle.trim().length > 0
    const hasBrandName =
      !!(payload as any).brand &&
      typeof (payload as any).brand === "object" &&
      typeof (payload as any).brand.name === "string" &&
      (payload as any).brand.name.trim().length > 0
    return (
      hasCourseTitle || hasBrandName
    )
  }

  const decodeBase64Url = (input: string): string => {
    const normalized = input.replace(/-/g, "+").replace(/_/g, "/")
    const pad = normalized.length % 4
    const padded = normalized + (pad ? "=".repeat(4 - pad) : "")
    return atob(padded)
  }

  const extractCoursePayloadFromContent = (
    raw: string
  ): { cleanContent: string; courseData: CoursePayload | null; courseTemplate: CourseTemplateId } => {
    const content = raw || ""
    const start = content.indexOf(COURSE_PAYLOAD_PREFIX)
    const end = content.indexOf(COURSE_PAYLOAD_SUFFIX, start + COURSE_PAYLOAD_PREFIX.length)
    if (start === -1 || end === -1) {
      return { cleanContent: content, courseData: null, courseTemplate: "sonos_typo" }
    }

    const encoded = content.slice(start + COURSE_PAYLOAD_PREFIX.length, end).trim()
    const cleanContent = (content.slice(0, start) + content.slice(end + COURSE_PAYLOAD_SUFFIX.length)).trim()
    try {
      const decoded = decodeBase64Url(encoded)
      const parsed = JSON.parse(decoded) as {
        course_data?: CoursePayload
        course_template?: CourseTemplateId
      }
      const parsedCourseData = parsed?.course_data
      const parsedTemplate = parsed?.course_template
      return {
        cleanContent,
        courseData: isValidCourseData(parsedCourseData) ? parsedCourseData : null,
        courseTemplate: isCourseTemplateId(parsedTemplate) ? parsedTemplate : "sonos_typo",
      }
    } catch {
      return { cleanContent, courseData: null, courseTemplate: "sonos_typo" }
    }
  }

  const openCoursePage = (courseData: CoursePayload, template: CourseTemplateId = "sonos_typo") => {
    if (!isValidCourseData(courseData)) return
    const courseKey = `course-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    try {
      window.sessionStorage.setItem(
        `xen:course:${courseKey}`,
        JSON.stringify({ courseData, template })
      )
    } catch {
      // Ignore storage errors in private browsing modes.
    }
    router.push(`/chat/course?courseKey=${encodeURIComponent(courseKey)}`)
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const rawChatId = searchParams.get("chatId")
    if (!rawChatId) return
    const parsedChatId = Number(rawChatId)
    if (!Number.isFinite(parsedChatId) || parsedChatId <= 0) return
    if (chatId === parsedChatId && isChatActive) return

    const hydrateChat = async () => {
      try {
        const [chatRes, messageRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/chats/${parsedChatId}`, { cache: "no-store" }),
          fetch(`${API_BASE_URL}/api/chats/${parsedChatId}/messages`, { cache: "no-store" }),
        ])
        if (!chatRes.ok || !messageRes.ok) return
        const chatData: { id: number; name: string } = await chatRes.json()
        const rows: Array<{ id: number; role: string; content: string; created_at: string }> =
          await messageRes.json()

        const hydrated: Message[] = (rows || []).map((r) => {
          const parsed =
            r.role === "assistant"
              ? extractCoursePayloadFromContent(r.content)
                : {
                  cleanContent: r.content,
                  courseData: null,
                  courseTemplate: "sonos_typo" as CourseTemplateId,
                }
          return {
            id: String(r.id),
            type: "message",
            kind: parsed.courseData ? "course" : "text",
            content: parsed.cleanContent,
            isUser: r.role === "user",
            isStreaming: false,
            timestamp: new Date(r.created_at),
            ragActive: false,
            contextChunksUsed: 0,
            courseData: parsed.courseData,
            courseSummary: parsed.courseData ? parsed.cleanContent : null,
            courseTemplate: parsed.courseTemplate,
          }
        })
        setMessages(hydrated)
        setChatId(parsedChatId)
        setIsChatActive(true)
        setActiveProjectName(chatData.name || null)
      } catch {
        // Ignore hydration failures and keep current local state.
      }
    }
    hydrateChat()
  }, [searchParams, chatId, isChatActive])

  const handleSendMessage = async (
    content: string,
    mentionedProject?: string,
    clarificationAnswers?: Record<string, string>,
    courseModeEnabledOverride?: boolean
  ) => {
    const effectiveCourseModeEnabled =
      typeof courseModeEnabledOverride === "boolean"
        ? courseModeEnabledOverride
        : false
    const resolvedCourseAnswers: Record<string, string> = {
      ...(clarificationAnswers || {}),
      course_template: "sonos_typo",
    }
    const normalizedMention = mentionedProject?.trim()
    const contextProjectId = selectedProject?.id ?? resolvedProjectId
    const isProjectSwitch =
      !!normalizedMention &&
      (!activeProjectName || activeProjectName.toLowerCase() !== normalizedMention.toLowerCase())

    const dividerMessage: Message | null = isProjectSwitch
      ? {
          id: `divider-${Date.now().toString()}`,
          type: "divider",
          content: "",
          projectName: normalizedMention,
          timestamp: new Date(),
        }
      : null

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "message",
      content,
      isUser: true,
      timestamp: new Date()
    }
    const assistantMessageId = `assistant-${Date.now().toString()}`
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      type: "message",
      kind: "text",
      content: "Thinking...",
      isUser: false,
      isStreaming: false,
      timestamp: new Date(),
      ragActive: false,
      contextChunksUsed: 0,
      courseData: null,
      courseSummary: null,
      courseTemplate: "sonos_typo",
    }

    setMessages(prev =>
      dividerMessage
        ? [...prev, dividerMessage, userMessage, assistantPlaceholder]
        : [...prev, userMessage, assistantPlaceholder]
    )
    if (isProjectSwitch && normalizedMention) {
      setActiveProjectName(normalizedMention)
    }
    setIsLoading(true)
    if (clarificationAnswers && Object.keys(clarificationAnswers).length > 0) {
      setCourseClarificationQuestions([])
      setCourseClarificationValues({})
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/chats/send-message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          project_id: normalizedMention ? undefined : (contextProjectId ?? undefined),
          message: content,
          user_id: null,
          course_clarification_answers: resolvedCourseAnswers,
          course_mode_enabled: effectiveCourseModeEnabled,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err?.detail || `Request failed (${res.status})`)
      }

      const data: {
        chat_id: number
        project: { id: number; name: string }
        messages: Array<{ role: string; content: string }>
        rag_active?: boolean
        context_chunks_used?: number
        context_chunks?: string[]
        course_generated?: boolean
        course_summary?: string | null
        course_data?: CoursePayload | null
        course_template?: CourseTemplateId | null
        course_clarification_needed?: boolean
        course_clarification_questions?: CourseClarificationQuestion[]
      } = await res.json()

      setChatId(data.chat_id)
      setActiveProjectName(data.project?.name || null)
      if (data.project?.id && data.project?.name) {
        setSelectedProject((prev) => {
          if (prev && prev.id === data.project.id) return prev
          return {
            id: data.project.id,
            name: data.project.name,
            thumbnail_url: null,
            video_url: null,
          }
        })
      }
      const finalRagActive = !!data.rag_active
      const finalContextChunksUsed =
        typeof data.context_chunks_used === "number" ? data.context_chunks_used : 0
      const finalContextChunks = Array.isArray(data.context_chunks) ? data.context_chunks : []
      setRagActive(finalRagActive)
      setContextChunks(finalContextChunks)

      const clarificationNeeded = !!data.course_clarification_needed
      const clarificationQuestions = Array.isArray(data.course_clarification_questions)
        ? data.course_clarification_questions
        : []
      if (clarificationNeeded && clarificationQuestions.length > 0) {
        setCourseClarificationQuestions(clarificationQuestions)
        setCourseClarificationIndex(0)
        const nextValues: Record<string, string> = {}
        for (const q of clarificationQuestions) {
          if (q?.id) nextValues[q.id] = ""
        }
        setCourseClarificationValues(nextValues)
      } else {
        setCourseClarificationQuestions([])
        setCourseClarificationIndex(0)
        setCourseClarificationValues({})
      }

      const assistant = [...(data.messages || [])].reverse().find(m => m.role === "assistant")
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMessageId
            ? {
                ...m,
                kind: data.course_generated ? "course" : "text",
                content:
                  data.course_summary ||
                  assistant?.content ||
                  "No response received.",
                isStreaming: false,
                ragActive: finalRagActive,
                contextChunksUsed: finalContextChunksUsed,
                courseData: data.course_generated && data.course_data ? data.course_data : null,
                courseSummary: data.course_summary || null,
                courseTemplate: isCourseTemplateId(data.course_template) ? data.course_template : "sonos_typo",
              }
            : m
        )
      )

      if (data.course_generated && data.course_data && isValidCourseData(data.course_data)) {
        const tpl = isCourseTemplateId(data.course_template) ? data.course_template : "sonos_typo"
        openCoursePage(data.course_data, tpl)
      }
    } catch (e: any) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMessageId
            ? { ...m, content: `Error: ${e?.message || "Failed to send message"}`, isStreaming: false }
            : m
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartChat = (message: string, initialProject?: SelectedChatProject | null) => {
    setIsChatActive(true)
    if (initialProject) {
      setSelectedProject(initialProject)
      setActiveProjectName(initialProject.name)
    }
    // Add welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      type: "message",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date()
    }
    setMessages([welcomeMessage])
    // Send the initial message
    setTimeout(() => handleSendMessage(message), 100)
  }

  const handleNewChat = () => {
    setIsChatActive(false)
    setMessages([])
    setIsLoading(false)
    setChatId(null)
    setRagActive(false)
    setContextOpen(false)
    setContextChunks([])
    setActiveProjectName(null)
    setSelectedProject(null)
    setCourseClarificationQuestions([])
    setCourseClarificationIndex(0)
    setCourseClarificationValues({})
  }

  const handleClarificationAnswerChange = (id: string, value: string) => {
    setCourseClarificationValues(prev => ({ ...prev, [id]: value }))
  }

  const parseChoiceValues = (raw: string): string[] => {
    if (!raw) return []
    return raw
      .split(CHOICE_SEP)
      .map(v => v.trim())
      .filter(Boolean)
  }

  const toggleChoiceAnswer = (question: CourseClarificationQuestion, option: string) => {
    const current = parseChoiceValues(courseClarificationValues[question.id] || "")
    if (question.input_type === "single_choice") {
      handleClarificationAnswerChange(question.id, option)
      return
    }

    const currentSet = new Set(current)
    if (currentSet.has(option)) {
      currentSet.delete(option)
    } else {
      const maxSelect = Math.max(1, question.max_select || 2)
      if (currentSet.size >= maxSelect) {
        const first = current[0]
        if (first) currentSet.delete(first)
      }
      currentSet.add(option)
    }
    handleClarificationAnswerChange(question.id, Array.from(currentSet).join(CHOICE_SEP))
  }

  const submitClarificationAnswers = async () => {
    if (courseClarificationQuestions.length === 0) return
    const answers: Record<string, string> = {}
    for (const q of courseClarificationQuestions) {
      const value = (courseClarificationValues[q.id] || "").trim()
      if (q.required && !value) return
      if (value) {
        const normalized =
          q.input_type === "multi_choice"
            ? parseChoiceValues(value).join(", ")
            : value
        answers[q.id] = `${q.label}: ${normalized}`
      }
    }
    await handleSendMessage(
      "Generate the course using the provided clarification answers.",
      undefined,
      answers,
      true
    )
  }

  const currentClarificationQuestion =
    courseClarificationQuestions.length > 0
      ? courseClarificationQuestions[Math.min(courseClarificationIndex, courseClarificationQuestions.length - 1)]
      : null
  const canContinueClarification = (() => {
    if (!currentClarificationQuestion) return false
    const value = (courseClarificationValues[currentClarificationQuestion.id] || "").trim()
    return !(currentClarificationQuestion.required && !value)
  })()

  const handleClarificationNext = async () => {
    if (!canContinueClarification) return
    if (courseClarificationIndex >= courseClarificationQuestions.length - 1) {
      await submitClarificationAnswers()
      return
    }
    setCourseClarificationIndex((prev) => Math.min(prev + 1, courseClarificationQuestions.length - 1))
  }

  const handleClarificationPrev = () => {
    setCourseClarificationIndex((prev) => Math.max(prev - 1, 0))
  }

  return (
    <div className="flex flex-col h-full bg-[#0F0F12] relative">
      {!isChatActive ? (
        <NewChatScreen onStartChat={handleStartChat} />
      ) : (
        <>
          {/* Top Bar - Fixed at very top, full width */}
          <div className="fixed top-0 left-0 right-0 z-20">
            <TopBar
              onNewChat={handleNewChat}
              ragActive={ragActive}
              contextOpen={contextOpen}
              onToggleContext={() => setContextOpen(v => !v)}
            />
          </div>

          {/* Retrieved Context Side Window */}
          {contextOpen && (
            <div className="fixed top-10 right-0 bottom-0 z-30 w-full md:w-[360px] bg-[#0B0B0E] border-l border-zinc-800/70">
              <div className="h-full flex flex-col">
                <div className="px-4 py-3 border-b border-zinc-800/70 flex items-center justify-between">
                  <div className="text-zinc-200 text-xs font-semibold tracking-tight">Retrieved context</div>
                  <button
                    onClick={() => setContextOpen(false)}
                    className="text-zinc-400 text-xs hover:text-zinc-200 transition-colors"
                  >
                    Close
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto px-4 py-3">
                  {!ragActive && (
                    <div className="text-zinc-500 text-xs leading-relaxed">
                      RAG is currently inactive for the last response.
                    </div>
                  )}
                  {ragActive && contextChunks.length === 0 && (
                    <div className="text-zinc-500 text-xs leading-relaxed">
                      No context chunks were returned.
                    </div>
                  )}
                  {contextChunks.map((chunk, idx) => (
                    <div key={idx} className="mb-3">
                      <div className="text-[10px] text-zinc-500 mb-1">Chunk {idx + 1}</div>
                      <pre className="whitespace-pre-wrap break-words text-[11px] leading-relaxed text-zinc-200 bg-zinc-950/40 border border-zinc-800/60 rounded-lg p-3">
                        {chunk}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {/* Chat Messages */}
          <div className={`flex-1 overflow-y-auto px-6 py-4 pt-12 pb-32 ${contextOpen ? "md:pr-[396px]" : ""}`}>
            <div className="max-w-4xl mx-auto">
              {messages.map((message) =>
                message.type === "divider" ? (
                  <div key={message.id} className="my-4 flex items-center gap-3">
                    <div className="h-px flex-1 bg-zinc-800/80" />
                    <div className="rounded-full border border-zinc-700/70 bg-zinc-900/70 px-3 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-300">
                      Project: {message.projectName}
                    </div>
                    <div className="h-px flex-1 bg-zinc-800/80" />
                  </div>
                ) : (
                  (() => {
                    const messageCourseData = message.courseData
                    return (
                      <ChatMessage
                        key={message.id}
                        content={message.content}
                        isUser={!!message.isUser}
                        isStreaming={!!message.isStreaming}
                        showActions={!message.isUser}
                        ragActive={message.ragActive}
                        contextChunksUsed={message.contextChunksUsed}
                        courseAvailable={!!messageCourseData}
                        courseTemplate={message.courseTemplate || "sonos_typo"}
                        onOpenCourse={
                          messageCourseData
                            ? () =>
                                openCoursePage(
                                  messageCourseData,
                                  message.courseTemplate || "sonos_typo"
                                )
                            : undefined
                        }
                      />
                    )
                  })()
                )
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Chat Input - Fixed at bottom */}
          <div className={`fixed bottom-0 ${contextOpen ? "md:right-[360px]" : "right-0"} bg-[#0F0F12] px-6 py-4 z-10 transition-all duration-300 ease-in-out ${
            isSidebarExpanded ? "left-60" : "left-16"
          }`}>
            <div className="max-w-2xl mx-auto">
              {courseClarificationQuestions.length > 0 && (
                <CourseClarificationWindow
                  questions={courseClarificationQuestions}
                  values={courseClarificationValues}
                  currentIndex={courseClarificationIndex}
                  onChange={handleClarificationAnswerChange}
                  onNext={handleClarificationNext}
                  onPrev={handleClarificationPrev}
                  onDismiss={() => {
                    setCourseClarificationQuestions([])
                    setCourseClarificationIndex(0)
                    setCourseClarificationValues({})
                  }}
                  onSubmit={submitClarificationAnswers}
                  parseChoiceValues={parseChoiceValues}
                  toggleChoiceAnswer={toggleChoiceAnswer}
                />
              )}
              {selectedProject && (
                <div className="mb-2 inline-flex items-center gap-2 rounded-xl bg-zinc-900/80 border border-zinc-800 px-2.5 py-2">
                  <div className="w-8 h-8 rounded-md overflow-hidden bg-zinc-800 flex items-center justify-center">
                    {(selectedProject.thumbnail_url || getThumbnailUrl(selectedProject.video_url)) ? (
                      <img
                        src={selectedProject.thumbnail_url || getThumbnailUrl(selectedProject.video_url)}
                        alt={selectedProject.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Image className="w-3.5 h-3.5 text-zinc-600" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-zinc-100 text-xs leading-tight truncate max-w-[220px]">{selectedProject.name}</p>
                    <p className="text-zinc-400 text-[10px] leading-tight">Context video</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedProject(null)
                      setActiveProjectName(null)
                    }}
                    className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                    title="Clear context video"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <ChatInput
                onSend={handleSendMessage}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatContainer
