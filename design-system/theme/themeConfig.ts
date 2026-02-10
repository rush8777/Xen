import React from "react"
/**
 * Theme Configuration
 * 
 * Central configuration for theme customization and application.
 */

import { colorTokens, darkColorTokens } from "@/design-system/tokens/colors"
import { typographyTokens } from "@/design-system/tokens/typography"
import { spacingTokens } from "@/design-system/tokens/spacing"
import { radiusTokens } from "@/design-system/tokens/radius"
import { shadowTokens, darkShadowTokens } from "@/design-system/tokens/shadows"

// Theme modes
export type ThemeMode = "light" | "dark" | "system"

// Theme configuration interface
export interface ThemeConfig {
  mode: ThemeMode
  colors: {
    light: Record<string, string>
    dark: Record<string, string>
  }
  typography: typeof typographyTokens
  spacing: typeof spacingTokens
  radius: typeof radiusTokens
  shadows: {
    light: typeof shadowTokens
    dark: typeof darkShadowTokens
  }
  breakpoints: Record<string, string>
}

// Export theme configuration
export const themeConfig: ThemeConfig = {
  mode: "light",
  colors: {
    light: colorTokens,
    dark: darkColorTokens,
  },
  typography: typographyTokens,
  spacing: spacingTokens,
  radius: radiusTokens,
  shadows: {
    light: shadowTokens,
    dark: darkShadowTokens,
  },
  breakpoints: {
    xs: "0px",
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
}

// Theme provider configuration
export interface ThemeProviderProps {
  children: React.ReactNode
  defaultTheme?: ThemeMode
  storageKey?: string
}

// Custom theme override interface
export interface ThemeOverride {
  colors?: Record<string, Record<string, string>>
  typography?: Partial<typeof typographyTokens>
  spacing?: Partial<typeof spacingTokens>
}

/**
 * Merge custom theme with default theme
 */
export function mergeTheme(baseTheme: ThemeConfig, override: ThemeOverride): ThemeConfig {
  return {
    ...baseTheme,
    colors: {
      light: { ...baseTheme.colors.light, ...override.colors?.light },
      dark: { ...baseTheme.colors.dark, ...override.colors?.dark },
    },
    typography: { ...baseTheme.typography, ...override.typography },
    spacing: { ...baseTheme.spacing, ...override.spacing },
  }
}

/**
 * Get CSS variables for theme
 */
export function getThemeCSSVariables(theme: "light" | "dark" = "light"): Record<string, string> {
  const colors = themeConfig.colors[theme]
  const cssVariables: Record<string, string> = {}

  Object.entries(colors).forEach(([key, value]) => {
    cssVariables[`--${key}`] = value
  })

  return cssVariables
}

/**
 * Apply theme to document
 */
export function applyTheme(mode: ThemeMode = "light"): void {
  const htmlElement = document.documentElement

  if (mode === "dark") {
    htmlElement.classList.add("dark")
  } else {
    htmlElement.classList.remove("dark")
  }

  // Apply CSS variables
  const variables = getThemeCSSVariables(mode === "dark" ? "dark" : "light")
  Object.entries(variables).forEach(([key, value]) => {
    htmlElement.style.setProperty(key, value)
  })
}
