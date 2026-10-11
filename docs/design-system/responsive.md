# ClassLens Design System — Responsive Behavior & Viewports

## 1. Supported Breakpoint Spectrum

ClassLens supports continuous fluid layouts tested across six standard target viewports:

| Device Category | Target Viewport | Columns | Layout Composition | Navigation Mode |
|---|---|---|---|---|
| **Mobile Phone** | `390×844` (iPhone 14) | 1 column | Linear stack, sticky bottom action bar, tabbed modal | Collapsible top bar with mobile sheet |
| **Tablet Portrait** | `768×1024` (iPad) | 2 columns | Adaptive grid, balanced card density | Compact side icon bar or header dropdown |
| **Tablet Landscape**| `1024×768` (iPad Mini) | 2–3 columns | Two-column review workspace, fluid metrics | Slim collapsible sidebar |
| **Small Laptop** | `1280×800` (MacBook 13) | 3 columns | Standard workspace, dual-pane review modal | Standard 240px persistent sidebar |
| **Standard Desktop**| `1440×900` (Primary) | 4 columns | Spacious 4-column card grid, large modal | Persistent 240px sidebar + sub-tabs |
| **Large Display** | `1920×1080` (FHD) | 4 columns | Max-width 1440px centered workspace | Persistent sidebar + extra canvas margin |

---

## 2. Component Reflow Strategies

### 2.1 Metric Cards Row
- **Desktop**: 4 equal columns in a single horizontal row.
- **Tablet**: 2×2 grid with 16px gaps.
- **Mobile**: 2×2 grid with compact metric padding.

### 2.2 Student Review Workspace
- **Desktop ($\ge 1024$px)**: Side-by-side dual-pane layout (7 columns for interactive canvas, 5 columns for step diagnostics and teacher review form).
- **Mobile ($< 1024$px)**: Segmented tabs (`Student Work` vs `Analysis & Feedback`) to ensure maximum image zoomability without vertical cramping.

### 2.3 Filter Bar
- **Desktop**: Inline horizontal pill group with active counts.
- **Mobile**: Horizontally scrolling container with fade indicators or segmented dropdown.
