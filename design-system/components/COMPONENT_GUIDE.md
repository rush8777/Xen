# Component Design Guide

## Component Structure

All components should follow this structure:

\`\`\`typescript
import React from "react"
import { cn } from "@/lib/utils"

interface ComponentProps extends React.HTMLAttributes<HTMLElement> {
  // Specific props
  variant?: "default" | "alternative"
  size?: "sm" | "md" | "lg"
  disabled?: boolean
}

export const Component = React.forwardRef<HTMLElement, ComponentProps>(
  ({ variant = "default", size = "md", disabled, className, ...props }, ref) => {
    return (
      <element
        ref={ref}
        className={cn(
          // Base styles
          "base-class",
          // Variant styles
          variant === "default" && "default-styles",
          variant === "alternative" && "alternative-styles",
          // Size styles
          size === "sm" && "sm-styles",
          size === "md" && "md-styles",
          size === "lg" && "lg-styles",
          // State styles
          disabled && "disabled-styles",
          // Custom className
          className
        )}
        {...props}
      />
    )
  }
)
Component.displayName = "Component"
\`\`\`

## Naming Conventions

- **Components**: PascalCase (e.g., `ButtonGroup`, `CardSection`)
- **Props**: camelCase (e.g., `isActive`, `onClick`)
- **Tokens**: kebab-case (e.g., `primary-color`, `spacing-md`)
- **Utilities**: camelCase (e.g., `paddingUtility`, `flexLayout`)

## Component Best Practices

### 1. Accessibility
- Always include ARIA labels where appropriate
- Support keyboard navigation
- Ensure proper color contrast
- Test with screen readers

### 2. Responsiveness
- Use Tailwind's responsive prefixes (sm:, md:, lg:)
- Mobile-first approach
- Test on multiple screen sizes

### 3. Reusability
- Keep components focused and single-responsibility
- Accept common props (className, style, ref)
- Use composition for complex UI

### 4. Performance
- Use React.forwardRef for component forwarding
- Memoize when necessary
- Avoid unnecessary re-renders

### 5. Styling
- Use cn() utility for className merging
- Follow design token naming
- Support both light and dark modes
- Use Tailwind utilities consistently

## Component Patterns

### Button Component Example
\`\`\`typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost"
  size?: "sm" | "md" | "lg"
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", isLoading, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={cn(
        "font-medium rounded-md transition-colors",
        variantStyles[variant],
        sizeStyles[size],
        (disabled || isLoading) && "opacity-50 cursor-not-allowed"
      )}
      {...props}
    />
  )
)
\`\`\`

### Card Component Example
\`\`\`typescript
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  interactive?: boolean
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ hover, interactive, className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border border-input bg-card p-6",
        hover && "hover:shadow-md transition-shadow",
        interactive && "cursor-pointer hover:shadow-lg",
        className
      )}
      {...props}
    />
  )
)
\`\`\`

## Testing Components

- Test props variations (variants, sizes, states)
- Test accessibility (keyboard navigation, ARIA attributes)
- Test responsiveness (mobile, tablet, desktop)
- Test dark mode support
- Test disabled/loading states

## Documentation

Each component should have:
- Clear prop descriptions
- Usage examples
- Accessibility notes
- Responsive behavior details
- Dark mode considerations
