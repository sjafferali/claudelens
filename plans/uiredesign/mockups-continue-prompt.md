# ClaudeLens UI Mockups - Continuation Prompt

## Instructions for Agent

You are tasked with creating UI/UX mockups for the ClaudeLens application. These are design-only tasks that create standalone HTML/CSS mockups without modifying the existing application codebase. Your work will guide future implementation efforts.

## Your Task

1. **Find the next mockup story**: Open `/plans/uiredesign/mockups-build-checklist.md` and locate the FIRST unchecked user story (not individual tasks)
2. **Complete ALL tasks in that story**: Work through every task within the story sequentially
3. **Update progress immediately**: Mark each task as complete `[x]` as you finish it
4. **Save files**: Store all mockups in `/plans/uiredesign/mockups/` directory
5. **STOP after completing ONE full story**: Do not continue to the next story

## Project Context

### About ClaudeLens
ClaudeLens is a web application that archives and visualizes Claude AI conversations. Your mockups will prototype new features and UI improvements that enhance the user experience.

### Current UI Stack
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **Components**: Custom components with some shadcn/ui patterns
- **Theme**: Dark mode support with layer-based design system

### Design System Reference

**Color Palette:**
```css
/* Primary Colors */
--color-primary: #3B82F6;        /* Blue-500 */
--color-secondary: #10B981;      /* Emerald-500 */
--color-accent: #8B5CF6;         /* Purple-500 */

/* Status Colors */
--color-warning: #F59E0B;        /* Amber-500 */
--color-error: #EF4444;          /* Red-500 */
--color-success: #22C55E;        /* Green-500 */

/* Neutral Colors - Light Mode */
--color-background: #FFFFFF;
--color-surface: #F9FAFB;
--color-border: #E5E7EB;
--color-text-primary: #111827;
--color-text-secondary: #6B7280;

/* Neutral Colors - Dark Mode */
--dark-background: #0F172A;
--dark-surface: #1E293B;
--dark-border: #334155;
--dark-text-primary: #F9FAFB;
--dark-text-secondary: #94A3B8;
```

**Typography:**
```css
/* Font Stack */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
```

**Spacing System:**
```css
/* Use 4px grid */
--space-1: 0.25rem;     /* 4px */
--space-2: 0.5rem;      /* 8px */
--space-3: 0.75rem;     /* 12px */
--space-4: 1rem;        /* 16px */
--space-6: 1.5rem;      /* 24px */
--space-8: 2rem;        /* 32px */
```

### Mockup Requirements

1. **Self-Contained**: Each mockup should work as a standalone HTML file
2. **Responsive**: Include mobile, tablet, and desktop layouts
3. **Interactive**: Use JavaScript to demonstrate interactions
4. **Accessible**: Follow WCAG 2.1 AA guidelines
5. **Themed**: Include both light and dark mode versions
6. **Documented**: Add comments explaining design decisions

### File Structure

```
/plans/uiredesign/mockups/
├── filter-ui-improvement.html
├── filter-ui-improvement.css
├── import-export-page.html
├── import-export-page.css
├── prompt-manager.html
├── prompt-manager.css
├── conversation-snippets.html
├── conversation-snippets.css
└── shared/
    ├── base-styles.css
    └── mock-data.js
```

## Implementation Guidelines

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClaudeLens - [Feature Name] Mockup</title>
    <style>
        /* Inline styles or link to CSS file */
    </style>
</head>
<body>
    <!-- Theme Toggle -->
    <button id="theme-toggle" class="theme-toggle">🌙/☀️</button>

    <!-- Main Content -->
    <div class="container">
        <!-- Your mockup here -->
    </div>

    <script>
        // Interactive functionality
    </script>
