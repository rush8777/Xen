/**
 * Layout Pattern Components
 * 
 * Reusable layout templates and structural components.
 */

import React from "react"
import { cn } from "@/lib/utils"

// Container wrapper
interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg" | "xl" | "full"
  centered?: boolean
}

export const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ size = "lg", centered = true, className, ...props }, ref) => {
    const sizeMap = {
      sm: "max-w-2xl",
      md: "max-w-4xl",
      lg: "max-w-6xl",
      xl: "max-w-7xl",
      full: "w-full",
    }

    return (
      <div
        ref={ref}
        className={cn(
          sizeMap[size],
          centered && "mx-auto",
          "px-4 sm:px-6 lg:px-8",
          className
        )}
        {...props}
      />
    )
  }
)
Container.displayName = "Container"

// Section wrapper with standardized spacing
interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  variant?: "default" | "alt" | "inverse"
  spacing?: "sm" | "md" | "lg" | "xl"
}

export const Section = React.forwardRef<HTMLElement, SectionProps>(
  ({ variant = "default", spacing = "lg", className, children, ...props }, ref) => {
    const spacingMap = {
      sm: "py-8 sm:py-12",
      md: "py-12 sm:py-16",
      lg: "py-16 sm:py-20",
      xl: "py-20 sm:py-24 lg:py-32",
    }

    const variantMap = {
      default: "bg-background",
      alt: "bg-secondary/50",
      inverse: "bg-primary text-primary-foreground",
    }

    return (
      <section
        ref={ref}
        className={cn(variantMap[variant], spacingMap[spacing], className)}
        {...props}
      >
        <Container>{children}</Container>
      </section>
    )
  }
)
Section.displayName = "Section"

// Grid layout
interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: number | { sm?: number; md?: number; lg?: number; xl?: number }
  gap?: "sm" | "md" | "lg" | "xl"
}

export const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ cols = 3, gap = "md", className, ...props }, ref) => {
    const gapMap = {
      sm: "gap-4",
      md: "gap-6",
      lg: "gap-8",
      xl: "gap-12",
    }

    let gridClasses = "grid"
    if (typeof cols === "number") {
      gridClasses += ` grid-cols-1 sm:grid-cols-${cols}`
    } else {
      gridClasses += ` grid-cols-1${cols.sm ? ` sm:grid-cols-${cols.sm}` : ""}${cols.md ? ` md:grid-cols-${cols.md}` : ""}${cols.lg ? ` lg:grid-cols-${cols.lg}` : ""}${cols.xl ? ` xl:grid-cols-${cols.xl}` : ""}`
    }

    return (
      <div ref={ref} className={cn(gridClasses, gapMap[gap], className)} {...props} />
    )
  }
)
Grid.displayName = "Grid"

// Stack (flex column)
interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: "vertical" | "horizontal"
  align?: "start" | "center" | "end" | "stretch"
  justify?: "start" | "center" | "end" | "between" | "around"
  gap?: "xs" | "sm" | "md" | "lg" | "xl"
}

export const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  (
    {
      direction = "vertical",
      align = "start",
      justify = "start",
      gap = "md",
      className,
      ...props
    },
    ref
  ) => {
    const directionMap = {
      vertical: "flex-col",
      horizontal: "flex-row",
    }

    const alignMap = {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    }

    const justifyMap = {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
    }

    const gapMap = {
      xs: "gap-2",
      sm: "gap-3",
      md: "gap-4",
      lg: "gap-6",
      xl: "gap-8",
    }

    return (
      <div
        ref={ref}
        className={cn(
          "flex",
          directionMap[direction],
          alignMap[align],
          justifyMap[justify],
          gapMap[gap],
          className
        )}
        {...props}
      />
    )
  }
)
Stack.displayName = "Stack"

// Flex spacer
export const Spacer = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex-1", className)} {...props} />
  )
)
Spacer.displayName = "Spacer"

// Center content wrapper
interface CenterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const Center = React.forwardRef<HTMLDivElement, CenterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center justify-center", className)}
      {...props}
    />
  )
)
Center.displayName = "Center"
