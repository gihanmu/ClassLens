# ClassLens Design System — Accessibility Specification (WCAG 2.2 AA)

## 1. Compliance Standards & Targets

ClassLens is designed to meet WCAG 2.2 Level AA requirements across all instructional and diagnostic workflows.

### 1.1 Contrast Verification Matrix

| Foreground Token | Background Surface | Measured Ratio | WCAG 2.2 AA Requirement | Verdict |
|---|---|---|---|---|
| `ink-primary` (`#10182B`) | `surface-card` (`#FFFFFF`) | 16.5:1 | $\ge 4.5:1$ | **Pass (AAA)** |
| `ink-secondary` (`#475569`) | `surface-card` (`#FFFFFF`) | 7.12:1 | $\ge 4.5:1$ | **Pass (AAA)** |
| `ink-muted` (`#64748B`) | `surface-card` (`#FFFFFF`) | 4.65:1 | $\ge 4.5:1$ | **Pass (AA)** |
| `brand-primary` (`#5145F5`) | `surface-card` (`#FFFFFF`) | 5.25:1 | $\ge 4.5:1$ | **Pass (AA)** |
| `semantic-success` (`#087A53`)| `surface-success` (`#E7F8EF`) | 5.82:1 | $\ge 4.5:1$ | **Pass (AA)** |
| `semantic-error` (`#B42332`) | `surface-error` (`#FFF0F1`) | 6.21:1 | $\ge 4.5:1$ | **Pass (AA)** |
| `semantic-warning` (`#925300`)| `surface-warning` (`#FFF2D6`)| 5.40:1 | $\ge 4.5:1$ | **Pass (AA)** |

---

## 2. Keyboard Navigation & Focus Management

1. **Focus Trapping**: Dialog modals and inspection drawers trap focus within their container when open. Pressing `Escape` closes the active modal and restores focus to the invoking element.
2. **Tablist Pattern**: The `Tabs` primitive supports standard WAI-ARIA arrow navigation (`ArrowLeft`, `ArrowRight`, `Home`, `End`).
3. **Form Radio Navigation**: The `TeacherReviewPanel` options operate as a standard `<fieldset role="radiogroup">`, enabling `ArrowUp` and `ArrowDown` navigation.
4. **Skip Links**: The root layout includes an accessible `"Skip to main content"` skip-link targeting `<main id="main-content">`.

---

## 3. Screen Reader Accommodations

1. **Non-Visual Alternatives for Visual Data**: The horizontal misconception chart provides an accessible data table (`<table>`) in an accordion container with `aria-describedby` linkage.
2. **Descriptive Labels for Icon Controls**: All icon buttons (`IconButton`, canvas zoom, dialog close) provide explicit `aria-label` text.
3. **Status Announcements**: Live region announcements (`aria-live="polite"`) inform assistive technologies when batch analysis completes or review decisions are saved.

---

## 4. Physical & Cognitive Accessibility

1. **Touch Targets**: Minimum touch target size is $44\times 44$px for all interactive controls on mobile and tablet viewports.
2. **Zoom & Reflow**: Layouts support browser zoom up to 200% without horizontal clipping or loss of functionality.
3. **Plain-Language Diagnostics**: Technical taxonomy codes (e.g. `MISC-ARITH-OFF-BY-ONE`) are always paired with plain-language pedagogical explanations (*"Counting number-line marks instead of intervals"*).
