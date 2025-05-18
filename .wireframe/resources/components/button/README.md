# Button Component

A versatile and accessible button component for the Legal Study System. This component provides a consistent button design across the application with various styles, sizes, and states.

## Usage

### Basic Button
```html
<button class="btn btn-primary">Primary Button</button>
```

### Button Variants
```html
<button class="btn btn-primary">Primary Button</button>
<button class="btn btn-secondary">Secondary Button</button>
<button class="btn btn-success">Success Button</button>
<button class="btn btn-warning">Warning Button</button>
<button class="btn btn-error">Error Button</button>
```

### Button Sizes
```html
<button class="btn btn-primary btn-sm">Small Button</button>
<button class="btn btn-primary">Default Button</button>
<button class="btn btn-primary btn-lg">Large Button</button>
```

### Button States
```html
<button class="btn btn-primary" disabled>Disabled Button</button>
<button class="btn btn-primary loading">
    <span class="spinner"></span>
    Loading Button
</button>
```

### Buttons with Icons
```html
<button class="btn btn-primary">
    <svg class="icon" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/>
    </svg>
    Add Item
</button>
```

### Button Groups
```html
<div class="button-group">
    <button class="btn btn-primary">Left</button>
    <button class="btn btn-primary">Middle</button>
    <button class="btn btn-primary">Right</button>
</div>
```

## Features

### Variants
- Primary: Main call-to-action buttons
- Secondary: Alternative actions
- Success: Positive actions
- Warning: Cautionary actions
- Error: Destructive actions

### Sizes
- Small (btn-sm): Compact buttons
- Default: Standard buttons
- Large (btn-lg): Prominent buttons

### States
- Default: Normal state
- Hover: Mouse over state
- Focus: Keyboard focus state
- Active: Pressed state
- Disabled: Non-interactive state
- Loading: Processing state

### Icons
- Support for SVG icons
- Consistent icon sizing
- Proper spacing with text

### Accessibility
- Keyboard navigation
- Focus indicators
- ARIA attributes
- Screen reader support

### Dark Mode
- Automatic dark mode support
- Consistent contrast ratios
- Preserved visual hierarchy

### Responsive Design
- Mobile-first approach
- Flexible layouts
- Stack on small screens

## CSS Variables

The button component uses the following CSS variables from the design system:

### Colors
```css
--color-primary-600: #4f46e5;
--color-primary-700: #4338ca;
--color-primary-800: #3730a3;
--color-secondary-200: #e2e8f0;
--color-secondary-300: #cbd5e1;
--color-secondary-700: #334155;
--color-success-500: #22c55e;
--color-success-700: #15803d;
--color-warning-500: #f59e0b;
--color-warning-700: #b45309;
--color-error-500: #ef4444;
--color-error-700: #b91c1c;
```

### Typography
```css
--font-size-sm: 0.875rem;
--font-size-base: 1rem;
--font-size-lg: 1.125rem;
--font-weight-medium: 500;
--line-height-normal: 1.5;
```

### Spacing
```css
--spacing-1: 0.25rem;
--spacing-2: 0.5rem;
--spacing-3: 0.75rem;
--spacing-4: 1rem;
--spacing-6: 1.5rem;
```

### Border Radius
```css
--radius-md: 0.375rem;
```

### Transitions
```css
--transition-all: all 0.15s ease-in-out;
```

## Best Practices

1. **Clear Labels**
   - Use descriptive button text
   - Keep labels concise
   - Include icons for visual cues

2. **Consistent Hierarchy**
   - Use primary buttons for main actions
   - Use secondary buttons for alternatives
   - Use appropriate variants for different actions

3. **Proper Spacing**
   - Maintain consistent spacing between buttons
   - Use button groups for related actions
   - Consider mobile spacing

4. **Loading States**
   - Show loading state for async actions
   - Disable button during loading
   - Provide visual feedback

5. **Disabled States**
   - Disable buttons when action is unavailable
   - Provide clear visual indication
   - Consider tooltips for explanation

6. **Icon Usage**
   - Use icons to enhance meaning
   - Maintain consistent icon style
   - Ensure proper spacing

7. **Button Groups**
   - Group related actions
   - Maintain visual consistency
   - Consider mobile layout

8. **Accessibility**
   - Include proper ARIA labels
   - Ensure keyboard navigation
   - Maintain focus indicators

## Figma Integration

The button component is designed to be easily integrated with Figma:

1. Create components for each variant
2. Include all states in the component
3. Use consistent spacing
4. Document usage guidelines

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow existing code style
2. Update documentation
3. Test in supported browsers
4. Ensure accessibility compliance
