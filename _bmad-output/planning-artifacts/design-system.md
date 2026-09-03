# TalentPilot-AI — Extracted Design System

Source: `frontend/src/` (Tailwind CSS v4 + `tailwind.config.js`), reverse-engineered from the 4 in-scope pages and their shared components. Reflects the codebase **as observed**, including its inconsistencies — see Notes at the end before treating this as a target system.

---

## Design Tokens

### Colors

| Purpose | Token | Value | Notes |
|---|---|---|---|
| **Brand** | `talentpilot-50` | `#eff6ff` | Custom scale defined in `tailwind.config.js` |
| | `talentpilot-100` | `#dbeafe` | |
| | `talentpilot-500` | `#2563eb` | Focus rings (`focus-visible:ring-talentpilot-500`) |
| | `talentpilot-600` | `#1d4ed8` | Primary button, links, active nav state (Content Discovery, AssignmentModal) |
| | `talentpilot-700` | `#1e40af` | Hover/darker text variant |
| **Brand (shadow system)** | `blue-50…800` | Tailwind default | Used for the **same roles** as `talentpilot-*` in other places (Login link, Dashboard nav active state, stat tiles, progress bars) — not merged into one token. See Notes. |
| **Text** | `gray-900` | default | Primary text, headings |
| | `gray-700` | | Secondary text, form labels |
| | `gray-600` / `gray-500` | | Muted text, captions, timestamps |
| | `gray-400` | | Placeholder text, disabled |
| **Background** | `gray-50` | | Page body background (`index.css`) |
| | `white` | | Cards, headers, dialogs |
| | `gray-100` | | Skeleton loaders, hover surfaces, neutral pills |
| **Border** | `gray-200` / `gray-300` | | Card/table/input borders |
| **Feedback — error** | `red-50/200/300` bg/border, `red-600/700` text | | Form errors, delete actions, error banners |
| **Feedback — success** | `green-100` bg, `green-600/700/800` text, `green-500` fill | | Completed states, "Approved" badge |
| **Feedback — warning** | `amber-50` bg, `amber-700/800` text | | Duplicate-assignment warning, "Needs Attention" copy |
| **Feedback — in-progress (badge only)** | `yellow-100` bg, `yellow-800` text | | `StatusBadge`'s "In Progress" — inconsistent with the `blue-*`/`talentpilot-*` used for "in progress" everywhere else (progress bars, card badges) |

### Typography

Family: `Inter, system-ui, sans-serif` (`font-sans`, set via `tailwind.config.js`, applied to `body`). No custom type scale — pure Tailwind defaults.

| Level | Class | Weight | Usage |
|---|---|---|---|
| Display | `text-3xl` | `font-bold` | Page titles ("Assigned Skills") |
| H1 | `text-2xl` | `font-bold` / `font-black` | "HR Dashboard", "Skill Assignments" |
| H2 | `text-xl` | `font-semibold` | Modal titles |
| H3 | `text-lg` | `font-bold` / `font-semibold` | Card/section titles, drill-down headers |
| Body | `text-sm` | normal / `font-medium` | Default UI text, form labels, buttons |
| Caption / label | `text-xs` | `font-medium`, often `uppercase tracking-wide` | Stat tile labels, timestamps, sublabels |

No explicit `line-height` overrides found — relies on Tailwind's default leading per size.

### Spacing

Base unit: **4px** (Tailwind default scale, unmodified).

| Pattern | Value | Usage |
|---|---|---|
| Card padding | `p-4`–`p-8` | `p-8` for Login card, `p-4`–`p-5` for grid cards |
| Page/section padding | `px-6` | Header and main content horizontal padding |
| Stack rhythm | `space-y-4`, `gap-2`/`gap-4`/`gap-6`/`gap-8` | Forms, flex rows, grids |
| Table cell padding | `px-3 py-2` / `px-4 py-3` | Two slightly different conventions between Dashboard's inline table and `DashboardRow.tsx` (unused) |

### Other Tokens

