/**
 * ClassName Helper Utilities
 * 
 * Utility functions for building conditional classNames and style combinations.
 */

/**
 * Responsive class builder
 * Creates responsive utility classes based on breakpoints
 */
export const responsive = {
  sm: (className: string) => `sm:${className}`,
  md: (className: string) => `md:${className}`,
  lg: (className: string) => `lg:${className}`,
  xl: (className: string) => `xl:${className}`,
  "2xl": (className: string) => `2xl:${className}`,
}

/**
 * State-based class builder
 * Creates state-based utility classes (hover, focus, active, disabled)
 */
export const states = {
  hover: (className: string) => `hover:${className}`,
  focus: (className: string) => `focus:${className}`,
  active: (className: string) => `active:${className}`,
  disabled: (className: string) => `disabled:${className}`,
  "group-hover": (className: string) => `group-hover:${className}`,
  dark: (className: string) => `dark:${className}`,
}

/**
 * Layout utility builders
 */
export const layout = {
  flex: (direction: "row" | "col" = "row", items = "center", justify = "start") =>
    `flex flex-${direction} items-${items} justify-${justify}`,
  
  grid: (cols: number, gap = "4") =>
    `grid grid-cols-${cols} gap-${gap}`,
  
  container: (maxWidth = "6xl", centered = true) =>
    `${centered ? "mx-auto" : ""} max-w-${maxWidth}`,
  
  section: (py = "12", px = "4") =>
    `py-${py} px-${px}`,
}

/**
 * Spacing utility builders
 */
export const spacing = {
  padding: (p: string | number) => `p-${p}`,
  paddingX: (px: string | number) => `px-${px}`,
  paddingY: (py: string | number) => `py-${py}`,
  margin: (m: string | number) => `m-${m}`,
  marginX: (mx: string | number) => `mx-${mx}`,
  marginY: (my: string | number) => `my-${my}`,
  gap: (g: string | number) => `gap-${g}`,
}

/**
 * Text utility builders
 */
export const text = {
  size: (size: "xs" | "sm" | "base" | "lg" | "xl" | "2xl") => `text-${size}`,
  weight: (weight: "light" | "normal" | "medium" | "semibold" | "bold") =>
    `font-${weight}`,
  align: (align: "left" | "center" | "right") => `text-${align}`,
  color: (color: string) => `text-${color}`,
  lineHeight: (height: "tight" | "snug" | "normal" | "relaxed" | "loose") =>
    `leading-${height}`,
}

/**
 * Color utility builders
 */
export const colors = {
  background: (color: string) => `bg-${color}`,
  text: (color: string) => `text-${color}`,
  border: (color: string) => `border-${color}`,
}

/**
 * Border utility builders
 */
export const borders = {
  radius: (size: "sm" | "md" | "lg" | "xl" | "2xl" | "full") => `rounded-${size}`,
  width: (width: "0" | "1" | "2" | "4" | "8") => `border-${width}`,
  color: (color: string) => `border-${color}`,
  sides: {
    top: (color: string) => `border-t border-${color}`,
    bottom: (color: string) => `border-b border-${color}`,
    left: (color: string) => `border-l border-${color}`,
    right: (color: string) => `border-r border-${color}`,
  },
}

/**
 * Shadow utility builders
 */
export const shadows = {
  shadow: (size: "sm" | "md" | "lg" | "xl" | "2xl") => `shadow-${size}`,
  hover: "hover:shadow-lg",
  none: "shadow-none",
}

/**
 * Visibility utility builders
 */
export const visibility = {
  hidden: "hidden",
  visible: "visible",
  sr: "sr-only", // Screen reader only
  flex: "flex",
  block: "block",
  inline: "inline",
}
