# ClassLens Design System — Foundations & Philosophy

## 1. Design Principles

### Principle 1: Clarity Before Decoration
A teacher in a busy classroom should understand the screen state within five seconds. Visual embellishments (pastels, doodles, illustrations) must never compete with student handwritten evidence, mathematical steps, or review actions. Every decorative element frames or clarifies information rather than obscuring it.

### Principle 2: Warm but Credible
ClassLens moves away from cold, sterile developer dashboards. It adopts a warm, welcoming educational identity—inspired by physical classroom workbooks, friendly vector characters, and tactile paper cards—balanced with the mathematical rigor of formal SymPy verification.

### Principle 3: Consistent Interaction Language
An action, state, and component looks and behaves identically across every screen. Primary actions always use Brand Purple (`#5145F5`), destructive or error states always use Crimson Error (`#B42332`), and verified pedagogical success always uses Mint/Emerald Green (`#087A53`).

### Principle 4: Evidence-First Presentation
Original handwritten student work is the primary source of truth. AI-generated interpretations, candidate hypotheses, and mathematical verifications are presented as structured hypotheses that are visually distinct from the student's authentic marks.

### Principle 5: Accessible by Default
Every component is engineered with WCAG 2.2 AA compliance:
- Minimum 4.5:1 text contrast for body text, 3:1 for large text and graphical controls.
- Keyboard navigation with visible, high-contrast focus rings (`outline: 2px solid var(--brand-primary)` with 2px offset).
- Non-color status indicators (every status includes an icon, label, and accessible aria attributes).
- Semantic HTML and WAI-ARIA role patterns.

### Principle 6: Responsive by Architecture
Layouts reflow intelligently using CSS Grid and Flexbox:
- Desktop: Wide workspaces, dual-pane review panels, persistent navigation.
- Tablet: Two-column adaptive grids with touch-optimized controls.
- Mobile: Tabbed linear layouts, bottom action sheets, 44×44px minimum touch targets, and zero horizontal scroll overflow.

---

## 2. Visual Reference Alignment

ClassLens derives its visual identity directly from `docs/wireframes/mockup.png` and `apps/web/public/logos/logo.png`:
- **Brand Emblem**: Optical lens icon combined with a math assignment paper featuring number line jumps ($-6, +12, -4$).
- **Hero Palette**: Soft warm cream (`#FFF9ED`), brand purple (`#5145F5`), playful coral (`#F76543`), cheerful yellow (`#FFCF78`), calming mint (`#D8F4E8`), and clear educational blue (`#3D91F5`).
- **Surface Elevation**: Restrained borders (`#DDE4ED`), soft resting card shadows (`0 1px 3px rgba(16, 24, 43, 0.05)`), and clean elevation steps without aggressive gradients or 3D skeuomorphism.
