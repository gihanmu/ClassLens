# ClassLens Design System — Spacing, Elevation & Layout

## 1. Spacing Scale

ClassLens uses a 4px base spatial grid. All margins, paddings, gaps, and component heights align to these values.

| Token | Value | Rem Equivalent | Common Application |
|---|---|---|---|
| `space-1` | 4px | 0.25rem | Icon spacing, tight badge padding, micro-offsets |
| `space-2` | 8px | 0.5rem | Small gaps, compact button padding, badge horizontal padding |
| `space-3` | 12px | 0.75rem | Form input vertical padding, card inner gaps |
| `space-4` | 16px | 1.0rem | Standard container padding, mobile gutters, grid gaps |
| `space-5` | 20px | 1.25rem | Standard card internal padding, card gaps |
| `space-6` | 24px | 1.5rem | Section inner margins, feature panel padding, tablet gutters |
| `space-8` | 32px | 2.0rem | Desktop page gutters, section spacing |
| `space-10` | 40px | 2.5rem | Major component separation |
| `space-12` | 48px | 3.0rem | Hero section vertical padding, page division |
| `space-16` | 64px | 4.0rem | Major layout block margins |
| `space-20` | 80px | 5.0rem | Landing page feature separation |
| `space-24` | 96px | 6.0rem | Hero top banner offset |

---

## 2. Border Radii Tokens

Radius values are assigned intentionally by component role rather than applying uniform large pills to all containers.

| Token | Value | Assigned Component Roles |
|---|---|---|
| `radius-xs` | 4px | Small inline code tags, micro-badges, tooltips |
| `radius-sm` | 6px | Checkboxes, compact table badges, step counters |
| `radius-md` | 10px | Primary buttons, text inputs, selects, textareas |
| `radius-lg` | 14px | Standard student cards, metric cards, dropdown menus |
| `radius-xl` | 20px | Feature panels, review dialog container, hero cards |
| `radius-2xl` | 28px | Hero landing container, warm educational banners |
| `radius-full` | 9999px | Avatars, filter pills, status indicator dots |

---

## 3. Elevation & Shadow System

ClassLens uses a soft, natural elevation system grounded in warm neutrals:

| Elevation Level | CSS Shadow Rule | Usage Context |
|---|---|---|
| **Elevation 0** | `none` (flat with 1px `border-default`) | Page background, nested inner cards, input fields |
| **Elevation 1** | `0 1px 3px rgba(16, 24, 43, 0.05), 0 1px 2px rgba(16, 24, 43, 0.03)` | Resting student cards, metric cards, review summary |
| **Elevation 2** | `0 4px 6px -1px rgba(16, 24, 43, 0.08), 0 2px 4px -1px rgba(16, 24, 43, 0.04)` | Hovered cards, active dropdowns, popovers |
| **Elevation 3** | `0 20px 25px -5px rgba(16, 24, 43, 0.12), 0 10px 10px -5px rgba(16, 24, 43, 0.04)` | Inspection modal dialog, audit trail drawer |

---

## 4. Layout Grid & Breakpoints

- **Max Content Width**: 1280px (Standard Dashboard & Insights)
- **Wide Workspace Width**: 1440px (Inspection Workspace)
- **Responsive Gutters**:
  - Desktop ($\ge 1024$px): 32px
  - Tablet ($768$px – $1023$px): 24px
  - Mobile ($< 768$px): 16px
- **Card Grid Composition**:
  - Mobile: 1 column
  - Tablet: 2 columns
  - Desktop: 4 columns (or 3 columns when sidebar expanded)
- **Section Spacing**: 32px to 48px between logical regions.
