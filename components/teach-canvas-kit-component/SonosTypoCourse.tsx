// @ts-nocheck
/**
 * SonosTypoCourse — Embeddable Course Slide Template
 *
 * Aesthetic: Pure typographic minimalism — Sonos-style.
 * Massive type as the visual hero, rotated vertical wordmark,
 * rich flat single-colour backgrounds, zero decoration.
 *
 * USAGE (embed in any React project):
 *   import SonosTypoCourse from './SonosTypoCourse';
 *   <SonosTypoCourse courseData={myCourseData} />
 *
 * Slide types:
 *   "cover"     — huge title left, vertical brand right, metadata top-right
 *   "statement" — oversized text bleeding off screen, two text columns bottom
 *   "contents"  — giant word top, ruled list, footer counter
 *   "overview"  — left vertical brand, large heading, body paragraphs
 *   "columns"   — heading top-left, 2–3 column text blocks below
 *   "divider"   — centred title only, near-black bg, gold text (section break)
 *   "highlights"— centred stacked large lines, right vertical label
 *   "quiz"      — dark bg, question + options, gated navigation
 *   "checklist" — heading + interactive check rows
 */

import { useState, useEffect, useRef, CSSProperties } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

export type SlideType =
  | "cover"
  | "statement"
  | "contents"
  | "overview"
  | "columns"
  | "cards"
  | "divider"
  | "highlights"
  | "checklist"
  | "quiz";

export type PaletteName =
  | "navy"
  | "maroon"
  | "powder"
  | "olive"
  | "peach"
  | "midnight"
  | "lilac"
  | "charcoal";

export interface ColumnItem {
  heading: string;
  body: string;
  description?: string;
}

export interface GenericCardItem {
  heading?: string;
  title?: string;
  description?: string;
  body?: string;
  text?: string;
}

export interface ChecklistItem {
  text: string;
  checked?: boolean;
}

export interface Slide {
  type: SlideType;
  palette?: PaletteName;
  title?: string;
  subtitle?: string;
  // cover
  buttonLabel?: string | false;
  // statement
  bigWord?: string;
  leftText?: string;
  rightLabel?: string;
  rightText?: string;
  // contents / highlights
  items?: string[] | ChecklistItem[];
  lines?: string[];
  // overview
  paragraphs?: string[];
  body?: string;
  // columns
  columns?: ColumnItem[];
  cards?: GenericCardItem[];
  // highlights
  rightLabel?: string;
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
  accent: string;
  footerFg: string;
}

const MAX_HIGHLIGHT_LINES = 5;
const MAX_HIGHLIGHT_LINE_CHARS = 56;
const MAX_HIGHLIGHTS_TOTAL_CHARS = 240;
const MAX_COLUMNS = 4;
const MAX_COLUMN_BODY_CHARS = 190;
const MAX_CONTENT_ITEMS = 7;

