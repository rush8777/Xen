# Getting Started with the Design System

## Overview

This design system provides a comprehensive set of tools, components, and patterns to ensure consistency across your application.

## Quick Start

### 1. Import Tokens

Use design tokens in your components for consistency:

\`\`\`typescript
import { colorTokens } from "@/design-system/tokens/colors"
import { spacingTokens } from "@/design-system/tokens/spacing"
import { typographyTokens } from "@/design-system/tokens/typography"
\`\`\`

### 2. Use Layout Components

Wrap your content with layout components:

\`\`\`typescript
import { Container, Section, Grid, Stack } from "@/design-system/layouts/layoutPatterns"

export default function Page() {
  return (
    <Section variant="default" spacing="lg">
      <Container>
        <Grid cols={3} gap="lg">
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Grid>
      </Container>
    </Section>
  )
}
\`\`\`

### 3. Apply Styling Utilities

Use utility helpers for consistent styling:

\`\`\`typescript
import { buttonVariants, cardStyles } from "@/design-system/utilities/componentHelpers"

export function MyButton() {
  return (
    <button className={buttonVariants.primary}>
      Click me
    </button>
  )
}

export function MyCard() {
  return (
    <div className={cardStyles.base + " " + cardStyles.hover}>
      Card content
    </div>
  )
}
\`\`\`

## File Structure

### Tokens (`/design-system/tokens/`)
- **colors.ts** - Color palette and semantic colors
- **spacing.ts** - Spacing scale (padding, margin, gap)
- **typography.ts** - Font sizes, weights, line heights
- **shadows.ts** - Shadow elevations
- **radius.ts** - Border radius values
- **breakpoints.ts** - Responsive breakpoints

### Utilities (`/design-system/utilities/`)
- **classNameHelpers.ts** - Helper functions for building classNames
- **componentHelpers.ts** - Reusable component patterns

### Layouts (`/design-system/layouts/`)
- **layoutPatterns.tsx** - Layout component templates

### Animations (`/design-system/animations/`)
- **keyframes.ts** - Animation definitions and presets

### Theme (`/design-system/theme/`)
- **themeConfig.ts** - Theme configuration and utilities

## Common Use Cases

### Creating a Responsive Grid

\`\`\`typescript
<Grid 
  cols={{ sm: 1, md: 2, lg: 3 }}
  gap="lg"
>
  {items.map(item => (
    <div key={item.id}>{item.name}</div>
  ))}
</Grid>
\`\`\`

### Building a Flexible Layout

\`\`\`typescript
<Stack 
  direction="horizontal"
  align="center"
  justify="between"
  gap="md"
>
  <h1>Title</h1>
  <button>Action</button>
</Stack>
\`\`\`

### Applying Consistent Spacing

\`\`\`typescript
<div className={`p-${spacingTokens[4]} gap-${spacingTokens[3]}`}>
  Content
</div>
\`\`\`

### Using Typography Tokens

\`\`\`typescript
<h1 style={{
  fontSize: headingStyles.h1.fontSize,
  fontWeight: headingStyles.h1.fontWeight,
  lineHeight: headingStyles.h1.lineHeight,
}}>
  Heading
</h1>
\`\`\`

## Best Practices

1. **Always use tokens** - Never hardcode values like colors or spacing
2. **Prefer composition** - Build complex UIs from simple, reusable components
3. **Follow naming conventions** - Use consistent naming across your codebase
4. **Test accessibility** - Ensure all components are accessible
5. **Maintain dark mode** - Test components in both light and dark modes
6. **Document changes** - Update documentation when modifying the system

## Extending the Design System

### Adding New Colors

Edit `/design-system/tokens/colors.ts`:

\`\`\`typescript
export const colorTokens = {
  // ... existing colors
  brand: {
    50: "240 100% 97%",
    // ... additional shades
  },
}
\`\`\`

### Adding New Components

Create new file in `/design-system/components/`:

\`\`\`typescript
export interface MyComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "alternative"
}

export const MyComponent = React.forwardRef<HTMLDivElement, MyComponentProps>(
  ({ variant = "default", className, ...props }, ref) => (
    <div ref={ref} className={cn(baseStyles, variantStyles[variant], className)} {...props} />
  )
)
\`\`\`

## Troubleshooting

### Colors not applying
- Ensure tokens are imported correctly
- Check that Tailwind is configured to use the tokens
- Verify theme mode is set correctly

### Spacing looks inconsistent
- Use token values instead of arbitrary values
- Check responsive breakpoints
- Verify spacing presets are being used

### Components not responsive
- Add responsive classes using Tailwind prefixes (sm:, md:, lg:)
- Test on different screen sizes
- Use Grid and Stack components for responsive layouts

## Additional Resources

- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Component Best Practices](./COMPONENT_GUIDE.md)
- [Token Reference](../tokens/)
- [Layout Patterns](../layouts/)

## Support

For issues or questions about the design system, refer to the documentation files or contact the design team.
