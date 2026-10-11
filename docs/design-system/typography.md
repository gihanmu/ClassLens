# ClassLens Design System — Typography Specification

## 1. Font Families

### Primary Font: Plus Jakarta Sans
Used for:
- Marketing headlines & hero banners
- Dashboard headings and subheadings
- Navigation labels and tab titles
- Buttons, form controls, and card content
- Teacher explanations and pedagogical feedback

Fallback stack:
```css
font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Technical & Monospace Font: IBM Plex Mono
Used for:
- Student response identifiers (`resp_80545ef3`)
- Number line coordinate values and displacement vectors ($\Delta = -6$)
- Verification hash digests and audit timestamps
- Monospace step arithmetic annotations

Fallback stack:
```css
font-family: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
```

---

## 2. Type Scale

| Level | Desktop Size / Leading | Mobile Size / Leading | Weight | Tracking | Primary Usage |
|---|---|---|---|---|---|
| **Display** | 56px / 1.08 (60px) | 38px / 1.15 (44px) | 800 (Extrabold) | -0.025em | Landing hero headline |
| **H1** | 40px / 1.15 (46px) | 30px / 1.20 (36px) | 800 (Extrabold) | -0.02em | Page title (Dashboard, Cohort) |
| **H2** | 30px / 1.20 (36px) | 25px / 1.25 (32px) | 700 (Bold) | -0.015em | Major section headers, modal title |
| **H3** | 24px / 1.30 (32px) | 21px / 1.30 (28px) | 700 (Bold) | -0.01em | Subsections, card group titles |
| **H4** | 20px / 1.35 (28px) | 18px / 1.35 (24px) | 700 (Bold) | -0.005em | Card headers, metric values |
| **Body Large** | 17px / 1.60 (28px) | 16px / 1.60 (26px) | 400 (Regular) | 0 | Hero subtext, executive summaries |
| **Body** | 15px / 1.55 (24px) | 15px / 1.55 (24px) | 400 (Regular) | 0 | Default explanations, descriptions |
| **Body Small** | 13px / 1.50 (20px) | 13px / 1.50 (20px) | 400 (Regular) | 0 | Secondary descriptions, helper text |
| **Label** | 13px / 1.40 (18px) | 13px / 1.40 (18px) | 600 (Semibold) | +0.01em | Form labels, button text, table headers |
| **Caption** | 12px / 1.40 (16px) | 12px / 1.40 (16px) | 500 (Medium) | +0.02em | Badges, tags, timestamps, metadata |

---

## 3. Typographic Hierarchy & Content Rules

1. **Heading Hierarchy**: Every page has exactly one `<h1>` tag. Subsequent sections nest hierarchically (`<h2>` -> `<h3>` -> `<h4>`) without skipping levels.
2. **Readability & Measure**: Maximum line width for continuous text is 65–75 characters (approx. 640px) to prevent eye fatigue.
3. **Restricted All-Caps**: Never use uppercase for body copy or card titles. All-caps is restricted exclusively to small badge identifiers (e.g. `MISC-ARITH-OFF-BY-ONE` in secondary metadata) or category labels with letter-spacing `tracking-wider`.
4. **Mathematical Expressions**: Expressions should be presented clearly (e.g. `Evaluate -6 + 12 - 4 using the number line`). Clean typography and vector diagrams are preferred over raw monospace strings when presenting to teachers.
