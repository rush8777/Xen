/**
 * Color Token Definitions
 * 
 * Primary color palette and semantic color tokens for the design system.
 * Uses HSL format for easy manipulation and dark mode support.
 */

export const colorTokens = {
  // Primary Brand Colors
  primary: {
    50: "0 0% 98%",
    100: "0 0% 96%",
    200: "0 0% 89%",
    300: "0 0% 82%",
    400: "0 0% 64%",
    500: "0 0% 45%",
    600: "0 0% 32%",
    700: "0 0% 20%",
    800: "0 0% 13%",
    900: "0 0% 9%",
  },

  // Secondary Colors
  secondary: {
    50: "210 100% 97%",
    100: "210 100% 94%",
    200: "210 97% 88%",
    300: "210 98% 78%",
    400: "210 98% 66%",
    500: "210 98% 52%",
    600: "210 89% 46%",
    700: "210 88% 38%",
    800: "210 84% 32%",
    900: "210 81% 26%",
  },

  // Accent Colors
  accent: {
    50: "280 100% 97%",
    100: "280 100% 94%",
    200: "280 97% 88%",
    300: "280 98% 78%",
    400: "280 98% 66%",
    500: "280 98% 52%",
    600: "280 89% 46%",
    700: "280 88% 38%",
    800: "280 84% 32%",
    900: "280 81% 26%",
  },

  // Semantic Colors
  success: {
    light: "120 73% 75%",
    DEFAULT: "120 73% 60%",
    dark: "120 71% 35%",
  },

  warning: {
    light: "45 100% 70%",
    DEFAULT: "45 100% 50%",
    dark: "45 100% 40%",
  },

  error: {
    light: "0 84% 75%",
    DEFAULT: "0 84% 60%",
    dark: "0 84% 40%",
  },

  info: {
    light: "210 100% 75%",
    DEFAULT: "210 100% 60%",
    dark: "210 100% 40%",
  },

  // Neutral/Gray Scale
  neutral: {
    50: "0 0% 98%",
    100: "0 0% 96%",
    200: "0 0% 89%",
    300: "0 0% 82%",
    400: "0 0% 64%",
    500: "0 0% 45%",
    600: "0 0% 32%",
    700: "0 0% 20%",
    800: "0 0% 13%",
    900: "0 0% 9%",
  },

  // Semantic Tokens (used in tailwind.config.ts)
  background: "0 0% 100%",
  foreground: "0 0% 3.9%",
  card: "0 0% 100%",
  "card-foreground": "0 0% 3.9%",
  border: "0 0% 89.8%",
  input: "0 0% 89.8%",
  ring: "0 0% 3.9%",
}

// Dark mode color tokens
export const darkColorTokens = {
  background: "0 0% 3.9%",
  foreground: "0 0% 98%",
  card: "0 0% 3.9%",
  "card-foreground": "0 0% 98%",
  border: "0 0% 14.9%",
  input: "0 0% 14.9%",
  ring: "0 0% 83.1%",
}

// Color aliases for convenience
export const colors = {
  light: {
    background: colorTokens.background,
    text: colorTokens.foreground,
    border: colorTokens.border,
    muted: "0 0% 96.1%",
  },
  dark: {
    background: darkColorTokens.background,
    text: darkColorTokens.foreground,
    border: darkColorTokens.border,
    muted: "0 0% 14.9%",
  },
}
