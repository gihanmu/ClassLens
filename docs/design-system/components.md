# ClassLens Design System — Component Specifications & Contracts

## 1. UI Primitives (`src/components/ui/`)

### 1.1 Button (`button.tsx`)
- **Variants**: `primary`, `secondary`, `outline`, `ghost`, `destructive`, `coral`.
- **Sizes**:
  - `sm`: Height 36px, font 13px/600, px 12px.
  - `md`: Height 44px, font 14px/600, px 18px (default).
  - `lg`: Height 48px, font 15px/700, px 22px.
- **Props**: `variant`, `size`, `isLoading`, `leftIcon`, `rightIcon`, native `button` attributes.
- **Radius**: `10px` (`rounded-[10px]`). Focus ring: `ring-2 ring-brand-primary ring-offset-2`.

### 1.2 IconButton (`icon-button.tsx`)
- **Variants**: `neutral`, `primary`, `destructive`, `inverse`.
- **Sizes**: 36px, 40px, 44px (ensuring $\ge 44\times 44$px touch area).
- **Mandatory Prop**: `aria-label` for screen reader announcement.

### 1.3 Card (`card.tsx`)
- **Variants**: `default`, `interactive`, `highlighted`, `educational`, `warning`, `flat`.
- **Subcomponents**: `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
- **Radius**: `14px`. Standard border: `1px solid var(--border-default)`.

### 1.4 Badge & StatusBadge (`badge.tsx`, `status-badge.tsx`)
- **Badge**: Decorative/informational tag (`neutral`, `primary`, `accent`).
- **StatusBadge**: Semantic status indicators (`success`, `error`, `warning`, `information`, `pending`, `mock`).
  - Always pairs semantic foreground, soft background, status icon, and human-readable text.

### 1.5 Form Controls (`input.tsx`, `textarea.tsx`, `select.tsx`, `checkbox.tsx`, `radio-group.tsx`)
- **Height**: 44px for inputs/selects.
- **Border**: 1px neutral border (`var(--border-default)`).
- **Radius**: `10px`. Text: 15px.
- **States**: default, focus (`border-brand-primary ring-2 ring-brand-primary/20`), error (`border-semantic-error ring-2 ring-semantic-error/20`), disabled (`bg-surface-subtle text-ink-muted`).

### 1.6 Tabs (`tabs.tsx`)
- **Structure**: `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`.
- **Keyboard Support**: Left/Right arrow keys navigation, Enter/Space activation, Home/End jumping.
- **Indicator**: Active tab uses `text-brand-primary` and a distinct 2px bottom border or pill background.

### 1.7 Dialog & Drawer (`dialog.tsx`, `drawer.tsx`)
- **Features**: Accessible modal container with backdrop blur, focus trapping, Escape key dismiss, and body scroll lock.
- **Subcomponents**: `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogContent`, `DialogFooter`, `DialogClose`.

### 1.8 Feedback (`alert.tsx`, `skeleton.tsx`, `spinner.tsx`, `empty-state.tsx`)
- **Alert**: Semantic message boxes (`info`, `success`, `warning`, `error`).
- **Skeleton**: Subtle pulse placeholder matching component geometry.
- **EmptyState**: Centered illustration, title, description, and primary CTA.

---

## 2. Shared Compositions (`src/components/shared/`)

- **`AppShell`**: Two-tier layout providing persistent collapsible sidebar on desktop and mobile top bar.
- **`AppHeader`**: Top bar with ClassLens branding, class switcher, offline demo pill, and teacher profile.
- **`AppSidebar`**: Side navigation containing Dashboard, Assessments, Students, Analysis, Class Insights, and Settings.
- **`MetricCard`**: Stat container displaying large numerical value, label, contextual trend/status, and category icon.
- **`OfflineDemoBanner`**: Top notification explaining simulated AI and SymPy formal verification.
- **`FilterBar`**: Segmented filter pills with active counts and quick-toggle states.

---

## 3. Domain Features (`src/components/features/`)

- **`StudentResponseCard`**: Displays student ID, handwritten thumbnail, separate answer/reasoning status badges, and inspect button.
- **`StudentWorkViewer`**: Canvas viewer with original handwritten worksheet, zoom/pan/reset toolbar, and SVG evidence hops overlay.
- **`ReasoningStepCard`**: Discloses step number, operation, expected value, observed value, and SymPy validity verdict.
- **`MisconceptionCard`**: Plain-language misconception title, first-error step callout, and side-by-side jump comparison.
- **`TeacherReviewPanel`**: Formal review controls: Approve, Override, or Mark Unreadable with pedagogical notes and audit save action.
- **`TeachingRecommendationCard`**: Categorized pedagogical intervention with affected student count and instructional steps.
