# ClassLens Design System — Color Tokens & Usage Rules

## 1. Color Palette Tokens

### 1.1 Brand Palette

| Token Name | Hex Code | Contrast on `#FFFFFF` | Primary Application |
|---|---|---|---|
| `brand-primary` | `#5145F5` | 5.25:1 (AA Pass) | Primary action buttons, active navigation items, focus rings |
| `brand-primary-hover` | `#4035D5` | 6.84:1 (AAA Pass) | Hover state for primary actions |
| `brand-primary-active` | `#3026B5` | 8.89:1 (AAA Pass) | Active/pressed state for primary actions |
| `brand-primary-soft` | `#EEECFF` | 1.18:1 (Bg token) | Active navigation background, secondary button surfaces |
| `brand-coral` | `#F76543` | 3.12:1 (Ui token) | Marketing call-to-actions, hero highlights, accent vectors |
| `brand-coral-hover` | `#D94D2D` | 4.62:1 (AA Pass) | Hover state for coral CTA buttons |
| `brand-yellow` | `#FFCF78` | 1.45:1 (Bg token) | Hero warm sections, sticky notes, card highlights |
| `brand-yellow-soft` | `#FFF3D6` | 1.12:1 (Bg token) | Educational callout backgrounds, pending review badge bg |
| `brand-mint` | `#D8F4E8` | 1.15:1 (Bg token) | Soft success cards, formative assessment activity containers |
| `brand-blue` | `#3D91F5` | 3.25:1 (Ui token) | Informational accents, secondary metrics |
| `brand-purple-soft` | `#F1ECFF` | 1.15:1 (Bg token) | AI insights card backgrounds, subtle highlight sections |

### 1.2 Neutral & Surface Palette

| Token Name | Hex Code | Contrast on `#FFFFFF` | Primary Application |
|---|---|---|---|
| `ink-primary` | `#10182B` | 16.5:1 (AAA Pass) | Headings, primary text, high-emphasis icons |
| `ink-secondary` | `#475569` | 7.12:1 (AAA Pass) | Subtitles, descriptions, supporting form labels |
| `ink-muted` | `#64748B` | 4.65:1 (AA Pass) | Metadata, table timestamps, secondary IDs |
| `surface-page` | `#F7F9FC` | 1.05:1 (Page Bg) | Default background of web app views |
| `surface-card` | `#FFFFFF` | Base Surface | Elevated cards, dialog surfaces, table rows |
| `surface-warm` | `#FFF9ED` | 1.04:1 (Warm Bg) | Hero landing section, warm pedagogical callouts |
| `surface-subtle` | `#F1F5F9` | 1.12:1 (Subtle Bg)| Secondary card backgrounds, code snippets, search inputs |
| `border-default` | `#DDE4ED` | 1.34:1 (Border) | Standard card and input perimeter borders |
| `border-strong` | `#B7C3D4` | 1.82:1 (Border) | Active card outlines, divider lines, focus offsets |

### 1.3 Semantic State Palette

| Semantic State | Foreground (Text / Icon) | Background Surface | Border Token | Usage Context |
|---|---|---|---|---|
| **Success** | `#087A53` (5.8:1) | `#E7F8EF` | `#A3E7C8` | Verified mathematical correctness, approved diagnosis |
| **Error** | `#B42332` (6.2:1) | `#FFF0F1` | `#FECDCA` | Procedural error detected, rejected input, destructive action |
| **Warning** | `#925300` (5.4:1) | `#FFF2D6` | `#FEDF89` | Pending review, unreadable handwriting flag, warning callout |
| **Information** | `#175CD3` (5.9:1) | `#EAF3FF` | `#B2DDFF` | Informational guides, SymPy verification badge, metadata |
| **Neutral** | `#475569` (7.1:1) | `#F1F5F9` | `#DDE4ED` | Unreviewed item, unverified response, default pill |

---

## 2. Color Usage Rules

1. **Purple is strictly interactive**: Purple (`#5145F5`) denotes clickable actions, active tabs, and primary controls. It must never be used to signify correctness, error, or warning.
2. **Never communicate status by color alone**: Every badge, card, and indicator must pair its background/border color with an explicit semantic icon (e.g. Check, AlertTriangle, XCircle) and clear textual label.
3. **Contrast Enforcement**: All text displayed on soft backgrounds (e.g. `#E7F8EF`, `#FFF0F1`, `#FFF2D6`) must use the hardened semantic foreground token (`#087A53`, `#B42332`, `#925300`) to guarantee $\ge 4.5:1$ contrast against both the tint and white surfaces.
4. **No Hardcoded Hex Values**: All application styles must reference either Tailwind theme tokens (`bg-brand-primary`, `text-ink-primary`) or CSS custom properties (`var(--brand-primary)`).
