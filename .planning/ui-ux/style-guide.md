# UI/UX Style Guide

## 1. Design Principles

### Minimalism
- Clean, uncluttered interfaces
- Clear visual hierarchy
- Purposeful whitespace
- Focused content presentation

### Consistency
- Uniform component styling
- Predictable interactions
- Standardized feedback patterns
- Cohesive color scheme

### Accessibility
- WCAG 2.1 compliance
- Keyboard navigation
- Screen reader support
- Color contrast standards

### Responsiveness
- Mobile-first approach
- Fluid layouts
- Adaptive components
- Touch-friendly interfaces

## 2. Color Palette

### Primary Colors
- Primary: #3B82F6 (Blue)
- Secondary: #10B981 (Green)
- Accent: #F59E0B (Amber)

### Neutral Colors
- Background: #FFFFFF
- Surface: #F9FAFB
- Border: #E5E7EB
- Text: #111827

### Semantic Colors
- Success: #10B981
- Warning: #F59E0B
- Error: #EF4444
- Info: #3B82F6

## 3. Typography

### Font Family
- Primary: Inter
- Monospace: Fira Code
- Fallback: system-ui

### Font Sizes
- H1: 2.5rem
- H2: 2rem
- H3: 1.5rem
- Body: 1rem
- Small: 0.875rem

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

## 4. Component Library

### Buttons
```html
<!-- Primary Button -->
<button class="btn btn-primary">
  Primary Action
</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">
  Secondary Action
</button>

<!-- Outline Button -->
<button class="btn btn-outline">
  Outline Action
</button>
```

### Forms
```html
<!-- Text Input -->
<div class="form-group">
  <label for="input">Label</label>
  <input type="text" id="input" class="form-control">
  <div class="form-help">Help text</div>
</div>

<!-- Select -->
<div class="form-group">
  <label for="select">Label</label>
  <select id="select" class="form-control">
    <option>Option 1</option>
    <option>Option 2</option>
  </select>
</div>
```

### Cards
```html
<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
  </div>
  <div class="card-body">
    Card content
  </div>
  <div class="card-footer">
    Card actions
  </div>
</div>
```

### Alerts
```html
<!-- Success Alert -->
<div class="alert alert-success">
  Success message
</div>

<!-- Error Alert -->
<div class="alert alert-error">
  Error message
</div>

<!-- Warning Alert -->
<div class="alert alert-warning">
  Warning message
</div>
```

## 5. Layout System

### Grid
- 12-column grid system
- Responsive breakpoints
- Flexible gutters
- Nested grids support

### Spacing
- Base unit: 4px
- Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128
- Consistent margins and padding
- Responsive spacing adjustments

## 6. Animation Guidelines

### Transitions
- Duration: 200ms
- Easing: cubic-bezier(0.4, 0, 0.2, 1)
- Purposeful motion
- Reduced motion support

### Micro-interactions
- Hover states
- Focus states
- Loading indicators
- Success/error feedback

## 7. Iconography

### Icon Set
- Heroicons
- Consistent stroke width
- Clear visual meaning
- Accessible labels

### Usage
- Decorative icons
- Functional icons
- Status indicators
- Navigation elements

## 8. Responsive Design

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Patterns
- Stack to columns
- Hide/show content
- Adjust spacing
- Modify typography

## 9. Accessibility

### Keyboard Navigation
- Focus indicators
- Tab order
- Skip links
- ARIA landmarks

### Screen Readers
- Semantic HTML
- ARIA labels
- Live regions
- Alternative text

## 10. Performance

### Loading States
- Skeleton screens
- Progress indicators
- Placeholder content
- Error boundaries

### Optimization
- Lazy loading
- Code splitting
- Image optimization
- Bundle size control 