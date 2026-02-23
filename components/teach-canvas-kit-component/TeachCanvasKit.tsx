"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Check, X } from "lucide-react";
import { cn } from "./lib/utils";
import { courseSlides, CourseSlides, Slide } from "./data/courseData";
import slideIllustration from "./assets/slide-illustration.png";

type ThemeId = "theme-midnight" | "theme-graphite" | "theme-neon" | "theme-emerald";

const THEMES: { id: ThemeId; label: string; bg: string; dot: string }[] = [
  { id: "theme-midnight", label: "Midnight", bg: "linear-gradient(135deg,#0f172a,#111827)", dot: "#22d3ee" },
  { id: "theme-graphite", label: "Graphite", bg: "linear-gradient(135deg,#0b0f19,#1f2937)", dot: "#f59e0b" },
  { id: "theme-neon", label: "Neon", bg: "linear-gradient(135deg,#08141f,#1a1031)", dot: "#a78bfa" },
  { id: "theme-emerald", label: "Emerald", bg: "linear-gradient(135deg,#071a17,#0f172a)", dot: "#34d399" },
];

function ProgressBar({ total, current }: { total: number; current: number }) {
  return (
    <div className="relative z-10 flex gap-1.5 px-6 py-3">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-1.5 flex-1 rounded-full transition-all duration-500",
            i < current ? "bg-primary" : i === current ? "bg-primary/55" : "bg-foreground/15"
          )}
        />
      ))}
    </div>
  );
}

function ThemeSwitcher({ active, onChange }: { active: ThemeId; onChange: (t: ThemeId) => void }) {
  return (
    <div className="flex items-center gap-2">
      {THEMES.map((t) => (
        <button
          key={t.id}
          title={t.label}
          onClick={() => onChange(t.id)}
          className={cn(
            "h-6 w-6 rounded-full border-2 transition-all",
            active === t.id ? "scale-110 border-white/70 shadow-sm" : "border-white/20 hover:scale-105"
          )}
          style={{ background: t.bg, boxShadow: active === t.id ? `0 0 0 2px ${t.dot}44` : undefined }}
        >
          {active === t.id && (
            <span className="mx-auto block h-2.5 w-2.5 rounded-full" style={{ background: t.dot }} />
          )}
        </button>
      ))}
    </div>
  );
}

function TitleSlide({ slide, onNext }: { slide: Slide; onNext: () => void }) {
  return (
    <div className="flex flex-1 items-center px-8 md:px-16">
      <div className="max-w-xl">
        <h1 className="mb-5 text-4xl font-bold leading-tight text-foreground md:text-5xl animate-[fadeInUp_420ms_ease-out]">{slide.title}</h1>
        <p className="mb-10 text-lg leading-relaxed text-foreground/70">{slide.subtitle}</p>
        <button
          onClick={onNext}
          className="rounded-full bg-primary px-8 py-3.5 text-base font-semibold text-primary-foreground shadow-[0_8px_24px_rgba(0,0,0,0.35)] transition-all hover:bg-primary/90"
        >
          {slide.buttonLabel || "Start"}
        </button>
      </div>
    </div>
  );
}

function TextImageSlide({ slide }: { slide: Slide }) {
  return (
    <div className="flex flex-1 flex-col items-center gap-10 px-8 md:flex-row md:gap-16 md:px-16">
      <div className="max-w-xl flex-1">
        <h1 className="mb-6 text-3xl font-bold leading-tight text-foreground md:text-4xl">{slide.title}</h1>
        <p className="text-base leading-relaxed text-foreground/75">{slide.body}</p>
      </div>
      <div className="flex h-72 w-72 shrink-0 items-center justify-center rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-md md:h-80 md:w-80">
        <img
          src={typeof slideIllustration === "string" ? slideIllustration : slideIllustration.src}
          alt="Illustration"
          className="h-full w-full animate-[floatY_5s_ease-in-out_infinite] object-contain drop-shadow-[0_18px_40px_rgba(0,0,0,0.5)]"
        />
      </div>
    </div>
  );
}

function TextOnlySlide({ slide }: { slide: Slide }) {
  return (
    <div className="flex flex-1 items-center px-8 md:px-16">
      <div className="max-w-2xl">
        <h1 className="mb-6 text-3xl font-bold leading-tight text-foreground md:text-4xl">{slide.title}</h1>
        <p className="text-lg leading-relaxed text-foreground/75">{slide.body}</p>
      </div>
    </div>
  );
}

function CardsSlide({ slide }: { slide: Slide }) {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-10 md:px-16 md:py-12">
      <h1 className="mb-10 text-3xl font-bold text-foreground md:text-4xl">{slide.title}</h1>
      <div className="grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {slide.cards?.map((card, i) => (
          <div
            key={i}
            className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition-all hover:-translate-y-0.5 hover:bg-white/[0.08] hover:shadow-[0_14px_40px_rgba(0,0,0,0.35)]"
          >
            {card.icon && <span className="mb-3 block text-2xl">{card.icon}</span>}
            <h3 className="mb-2 text-base font-bold text-foreground">{card.heading}</h3>
            <p className="text-sm leading-relaxed text-foreground/65">{card.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChecklistSlide({ slide }: { slide: Slide }) {
  const [checked, setChecked] = useState<Set<number>>(
    new Set(slide.items?.map((item, i) => (item.checked ? i : -1)).filter((i) => i >= 0) ?? [])
  );

  const toggle = (i: number) =>
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  return (
    <div className="flex-1 overflow-y-auto px-8 py-10 md:px-16 md:py-12">
      <h1 className="mb-8 text-3xl font-bold text-foreground md:text-4xl">{slide.title}</h1>
      <ul className="max-w-2xl space-y-4">
        {slide.items?.map((item, i) => {
          const isChecked = checked.has(i);
          return (
            <li key={i} onClick={() => toggle(i)} className="group flex cursor-pointer items-start gap-4">
              <span
                className={cn(
                  "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 transition-all",
                  isChecked
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-foreground/30 text-transparent group-hover:border-primary/50"
                )}
              >
                <Check className="h-4 w-4" />
              </span>
              <p
                className={cn(
                  "text-base leading-relaxed transition-colors",
                  isChecked ? "text-foreground/45 line-through" : "text-foreground/80"
                )}
              >
                {item.text}
              </p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function QuizSlide({ slide, onComplete }: { slide: Slide; onComplete: () => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (selected === null) return;
    setSubmitted(true);
    if (selected === slide.correctAnswer) setTimeout(onComplete, 800);
  };

  return (
    <div className="flex-1 overflow-y-auto px-8 py-10 md:px-16 md:py-12">
      <div className="max-w-2xl">
        <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-primary">Knowledge Check</p>
        <h1 className="mb-2 text-3xl font-bold text-foreground">{slide.title}</h1>
        <p className="mb-8 text-base text-foreground/70">{slide.quizQuestion}</p>
        <div className="space-y-3">
          {slide.quizOptions?.map((opt, i) => {
            const isSelected = selected === i;
            const isCorrect = i === slide.correctAnswer;
            return (
              <button
                key={i}
                onClick={() => !submitted && setSelected(i)}
                disabled={submitted}
                className={cn(
                  "flex w-full items-center gap-4 rounded-2xl border-2 p-4 text-left transition-all",
                  !submitted && !isSelected && "border-foreground/15 bg-background/30 hover:border-primary/40 hover:bg-background/50",
                  !submitted && isSelected && "border-primary bg-primary/10",
                  submitted && isCorrect && "border-primary bg-primary/15",
                  submitted && isSelected && !isCorrect && "border-destructive bg-destructive/10",
                  submitted && !isSelected && !isCorrect && "border-foreground/10 bg-background/20 opacity-50"
                )}
              >
                <span
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold transition-all",
                    !submitted && isSelected ? "border-primary bg-primary text-primary-foreground" : "border-foreground/20 text-foreground/50",
                    submitted && isCorrect && "border-primary bg-primary text-primary-foreground",
                    submitted && isSelected && !isCorrect && "border-destructive bg-destructive text-destructive-foreground"
                  )}
                >
                  {submitted && isCorrect ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : submitted && isSelected && !isCorrect ? (
                    <X className="h-3.5 w-3.5" />
                  ) : (
                    String.fromCharCode(65 + i)
                  )}
                </span>
                <span className={cn("text-sm font-medium", isSelected && !submitted ? "text-primary" : "text-foreground/80")}>{opt}</span>
              </button>
            );
          })}
        </div>

        {!submitted && (
          <button
            onClick={handleSubmit}
            disabled={selected === null}
            className={cn(
              "mt-6 rounded-full px-8 py-3 text-sm font-semibold transition-all",
              selected !== null ? "bg-primary text-primary-foreground hover:bg-primary/90" : "cursor-not-allowed bg-foreground/10 text-foreground/30"
            )}
          >
            Submit Answer
          </button>
        )}

        {submitted && (
          <div className={cn("mt-4 flex items-center gap-2 text-sm font-medium", selected === slide.correctAnswer ? "text-primary" : "text-destructive")}>
            {selected === slide.correctAnswer ? (
              <>
                <Check className="h-4 w-4" /> Correct! Moving to next slide...
              </>
            ) : (
              <>
                <X className="h-4 w-4" /> Not quite - the correct answer is highlighted.
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export interface TeachCanvasKitProps {
  courseData?: CourseSlides;
  className?: string;
}

export default function TeachCanvasKit({ courseData = courseSlides, className }: TeachCanvasKitProps) {
  const slides = courseData.slides || [];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [quizPassed, setQuizPassed] = useState(false);
  const [theme, setTheme] = useState<ThemeId>("theme-midnight");

  if (slides.length === 0) {
    return (
      <div className={cn("flex h-full min-h-0 items-center justify-center rounded-xl border border-white/10 bg-black/20", className)}>
        <p className="text-sm text-zinc-400">No slides available for this course.</p>
      </div>
    );
  }

  const slide = slides[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === slides.length - 1;

  const goNext = () => {
    if (!isLast) {
      setCurrentIndex((i) => i + 1);
      setQuizPassed(false);
    }
  };

  const goPrev = () => {
    if (!isFirst) {
      setCurrentIndex((i) => i - 1);
      setQuizPassed(false);
    }
  };

  const canGoNext = slide.type !== "quiz" || quizPassed;

  const renderSlide = () => {
    switch (slide.type) {
      case "title":
        return <TitleSlide slide={slide} onNext={goNext} />;
      case "text-image":
        return <TextImageSlide slide={slide} />;
      case "text-only":
        return <TextOnlySlide slide={slide} />;
      case "checklist":
        return <ChecklistSlide slide={slide} />;
      case "quiz":
        return <QuizSlide slide={slide} onComplete={() => setQuizPassed(true)} />;
      case "cards":
        return <CardsSlide slide={slide} />;
      default:
        return null;
    }
  };

  return (
    <div className={cn("relative flex h-full min-h-0 flex-col overflow-hidden rounded-xl transition-colors duration-500", theme, className)}>
      <div className="pointer-events-none absolute inset-0">
        <div className="tk-orb tk-orb-one" />
        <div className="tk-orb tk-orb-two" />
        <div className="tk-grid" />
      </div>

      <div className="relative z-10 flex shrink-0 items-center justify-between border-b border-foreground/10 bg-black/20 px-5 py-3 backdrop-blur-md">
        <span className="text-xs font-semibold uppercase tracking-wider text-foreground/70">{courseData.courseTitle}</span>
        <ThemeSwitcher active={theme} onChange={setTheme} />
      </div>

      <ProgressBar total={slides.length} current={currentIndex} />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden">{renderSlide()}</div>

      <div className="relative z-10 flex shrink-0 items-center justify-between border-t border-foreground/10 bg-black/20 px-6 py-4 backdrop-blur-md md:px-8 md:py-5">
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2">
          <div className="h-3.5 w-3.5 rounded-full bg-primary" />
          <span className="text-xs font-semibold text-foreground/70">Premium Course Mode</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={goPrev}
            disabled={isFirst}
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-full border-2 transition-all",
              !isFirst ? "border-foreground/25 bg-background/40 text-foreground/70 hover:border-foreground/45" : "cursor-not-allowed border-foreground/10 text-foreground/20"
            )}
          >
            <ChevronLeft className="h-5 w-5" />
          </button>

          <div className="min-w-[64px] rounded-full bg-foreground/10 px-4 py-2 text-center text-sm font-semibold text-foreground/70">
            {currentIndex + 1}/{slides.length}
          </div>

          <button
            onClick={goNext}
            disabled={isLast || !canGoNext}
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-full transition-all",
              !isLast && canGoNext ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90" : "cursor-not-allowed bg-foreground/10 text-foreground/25"
            )}
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
