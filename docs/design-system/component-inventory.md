# ClassLens Design System — Complete Component Inventory

## 1. UI Primitives (`src/components/ui/`)

| Component | Export Path | Primary Purpose | Key Props / Variants |
|---|---|---|---|
| `Button` | `ui/button.tsx` | Main interactive button control | `variant`: primary, secondary, outline, ghost, destructive, coral; `size`: sm, md, lg; `isLoading` |
| `IconButton` | `ui/icon-button.tsx` | Accessible icon-only button | `variant`: neutral, primary, destructive, inverse; `size`: sm, md, lg; `aria-label` (mandatory) |
| `Badge` | `ui/badge.tsx` | Informational label tag | `variant`: neutral, primary, accent; `size`: sm, md |
| `StatusBadge` | `ui/status-badge.tsx` | High-contrast status indicator | `status`: success, error, warning, information, pending, mock |
| `Card` | `ui/card.tsx` | Structured surface container | `variant`: default, interactive, highlighted, educational, warning, flat |
| `CardHeader` | `ui/card.tsx` | Card header region | Subcomponent of `Card` |
| `CardTitle` | `ui/card.tsx` | Card title heading | Subcomponent of `Card` |
| `CardDescription` | `ui/card.tsx` | Card subtitle / description | Subcomponent of `Card` |
| `CardContent` | `ui/card.tsx` | Card main body | Subcomponent of `Card` |
| `CardFooter` | `ui/card.tsx` | Card bottom action footer | Subcomponent of `Card` |
| `Input` | `ui/input.tsx` | Text entry field | `isError`, `size`: sm, md; standard HTML input props |
| `Textarea` | `ui/textarea.tsx` | Multiline text entry | `isError`, standard HTML textarea props |
| `Select` | `ui/select.tsx` | Dropdown selector | `isError`, options array, standard HTML select props |
| `Checkbox` | `ui/checkbox.tsx` | Accessible checkbox toggle | `checked`, `onChange`, label, description |
| `RadioGroup` | `ui/radio-group.tsx` | Accessible radio option list | `name`, `value`, `onChange`, options array |
| `Tabs` | `ui/tabs.tsx` | WAI-ARIA tab container | `value`, `onValueChange`, defaultValue |
| `TabsList` | `ui/tabs.tsx` | Tab header list container | Subcomponent of `Tabs` |
| `TabsTrigger` | `ui/tabs.tsx` | Individual tab selector | `value`, disabled |
| `TabsContent` | `ui/tabs.tsx` | Tab panel content | `value` |
| `Dialog` | `ui/dialog.tsx` | Modal dialog primitive | `isOpen`, `onClose`, title, description |
| `Drawer` | `ui/drawer.tsx` | Slide-out panel primitive | `isOpen`, `onClose`, side: right, title |
| `Alert` | `ui/alert.tsx` | In-page feedback message | `variant`: info, success, warning, error; title, children |
| `Skeleton` | `ui/skeleton.tsx` | Animated loading placeholder | `className`, shape |
| `Spinner` | `ui/spinner.tsx` | Accessible loading spinner | `size`: sm, md, lg |
| `Typography` | `ui/typography.tsx` | Semantic text primitives | `variant`: display, h1, h2, h3, h4, body-lg, body, body-sm, label, caption |

---

## 2. Shared Compositions (`src/components/shared/`)

| Component | Export Path | Primary Purpose |
|---|---|---|
| `AppShell` | `shared/app-shell.tsx` | Top-level frame managing sidebar, header, and content regions |
| `AppHeader` | `shared/app-header.tsx` | Top navigation bar with branding, class switcher, demo status, and user avatar |
| `AppSidebar` | `shared/app-sidebar.tsx` | Collapsible sidebar with Dashboard, Assessments, Students, Insights, Settings |
| `PageHeader` | `shared/page-header.tsx` | Standardized title, subtitle, breadcrumb, and primary action group |
| `SectionHeader` | `shared/section-header.tsx` | Section title with optional badge, subtitle, and right-aligned controls |
| `BrandLogo` | `shared/brand-logo.tsx` | Responsive ClassLens logo with icon mark and wordmark |
| `MetricCard` | `shared/metric-card.tsx` | 4-metric summary card with icon, count, total denominator, and color accent |
| `FilterBar` | `shared/filter-bar.tsx` | Segmented filter pill group with counts |
| `OfflineDemoBanner` | `shared/offline-demo-banner.tsx`| Sticky header bar disclosing simulated AI and SymPy formal verification |
| `EmptyState` | `shared/empty-state.tsx` | Friendly empty condition container with icon, message, and action |
| `LoadingState` | `shared/loading-state.tsx` | Skeleton / spinner loading screen with educational copy |
| `ErrorState` | `shared/error-state.tsx` | Error recovery screen with retry action |

---

## 3. Domain Features (`src/components/features/`)

| Component | Export Path | Primary Purpose |
|---|---|---|
| `StudentResponseCard` | `features/students/StudentResponseCard.tsx` | Card displaying student submission, thumbnail, badges, and inspect action |
| `AnswerStatusBadge` | `features/students/AnswerStatusBadge.tsx` | Distinct badge for final answer correctness (Correct, Incorrect, Unassessable) |
| `ReasoningStatusBadge` | `features/students/ReasoningStatusBadge.tsx` | Distinct badge for visible reasoning (Valid, Procedural Error, Incomplete) |
| `AnalysisProvenancePill`| `features/analysis/AnalysisProvenancePill.tsx` | Discloses Offline Simulated vs AI-Proposed vs Teacher Confirmed |
| `StudentWorkViewer` | `features/students/StudentWorkViewer.tsx` | Large worksheet viewer with zoom, pan, rotation, and SVG hop overlays |
| `ReasoningStepCard` | `features/analysis/ReasoningStepCard.tsx` | Step-by-step card showing expected vs observed jump and SymPy verdict |
| `MisconceptionCard` | `features/analysis/MisconceptionCard.tsx` | First-error localization card with plain-language misconception title |
| `TeacherReviewPanel` | `features/teacher-review/TeacherReviewPanel.tsx` | Teacher override and review form with audit persistence |
| `TeachingRecommendationCard`| `features/cohort/TeachingRecommendationCard.tsx` | Differentiated action card with student count and concrete steps |
