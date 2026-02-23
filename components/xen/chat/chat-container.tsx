"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import ChatInput from "./chatinputui"
import ChatMessage from "./chatmassegeui"
import { useSidebarContext } from "../main/layout"
import { TopBar } from "./chatmassegeui"
import NewChatScreen from "./new-chat-screen"
import type { CourseSlides } from "@/components/teach-canvas-kit-component/data/courseData"

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
  courseData?: CourseSlides | null
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
type CourseTemplateId = "default" | "sonos_typo" | "pixel_brutalist"
const COURSE_PAYLOAD_PREFIX = "[[COURSE_PAYLOAD_V1:"
const COURSE_PAYLOAD_SUFFIX = "]]"

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
  const [courseClarificationQuestions, setCourseClarificationQuestions] = useState<CourseClarificationQuestion[]>([])
  const [courseClarificationValues, setCourseClarificationValues] = useState<Record<string, string>>({})
  const [selectedCourseTemplate, setSelectedCourseTemplate] = useState<CourseTemplateId>("default")
  const [courseModeEnabled, setCourseModeEnabled] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const projectIdParam = searchParams.get("projectId")
  const resolvedProjectId =
    projectIdParam && Number.isFinite(Number(projectIdParam))
      ? Number(projectIdParam)
      : null

  const isValidCourseData = (value: unknown): value is CourseSlides => {
    if (!value || typeof value !== "object") return false
    const payload = value as CourseSlides
    return (
      typeof payload.courseTitle === "string" &&
      payload.courseTitle.trim().length > 0 &&
      Array.isArray(payload.slides) &&
      payload.slides.length > 0
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
  ): { cleanContent: string; courseData: CourseSlides | null; courseTemplate: CourseTemplateId } => {
    const content = raw || ""
    const start = content.indexOf(COURSE_PAYLOAD_PREFIX)
    const end = content.indexOf(COURSE_PAYLOAD_SUFFIX, start + COURSE_PAYLOAD_PREFIX.length)
    if (start === -1 || end === -1) {
      return { cleanContent: content, courseData: null, courseTemplate: "default" }
    }

    const encoded = content.slice(start + COURSE_PAYLOAD_PREFIX.length, end).trim()
    const cleanContent = (content.slice(0, start) + content.slice(end + COURSE_PAYLOAD_SUFFIX.length)).trim()
    try {
      const decoded = decodeBase64Url(encoded)
      const parsed = JSON.parse(decoded) as {
        course_data?: CourseSlides
        course_template?: CourseTemplateId
      }
      const parsedCourseData = parsed?.course_data
      const parsedTemplate = parsed?.course_template
      return {
        cleanContent,
        courseData: isValidCourseData(parsedCourseData) ? parsedCourseData : null,
        courseTemplate:
          parsedTemplate === "sonos_typo" || parsedTemplate === "pixel_brutalist"
            ? parsedTemplate
            : "default",
      }
    } catch {
      return { cleanContent, courseData: null, courseTemplate: "default" }
    }
  }

  const openCoursePage = (courseData: CourseSlides, template: CourseTemplateId = selectedCourseTemplate) => {
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
                  courseTemplate: "default" as CourseTemplateId,
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
        : courseModeEnabled
    const resolvedCourseAnswers: Record<string, string> = {
      ...(clarificationAnswers || {}),
      course_template: selectedCourseTemplate,
    }
    const normalizedMention = mentionedProject?.trim()
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
      content: "",
      isUser: false,
      isStreaming: true,
      timestamp: new Date(),
      ragActive: false,
      contextChunksUsed: 0,
      courseData: null,
      courseSummary: null,
      courseTemplate: selectedCourseTemplate,
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
      const res = await fetch(`${API_BASE_URL}/api/chats/send-message-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          project_id: resolvedProjectId,
          message: content,
          user_id: null,
          course_clarification_answers: resolvedCourseAnswers,
          course_mode_enabled: effectiveCourseModeEnabled,
        })
      })

      const handleLegacyNonStreaming = async () => {
        const legacyRes = await fetch(`${API_BASE_URL}/api/chats/send-message`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: chatId,
            project_id: resolvedProjectId,
            message: content,
            user_id: null,
            course_clarification_answers: resolvedCourseAnswers,
            course_mode_enabled: effectiveCourseModeEnabled,
          }),
        })

        if (!legacyRes.ok) {
          const legacyErr = await legacyRes.json().catch(() => ({}))
          throw new Error(legacyErr?.detail || `Request failed (${legacyRes.status})`)
        }

        const data: {
          chat_id: number
          messages: Array<{ role: string; content: string }>
          rag_active?: boolean
          context_chunks_used?: number
          context_chunks?: string[]
          course_generated?: boolean
          course_summary?: string | null
          course_data?: CourseSlides | null
          course_template?: CourseTemplateId | null
          course_clarification_needed?: boolean
          course_clarification_questions?: CourseClarificationQuestion[]
        } = await legacyRes.json()

        setChatId(data.chat_id)
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
          const nextValues: Record<string, string> = {}
          for (const q of clarificationQuestions) {
            if (q?.id) nextValues[q.id] = ""
          }
          setCourseClarificationValues(nextValues)
        } else {
          setCourseClarificationQuestions([])
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
                  courseTemplate:
                    data.course_template === "sonos_typo" || data.course_template === "pixel_brutalist"
                      ? data.course_template
                      : "default",
                }
              : m
          )
        )

        if (data.course_generated && data.course_data && isValidCourseData(data.course_data)) {
          const tpl =
            data.course_template === "sonos_typo" || data.course_template === "pixel_brutalist"
              ? data.course_template
              : "default"
          openCoursePage(data.course_data, tpl)
        }
      }

      if (!res.ok) {
        if (res.status === 404 || res.status === 405) {
          await handleLegacyNonStreaming()
          return
        }
        const err = await res.json().catch(() => ({}))
        throw new Error(err?.detail || `Request failed (${res.status})`)
      }
      if (!res.body) {
        throw new Error("Streaming response body is not available")
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let streamErrored = false

      const processSseEvent = (rawEvent: string) => {
        const lines = rawEvent.split(/\r?\n/)
        let eventType = "message"
        const dataLines: string[] = []

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim()
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trimStart())
          }
        }

        if (dataLines.length === 0) return

        let payload: any = null
        try {
          payload = JSON.parse(dataLines.join("\n"))
        } catch {
          return
        }

        if (eventType === "meta") {
          if (typeof payload.chat_id === "number") {
            setChatId(payload.chat_id)
          }
          setRagActive(!!payload.rag_active)
          setContextChunks(Array.isArray(payload.context_chunks) ? payload.context_chunks : [])
          const clarificationNeeded = !!payload.course_clarification_needed
          const clarificationQuestions = Array.isArray(payload.course_clarification_questions)
            ? payload.course_clarification_questions
            : []
          if (clarificationNeeded && clarificationQuestions.length > 0) {
            setCourseClarificationQuestions(clarificationQuestions)
            const nextValues: Record<string, string> = {}
            for (const q of clarificationQuestions) {
              if (q?.id) nextValues[q.id] = ""
            }
            setCourseClarificationValues(nextValues)
          } else if (!clarificationNeeded) {
            setCourseClarificationQuestions([])
            setCourseClarificationValues({})
          }
          return
        }

        if (eventType === "token") {
          const delta = typeof payload.delta === "string" ? payload.delta : ""
          if (!delta) return
          setIsLoading(false)
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, content: (m.content || "") + delta }
                : m
            )
          )
          return
        }

        if (eventType === "done") {
          if (typeof payload.chat_id === "number") {
            setChatId(payload.chat_id)
          }
          const finalRagActive = !!payload.rag_active
          const finalContextChunksUsed =
            typeof payload.context_chunks_used === "number" ? payload.context_chunks_used : 0
          const finalContextChunks = Array.isArray(payload.context_chunks) ? payload.context_chunks : []

          const courseGenerated = !!payload.course_generated
          const courseSummary = typeof payload.course_summary === "string" ? payload.course_summary : null
          const courseData = payload.course_data
          const clarificationNeeded = !!payload.course_clarification_needed
          const clarificationQuestions = Array.isArray(payload.course_clarification_questions)
            ? payload.course_clarification_questions
            : []

          setRagActive(finalRagActive)
          setContextChunks(finalContextChunks)
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? {
                    ...m,
                    kind: courseGenerated ? "course" : "text",
                    content:
                      courseSummary ||
                      (typeof payload.content === "string" && payload.content.length > 0
                        ? payload.content
                        : m.content || "No response received."),
                    isStreaming: false,
                    ragActive: finalRagActive,
                    contextChunksUsed: finalContextChunksUsed,
                    courseData: courseGenerated && isValidCourseData(courseData) ? courseData : null,
                    courseSummary,
                    courseTemplate:
                      payload.course_template === "sonos_typo" || payload.course_template === "pixel_brutalist"
                        ? payload.course_template
                        : "default",
                  }
                : m
            )
          )

          if (clarificationNeeded && clarificationQuestions.length > 0) {
            setCourseClarificationQuestions(clarificationQuestions)
            const nextValues: Record<string, string> = {}
            for (const q of clarificationQuestions) {
              if (q?.id) nextValues[q.id] = ""
            }
            setCourseClarificationValues(nextValues)
          } else if (!clarificationNeeded && courseGenerated) {
            setCourseClarificationQuestions([])
            setCourseClarificationValues({})
          }

          if (courseGenerated && isValidCourseData(courseData)) {
            const tpl =
              payload.course_template === "sonos_typo" || payload.course_template === "pixel_brutalist"
                ? payload.course_template
                : "default"
            openCoursePage(courseData, tpl)
          }
          return
        }

        if (eventType === "error") {
          streamErrored = true
          const errMsg =
            typeof payload.error === "string" && payload.error.length > 0
              ? payload.error
              : "Streaming generation failed"
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, content: `Error: ${errMsg}`, isStreaming: false }
                : m
            )
          )
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n")

        let boundaryIndex = buffer.indexOf("\n\n")
        while (boundaryIndex !== -1) {
          const rawEvent = buffer.slice(0, boundaryIndex)
          buffer = buffer.slice(boundaryIndex + 2)
          processSseEvent(rawEvent)
          boundaryIndex = buffer.indexOf("\n\n")
        }
      }

      if (!streamErrored) {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantMessageId && !(m.content || "").trim()
              ? { ...m, content: "No response received.", isStreaming: false }
              : m
          )
        )
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

  const handleStartChat = (message: string) => {
    setIsChatActive(true)
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
    setCourseClarificationQuestions([])
    setCourseClarificationValues({})
    setSelectedCourseTemplate("default")
    setCourseModeEnabled(false)
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
                        courseTemplate={message.courseTemplate || "default"}
                        onOpenCourse={
                          messageCourseData
                            ? () =>
                                openCoursePage(
                                  messageCourseData,
                                  message.courseTemplate || selectedCourseTemplate
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
              <div className="mb-2 flex items-center gap-1.5">
                <span className="text-[10px] uppercase tracking-wide text-zinc-500">Course Template</span>
                {[
                  { id: "default", label: "Default" },
                  { id: "sonos_typo", label: "Sonos Typo" },
                  { id: "pixel_brutalist", label: "Pixel Brutalist" },
                ].map((tpl) => {
                  const active = selectedCourseTemplate === tpl.id
                  return (
                    <button
                      key={tpl.id}
                      type="button"
                      onClick={() => setSelectedCourseTemplate(tpl.id as CourseTemplateId)}
                      className={`rounded-full border px-2.5 py-1 text-[10px] font-medium transition-colors ${
                        active
                          ? "border-zinc-200 bg-zinc-100 text-zinc-900"
                          : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500"
                      }`}
                    >
                      {tpl.label}
                    </button>
                  )
                })}
              </div>
              {courseClarificationQuestions.length > 0 && (
                <div className="mb-3 rounded-2xl border border-zinc-700/80 bg-zinc-900/95 p-3 shadow-2xl">
                  <div className="mb-2 text-xs font-semibold text-zinc-100">Quick Course Setup</div>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {courseClarificationQuestions.map((q) => (
                      <div key={q.id} className="space-y-1">
                        <label className="text-[11px] text-zinc-300">
                          {q.label}
                          {q.required ? " *" : ""}
                        </label>
                        {q.input_type === "multi_choice" && (
                          <div className="text-[10px] text-zinc-500">
                            Select up to {Math.max(1, q.max_select || 2)}
                          </div>
                        )}
                        {(q.input_type === "single_choice" || q.input_type === "multi_choice") &&
                        Array.isArray(q.options) &&
                        q.options.length > 0 ? (
                          <div className="flex flex-wrap gap-1.5">
                            {q.options.map((option) => {
                              const selectedChoices = parseChoiceValues(courseClarificationValues[q.id] || "")
                              const selected = selectedChoices.includes(option)
                              return (
                                <button
                                  key={`${q.id}-${option}`}
                                  type="button"
                                  onClick={() => toggleChoiceAnswer(q, option)}
                                  className={`rounded-full border px-2.5 py-1 text-[11px] transition-colors ${
                                    selected
                                      ? "border-zinc-200 bg-zinc-100 text-zinc-900"
                                      : "border-zinc-700 bg-zinc-950 text-zinc-300 hover:border-zinc-500"
                                  }`}
                                >
                                  {option}
                                </button>
                              )
                            })}
                          </div>
                        ) : q.input_type === "long_text" ? (
                          <textarea
                            value={courseClarificationValues[q.id] || ""}
                            onChange={(e) => handleClarificationAnswerChange(q.id, e.target.value)}
                            placeholder={q.placeholder || ""}
                            rows={3}
                            className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-zinc-500"
                          />
                        ) : (
                          <input
                            type={q.input_type === "number" ? "number" : "text"}
                            value={courseClarificationValues[q.id] || ""}
                            onChange={(e) => handleClarificationAnswerChange(q.id, e.target.value)}
                            placeholder={q.placeholder || ""}
                            className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100 outline-none focus:border-zinc-500"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setCourseClarificationQuestions([])
                        setCourseClarificationValues({})
                      }}
                      className="rounded-md border border-zinc-700 px-2 py-1 text-[11px] text-zinc-300 hover:bg-zinc-800"
                    >
                      Dismiss
                    </button>
                    <button
                      type="button"
                      onClick={submitClarificationAnswers}
                      className="rounded-md bg-zinc-100 px-2 py-1 text-[11px] font-semibold text-zinc-900 hover:bg-white"
                    >
                      Generate Course
                    </button>
                  </div>
                </div>
              )}
              <ChatInput
                onSend={handleSendMessage}
                courseModeEnabled={courseModeEnabled}
                onToggleCourseMode={() => setCourseModeEnabled((prev) => !prev)}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatContainer
