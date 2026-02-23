// @ts-nocheck
/**
 * PixelBrutalistCourse — Embeddable Course Slide Template
 *
 * Aesthetic: Pixel-Brutalist editorial — electric yellow + royal blue + near-black
 * Inspired by Clario pitch deck visual language.
 *
 * USAGE (embed in any React project):
 *   import PixelBrutalistCourse from './PixelBrutalistCourse';
 *   <PixelBrutalistCourse courseData={myCourseData} />
 *
 * courseData shape mirrors the CourseData interface below.
 *
 * Slide types: "title" | "text-only" | "text-stat" | "cards" | "checklist" | "quiz"
 */

import { useState, useEffect, useRef, CSSProperties, ReactNode } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CardItem {
  icon?: string;
  heading: string;
  description: string;
}

export interface ChecklistItem {
  text: string;
  checked?: boolean;
}

export type SlideType =
  | "title"
  | "text-only"
  | "text-stat"
  | "cards"
  | "checklist"
  | "quiz";

export type PaletteName = "dark" | "yellow" | "blue" | "light";

export interface Slide {
  type: SlideType;
  palette?: PaletteName;
  title: string;
  // title slide
  label?: string;
  subtitle?: string;
  buttonLabel?: string;
  courseTitle?: string;
  // text-only / text-stat
  eyebrow?: string;
  body?: string;
  // text-stat
  stat?: string;
  // cards
  cards?: CardItem[];
  // checklist
  items?: ChecklistItem[];
  // quiz
  quizQuestion?: string;
  quizOptions?: string[];
  correctAnswer?: number;
}

export interface CourseData {
  courseTitle: string;
  subtitle?: string;
  slides: Slide[];
}

interface PaletteConfig {
  bg: string;
  fg: string;
  fg2: string;
  accent: string;
  accent2: string;
  border: string;
  cardBg: string;
  navBg: string;
  pixelPalette: "dark" | "yellow" | "blue";
}

// ─── Pixel noise squares scattered in background ──────────────────────────────

interface PixelConfig {
  top?: string;
  left?: string;
  right?: string;
  bottom?: string;
  size: number;
  color: string;
  opacity: number;
}

const PIXEL_CONFIGS: PixelConfig[] = [
  { top: "4%",   left: "8%",   size: 28, color: "#E8FF00", opacity: 0.85 },
  { top: "6%",   left: "14%",  size: 18, color: "#0000FF", opacity: 0.7  },
  { top: "2%",   left: "22%",  size: 36, color: "#E8FF00", opacity: 0.5  },
  { top: "8%",   right: "5%",  size: 44, color: "#0000FF", opacity: 0.9  },
  { top: "3%",   right: "14%", size: 22, color: "#E8FF00", opacity: 0.6  },
  { top: "12%",  right: "8%",  size: 18, color: "#ffffff", opacity: 0.4  },
  { bottom: "4%",left: "5%",   size: 32, color: "#0000FF", opacity: 0.8  },
  { bottom: "8%",left: "15%",  size: 20, color: "#E8FF00", opacity: 0.55 },
  { bottom: "3%",left: "25%",  size: 14, color: "#0000FF", opacity: 0.4  },
  { bottom: "6%",right: "4%",  size: 26, color: "#E8FF00", opacity: 0.7  },
  { bottom: "12%",right: "12%",size: 40, color: "#0000FF", opacity: 0.5  },
  { bottom: "4%",right: "20%", size: 16, color: "#ffffff", opacity: 0.3  },
  { top: "35%",  left: "2%",   size: 22, color: "#E8FF00", opacity: 0.4  },
  { top: "55%",  right: "2%",  size: 30, color: "#0000FF", opacity: 0.35 },
];

interface PixelScatterProps {
  palette?: "dark" | "yellow" | "blue";
}

function PixelScatter({ palette = "dark" }: PixelScatterProps): JSX.Element {
  const configs = PIXEL_CONFIGS.map((cfg, i) => ({
    ...cfg,
    color:
      palette === "yellow"
        ? i % 3 === 0 ? "#0000FF" : i % 3 === 1 ? "#1a1a1a" : "#ffffff"
        : palette === "blue"
        ? i % 3 === 0 ? "#E8FF00" : i % 3 === 1 ? "#E8FF0088" : "#ffffff44"
        : cfg.color,
  }));

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        overflow: "hidden",
        zIndex: 0,
      }}
    >
      {configs.map((cfg, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: cfg.top,
            left: cfg.left,
            right: cfg.right,
            bottom: cfg.bottom,
            width: cfg.size,
            height: cfg.size,
            background: cfg.color,
            opacity: cfg.opacity,
          }}
        />
      ))}
    </div>
  );
}

// ─── Course-wide font injection ───────────────────────────────────────────────

const FONT_STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@700;800&display=swap');

  .pbc-root * { box-sizing: border-box; }
  .pbc-root { font-family: 'Space Mono', monospace; }

  .pbc-heading {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.05;
    text-transform: uppercase;
  }

  @keyframes pbc-fadeUp {
    from { opacity: 0; transform: translateY(22px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pbc-blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }

  .pbc-animate-up   { animation: pbc-fadeUp 0.45s ease-out both; }
  .pbc-animate-up-2 { animation: pbc-fadeUp 0.45s 0.1s ease-out both; }
  .pbc-animate-up-3 { animation: pbc-fadeUp 0.45s 0.2s ease-out both; }

  .pbc-cursor {
    display: inline-block;
    width: 3px; height: 1.1em;
    background: #E8FF00;
    margin-left: 4px;
    vertical-align: bottom;
    animation: pbc-blink 1s step-end infinite;
  }

  .pbc-card { transition: transform 0.2s, box-shadow 0.2s; }
  .pbc-card:hover {
    transform: translateY(-4px);
    box-shadow: 6px 6px 0 #E8FF00;
  }

  .pbc-btn {
    cursor: pointer; border: none; outline: none;
    font-family: 'Space Mono', monospace; font-weight: 700;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .pbc-btn:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 4px 4px 0 rgba(0,0,0,0.6); }
  .pbc-btn:active:not(:disabled){ transform: translate(0,0); box-shadow: none; }

  .pbc-progress-seg { height: 4px; border-radius: 0; flex: 1; transition: background 0.4s; }

  .pbc-checklist-item { cursor: pointer; user-select: none; }
  .pbc-checklist-item:hover .pbc-check-box { border-color: #E8FF00; }
`;

// ─── Progress Bar ─────────────────────────────────────────────────────────────

interface ProgressBarProps {
  total: number;
  current: number;
  accent: string;
}

function ProgressBar({ total, current, accent }: ProgressBarProps): JSX.Element {
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className="pbc-progress-seg"
          style={{
            background:
              i < current
                ? accent
                : i === current
                ? accent + "88"
                : "rgba(255,255,255,0.15)",
          }}
        />
      ))}
    </div>
  );
}

// ─── Palette map ──────────────────────────────────────────────────────────────

const PALETTE: Record<PaletteName, PaletteConfig> = {
  dark: {
    bg: "#111111",
    fg: "#ffffff",
    fg2: "rgba(255,255,255,0.6)",
    accent: "#E8FF00",
    accent2: "#0000FF",
    border: "rgba(255,255,255,0.12)",
    cardBg: "rgba(255,255,255,0.04)",
    navBg: "rgba(0,0,0,0.5)",
    pixelPalette: "dark",
  },
  yellow: {
    bg: "#E8FF00",
    fg: "#111111",
    fg2: "rgba(0,0,0,0.55)",
    accent: "#0000FF",
    accent2: "#111111",
    border: "rgba(0,0,0,0.15)",
    cardBg: "rgba(0,0,0,0.06)",
    navBg: "rgba(232,255,0,0.85)",
    pixelPalette: "yellow",
  },
  blue: {
    bg: "#0000FF",
    fg: "#ffffff",
    fg2: "rgba(255,255,255,0.7)",
    accent: "#E8FF00",
    accent2: "#111111",
    border: "rgba(255,255,255,0.15)",
    cardBg: "rgba(255,255,255,0.06)",
    navBg: "rgba(0,0,0,0.35)",
    pixelPalette: "blue",
  },
  light: {
    bg: "#f5f5ef",
    fg: "#111111",
    fg2: "rgba(0,0,0,0.5)",
    accent: "#0000FF",
    accent2: "#E8FF00",
    border: "rgba(0,0,0,0.12)",
    cardBg: "rgba(0,0,0,0.04)",
    navBg: "rgba(245,245,239,0.85)",
    pixelPalette: "yellow",
  },
};

const TYPE_PALETTE: Record<SlideType, PaletteName> = {
  "title":      "dark",
  "text-only":  "dark",
  "text-stat":  "blue",
  "cards":      "yellow",
  "checklist":  "light",
  "quiz":       "dark",
};

// ─── Slide component prop types ───────────────────────────────────────────────

interface SlideBaseProps {
  slide: Slide;
  p: PaletteConfig;
  animKey: number;
}

interface TitleSlideProps extends SlideBaseProps {
  onNext: () => void;
}

// ─── SLIDE RENDERERS ──────────────────────────────────────────────────────────

function TitleSlide({ slide, p, animKey, onNext }: TitleSlideProps): JSX.Element {
  return (
    <div
      key={animKey}
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        padding: "40px 60px",
        position: "relative",
        zIndex: 1,
      }}
    >
      <div style={{ maxWidth: 700 }}>
        <p
          className="pbc-animate-up"
          style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: 11,
            letterSpacing: "0.2em",
            color: p.accent,
            marginBottom: 24,
            textTransform: "uppercase",
          }}
        >
          {slide.label ?? "Course Module"}
        </p>
        <h1
          className="pbc-heading pbc-animate-up-2"
          style={{ fontSize: "clamp(36px, 5vw, 64px)", color: p.fg, marginBottom: 28, position: "relative" }}
        >
          {slide.title}
          <span className="pbc-cursor" />
        </h1>
        {slide.subtitle && (
          <p
            className="pbc-animate-up-3"
            style={{ fontSize: 16, lineHeight: 1.75, color: p.fg2, marginBottom: 40, maxWidth: 500 }}
          >
            {slide.subtitle}
          </p>
        )}
        <button
          className="pbc-btn pbc-animate-up-3"
          onClick={onNext}
          style={{
            background: p.accent,
            color: p.accent === "#E8FF00" ? "#111" : "#fff",
            padding: "14px 36px",
            fontSize: 13,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            border: `2px solid ${p.accent}`,
          }}
        >
          {slide.buttonLabel ?? "Begin →"}
        </button>
      </div>

      {/* Ghost background text */}
      <div
        style={{
          position: "absolute",
          right: "-2%",
          bottom: "8%",
          fontSize: "clamp(80px, 18vw, 220px)",
          fontFamily: "'Syne', sans-serif",
          fontWeight: 800,
          color: "rgba(255,255,255,0.03)",
          letterSpacing: "-0.05em",
          lineHeight: 1,
          userSelect: "none",
          pointerEvents: "none",
          textTransform: "uppercase",
        }}
      >
        {(slide.courseTitle ?? "LEARN").slice(0, 6)}
      </div>
    </div>
  );
}

function TextOnlySlide({ slide, p, animKey }: SlideBaseProps): JSX.Element {
  return (
    <div
      key={animKey}
      style={{ flex: 1, display: "flex", alignItems: "center", padding: "40px 60px", position: "relative", zIndex: 1 }}
    >
      <div style={{ maxWidth: 680 }}>
        {slide.eyebrow && (
          <p
            className="pbc-animate-up"
            style={{
              fontFamily: "'Space Mono',monospace",
              fontSize: 11,
              letterSpacing: "0.2em",
              color: p.accent,
              marginBottom: 20,
              textTransform: "uppercase",
            }}
          >
            {slide.eyebrow}
          </p>
        )}
        <h1 className="pbc-heading pbc-animate-up-2" style={{ fontSize: "clamp(28px, 4vw, 52px)", color: p.fg, marginBottom: 28 }}>
          {slide.title}
        </h1>
        <p className="pbc-animate-up-3" style={{ fontSize: 16, lineHeight: 1.85, color: p.fg2 }}>
          {slide.body}
        </p>
      </div>
    </div>
  );
}

function TextStatSlide({ slide, p, animKey }: SlideBaseProps): JSX.Element {
  return (
    <div
      key={animKey}
      style={{ flex: 1, display: "flex", alignItems: "flex-end", padding: "40px 60px 50px", position: "relative", zIndex: 1, gap: 40 }}
    >
      <div style={{ flex: 1, maxWidth: 520 }}>
        {slide.eyebrow && (
          <p
            style={{
              fontFamily: "'Space Mono',monospace",
              fontSize: 11,
              letterSpacing: "0.2em",
              color: p.accent,
              marginBottom: 20,
              textTransform: "uppercase",
            }}
          >
            {slide.eyebrow}
          </p>
        )}
        <h1 className="pbc-heading pbc-animate-up" style={{ fontSize: "clamp(28px, 3.5vw, 46px)", color: p.fg, marginBottom: 24 }}>
          {slide.title}
        </h1>
        <p style={{ fontSize: 15, lineHeight: 1.8, color: p.fg2 }}>{slide.body}</p>
      </div>

      {slide.stat && (
        <div
          className="pbc-animate-up-2"
          style={{
            position: "absolute",
            right: "4%",
            bottom: "0%",
            fontFamily: "'Syne',sans-serif",
            fontWeight: 800,
            fontSize: "clamp(100px, 22vw, 260px)",
            color: p.accent,
            lineHeight: 0.85,
            letterSpacing: "-0.04em",
            userSelect: "none",
          }}
        >
          {slide.stat}
        </div>
      )}
    </div>
  );
}

function CardsSlide({ slide, p, animKey }: SlideBaseProps): JSX.Element {
  return (
    <div key={animKey} style={{ flex: 1, overflow: "auto", padding: "32px 60px 40px", position: "relative", zIndex: 1 }}>
      {slide.eyebrow && (
        <p style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, letterSpacing: "0.2em", color: p.accent, marginBottom: 16, textTransform: "uppercase" }}>
          {slide.eyebrow}
        </p>
      )}
      <h1 className="pbc-heading" style={{ fontSize: "clamp(24px, 3.5vw, 44px)", color: p.fg, marginBottom: 32 }}>
        {slide.title}
      </h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16, maxWidth: 960 }}>
        {slide.cards?.map((card, i) => (
          <div
            key={i}
            className="pbc-card"
            style={{
              background: p.cardBg,
              border: `2px solid ${i % 2 === 0 ? p.accent2 : p.fg}`,
              padding: "24px 20px",
            }}
          >
            {card.icon && <span style={{ fontSize: 26, display: "block", marginBottom: 12 }}>{card.icon}</span>}
            <h3 style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 16, color: p.fg, marginBottom: 10, textTransform: "uppercase" }}>
              {card.heading}
            </h3>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: p.fg2 }}>{card.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChecklistSlide({ slide, p, animKey }: SlideBaseProps): JSX.Element {
  const [checked, setChecked] = useState<Set<number>>(
    new Set((slide.items ?? []).map((item, i) => (item.checked ? i : -1)).filter((i) => i >= 0))
  );

  const toggle = (i: number): void => {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  return (
    <div key={animKey} style={{ flex: 1, overflow: "auto", padding: "32px 60px 40px", position: "relative", zIndex: 1 }}>
      {slide.eyebrow && (
        <p style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, letterSpacing: "0.2em", color: p.accent, marginBottom: 16, textTransform: "uppercase" }}>
          {slide.eyebrow}
        </p>
      )}
      <h1 className="pbc-heading" style={{ fontSize: "clamp(24px, 3.5vw, 44px)", color: p.fg, marginBottom: 32 }}>
        {slide.title}
      </h1>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, maxWidth: 620, display: "flex", flexDirection: "column", gap: 14 }}>
        {slide.items?.map((item, i) => {
          const isChecked = checked.has(i);
          return (
            <li
              key={i}
              className="pbc-checklist-item"
              onClick={() => toggle(i)}
              style={{ display: "flex", alignItems: "flex-start", gap: 16 }}
            >
              <div
                className="pbc-check-box"
                style={{
                  width: 28,
                  height: 28,
                  flexShrink: 0,
                  marginTop: 2,
                  border: `2px solid ${isChecked ? p.accent : p.border}`,
                  background: isChecked ? p.accent : "transparent",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s",
                }}
              >
                {isChecked && (
                  <svg width="14" height="11" viewBox="0 0 14 11" fill="none">
                    <path
                      d="M1 5L5.5 9.5L13 1"
                      stroke={p.accent === "#E8FF00" ? "#111" : "#fff"}
                      strokeWidth="2.5"
                      strokeLinecap="square"
                    />
                  </svg>
                )}
              </div>
              <p
                style={{
                  fontSize: 15,
                  lineHeight: 1.7,
                  color: isChecked ? p.fg2 : p.fg,
                  textDecoration: isChecked ? "line-through" : "none",
                  transition: "all 0.2s",
                }}
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

interface QuizSlideProps extends SlideBaseProps {
  onComplete: () => void;
}

function QuizSlide({ slide, p, animKey, onComplete }: QuizSlideProps): JSX.Element {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState<boolean>(false);

  const handleSubmit = (): void => {
    if (selected === null) return;
    setSubmitted(true);
    if (selected === slide.correctAnswer) setTimeout(onComplete, 900);
  };

  return (
    <div key={animKey} style={{ flex: 1, overflow: "auto", padding: "32px 60px 40px", position: "relative", zIndex: 1 }}>
      <p style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, letterSpacing: "0.2em", color: p.accent, marginBottom: 16, textTransform: "uppercase" }}>
        Knowledge Check
      </p>
      <h1 className="pbc-heading" style={{ fontSize: "clamp(22px, 3vw, 38px)", color: p.fg, marginBottom: 10 }}>
        {slide.title}
      </h1>
      {slide.quizQuestion && (
        <p style={{ fontSize: 15, color: p.fg2, marginBottom: 28 }}>{slide.quizQuestion}</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 580 }}>
        {slide.quizOptions?.map((opt, i) => {
          const isSelected = selected === i;
          const isCorrect = i === slide.correctAnswer;
          const borderColor = submitted
            ? isCorrect ? p.accent : isSelected ? "#ff3b3b" : p.border
            : isSelected ? p.accent : p.border;
          const bg = submitted
            ? isCorrect ? p.accent + "22" : isSelected ? "#ff3b3b22" : "transparent"
            : isSelected ? p.accent + "18" : "transparent";

          return (
            <button
              key={i}
              className="pbc-btn"
              onClick={() => !submitted && setSelected(i)}
              disabled={submitted}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: "14px 18px",
                textAlign: "left",
                border: `2px solid ${borderColor}`,
                background: bg,
                color: p.fg,
                opacity: submitted && !isCorrect && !isSelected ? 0.4 : 1,
              }}
            >
              <span
                style={{
                  width: 30,
                  height: 30,
                  flexShrink: 0,
                  border: `2px solid ${borderColor}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 12,
                  fontWeight: 700,
                  background:
                    submitted && isCorrect
                      ? p.accent
                      : submitted && isSelected && !isCorrect
                      ? "#ff3b3b"
                      : "transparent",
                  color:
                    submitted && (isCorrect || (isSelected && !isCorrect))
                      ? p.accent === "#E8FF00" ? "#111" : "#fff"
                      : p.fg,
                }}
              >
                {submitted && isCorrect
                  ? "✓"
                  : submitted && isSelected && !isCorrect
                  ? "✗"
                  : String.fromCharCode(65 + i)}
              </span>
              <span style={{ fontSize: 14, lineHeight: 1.5 }}>{opt}</span>
            </button>
          );
        })}
      </div>

      {!submitted && (
        <button
          className="pbc-btn"
          onClick={handleSubmit}
          disabled={selected === null}
          style={{
            marginTop: 24,
            padding: "12px 32px",
            fontSize: 12,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            background: selected !== null ? p.accent : "rgba(255,255,255,0.08)",
            color: selected !== null ? (p.accent === "#E8FF00" ? "#111" : "#fff") : p.fg2,
            border: "none",
          }}
        >
          Submit Answer
        </button>
      )}

      {submitted && (
        <p style={{ marginTop: 16, fontSize: 13, color: selected === slide.correctAnswer ? p.accent : "#ff6b6b", fontWeight: 700, letterSpacing: "0.05em" }}>
          {selected === slide.correctAnswer
            ? "▶ CORRECT — advancing to next slide..."
            : "✗ Incorrect — correct answer is highlighted above"}
        </p>
      )}
    </div>
  );
}

// ─── DEFAULT COURSE DATA ──────────────────────────────────────────────────────

const DEFAULT_COURSE: CourseData = {
  courseTitle: "Pixel Brutalist Course",
  slides: [
    {
      type: "title",
      title: "The Art Of Creative Thinking",
      subtitle: "A bold journey through ideation, clarity, and execution. Press begin when you're ready.",
      buttonLabel: "Begin →",
      label: "Module 01 — Introduction",
    },
    {
      type: "text-only",
      eyebrow: "The Foundation",
      title: "Why Creativity Needs Structure",
      body: "Raw creativity without a framework is just noise. The most innovative minds of our century didn't work in chaos—they built systems that channeled their intuition into repeatable, scalable outcomes. In this module, we explore the scaffolding behind brilliant ideas.",
    },
    {
      type: "text-stat",
      eyebrow: "Market Context",
      title: "The Creative Intelligence Revolution",
      body: "The global creative economy is undergoing a seismic shift. AI tools, collaborative platforms, and new methodologies are compressing the ideation cycle from weeks into hours—rewarding those who can think fast and execute with precision.",
      stat: "25%",
    },
    {
      type: "cards",
      eyebrow: "Core Pillars",
      title: "Three Principles Of Creative Clarity",
      cards: [
        { icon: "⚡", heading: "Ideation Velocity",  description: "Generate ideas faster by removing cognitive friction. Quantity first, quality through iteration." },
        { icon: "🎯", heading: "Focused Execution",  description: "Narrow the field ruthlessly. One strong idea executed brilliantly beats ten scattered ones." },
        { icon: "🔁", heading: "Adaptive Rhythm",    description: "Build feedback loops that improve your output with every cycle. Learn, adjust, repeat." },
        { icon: "🧠", heading: "Mental Models",      description: "Borrow frameworks from design, science, and strategy to reframe any creative challenge." },
      ],
    },
    {
      type: "checklist",
      eyebrow: "Your Creative Toolkit",
      title: "Before You Start Any Project",
      items: [
        { text: "Define the core problem in a single sentence — no jargon." },
        { text: "Identify your audience and what they already believe." },
        { text: "Set a non-negotiable deadline for the first rough draft." },
        { text: "Gather 5 reference works that excite you.", checked: true },
        { text: "Write down what failure looks like so you can avoid it." },
      ],
    },
    {
      type: "quiz",
      title: "Test Your Understanding",
      quizQuestion: "According to this module, what is the primary purpose of structure in the creative process?",
      quizOptions: [
        "To slow down the ideation phase and filter weak ideas early.",
        "To channel intuition into repeatable, scalable outcomes.",
        "To replace human creativity with algorithmic decision-making.",
        "To standardize outputs so they match market expectations.",
      ],
      correctAnswer: 1,
    },
  ],
};

// ─── Main component props ─────────────────────────────────────────────────────

export interface PixelBrutalistCourseProps {
  courseData?: CourseData;
  style?: CSSProperties;
  className?: string;
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function PixelBrutalistCourse({
  courseData = DEFAULT_COURSE,
  style = {},
  className = "",
}: PixelBrutalistCourseProps): JSX.Element | null {
  const slides = courseData.slides ?? [];
  const [idx, setIdx] = useState<number>(0);
  const [quizPassed, setQuizPassed] = useState<boolean>(false);
  const [animKey, setAnimKey] = useState<number>(0);
  const stylesInjected = useRef<boolean>(false);

  useEffect(() => {
    if (stylesInjected.current) return;
    stylesInjected.current = true;
    const el = document.createElement("style");
    el.textContent = FONT_STYLE;
    document.head.appendChild(el);
  }, []);

  if (!slides.length) return null;

  const slide = slides[idx];
  const paletteName: PaletteName = slide.palette ?? TYPE_PALETTE[slide.type] ?? "dark";
  const p: PaletteConfig = PALETTE[paletteName];

  const isFirst = idx === 0;
  const isLast  = idx === slides.length - 1;
  const canNext = slide.type !== "quiz" || quizPassed;

  const navigate = (dir: number): void => {
    const next = idx + dir;
    if (next < 0 || next >= slides.length) return;
    setIdx(next);
    setQuizPassed(false);
    setAnimKey((k) => k + 1);
  };

  const renderSlide = (): JSX.Element | null => {
    const shared: SlideBaseProps = { slide, p, animKey };
    switch (slide.type) {
      case "title":     return <TitleSlide     {...shared} onNext={() => navigate(1)} />;
      case "text-only": return <TextOnlySlide  {...shared} />;
      case "text-stat": return <TextStatSlide  {...shared} />;
      case "cards":     return <CardsSlide     {...shared} />;
      case "checklist": return <ChecklistSlide {...shared} />;
      case "quiz":      return <QuizSlide      {...shared} onComplete={() => setQuizPassed(true)} />;
      default:          return null;
    }
  };

  return (
    <div
      className={`pbc-root ${className}`}
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        background: p.bg,
        color: p.fg,
        overflow: "hidden",
        transition: "background 0.4s, color 0.3s",
        ...style,
      }}
    >
      <PixelScatter palette={p.pixelPalette} />

      {/* Top nav bar */}
      <div
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          background: p.navBg,
          backdropFilter: "blur(8px)",
          borderBottom: `1px solid ${p.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 14, height: 14, background: p.accent }} />
          <span style={{ fontFamily: "'Space Mono',monospace", fontWeight: 700, fontSize: 12, letterSpacing: "0.15em", textTransform: "uppercase", color: p.fg }}>
            {courseData.courseTitle}
          </span>
        </div>
        <span style={{ fontFamily: "'Space Mono',monospace", fontSize: 11, color: p.fg2, letterSpacing: "0.1em" }}>
          {String(idx + 1).padStart(2, "0")} / {String(slides.length).padStart(2, "0")}
        </span>
      </div>

      {/* Progress */}
      <div style={{ position: "relative", zIndex: 10 }}>
        <ProgressBar total={slides.length} current={idx} accent={p.accent} />
      </div>

      {/* Slide content */}
      <div style={{ position: "relative", zIndex: 2, flex: 1, display: "flex", flexDirection: "column", minHeight: 0, overflow: "hidden" }}>
        {renderSlide()}
      </div>

      {/* Bottom nav */}
      <div
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          background: p.navBg,
          backdropFilter: "blur(8px)",
          borderTop: `1px solid ${p.border}`,
        }}
      >
        <div
          style={{
            padding: "6px 14px",
            border: `1px solid ${p.border}`,
            fontFamily: "'Space Mono',monospace",
            fontSize: 10,
            letterSpacing: "0.15em",
            textTransform: "uppercase",
            color: p.fg2,
          }}
        >
          {slide.type ?? "—"}
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button
            className="pbc-btn"
            onClick={() => navigate(-1)}
            disabled={isFirst}
            style={{
              width: 44,
              height: 44,
              border: `2px solid ${isFirst ? p.border : p.fg}`,
              background: "transparent",
              color: isFirst ? p.fg2 : p.fg,
              fontSize: 18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: isFirst ? "not-allowed" : "pointer",
            }}
          >
            ←
          </button>
          <button
            className="pbc-btn"
            onClick={() => navigate(1)}
            disabled={isLast || !canNext}
            style={{
              width: 44,
              height: 44,
              border: "none",
              background: !isLast && canNext ? p.accent : p.border,
              color: !isLast && canNext ? (p.accent === "#E8FF00" ? "#111" : "#fff") : p.fg2,
              fontSize: 18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: isLast || !canNext ? "not-allowed" : "pointer",
            }}
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}

