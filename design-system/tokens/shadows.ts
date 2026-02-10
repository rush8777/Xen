/**
 * Shadow Token Definitions
 * 
 * Box shadow presets for depth and elevation hierarchy.
 */

export const shadowTokens = {
  // Elevation shadows
  none: "none",
  xs: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  sm: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
  "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
  inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",

  // Component specific shadows
  card: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  button: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  dropdown: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  modal: "0 25px 50px -12px rgb(0 0 0 / 0.25)",
  input: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",

  // Interactive states
  hover: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  active: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
  focus: "0 0 0 3px rgb(59 130 246 / 0.1)",
}

// Dark mode shadows
export const darkShadowTokens = {
  xs: "0 1px 2px 0 rgb(0 0 0 / 0.3)",
  sm: "0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.3)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.3), 0 8px 10px -6px rgb(0 0 0 / 0.3)",
  "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.5)",
  inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.3)",
}