function cleanText(value: unknown): string {
  if (typeof value !== "string") return "";
  return value
    .replace(/[*_`#>~]/g, " ")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function truncateText(value: string, maxChars: number): string {
  const text = cleanText(value);
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars - 1).trimEnd()}…`;
}

function normalizeLinesFromAny(slide: Slide): string[] {
  const linesFromSource = [
    ...(slide.lines ?? []),
    ...(((slide.items ?? []) as string[]) || []),
    slide.leftText ?? "",
    slide.rightText ?? "",
    slide.body ?? "",
  ]
    .flatMap((raw) => cleanText(raw).split(/\n|(?<=[.!?])\s+/))
    .map((line) => line.trim())
    .filter(Boolean);

  return linesFromSource;
}

function asColumnItemsFromLines(lines: string[]): ColumnItem[] {
  return lines.slice(0, MAX_COLUMNS).map((line, i) => {
    const words = line.split(" ").filter(Boolean);
    const heading = words.slice(0, 4).join(" ") || `Point ${i + 1}`;
    return {
      heading: truncateText(heading, 36),
      body: truncateText(line, MAX_COLUMN_BODY_CHARS),
    };
  });
}

function normalizeSlideForLayout(slide: Slide): Slide {
  const next: Slide = {
    ...slide,
    title: cleanText(slide.title),
    subtitle: cleanText(slide.subtitle),
    body: cleanText(slide.body),
    bigWord: truncateText(slide.bigWord ?? "", 26),
    leftText: truncateText(slide.leftText ?? "", 260),
    rightLabel: truncateText(slide.rightLabel ?? "", 38),
    rightText: truncateText(slide.rightText ?? "", 260),
    lines: (slide.lines ?? []).map((line) => cleanText(line)).filter(Boolean),
    paragraphs: (slide.paragraphs ?? []).map((p) => cleanText(p)).filter(Boolean),
    items: (slide.items ?? []).map((it: any) => (
      typeof it === "string"
        ? truncateText(it, 88)
        : { ...it, text: truncateText((it && it.text) || "", 88) }
    )),
    columns: (slide.columns ?? [])
      .map((col) => ({
        heading: truncateText(col?.heading ?? "", 42),
        body: truncateText(col?.body ?? col?.description ?? "", MAX_COLUMN_BODY_CHARS),
      }))
      .filter((c) => c.heading || c.body)
      .slice(0, MAX_COLUMNS),
    cards: (slide.cards ?? [])
      .map((card) => ({
        ...card,
        heading: truncateText(card?.heading ?? card?.title ?? "", 42),
        title: truncateText(card?.title ?? card?.heading ?? "", 42),
        description: truncateText(card?.description ?? card?.body ?? card?.text ?? "", MAX_COLUMN_BODY_CHARS),
        body: truncateText(card?.body ?? card?.description ?? card?.text ?? "", MAX_COLUMN_BODY_CHARS),
        text: truncateText(card?.text ?? card?.body ?? card?.description ?? "", MAX_COLUMN_BODY_CHARS),
      }))
      .filter((c) => c.heading || c.title || c.description || c.body || c.text)
      .slice(0, MAX_COLUMNS),
    quizQuestion: cleanText(slide.quizQuestion),
    quizOptions: (slide.quizOptions ?? []).map((opt) => truncateText(opt, 84)).slice(0, 6),
  };

  if (next.type === "contents") {
    const contentItems = ((next.items ?? []) as string[])
      .map((item) => truncateText(String(item), 70))
      .slice(0, MAX_CONTENT_ITEMS);
    return { ...next, items: contentItems };
  }

  if (next.type === "highlights") {
    const candidateLines = normalizeLinesFromAny(next);
    const cleanedLines = candidateLines.map((line) => truncateText(line, MAX_HIGHLIGHT_LINE_CHARS));
    const totalChars = cleanedLines.reduce((sum, line) => sum + line.length, 0);
    const tooDense =
      cleanedLines.length > MAX_HIGHLIGHT_LINES || totalChars > MAX_HIGHLIGHTS_TOTAL_CHARS;

    if (!cleanedLines.length) {
      return {
        ...next,
        type: "overview",
        title: next.title || "Overview",
        paragraphs: [next.body || "Content unavailable for this slide."],
      };
    }

    if (tooDense) {
      return {
        ...next,
        type: "columns",
        title: next.title || "Key Ideas",
        columns: asColumnItemsFromLines(candidateLines),
      };
    }

    return {
      ...next,
      lines: cleanedLines.slice(0, MAX_HIGHLIGHT_LINES),
    };
  }

  return next;
}

function normalizeCourseSlides(slides: Slide[]): Slide[] {
  return (slides ?? []).map(normalizeSlideForLayout);
}

// ─── Palette definitions ──────────────────────────────────────────────────────

const PALETTES: Record<PaletteName, PaletteConfig> = {
  navy:     { bg: "#1b2f52", fg: "#a8bdd8", accent: "#a8bdd8", footerFg: "#7a98bc" },
  maroon:   { bg: "#5a2035", fg: "#ff6b1a", accent: "#ff6b1a", footerFg: "#c45a30" },
  powder:   { bg: "#b8cfe0", fg: "#1b2f52", accent: "#1b2f52", footerFg: "#2e4a70" },
  olive:    { bg: "#4a5a28", fg: "#c8e040", accent: "#c8e040", footerFg: "#90a040" },
  peach:    { bg: "#f4b896", fg: "#1b2f52", accent: "#1b2f52", footerFg: "#2e4a70" },
  midnight: { bg: "#171717", fg: "#c8a46e", accent: "#c8a46e", footerFg: "#806040" },
  lilac:    { bg: "#d4c0f8", fg: "#7040d0", accent: "#7040d0", footerFg: "#8050e0" },
  charcoal: { bg: "#232323", fg: "#e8e8e8", accent: "#c8a46e", footerFg: "#888888" },
};

const TYPE_PALETTE: Record<SlideType, PaletteName> = {
  cover:      "navy",
  statement:  "maroon",
  contents:   "powder",
  overview:   "olive",
  columns:    "peach",
  cards:      "peach",
  divider:    "midnight",
  highlights: "lilac",
  checklist:  "navy",
  quiz:       "charcoal",
};

// ─── Font injection ───────────────────────────────────────────────────────────

const FONT_CSS = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&display=swap');

.stc-root * { box-sizing: border-box; margin: 0; padding: 0; }
.stc-root { font-family: 'DM Sans', sans-serif; user-select: none; }

@keyframes stc-fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes stc-slideRight {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.stc-animate   { animation: stc-fadeIn 0.5s ease-out both; }
.stc-animate-2 { animation: stc-fadeIn 0.5s 0.1s ease-out both; }
.stc-animate-3 { animation: stc-fadeIn 0.5s 0.2s ease-out both; }
.stc-animate-r { animation: stc-slideRight 0.5s 0.15s ease-out both; }

.stc-nav-btn { cursor: pointer; border: none; outline: none; font-family: 'DM Sans', sans-serif; transition: opacity 0.15s; }
.stc-nav-btn:hover:not(:disabled) { opacity: 0.7; }
.stc-nav-btn:disabled { opacity: 0.2; cursor: not-allowed; }

.stc-opt-btn { cursor: pointer; border: none; outline: none; font-family: 'DM Sans', sans-serif; text-align: left; width: 100%; transition: opacity 0.2s, background 0.2s; }
.stc-opt-btn:hover:not(:disabled) { opacity: 0.8; }

.stc-cl-row { cursor: pointer; }
.stc-cl-row:hover .stc-cl-box { opacity: 0.7; }

.stc-submit-btn { cursor: pointer; border: none; outline: none; font-family: 'DM Sans', sans-serif; transition: opacity 0.15s; }
.stc-submit-btn:hover:not(:disabled) { opacity: 0.8; }
.stc-submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }
`;

// ─── Shared sub-components ───────────────────────────────────────────────────

interface VerticalBrandProps {
  text: string;
  color: string;
  side?: "left" | "right";
  style?: CSSProperties;
}

function VerticalBrand({ text, color, side = "left", style: extraStyle = {} }: VerticalBrandProps): JSX.Element {
  return (
    <div
      style={{
        position: "absolute",
        [side]: 0,
        top: 0,
        bottom: 0,
        width: 36,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        ...extraStyle,
      }}
    >
      <span
        style={{
          writingMode: "vertical-rl",
          transform: side === "left" ? "rotate(180deg)" : "none",
          fontSize: 11,
          fontWeight: 500,
          letterSpacing: "0.22em",
          textTransform: "uppercase",
          color,
          opacity: 0.9,
        }}
      >
        {text}
      </span>
    </div>
  );
}

interface FooterProps {
  docName: string;
  subtitle?: string;
  slideNum: number;
  totalSlides: number;
  fg: string;
}

function Footer({ docName, subtitle, slideNum, totalSlides, fg }: FooterProps): JSX.Element {
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        padding: "0 44px 18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        zIndex: 5,
      }}
    >
      <div style={{ lineHeight: 1.4 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: fg, opacity: 0.75 }}>{docName}</div>
        {subtitle && <div style={{ fontSize: 10, color: fg, opacity: 0.45 }}>{subtitle}</div>}
      </div>
      {totalSlides > 1 && (
        <div style={{ fontSize: 11, color: fg, opacity: 0.5, fontWeight: 500, letterSpacing: "0.05em" }}>
          {String(slideNum).padStart(2, "0")}
        </div>
      )}
    </div>
  );
}

interface ProgressBarProps {
  total: number;
  current: number;
  accent: string;
}

function ProgressBar({ total, current, accent }: ProgressBarProps): JSX.Element {
  return (
    <div style={{ display: "flex", gap: 2, position: "absolute", top: 0, left: 0, right: 0, zIndex: 10 }}>
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: 3,
            background: i <= current ? accent : "rgba(255,255,255,0.15)",
            transition: "background 0.4s",
          }}
        />
      ))}
    </div>
  );
}

// ─── Slide component shared prop shape ───────────────────────────────────────

interface SlideSharedProps {
  slide: Slide;
  p: PaletteConfig;
  course: CourseData;
  slideNum: number;
  totalSlides: number;
}

// ─── SLIDE: Cover ─────────────────────────────────────────────────────────────

interface CoverSlideProps extends SlideSharedProps {
  onNext: () => void;
}

function CoverSlide({ slide, p, course, slideNum, totalSlides, onNext }: CoverSlideProps): JSX.Element {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* Top-right metadata */}
      <div style={{ position: "absolute", top: 28, right: 64, textAlign: "right", zIndex: 2 }}>
        <div style={{ fontSize: 11, color: p.fg, opacity: 0.6, lineHeight: 1.6 }}>{course.courseTitle}</div>
        <div style={{ fontSize: 11, color: p.fg, opacity: 0.6 }}>{course.subtitle ?? ""}</div>
      </div>

      <VerticalBrand text={course.courseTitle} color={p.fg} side="right" style={{ right: 0, width: 44 }} />

      <div
        className="stc-animate"
        style={{ position: "absolute", left: 52, top: "50%", transform: "translateY(-50%)", right: 60 }}
      >
        <h1
          style={{
            fontSize: "clamp(52px, 8vw, 112px)",
            fontWeight: 700,
            lineHeight: 1.02,
            color: p.fg,
            letterSpacing: "-0.02em",
          }}
        >
          {slide.title}
        </h1>
        {slide.subtitle && (
          <p className="stc-animate-2" style={{ marginTop: 32, fontSize: 16, color: p.fg, opacity: 0.6, maxWidth: 480, lineHeight: 1.6 }}>
            {slide.subtitle}
          </p>
        )}
        {slide.buttonLabel !== false && (
          <button
            className="stc-nav-btn stc-animate-3"
            onClick={onNext}
            style={{
              marginTop: 44,
              padding: "13px 36px",
              background: p.fg,
              color: p.bg,
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: "0.04em",
            }}
          >
            {slide.buttonLabel ?? "Begin →"}
          </button>
        )}
      </div>

      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Statement ─────────────────────────────────────────────────────────

function StatementSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      {/* Vertical brand top-centre */}
      <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", zIndex: 2, padding: "14px 0" }}>
        <span style={{ writingMode: "vertical-rl", fontSize: 11, fontWeight: 500, letterSpacing: "0.22em", textTransform: "uppercase", color: p.accent, opacity: 0.85 }}>
          {course.courseTitle}
        </span>
      </div>

      {/* Huge bleed word */}
      <div className="stc-animate" style={{ position: "absolute", left: -8, top: "50%", transform: "translateY(-62%)", whiteSpace: "nowrap", zIndex: 1 }}>
        <span style={{ fontSize: "clamp(90px, 18vw, 200px)", fontWeight: 700, color: p.accent, letterSpacing: "-0.04em", lineHeight: 1 }}>
          {slide.bigWord ?? slide.title}
        </span>
      </div>

      {/* Two columns bottom */}
      <div className="stc-animate-2" style={{ position: "absolute", bottom: 52, left: 52, right: 52, display: "flex", gap: 60, zIndex: 2 }}>
        {slide.leftText && (
          <div style={{ flex: 1, maxWidth: 340 }}>
            <p style={{ fontSize: 15, lineHeight: 1.65, color: p.fg, opacity: 0.85 }}>{slide.leftText}</p>
          </div>
        )}
        {slide.rightText && (
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: p.fg, opacity: 0.65 }}>
              {slide.rightLabel && <strong style={{ opacity: 1 }}>{slide.rightLabel} </strong>}
              {slide.rightText}
            </p>
          </div>
        )}
      </div>

      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Contents ──────────────────────────────────────────────────────────

const ROMAN_NUMERALS = ["I.", "II.", "III.", "IV.", "V.", "VI.", "VII."] as const;

function ContentsSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  const items = (slide.items ?? []) as string[];
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      <div className="stc-animate" style={{ position: "absolute", top: -12, left: -8, right: 0, overflow: "hidden", zIndex: 1 }}>
        <span style={{ fontSize: "clamp(80px, 15vw, 160px)", fontWeight: 700, color: p.fg, letterSpacing: "-0.04em", lineHeight: 0.9, display: "block" }}>
          {slide.title ?? "Contents"}
        </span>
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: "clamp(100px, 22%, 180px)", height: 1, background: p.fg, opacity: 0.25, zIndex: 2 }} />

      <div className="stc-animate-2" style={{ position: "absolute", top: "clamp(110px, 24%, 192px)", left: 52, right: 52, zIndex: 2 }}>
        {items.map((item, i) => (
          <div
            key={i}
            style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "14px 0", borderBottom: `1px solid ${p.fg}`, opacity: 0.37 + 0.1 }}
          >
            <span style={{ fontSize: 16, color: p.fg, opacity: 0.65, fontWeight: 400 }}>
              {ROMAN_NUMERALS[i] ?? `${i + 1}.`}
            </span>
            <span style={{ fontSize: 16, color: p.fg, fontWeight: 400, textAlign: "right" }}>{item}</span>
          </div>
        ))}
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, bottom: 48, height: 1, background: p.fg, opacity: 0.2, zIndex: 2 }} />
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Overview ──────────────────────────────────────────────────────────

function OverviewSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  const paragraphs = slide.paragraphs ?? (slide.body ? [slide.body] : []);
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.accent} side="left" />
      <div className="stc-animate" style={{ position: "absolute", left: 80, right: 52, top: "10%", bottom: 60 }}>
        <h2 style={{ fontSize: "clamp(36px, 6vw, 80px)", fontWeight: 700, color: p.accent, letterSpacing: "-0.02em", lineHeight: 1.05, marginBottom: 36 }}>
          {slide.title}
        </h2>
        {paragraphs.map((para, i) => (
          <p
            key={i}
            className={i === 0 ? "stc-animate-2" : "stc-animate-3"}
            style={{ fontSize: 15, lineHeight: 1.75, color: p.accent, opacity: i === 0 ? 0.9 : 0.75, marginBottom: 20, maxWidth: 680 }}
          >
            {para}
          </p>
        ))}
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.accent} />
    </div>
  );
}

// ─── SLIDE: Columns ───────────────────────────────────────────────────────────

function ColumnsSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  const fallbackFromCards: ColumnItem[] = (slide.cards ?? [])
    .map((card) => ({
      heading: String(card?.heading ?? card?.title ?? "").trim(),
      body: String(card?.description ?? card?.body ?? card?.text ?? "").trim(),
    }))
    .filter((c) => c.heading || c.body);

  const cols: ColumnItem[] = (slide.columns ?? [])
    .map((col) => ({
      heading: String(col?.heading ?? "").trim(),
      body: String(col?.body ?? col?.description ?? "").trim(),
    }))
    .filter((c) => c.heading || c.body);

  const finalCols = cols.length > 0 ? cols : fallbackFromCards;
  const gridCount = Math.max(1, Math.min(finalCols.length || 1, MAX_COLUMNS));

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.fg} side="left" style={{ opacity: 0.5 }} />
      <div style={{ position: "absolute", left: 80, right: 52, top: "8%", bottom: 60 }}>
        <h2 className="stc-animate" style={{ fontSize: "clamp(36px, 6vw, 80px)", fontWeight: 700, color: p.fg, letterSpacing: "-0.02em", lineHeight: 1.05, marginBottom: 44 }}>
          {slide.title}
        </h2>
        <div
          className="stc-animate-2"
          style={{ display: "grid", gridTemplateColumns: `repeat(${gridCount}, 1fr)`, gap: 32 }}
        >
          {finalCols.map((col, i) => (
            <div key={i}>
              <h3 style={{ fontSize: 17, fontWeight: 700, color: p.fg, marginBottom: 14, lineHeight: 1.3 }}>
                {col.heading || `Point ${i + 1}`}
              </h3>
              <p style={{ fontSize: 14, lineHeight: 1.75, color: p.fg, opacity: 0.85 }}>
                {col.body || "Details coming soon."}
              </p>
            </div>
          ))}
        </div>
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Divider ───────────────────────────────────────────────────────────

function DividerSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.accent} side="left" />
      <div className="stc-animate" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <h2 style={{ fontSize: "clamp(40px, 7vw, 96px)", fontWeight: 500, color: p.accent, letterSpacing: "-0.01em", textAlign: "center" }}>
          {slide.title}
        </h2>
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.footerFg} />
    </div>
  );
}

// ─── SLIDE: Highlights ────────────────────────────────────────────────────────

function HighlightsSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  const lines: string[] = slide.lines ?? [];
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.fg} side="left" style={{ opacity: 0.7 }} />
      {slide.rightLabel && (
        <VerticalBrand text={slide.rightLabel} color={p.fg} side="right" style={{ opacity: 0.7 }} />
      )}
      <div
        className="stc-animate"
        style={{ position: "absolute", inset: "0 60px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4 }}
      >
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              fontSize: "clamp(28px, 5vw, 68px)",
              fontWeight: 700,
              color: p.fg,
              letterSpacing: "-0.02em",
              lineHeight: 1.15,
              textAlign: "center",
              animation: `stc-fadeIn 0.5s ${i * 0.08}s ease-out both`,
            }}
          >
            {line}
          </div>
        ))}
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Checklist ─────────────────────────────────────────────────────────

function ChecklistSlide({ slide, p, course, slideNum, totalSlides }: SlideSharedProps): JSX.Element {
  const checklistItems = (slide.items ?? []) as ChecklistItem[];

  const [checked, setChecked] = useState<Set<number>>(
    new Set(checklistItems.map((it, i) => (it.checked ? i : -1)).filter((i) => i >= 0))
  );

  const toggle = (i: number): void => {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.fg} side="left" style={{ opacity: 0.6 }} />
      <div style={{ position: "absolute", left: 80, right: 52, top: "8%", bottom: 60, overflow: "auto" }}>
        <h2 className="stc-animate" style={{ fontSize: "clamp(30px, 5vw, 64px)", fontWeight: 700, color: p.fg, letterSpacing: "-0.02em", marginBottom: 36 }}>
          {slide.title}
        </h2>
        <ul className="stc-animate-2" style={{ listStyle: "none" }}>
          {checklistItems.map((item, i) => {
            const isCk = checked.has(i);
            return (
              <li
                key={i}
                className="stc-cl-row"
                onClick={() => toggle(i)}
                style={{ display: "flex", alignItems: "flex-start", gap: 18, padding: "13px 0", borderBottom: `1px solid ${p.fg}`, opacity: isCk ? 0.35 : 1, transition: "opacity 0.25s", cursor: "pointer" }}
              >
                <div
                  className="stc-cl-box"
                  style={{
                    width: 22,
                    height: 22,
                    flexShrink: 0,
                    marginTop: 1,
                    border: `2px solid ${p.fg}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: isCk ? p.fg : "transparent",
                    transition: "all 0.2s",
                  }}
                >
                  {isCk && (
                    <svg width="12" height="9" viewBox="0 0 12 9" fill="none">
                      <path d="M1 4L4.5 7.5L11 1" stroke={p.bg} strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  )}
                </div>
                <span style={{ fontSize: 15, color: p.fg, lineHeight: 1.55, textDecoration: isCk ? "line-through" : "none" }}>
                  {item.text}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.fg} />
    </div>
  );
}

