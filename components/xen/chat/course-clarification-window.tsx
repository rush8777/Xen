"use client"

import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, ArrowRight, ChevronLeft, ChevronRight } from "lucide-react"

export interface CourseClarificationQuestion {
  id: string
  label: string
  input_type: "single_choice" | "multi_choice" | "short_text" | "long_text" | "number"
  options?: string[]
  max_select?: number
  placeholder?: string
  required?: boolean
  help_text?: string
}

interface Props {
  questions: CourseClarificationQuestion[]
  values: Record<string, string>
  currentIndex: number
  onChange: (id: string, value: string) => void
  onNext: () => void
  onPrev: () => void
  onDismiss: () => void
  onSubmit: () => void
  parseChoiceValues: (raw: string) => string[]
  toggleChoiceAnswer: (question: CourseClarificationQuestion, option: string) => void
}

export default function CourseClarificationWindow({
  questions,
  values,
  currentIndex,
  onChange,
  onNext,
  onPrev,
  onDismiss,
  onSubmit,
  parseChoiceValues,
  toggleChoiceAnswer,
}: Props) {
  const [activeChoiceIndex, setActiveChoiceIndex] = useState(0)
  const total = questions.length
  const question = questions[currentIndex]

  const hasOptions =
    !!question &&
    (question.input_type === "single_choice" || question.input_type === "multi_choice") &&
    Array.isArray(question.options) &&
    question.options.length > 0

  const selectedChoices = useMemo(
    () => (question ? parseChoiceValues(values[question.id] || "") : []),
    [parseChoiceValues, question, values]
  )
  const currentValue = question ? values[question.id] || "" : ""
  const isFinalStep = currentIndex >= total - 1
  const isRequiredMissing = !!question?.required && !currentValue.trim()
  const canAdvance = !isRequiredMissing

  useEffect(() => {
    setActiveChoiceIndex(0)
  }, [currentIndex])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!question) return
      if (event.key === "Escape") {
        event.preventDefault()
        onDismiss()
        return
      }
      if (event.key === "Enter") {
        event.preventDefault()
        if (!canAdvance) return
        if (isFinalStep) {
          onSubmit()
        } else {
          onNext()
        }
        return
      }

      if (!hasOptions || !Array.isArray(question.options) || question.options.length === 0) {
        return
      }
      if (question.input_type !== "single_choice") {
        return
      }

      if (event.key === "ArrowDown") {
        event.preventDefault()
        setActiveChoiceIndex((prev) => (prev + 1) % question.options!.length)
      } else if (event.key === "ArrowUp") {
        event.preventDefault()
        setActiveChoiceIndex((prev) => (prev === 0 ? question.options!.length - 1 : prev - 1))
      } else if (event.key === " ") {
        event.preventDefault()
        const option = question.options[activeChoiceIndex]
        if (option) {
          toggleChoiceAnswer(question, option)
        }
      }
    }

    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [
    activeChoiceIndex,
    canAdvance,
    hasOptions,
    isFinalStep,
    onDismiss,
    onNext,
    onSubmit,
    question,
    toggleChoiceAnswer,
  ])

  if (!question) return null

  return (
    <div className="mb-3 w-full animate-in slide-in-from-bottom-3 fade-in duration-150">
      <div
        className="mx-auto w-full max-w-[620px] rounded-[20px] border p-4 shadow-[0_18px_45px_rgba(0,0,0,0.45)] md:p-5"
        style={{
          borderColor: "#3a3b40",
          background: "linear-gradient(180deg, #2a2a2d 0%, #222326 100%)",
        }}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <h3 className="text-[23px] font-semibold leading-[1.2] text-zinc-100">{question.label}</h3>
          <div className="flex items-center gap-2 text-zinc-400">
            <button
              type="button"
              onClick={onPrev}
              disabled={currentIndex === 0}
              className="rounded-md p-1 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-35"
              aria-label="Previous question"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="min-w-[50px] text-xs font-medium text-zinc-300">{currentIndex + 1} of {total}</span>
            <button
              type="button"
              onClick={isFinalStep ? onSubmit : onNext}
              disabled={!canAdvance}
              className="rounded-md p-1 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-35"
              aria-label={isFinalStep ? "Submit answers" : "Next question"}
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="min-h-[132px]">
          {hasOptions && Array.isArray(question.options) ? (
            <div className="space-y-1.5">
              {question.options.map((option, idx) => {
                const selected = selectedChoices.includes(option)
                const focused = question.input_type === "single_choice" && activeChoiceIndex === idx
                return (
                  <button
                    key={`${question.id}-${option}`}
                    type="button"
                    onClick={() => toggleChoiceAnswer(question, option)}
                    className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left text-[14px] transition-all duration-150 ${
                      selected
                        ? "border-zinc-500 bg-white/9 text-zinc-100"
                        : "border-transparent bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06]"
                    } ${focused ? "ring-1 ring-blue-400/50" : ""}`}
                  >
                    <span className="w-6 shrink-0 text-zinc-400">{idx + 1}.</span>
                    <span className="flex-1">{option}</span>
                  </button>
                )
              })}
            </div>
          ) : question.input_type === "long_text" ? (
            <textarea
              value={currentValue}
              onChange={(e) => onChange(question.id, e.target.value)}
              placeholder={question.placeholder || "Type your answer..."}
              rows={4}
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 outline-none transition-colors duration-150 placeholder:text-zinc-500 focus:border-blue-400/60"
            />
          ) : (
            <input
              type={question.input_type === "number" ? "number" : "text"}
              value={currentValue}
              onChange={(e) => onChange(question.id, e.target.value)}
              placeholder={question.placeholder || "Type your answer..."}
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 outline-none transition-colors duration-150 placeholder:text-zinc-500 focus:border-blue-400/60"
            />
          )}

          {question.input_type === "multi_choice" && (
            <p className="mt-2 text-[11px] text-zinc-400">
              Select up to {Math.max(1, question.max_select || 2)} options.
            </p>
          )}
          {question.help_text && <p className="mt-2 text-[11px] text-zinc-400">{question.help_text}</p>}
          {isRequiredMissing && (
            <p className="mt-2 text-[11px] text-amber-300">This question is required to continue.</p>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button
            type="button"
            onClick={onDismiss}
            className="inline-flex items-center gap-2 rounded-lg px-1 py-1 text-sm text-zinc-300 transition-colors hover:text-zinc-100"
          >
            <span>Dismiss</span>
            <span className="rounded-md border border-zinc-600 bg-zinc-800/80 px-1.5 py-0.5 text-[11px] text-zinc-200">
              ESC
            </span>
          </button>

          <button
            type="button"
            onClick={isFinalStep ? onSubmit : onNext}
            disabled={!canAdvance}
            className="inline-flex items-center gap-2 rounded-full bg-[#3DA8FF] px-4 py-2 text-sm font-medium text-zinc-950 transition-all duration-150 hover:bg-[#59B5FF] disabled:cursor-not-allowed disabled:opacity-45"
          >
            <span>{isFinalStep ? "Generate" : "Continue"}</span>
            {isFinalStep ? <ArrowRight className="h-4 w-4" /> : <ArrowLeft className="h-4 w-4 rotate-180" />}
          </button>
        </div>
      </div>
    </div>
  )
}
