# ClassLens Design System — Interaction States & Micro-interactions

## 1. Interaction States Matrix

Every interactive element (Buttons, Links, Cards, Inputs, Tabs, Menus) must define all six standard lifecycle states:

| State | Visual Treatment | CSS / Token Expression | User Expectation |
|---|---|---|---|
| **Default** | Resting state, clear boundary, legible typography | `bg-surface-card border-border-default` | Component is available and waiting for input |
| **Hover** | Subtle elevation or 10% brightness shift, cursor: pointer | `bg-brand-primary-hover` or `border-border-strong` | Indicates interactive affordance |
| **Active / Pressed** | 20% deeper tint, resting elevation, no aggressive scale | `bg-brand-primary-active` | Confirms registration of user tap/click |
| **Focus-Visible** | 2px solid ring with 2px offset | `ring-2 ring-brand-primary ring-offset-2` | Clear positional awareness for keyboard users |
| **Disabled** | Muted surface (opacity 50%), cursor: not-allowed | `opacity-50 cursor-not-allowed pointer-events-none` | Prevents interaction, communicates unavailability |
| **Loading** | Spinner replaces or accompanies label, disabled clicks | `aria-busy="true"` + Spinner | Prevents duplicate submissions during async actions |

---

## 2. Micro-interaction Guidelines

1. **Duration & Easing**:
   - Micro-transitions (hover, background color, focus ring): `150ms ease-out`.
   - Structural transitions (dialog open, drawer slide, tab content switch): `200ms cubic-bezier(0.16, 1, 0.3, 1)`.
2. **Reduced Motion**:
   - When `@media (prefers-reduced-motion: reduce)` is active, all transitions and animations degrade to instant property switches (`transition: none !important; animation: none !important;`).
3. **Restraint Against Bouncing**:
   - Avoid physics-based bouncy springs or scaling transformations on cards and buttons. Educational tools demand steady, predictable visual stability.
