/**
 * Animation Keyframes
 * 
 * Reusable animation definitions for consistent motion across the design system.
 */

export const keyframes = {
  // Fade animations
  fadeIn: {
    from: { opacity: "0" },
    to: { opacity: "1" },
  },
  fadeOut: {
    from: { opacity: "1" },
    to: { opacity: "0" },
  },

  // Slide animations
  slideInFromLeft: {
    from: { transform: "translateX(-100%)" },
    to: { transform: "translateX(0)" },
  },
  slideInFromRight: {
    from: { transform: "translateX(100%)" },
    to: { transform: "translateX(0)" },
  },
  slideInFromTop: {
    from: { transform: "translateY(-100%)" },
    to: { transform: "translateY(0)" },
  },
  slideInFromBottom: {
    from: { transform: "translateY(100%)" },
    to: { transform: "translateY(0)" },
  },
  slideOutToLeft: {
    from: { transform: "translateX(0)" },
    to: { transform: "translateX(-100%)" },
  },
  slideOutToRight: {
    from: { transform: "translateX(0)" },
    to: { transform: "translateX(100%)" },
  },

  // Scale animations
  scaleIn: {
    from: { transform: "scale(0.95)", opacity: "0" },
    to: { transform: "scale(1)", opacity: "1" },
  },
  scaleOut: {
    from: { transform: "scale(1)", opacity: "1" },
    to: { transform: "scale(0.95)", opacity: "0" },
  },

  // Bounce animations
  bounce: {
    "0%, 100%": { transform: "translateY(0)" },
    "50%": { transform: "translateY(-10px)" },
  },
  bounceIn: {
    "0%": { opacity: "0", transform: "scale(0.3)" },
    "50%": { opacity: "1", transform: "scale(1.05)" },
    "70%": { transform: "scale(0.9)" },
    "100%": { transform: "scale(1)" },
  },

  // Pulse animations
  pulse: {
    "0%, 100%": { opacity: "1" },
    "50%": { opacity: "0.5" },
  },
  shimmer: {
    "0%": { backgroundPosition: "-1000px 0" },
    "100%": { backgroundPosition: "1000px 0" },
  },

  // Rotate animations
  spin: {
    from: { transform: "rotate(0deg)" },
    to: { transform: "rotate(360deg)" },
  },

  // Custom animations
  wiggle: {
    "0%, 100%": { transform: "rotate(0deg)" },
    "25%": { transform: "rotate(-1deg)" },
    "75%": { transform: "rotate(1deg)" },
  },
  shake: {
    "0%, 100%": { transform: "translateX(0)" },
    "10%, 30%, 50%, 70%, 90%": { transform: "translateX(-5px)" },
    "20%, 40%, 60%, 80%": { transform: "translateX(5px)" },
  },
  heartbeat: {
    "0%, 100%": { transform: "scale(1)" },
    "25%": { transform: "scale(1.3)" },
    "50%": { transform: "scale(1.1)" },
  },
}

// Animation durations (in milliseconds)
export const animationDurations = {
  fast: "150ms",
  base: "300ms",
  slow: "500ms",
  slower: "700ms",
  slowest: "1000ms",
}

// Animation timing functions
export const timingFunctions = {
  linear: "linear",
  easeIn: "cubic-bezier(0.4, 0, 1, 1)",
  easeOut: "cubic-bezier(0, 0, 0.2, 1)",
  easeInOut: "cubic-bezier(0.4, 0, 0.2, 1)",
  easeInQuad: "cubic-bezier(0.11, 0, 0.5, 0)",
  easeOutQuad: "cubic-bezier(0.5, 1, 0.89, 1)",
}

// Preset animations
export const animations = {
  fadeIn: `fadeIn 300ms ease-out`,
  fadeOut: `fadeOut 300ms ease-out`,
  slideIn: `slideInFromLeft 300ms ease-out`,
  scaleIn: `scaleIn 300ms ease-out`,
  bounceIn: `bounceIn 600ms ease-out`,
  pulse: `pulse 2000ms ease-in-out infinite`,
  spin: `spin 1000ms linear infinite`,
  wiggle: `wiggle 300ms ease-in-out`,
}
