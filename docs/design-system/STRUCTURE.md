# Design System File Structure

## Directory Organization

\`\`\`
design-system/
├── README.md                          # Design system overview and principles
├── STRUCTURE.md                       # This file - complete structure guide
│
├── tokens/                            # Design tokens (values, not components)
│   ├── index.ts                       # Central export for all tokens
│   ├── colors.ts                      # Color palette and semantic tokens
│   ├── spacing.ts                     # Spacing scale (rem-based)
│   ├── typography.ts                  # Font sizes, weights, line heights
│   ├── shadows.ts                     # Box shadow presets
│   ├── radius.ts                      # Border radius values
│   └── breakpoints.ts                 # Responsive breakpoints
│
├── utilities/                         # Helper functions and utilities
│   ├── index.ts                       # Central export for utilities
│   ├── classNameHelpers.ts            # ClassName building utilities
│   └── componentHelpers.ts            # Component pattern builders
│
├── layouts/                           # Layout components and patterns
│   └── layoutPatterns.tsx             # Container, Grid, Stack, Center, etc.
│
├── animations/                        # Animation definitions
│   └── keyframes.ts                   # Keyframes, durations, timing functions
│
├── theme/                             # Theme configuration
│   └── themeConfig.ts                 # Theme setup and customization
│
├── components/                        # Component guidelines
│   └── COMPONENT_GUIDE.md             # Best practices for component creation
│
└── documentation/                     # Additional documentation
    ├── GETTING_STARTED.md             # Quick start guide
    └── ...                            # Other guides and references
\`\`\`

## What Goes Where

### Tokens (`/tokens/`)
**Purpose**: Define values used across the design system

**Examples**:
- Color values (HSL, RGB)
- Font sizes, weights
- Spacing measurements
- Shadow elevations
- Border radius sizes
- Breakpoint widths

**Guidelines**:
- Use consistent units (rem for sizing)
- Export as constants/objects
- Group related values
- Include light and dark variants

### Utilities (`/utilities/`)
**Purpose**: Helper functions and reusable patterns

**Examples**:
- className builders
- Component style presets
- Responsive helpers
- State builders (hover, focus, etc.)

**Guidelines**:
- Keep functions pure and simple
- Return strings (className format)
- Provide common patterns
- Export for easy import

### Layouts (`/layouts/`)
**Purpose**: Reusable layout components

**Examples**:
- Container wrapper
- Section wrapper
- Grid component
- Stack (flex layout)
- Center component
- Spacer component

**Guidelines**:
- Use React.forwardRef
- Accept common props (className, children)
- Support responsive variants
- Use cn() for className merging

### Animations (`/animations/`)
**Purpose**: Animation definitions and presets

**Examples**:
- Keyframe definitions
- Animation durations
- Timing functions
- Preset animations

**Guidelines**:
- Use standard keyframe format
- Include common durations
- Provide preset combinations
- Document animation intent

### Theme (`/theme/`)
**Purpose**: Theme configuration and management

**Examples**:
- Theme config interface
- Theme application functions
- CSS variable generation
- Theme merge utilities

**Guidelines**:
- Centralize theme logic
- Support light/dark modes
- Allow customization
- Export utilities for theme switching

### Components (`/components/`)
**Purpose**: Documentation and guidelines

**Examples**:
- Component structure guide
- Best practices
- Naming conventions
- Component patterns

**Guidelines**:
- Provide clear examples
- Document accessibility needs
- Show responsive behavior
- Include testing tips

### Documentation (`/documentation/`)
**Purpose**: User-facing guides and references

**Examples**:
- Getting started guides
- API references
- Usage examples
- Troubleshooting

**Guidelines**:
- Write for users of the system
- Include code examples
- Keep up to date
- Link to related resources

## Import Patterns

### Importing Tokens
\`\`\`typescript
// Option 1: Import specific tokens
import { colorTokens, spacingTokens } from "@/design-system/tokens"

// Option 2: Import from index
import { colorTokens } from "@/design-system/tokens/colors"

// Option 3: Use destructuring
import { colorTokens } from "@/design-system/tokens"
const { primary, secondary } = colorTokens
\`\`\`

### Importing Utilities
\`\`\`typescript
// Option 1: Import index
import { buttonVariants, cardStyles } from "@/design-system/utilities"

// Option 2: Import specific file
import { buttonVariants } from "@/design-system/utilities/componentHelpers"
\`\`\`

### Importing Layouts
\`\`\`typescript
import { Container, Grid, Stack } from "@/design-system/layouts/layoutPatterns"
\`\`\`

### Importing Animations
\`\`\`typescript
import { keyframes, animations } from "@/design-system/animations/keyframes"
\`\`\`

## Naming Conventions

### Files
- **Tokens**: kebab-case.ts (colors.ts, spacing.ts)
- **Utilities**: camelCase.ts (classNameHelpers.ts)
- **Components**: PascalCase.tsx (layoutPatterns.tsx)
- **Docs**: UPPERCASE.md (README.md, GETTING_STARTED.md)

### Exports
- **Objects**: camelCase (colorTokens, spacingPresets)
- **Functions**: camelCase (mergeTheme, applyTheme)
- **Interfaces**: PascalCase (ThemeConfig, ContainerProps)
- **Types**: PascalCase (ThemeMode)

## Adding to the Design System

### Add a New Token
1. Create/edit token file in `/tokens/`
2. Add export to `/tokens/index.ts`
3. Update documentation

### Add a New Utility
1. Create/edit utility file in `/utilities/`
2. Add export to `/utilities/index.ts`
3. Document usage

### Add a New Layout Component
1. Add component to `/layouts/layoutPatterns.tsx`
2. Document props and usage
3. Add examples to documentation

### Add Documentation
1. Create .md file in `/documentation/`
2. Link from README.md or GETTING_STARTED.md
3. Include code examples

## Design System Principles

1. **Consistency** - All values come from defined tokens
2. **Reusability** - Components and utilities are composable
3. **Accessibility** - Built-in accessibility considerations
4. **Scalability** - Easy to extend without breaking changes
5. **Maintainability** - Centralized definitions for easy updates
6. **Performance** - Optimized component structure
7. **Documentation** - Clear guides and examples

## Version Updates

When updating the design system:
1. Update relevant files
2. Update version in documentation
3. Document breaking changes
4. Update examples and guides
5. Test across components
6. Communicate changes to team

## Related Files (Outside Design System)

- `/tailwind.config.ts` - Tailwind configuration
- `/styles/globals.css` - Global styles
- `/lib/utils.ts` - Utility functions (cn function)
- `/components/ui/` - shadcn UI components
- `/components/xen/` - Custom components

## Performance Considerations

- Design tokens are zero-runtime (build-time evaluation)
- Utilities are string-based (no CSS-in-JS overhead)
- Components use standard React patterns
- Animations use CSS keyframes (optimized)
- Theme switching uses CSS variables (performant)

## Maintenance Checklist

- [ ] Review tokens quarterly
- [ ] Update components when Tailwind versions change
- [ ] Test animations across browsers
- [ ] Keep documentation current
- [ ] Check accessibility compliance
- [ ] Verify responsive behavior
- [ ] Test dark mode support
- [ ] Performance benchmark

## Support and Questions

Refer to specific documentation files:
- Quick start: GETTING_STARTED.md
- Component creation: components/COMPONENT_GUIDE.md
- Token reference: tokens/
- Layout patterns: layouts/
