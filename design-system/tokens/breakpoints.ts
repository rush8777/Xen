/**
 * Breakpoint Token Definitions
 * 
 * Responsive design breakpoints for consistent responsive behavior.
 */

export const breakpoints = {
  xs: "0px",
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const

// Breakpoint aliases for convenience
export const breakpointNames = {
  mobile: "xs",
  tablet: "md",
  desktop: "lg",
  wide: "xl",
  ultraWide: "2xl",
} as const

// Media query helpers
export const mediaQueries = {
  sm: "@media (min-width: 640px)",
  md: "@media (min-width: 768px)",
  lg: "@media (min-width: 1024px)",
  xl: "@media (min-width: 1280px)",
  "2xl": "@media (min-width: 1536px)",
  
  smDown: "@media (max-width: 639px)",
  mdDown: "@media (max-width: 767px)",
  lgDown: "@media (max-width: 1023px)",
  xlDown: "@media (max-width: 1279px)",
  "2xlDown": "@media (max-width: 1535px)",
}
