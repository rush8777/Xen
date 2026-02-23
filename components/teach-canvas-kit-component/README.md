# Teach Canvas Kit

A React component for creating interactive course presentations with slides, quizzes, and checklists. Perfect for educational content, training materials, and interactive presentations.

## Features

- **Multiple Slide Types**: Title slides, text-only, text-image, cards, checklists, and quizzes
- **Interactive Elements**: Clickable checklists, quiz questions with immediate feedback
- **Theme System**: 4 built-in themes (Ocean, Peach, Sage, Lavender)
- **Progress Tracking**: Visual progress bar showing course completion
- **Responsive Design**: Works on all screen sizes
- **TypeScript Support**: Full TypeScript support with type definitions

## Installation

```bash
npm install teach-canvas-kit
```

## Dependencies

This component requires the following peer dependencies:

```bash
npm install react react-dom
```

And these dependencies:

```bash
npm install clsx lucide-react tailwind-merge
```

## Setup

### 1. Import CSS

Import the CSS file in your application's main CSS file or component:

```tsx
import 'teach-canvas-kit/styles.css';
```

### 2. Configure Tailwind CSS

Make sure your Tailwind CSS configuration includes the component's CSS. If you're using Next.js, update your `tailwind.config.js`:

```js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/teach-canvas-kit/**/*.{js,ts,jsx,tsx}',
  ],
  // ... rest of your config
}
```

## Usage

### Basic Usage

```tsx
import { TeachCanvasKit } from 'teach-canvas-kit';

function MyCourse() {
  return (
    <div className="h-screen">
      <TeachCanvasKit />
    </div>
  );
}
```

### Custom Course Data

```tsx
import { TeachCanvasKit } from 'teach-canvas-kit';
import { CourseSlides } from 'teach-canvas-kit';

const customCourse: CourseSlides = {
  courseTitle: "My Custom Course",
  slides: [
    {
      id: "intro",
      type: "title",
      title: "Welcome to My Course",
      subtitle: "Learn something amazing today!",
      buttonLabel: "Get Started"
    },
    {
      id: "content",
      type: "text-only",
      title: "Getting Started",
      body: "This is where your learning journey begins..."
    }
  ]
};

function MyCustomCourse() {
  return (
    <div className="h-screen">
      <TeachCanvasKit courseData={customCourse} />
    </div>
  );
}
```

### With Custom Styling

```tsx
import { TeachCanvasKit } from 'teach-canvas-kit';

function StyledCourse() {
  return (
    <div className="h-screen">
      <TeachCanvasKit className="my-custom-class" />
    </div>
  );
}
```

## Slide Types

### Title Slide
```tsx
{
  id: "title",
  type: "title",
  title: "Course Title",
  subtitle: "Course description",
  buttonLabel: "Start Course"
}
```

### Text-Only Slide
```tsx
{
  id: "text",
  type: "text-only",
  title: "Slide Title",
  body: "Your content here..."
}
```

### Text-Image Slide
```tsx
{
  id: "text-image",
  type: "text-image",
  title: "Slide Title",
  body: "Your content here..."
}
```

### Cards Slide
```tsx
{
  id: "cards",
  type: "cards",
  title: "Topic Overview",
  cards: [
    {
      heading: "Card Title",
      description: "Card description",
      icon: "🎯"
    }
  ]
}
```

### Checklist Slide
```tsx
{
  id: "checklist",
  type: "checklist",
  title: "Task List",
  items: [
    {
      text: "Task description",
      checked: false
    }
  ]
}
```

### Quiz Slide
```tsx
{
  id: "quiz",
  type: "quiz",
  title: "Knowledge Check",
  quizQuestion: "What is 2 + 2?",
  quizOptions: ["3", "4", "5", "6"],
  correctAnswer: 1
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `courseData` | `CourseSlides` | Default course | Custom course data |
| `className` | `string` | `""` | Additional CSS classes |

## TypeScript Types

```tsx
import type { Slide, TopicCard, ChecklistItem, CourseSlides } from 'teach-canvas-kit';
```

## Themes

The component includes 4 built-in themes:
- **Ocean** (default) - Blue and orange color scheme
- **Peach** - Warm peach and teal colors
- **Sage** - Soft green and orange tones
- **Lavender** - Purple and orange accent colors

Users can switch themes using the theme selector in the top-right corner.

## License

MIT
