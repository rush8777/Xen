/**
 * Component Helper Utilities
 * 
 * Reusable component patterns and builders.
 */

// Button size variants
export const buttonSizes = {
  xs: "px-2 py-1 text-xs",
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-6 py-3 text-lg",
  xl: "px-8 py-4 text-xl",
}

// Button variant builders
export const buttonVariants = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/90",
  outline: "border border-input bg-background hover:bg-accent",
  ghost: "hover:bg-accent hover:text-accent-foreground",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  link: "text-primary underline-offset-4 hover:underline",
}

// Card style builders
export const cardStyles = {
  base: "rounded-lg border border-input bg-card text-card-foreground",
  hover: "hover:shadow-md transition-shadow",
  interactive: "cursor-pointer hover:shadow-md transition-all",
}

// Input style builders
export const inputStyles = {
  base: "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
  error: "border-destructive focus-visible:ring-destructive",
  success: "border-emerald-500 focus-visible:ring-emerald-500",
}

// Badge style builders
export const badgeVariants = {
  default: "inline-flex items-center rounded-md bg-secondary px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground",
  primary: "bg-primary text-primary-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "border border-input bg-background text-foreground",
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
}

// Avatar style builders
export const avatarStyles = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-12 w-12",
  xl: "h-16 w-16",
}

// Tooltip position variants
export const tooltipPositions = {
  top: "bottom-full mb-2",
  bottom: "top-full mt-2",
  left: "right-full mr-2",
  right: "left-full ml-2",
}

// Loading state builders
export const loadingStates = {
  opacity: "opacity-50 pointer-events-none",
  cursor: "cursor-wait",
  disabled: "disabled:opacity-50 disabled:cursor-not-allowed",
}

// Focus states for accessibility
export const focusStates = {
  outline: "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
  ring: "focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring",
  shadow: "focus-visible:shadow-md",
}

// Transition utilities
export const transitions = {
  fast: "transition-all duration-150",
  normal: "transition-all duration-300",
  slow: "transition-all duration-500",
}

// Animation utilities
export const animations = {
  fadeIn: "animate-in fade-in",
  fadeOut: "animate-out fade-out",
  slideIn: "animate-in slide-in",
  scaleIn: "animate-in zoom-in",
}