| Token | Value | Usage |
|---|---|---|
| Border radius (default) | `rounded-lg` (8px) | Cards, buttons, inputs, dialogs, modals |
| Border radius (pill) | `rounded-full` | Avatars, status badges, progress-bar tracks |
| Shadow | `shadow-sm` | Cards, table containers |
| Shadow (elevated) | `shadow-lg` / `shadow-xl` | Dropdown menus, Dialog panel |
| Breakpoints | Tailwind defaults (`md:`, `lg:`) | No custom breakpoints defined |

---

## Components

### Button (`ui/button.tsx`)
- **Variants:** `default` (brand-filled), `outline` (bordered), `ghost` (transparent)
- **Sizes:** `default` (h-10), `sm` (h-9)
- **States:** default, hover, `focus-visible` (ring), `disabled` (opacity-50, pointer-events-none)
- **Content slots:** label text only (no icon slot; icons are inlined ad hoc where used, e.g. "▶ Play")

### Card / CardHeader / CardTitle / CardContent (`ui/card.tsx`)
- **Variants:** none — single style (`border border-gray-200 bg-white shadow-sm rounded-lg`)
- **Content slots:** free-form children; `CardContent` adds `p-6 pt-0`

### Input / Label (`ui/input.tsx`, `ui/label.tsx`)
- **States:** default, `focus-visible`, `disabled`
- **Content slots:** none beyond native input; validation state communicated externally via `aria-invalid` + adjacent `FormErrorText`

### FormErrorText (`ui/form-error-text.tsx`)
- **Variant:** single style, `role="alert"`, red text
- **Usage:** inline field errors, generic error banners

### Dialog (`ui/dialog.tsx`)
- **States:** open/closed (no open animation observed)
- **Behavior:** focus trap, Escape-to-close, backdrop-click-to-close, `aria-modal`
- **Content slots:** free-form children; caller supplies its own heading + `titleId` for `aria-labelledby`

### Toast (`ui/toast.tsx`)
- **Variant:** single style (dark pill, bottom-center)
- **States:** hidden (message === null) / visible
- **Behavior:** auto-dismiss after 4s (configurable), `role="status" aria-live="polite"`

### Combobox (`ui/combobox.tsx`)
- **States:** closed, open, loading, empty-results, option-active (keyboard), option-selected
- **Content slots:** label + optional sublabel per option
- **Behavior:** full keyboard nav (Arrow/Enter/Escape), click-outside-to-close

### Accordion / AccordionItem (`ui/accordion.tsx`)
- **States:** open/closed per item
- **Status:** defined but **unused** — `DashboardPage.tsx` reimplements equivalent behavior inline instead of consuming this primitive

### StatusBadge (`components/StatusBadge.tsx`)
- **Variants:** Not Started (gray, ○) / In Progress (**yellow**, ▶) / Completed (green, ✓)
- **Content slots:** icon + label, optional percentage suffix, optional `employeeName`/`skillName` for full aria-label context
- **Note:** a second, differently-colored status-badge implementation exists inline in `AssignmentCard.tsx` (blue for in-progress) and again inline in the Dashboard's own table markup — three renderings of the same concept, not unified

### AssignmentCard (`components/AssignmentCard.tsx`)
- **States:** with content / without content, Not Started / In Progress / Completed, keyboard-focusable
- **Content slots:** thumbnail (or fallback placeholder), title, source, duration, description, progress bar

### VideoPlayer (`components/VideoPlayer.tsx`)
- **States:** loading, ready (capture active), error (with retry)
- **Note:** inline styles, not Tailwind classes — visually inconsistent with the rest of the token system (hardcoded hex `#d32f2f`, `#666`, `#000` instead of `red-*`/`gray-*`)

### Feature-level compositions (not reusable primitives, cataloged for completeness)
- `AssignmentModal` — 3-step wizard shell, built from Dialog + Combobox + Button + FormErrorText
- `ProvenanceDrillDownModal` — detail view with 4 content branches by provenance state, built from Dialog + StatusBadge
- `DeleteAssignmentModal` — confirmation shell, built from Dialog
- User menu (avatar + dropdown) — implemented **twice independently** (Dashboard header, Content Discovery header) with identical visual output; no shared component

