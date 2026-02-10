/**
 * Typography Token Definitions
 * 
 * Font sizes, weights, line heights, and letter spacing for consistent typography.
 */

export const typographyTokens = {
  // Font sizes (in rem)
  fontSize: {
    xs: "0.75rem",     // 12px
    sm: "0.875rem",    // 14px
    base: "1rem",      // 16px
    lg: "1.125rem",    // 18px
    xl: "1.25rem",     // 20px
    "2xl": "1.5rem",   // 24px
    "3xl": "1.875rem", // 30px
    "4xl": "2.25rem",  // 36px
    "5xl": "3rem",     // 48px
    "6xl": "3.75rem",  // 60px
    "7xl": "4.5rem",   // 72px
  },

  // Font weights
  fontWeight: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },

  // Line heights
  lineHeight: {
    none: "1",
    tight: "1.25",
    snug: "1.375",
    normal: "1.5",
    relaxed: "1.625",
    loose: "2",
  },

  // Letter spacing
  letterSpacing: {
    tighter: "-0.05em",
    tight: "-0.025em",
    normal: "0em",
    wide: "0.025em",
    wider: "0.05em",
    widest: "0.1em",
  },
}

// Heading styles
export const headingStyles = {
  h1: {
    fontSize: typographyTokens.fontSize["5xl"],
    fontWeight: typographyTokens.fontWeight.bold,
    lineHeight: typographyTokens.lineHeight.tight,
    letterSpacing: typographyTokens.letterSpacing.tight,
  },
  h2: {
    fontSize: typographyTokens.fontSize["4xl"],
    fontWeight: typographyTokens.fontWeight.bold,
    lineHeight: typographyTokens.lineHeight.tight,
    letterSpacing: typographyTokens.letterSpacing.tight,
  },
  h3: {
    fontSize: typographyTokens.fontSize["3xl"],
    fontWeight: typographyTokens.fontWeight.semibold,
    lineHeight: typographyTokens.lineHeight.snug,
    letterSpacing: typographyTokens.letterSpacing.tight,
  },
  h4: {
    fontSize: typographyTokens.fontSize["2xl"],
    fontWeight: typographyTokens.fontWeight.semibold,
    lineHeight: typographyTokens.lineHeight.snug,
    letterSpacing: typographyTokens.letterSpacing.normal,
  },
  h5: {
    fontSize: typographyTokens.fontSize.xl,
    fontWeight: typographyTokens.fontWeight.semibold,
    lineHeight: typographyTokens.lineHeight.normal,
    letterSpacing: typographyTokens.letterSpacing.normal,
  },
  h6: {
    fontSize: typographyTokens.fontSize.lg,
    fontWeight: typographyTokens.fontWeight.semibold,
    lineHeight: typographyTokens.lineHeight.normal,
    letterSpacing: typographyTokens.letterSpacing.normal,
  },
}

// Body text styles
export const textStyles = {
  body: {
    large: {
      fontSize: typographyTokens.fontSize.lg,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.relaxed,
      letterSpacing: typographyTokens.letterSpacing.normal,
    },
    default: {
      fontSize: typographyTokens.fontSize.base,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.relaxed,
      letterSpacing: typographyTokens.letterSpacing.normal,
    },
    small: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
      letterSpacing: typographyTokens.letterSpacing.normal,
    },
  },

  // UI text styles
  ui: {
    label: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.tight,
      letterSpacing: typographyTokens.letterSpacing.normal,
    },
    caption: {
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.tight,
      letterSpacing: typographyTokens.letterSpacing.wide,
    },
    code: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
      letterSpacing: typographyTokens.letterSpacing.normal,
    },
  },
}