</body>
</html>
```

### CSS Best Practices
- Use CSS custom properties for theming
- Include smooth transitions for interactions
- Ensure proper contrast ratios
- Use flexbox/grid for layouts
- Include hover and focus states

### JavaScript Interactions
- Theme switching
- Tab navigation
- Modal/drawer animations
- Form validations
- Drag and drop demonstrations
- Filter/search previews

## Mockup Story Templates

### For Feature Pages
1. Header with navigation
2. Main content area
3. Sidebar (if applicable)
4. Footer with actions

### For Modal/Dialog Mockups
1. Overlay background
2. Modal container
3. Header with close button
4. Content area
5. Footer with action buttons

### For Dashboard/Analytics
1. Summary cards row
2. Chart sections
3. Data tables
4. Filter controls
5. Export options

## Working Process

1. **Identify Current Story**
   - Read the checklist to find the first incomplete user story
   - Note all tasks within that story
   - Plan your approach for the entire story

2. **For Each Task in the Story**:
   - Research: Review existing UI patterns
   - Design: Create HTML structure
   - Style: Apply consistent CSS
   - Interact: Add JavaScript functionality
   - Update: Mark task complete `[x]` immediately

3. **Story Completion**
   - Verify all tasks in the story are marked `[x]`
   - Test the complete mockup set
   - Commit with descriptive message
   - STOP - Do not proceed to next story

4. **If Blocked**
   - Mark the specific task as blocked
   - Document the blocker clearly
   - STOP - Do not attempt workarounds

## Example Commit Messages

```
feat(mockups): create improved filter UI mockup

- Add multi-select dropdowns for message types
- Include date range picker
- Design cost range slider
- Create responsive mobile version
```

## Sample Data to Include

Use realistic sample data in your mockups:

```javascript
// Sample conversation data
const sampleConversation = {
    id: "conv_abc123",
    title: "Building a React Application",
    messageCount: 156,
    cost: 2.45,
    duration: "2h 15m",
    startedAt: "2024-01-15T10:30:00Z"
};

// Sample message types
const messageTypes = [
    "user",
    "assistant",
    "tool_use",
    "tool_result",
    "summary"
];

// Sample filter presets
const filterPresets = [
    "Today's Conversations",
    "High Cost Sessions",
    "Long Conversations",
    "With Errors",
    "Using Tools"
];
```

## Quality Checklist

Before marking a mockup as complete, verify:

- [ ] Works in Chrome, Firefox, Safari
- [ ] Responsive at 320px, 768px, 1024px, 1440px
- [ ] Dark mode fully implemented
- [ ] All interactive elements have hover states
- [ ] Keyboard navigation works
- [ ] Color contrast passes WCAG AA
- [ ] Loading states included
- [ ] Error states designed
- [ ] Empty states considered
- [ ] Sample data looks realistic

## Stop Conditions

Stop work and update the checklist when:
1. **You complete ONE full mockup story** (all tasks within that story checked)
2. **You encounter a blocking issue** that prevents progress:
   - Mark the task as `[BLOCKED - <reason>]`
   - Document what needs to be resolved
   - Stop work immediately
3. **Technical limitations** prevent completing the mockup:
   - Mark as `[FAILED - <reason>]`
   - Document the limitation
   - Stop work immediately

## Example Checklist Updates

```markdown
# Before
## User Story 1: Filter UI Improvements
- [ ] Create improved filter mockup with multi-select
- [ ] Add date range picker component
- [ ] Design cost range slider

# After successful completion
## User Story 1: Filter UI Improvements
- [x] Create improved filter mockup with multi-select
- [x] Add date range picker component
- [x] Design cost range slider

# After encountering a blocker
## User Story 1: Filter UI Improvements
- [x] Create improved filter mockup with multi-select
- [BLOCKED - Need clarification on date format] Add date range picker component
- [ ] Design cost range slider
```

## Important Notes

- **Complete ONE story fully** - Do not jump between stories
- **Update checklist immediately** - Mark tasks as you complete them
- **These are design mockups**, not production code
- **Focus on user experience** over technical implementation
- **Be creative** but maintain consistency with existing UI
- **Document your design rationale** for developers
- **Consider edge cases** and error states
- **Make mockups interactive** as reasonably possible

## Critical Reminders

1. **ONE STORY ONLY**: Complete all tasks in one user story, then STOP
2. **SEQUENTIAL WORK**: Complete tasks in order within the story
3. **IMMEDIATE UPDATES**: Mark checklist items as soon as completed
4. **CLEAR DOCUMENTATION**: Your mockups guide implementation
5. **STOP WHEN DONE**: After completing one story, stop work

Remember: Your mockups will directly influence the final implementation. Make them clear, comprehensive, and user-friendly. Focus on completing one story thoroughly rather than starting multiple stories.