---

## Token-to-Component Mapping

| Component | Colors Used | Typography | Spacing | Border Radius |
|---|---|---|---|---|
| Button (default) | `talentpilot-600` bg → `talentpilot-700` hover, white text | `text-sm font-medium` | `px-4 py-2` (default) / `px-3` (sm) | `rounded-lg` |
| Card | `white` bg, `gray-200` border | inherits | `p-6` (CardContent) | `rounded-lg` |
| Input / Combobox trigger | `gray-300` border, `talentpilot-500` focus ring | `text-sm` | `px-3 py-2`, `h-10` | `rounded-lg` |
| Dialog panel | `white` bg, `black/40` backdrop | inherits from content | `p-6` | `rounded-lg` |
| Toast | `gray-900` bg, `white` text | `text-sm` | `px-4 py-2` | `rounded-lg` |
| StatusBadge | gray/yellow/green by state | `text-xs`/`text-sm` `font-medium` | `px-3 py-1` / `px-2.5 py-1` | `rounded` (not full, not `rounded-lg` — its own value) |
| AssignmentCard | `gray-200` border, `talentpilot-400` hover border | `text-sm`/`text-xs` | `p-5`, `gap-2` | `rounded-lg` (Card base) |
| VideoPlayer | inline hex (`#d32f2f`, `#666`, `#000`) — **not tokenized** | inline styles — **not tokenized** | inline `rem` values | `4px` inline (not `rounded-lg`) |

---

## Patterns

- **Loading:** `animate-pulse` skeleton blocks matching the shape of the eventual content (rows, tiles, cards) — used consistently except `VideoPlayer`, which uses plain text ("Loading player...")
- **Error + retry:** consistent shape across the app — icon/message + a `Button` or text-link labeled "Retry"/"Try again", never a silent failure
- **Empty state:** dashed border box + muted message, sometimes with a secondary hint line
- **Async staleness guards:** a recurring hand-rolled pattern (`requestIdRef` / token counters) across `DashboardPage`, `ProvenanceDrillDownModal`, `DeleteAssignmentModal`, `AssignmentModal`, `VideoPlayer` to discard out-of-order async responses — a de facto architectural convention, not a UI token, but worth knowing before building new async components
- **Never-color-only feedback:** status and staleness are always paired with text/icon, not color alone (explicit accessibility requirement referenced in code comments as "AC2"/"NFR-A2")

---

## Notes (read before using this as a target system)

1. **Two brand-blue systems coexist** (`talentpilot-*` custom scale vs. Tailwind's default `blue-*`) used interchangeably for the same semantic role across pages. Recommend consolidating to one before this feeds prototyping — decide which is canonical.
2. **`StatusBadge`'s "In Progress" is yellow**, while every other in-progress indicator (bars, card badges, Dashboard table pills) is blue. Likely a genuine inconsistency rather than an intentional distinction.
3. **Three separate status-badge implementations** (`components/StatusBadge.tsx`, inline in `AssignmentCard.tsx`, inline in `DashboardPage.tsx`'s table) — candidate for unification.
4. **`ui/Accordion` primitive is unused**; `DashboardPage.tsx` reimplements the same interaction inline. Candidate for either adopting the primitive or deleting it.
5. **User menu dropdown built twice** (Dashboard vs. Content Discovery headers) with no shared component.
6. **`VideoPlayer` doesn't use the token system at all** — inline styles with hardcoded hex colors and pixel values, the one visual outlier in an otherwise Tailwind-token-driven codebase.
7. Dead/unreachable code excluded from this extraction (per Step 2): `DashboardStub.tsx`, `DashboardRow.tsx`, `ContinueWatchingCard.tsx`.

**Consistent with page specs from Step 3** — every component and token referenced there is captured here.
