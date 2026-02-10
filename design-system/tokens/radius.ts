/**
 * Border Radius Token Definitions
 * 
 * Border radius values for creating consistent rounded corners.
 */

export const radiusTokens = {
  // Base radius values (in rem)
  none: "0",
  xs: "0.125rem",    // 2px
  sm: "0.25rem",     // 4px
  md: "0.5rem",      // 8px
  lg: "0.75rem",     // 12px
  xl: "1rem",        // 16px
  "2xl": "1.5rem",   // 24px
  "3xl": "2rem",     // 32px
  full: "9999px",    // Full (circular)
}

// Component-specific radius presets
export const radiusPresets = {
  // Buttons
  button: {
    sm: radiusTokens.sm,
    md: radiusTokens.md,
    lg: radiusTokens.lg,
    full: radiusTokens.full,
  },

  // Cards
  card: {
    sm: radiusTokens.lg,
    md: radiusTokens.xl,
    lg: radiusTokens["2xl"],
  },

  // Input fields
  input: {
    default: radiusTokens.md,
    large: radiusTokens.lg,
  },

  // Modals & Dialogs
  modal: {
    default: radiusTokens.xl,
    large: radiusTokens["2xl"],
  },

  // Badges & Pills
  badge: {
    default: radiusTokens.md,
    pill: radiusTokens.full,
  },

  // Avatars
  avatar: {
    sm: radiusTokens.md,
    md: radiusTokens.lg,
    lg: radiusTokens.xl,
    full: radiusTokens.full,
  },

  // Images
  image: {
    sm: radiusTokens.md,
    md: radiusTokens.lg,
    lg: radiusTokens.xl,
  },
}