// ─── SLIDE: Quiz ──────────────────────────────────────────────────────────────

interface QuizSlideProps extends SlideSharedProps {
  onComplete: () => void;
}

function QuizSlide({ slide, p, course, slideNum, totalSlides, onComplete }: QuizSlideProps): JSX.Element {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState<boolean>(false);

  const submit = (): void => {
    if (selected === null) return;
    setSubmitted(true);
    if (selected === slide.correctAnswer) setTimeout(onComplete, 800);
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <VerticalBrand text={course.courseTitle} color={p.accent} side="left" style={{ opacity: 0.5 }} />
      <div style={{ position: "absolute", left: 80, right: 52, top: "8%", bottom: 60, overflow: "auto" }}>
        <p className="stc-animate" style={{ fontSize: 11, letterSpacing: "0.18em", textTransform: "uppercase", color: p.accent, opacity: 0.7, marginBottom: 16 }}>
          Knowledge Check
        </p>
        <h2 className="stc-animate" style={{ fontSize: "clamp(24px, 3.5vw, 46px)", fontWeight: 700, color: p.accent, letterSpacing: "-0.02em", marginBottom: 14 }}>
          {slide.title}
        </h2>
        {slide.quizQuestion && (
          <p className="stc-animate-2" style={{ fontSize: 15, color: p.fg, opacity: 0.6, marginBottom: 32, maxWidth: 580, lineHeight: 1.6 }}>
            {slide.quizQuestion}
          </p>
        )}

        <div className="stc-animate-2" style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 560 }}>
          {(slide.quizOptions ?? []).map((opt, i) => {
            const isSel = selected === i;
            const isCorrect = i === slide.correctAnswer;
            const bg = submitted
              ? isCorrect ? p.accent : isSel ? "#cc3333" : "transparent"
              : isSel ? `${p.accent}22` : "transparent";
            const borderColor = submitted
              ? isCorrect ? p.accent : isSel ? "#cc3333" : `${p.fg}30`
              : isSel ? p.accent : `${p.fg}30`;

            return (
              <button
                key={i}
                className="stc-opt-btn"
                onClick={() => !submitted && setSelected(i)}
                disabled={submitted}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "12px 16px",
                  background: bg,
                  border: `1px solid ${borderColor}`,
                  color: p.fg,
                  fontSize: 14,
                  opacity: submitted && !isCorrect && !isSel ? 0.3 : 1,
                  transition: "all 0.2s",
                }}
              >
                <span
                  style={{
                    width: 26,
                    height: 26,
                    flexShrink: 0,
                    border: `1px solid ${borderColor}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 11,
                    fontWeight: 700,
                    background: submitted && isCorrect ? p.accent : submitted && isSel && !isCorrect ? "#cc3333" : "transparent",
                    color: submitted && (isCorrect || (isSel && !isCorrect)) ? p.bg : p.fg,
                  }}
                >
                  {submitted && isCorrect ? "✓" : submitted && isSel && !isCorrect ? "✗" : String.fromCharCode(65 + i)}
                </span>
                <span style={{ lineHeight: 1.4 }}>{opt}</span>
              </button>
            );
          })}
        </div>

        {!submitted && (
          <button
            className="stc-submit-btn"
            onClick={submit}
            disabled={selected === null}
            style={{
              marginTop: 24,
              padding: "11px 32px",
              fontSize: 13,
              fontWeight: 700,
              letterSpacing: "0.06em",
              background: selected !== null ? p.accent : `${p.fg}18`,
              color: selected !== null ? p.bg : p.fg,
            }}
          >
            Submit
          </button>
        )}

        {submitted && (
          <p style={{ marginTop: 18, fontSize: 13, fontWeight: 700, color: selected === slide.correctAnswer ? p.accent : "#cc6666", letterSpacing: "0.04em" }}>
            {selected === slide.correctAnswer ? "Correct — advancing to next slide." : "Not quite. The correct answer is highlighted above."}
          </p>
        )}
      </div>
      <Footer docName={course.courseTitle} subtitle={course.subtitle} slideNum={slideNum} totalSlides={totalSlides} fg={p.footerFg} />
    </div>
  );
}

// ─── DEFAULT COURSE DATA ──────────────────────────────────────────────────────

const DEFAULT_COURSE: CourseData = {
  courseTitle: "Foundations",
  subtitle: "2025 Confidential",
  slides: [
    { type: "cover",      title: "This Is Your Learning Journey", subtitle: "A course built for clarity, depth, and lasting retention.", buttonLabel: "Begin Course →" },
    { type: "statement",  bigWord: "Document", leftText: "Purpose of this module will be clear from the first slide. Designed to engage.", rightLabel: "Definition:", rightText: "Some form of optional text that describes the problem you will be solving in this course." },
    { type: "contents",   title: "Contents", items: ["The Foundation", "Core Concepts", "Deep Dive", "Practical Application", "Assessment"] },
    { type: "overview",   title: "Overview", paragraphs: ["The purpose of this course is to build a rigorous understanding of the fundamentals.", "Learning is most effective when it follows a rhythm — concept, example, reflection, practice."] },
    { type: "columns",    title: "Core Concepts", columns: [
        { heading: "First Principle",  body: "Understanding the root cause of a problem is more valuable than memorising a hundred surface-level solutions." },
        { heading: "Second Principle", body: "Deliberate practice with feedback loops accelerates skill acquisition faster than passive exposure." },
        { heading: "Third Principle",  body: "Reflection and articulation consolidate learning — if you can explain it simply, you truly understand it." },
    ]},
    { type: "divider",    title: "Application" },
    { type: "highlights", rightLabel: "Index", lines: ["Clear Thinking", "Deep Focus", "Rapid Iteration", "Lasting Results"] },
    { type: "checklist",  title: "Before You Continue", items: [
        { text: "Review your notes from the previous section." },
        { text: "Write one sentence summarising the core idea." },
        { text: "Identify one area where you'd like more clarity.", checked: true },
        { text: "Set a realistic target before the next session." },
    ]},
    { type: "quiz",       title: "Test Your Understanding", quizQuestion: "Which best describes the role of deliberate practice?", quizOptions: [
        "Passive re-reading until it feels familiar.",
        "Practising with structured feedback to accelerate skill acquisition.",
        "Watching experts without attempting tasks yourself.",
        "Focusing solely on theory before any hands-on practice.",
    ], correctAnswer: 1 },
  ],
};

// ─── Main component props ─────────────────────────────────────────────────────

export interface SonosTypoCourseProps {
  courseData?: CourseData;
  style?: CSSProperties;
  className?: string;
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function SonosTypoCourse({
  courseData = DEFAULT_COURSE,
  style = {},
  className = "",
}: SonosTypoCourseProps): JSX.Element | null {
  const normalizedCourse: CourseData = {
    ...courseData,
    slides: normalizeCourseSlides(courseData.slides ?? []),
  };
  const slides = normalizedCourse.slides ?? [];
  const [idx, setIdx] = useState<number>(0);
  const [quizPassed, setQuizPassed] = useState<boolean>(false);
  const [animKey, setAnimKey] = useState<number>(0);
  const stylesInjected = useRef<boolean>(false);

  useEffect(() => {
    if (stylesInjected.current) return;
    stylesInjected.current = true;
    const el = document.createElement("style");
    el.textContent = FONT_CSS;
    document.head.appendChild(el);
  }, []);

  useEffect(() => {
    if (!slides.length) return;
    if (idx >= slides.length) setIdx(slides.length - 1);
  }, [slides.length, idx]);

  if (!slides.length) return null;

  const slide = slides[idx];
  const palName: PaletteName = slide.palette ?? TYPE_PALETTE[slide.type] ?? "navy";
  const p: PaletteConfig = PALETTES[palName];

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

  const sharedProps: SlideSharedProps = {
    slide,
    p,
    course: normalizedCourse,
    slideNum: idx + 1,
    totalSlides: slides.length,
  };

  const renderSlide = (): JSX.Element | null => {
    switch (slide.type) {
      case "cover":      return <CoverSlide      key={animKey} {...sharedProps} onNext={() => navigate(1)} />;
      case "statement":  return <StatementSlide  key={animKey} {...sharedProps} />;
      case "contents":   return <ContentsSlide   key={animKey} {...sharedProps} />;
      case "overview":   return <OverviewSlide   key={animKey} {...sharedProps} />;
      case "columns":    return <ColumnsSlide    key={animKey} {...sharedProps} />;
      case "cards":      return <ColumnsSlide    key={animKey} {...sharedProps} />;
      case "divider":    return <DividerSlide    key={animKey} {...sharedProps} />;
      case "highlights": return <HighlightsSlide key={animKey} {...sharedProps} />;
      case "checklist":  return <ChecklistSlide  key={animKey} {...sharedProps} />;
      case "quiz":       return <QuizSlide       key={animKey} {...sharedProps} onComplete={() => setQuizPassed(true)} />;
      default:           return null;
    }
  };

  return (
    <div
      className={`stc-root ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: 0,
        background: p.bg,
        overflow: "hidden",
        transition: "background 0.45s",
        ...style,
      }}
    >
      <ProgressBar total={slides.length} current={idx} accent={p.accent} />

      <div style={{ position: "absolute", inset: 0, paddingTop: 3 }}>
        {renderSlide()}
      </div>

      {/* Navigation */}
      <div style={{ position: "absolute", top: 18, right: 52, display: "flex", gap: 6, zIndex: 20 }}>
        <button
          className="stc-nav-btn"
          onClick={() => navigate(-1)}
          disabled={isFirst}
          style={{
            width: 36, height: 36,
            background: "transparent",
            border: `1px solid ${p.fg}`,
            color: p.fg,
            fontSize: 16,
            display: "flex", alignItems: "center", justifyContent: "center",
            opacity: isFirst ? 0.15 : 0.55,
          }}
        >
          ←
        </button>
        <button
          className="stc-nav-btn"
          onClick={() => navigate(1)}
          disabled={isLast || !canNext}
          style={{
            width: 36, height: 36,
            background: !isLast && canNext ? p.fg : "transparent",
            border: `1px solid ${p.fg}`,
            color: !isLast && canNext ? p.bg : p.fg,
            fontSize: 16,
            display: "flex", alignItems: "center", justifyContent: "center",
            opacity: isLast || !canNext ? 0.15 : 1,
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}

