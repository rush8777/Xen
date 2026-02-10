/**
 * Spacing Token Definitions
 * 
 * Consistent spacing scale for padding, margins, and gaps.
 * Based on 4px base unit.
 */

export const spacingTokens = {
  // Base spacing units (in rem)
  0: "0",
  1: "0.25rem",      // 4px
  2: "0.5rem",       // 8px
  3: "0.75rem",      // 12px
  4: "1rem",         // 16px
  5: "1.25rem",      // 20px
  6: "1.5rem",       // 24px
  7: "1.75rem",      // 28px
  8: "2rem",         // 32px
  10: "2.5rem",      // 40px
  12: "3rem",        // 48px
  14: "3.5rem",      // 56px
  16: "4rem",        // 64px
  20: "5rem",        // 80px
  24: "6rem",        // 96px
  28: "7rem",        // 112px
  32: "8rem",        // 128px
  36: "9rem",        // 144px
  40: "10rem",       // 160px
  44: "11rem",       // 176px
  48: "12rem",       // 192px
  52: "13rem",       // 208px
  56: "14rem",       // 224px
  60: "15rem",       // 240px
  64: "16rem",       // 256px
  72: "18rem",       // 288px
  80: "20rem",       // 320px
  96: "24rem",       // 384px
} as const

// Common spacing combinations
export const spacingPresets = {
  // Padding presets
  padding: {
    xs: spacingTokens[2],
    sm: spacingTokens[3],
    md: spacingTokens[4],
    lg: spacingTokens[6],
    xl: spacingTokens[8],
    "2xl": spacingTokens[12],
  },
  
  // Margin presets
  margin: {
    xs: spacingTokens[2],
    sm: spacingTokens[3],
    md: spacingTokens[4],
    lg: spacingTokens[6],
    xl: spacingTokens[8],
    "2xl": spacingTokens[12],
  },

  // Gap presets (for flex/grid)
  gap: {
    xs: spacingTokens[2],
    sm: spacingTokens[3],
    md: spacingTokens[4],
    lg: spacingTokens[6],
    xl: spacingTokens[8],
    "2xl": spacingTokens[12],
  },

  // Common section spacing
  section: {
    vertical: spacingTokens[12],
    horizontal: spacingTokens[8],
  },

  // Component spacing
  component: {
    padding: spacingTokens[4],
    gap: spacingTokens[3],
  },
}
