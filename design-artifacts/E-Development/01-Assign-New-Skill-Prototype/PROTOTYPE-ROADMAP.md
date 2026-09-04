# Scenario 01: Assign a New Skill - Prototype Roadmap

**Scenario**: Assign a New Skill (HR Admin)
**Pages**: HR Dashboard (host page + 3-step Assign modal)
**Device Compatibility**: Fully Responsive (375px - 1920px+)
**Design Fidelity**: Design System Components
**Last Updated**: 2026-09-03

---

## Scenario Overview

**User Journey**: An HR Admin (Rita) opens the HR Dashboard, clicks "+ New Assignment", and works through a 3-step wizard — pick an employee, pick a skill (with a duplicate-assignment check), review the AI-matched training content, then confirm — resulting in a new assignment appearing on the dashboard grid with a success toast.

Source of truth: `_bmad-output/planning-artifacts/scenarios/scenario-assign-new-skill.md` and `_bmad-output/planning-artifacts/specs/page-hr-dashboard.md` (from the Reverse Engineering activity).

**Pages in this Scenario**:
1. `hr-dashboard.html` — Host page: header/nav, toolbar, employee-grouped assignment table, entry point for the modal
2. Assign modal is a section of the same page (not a separate HTML file) — Step 1 (Employee) → Step 2 (Skill, + duplicate interstitial) → Step 3 (Review + Confirm)

---

## Device Compatibility

**Type**: Fully Responsive

**Reasoning**: Matches the real app's grid/card components, which already carry responsive Tailwind classes (`md:`, `lg:` prefixes), even though the Dashboard's own table is fixed-width in production. Chosen by the designer over Desktop-Only to validate how the assignment table and modal behave down to tablet width.

**Test Viewports**:
- Mobile (390px × 844px) — iPhone-class, lowest priority for this admin tool but included for completeness
- Tablet (768px × 1024px) — breakpoint validation
- Desktop (1440px × 900px) — primary target, matches real-world HR Admin usage

**Optimization Strategy**:
- ✅ Fluid table/accordion that reflows at `md:`/`lg:` breakpoints
- ✅ Modal stays centered and scrollable on short viewports
- ✅ Touch-friendly hit targets on the Combobox and buttons at tablet width
- ❌ No dedicated mobile-first redesign of the table (out of scope — matches production's admin-tool assumption)

**Tailwind Approach**: CDN Tailwind (`cdn.tailwindcss.com`) with an inline config extending the `talentpilot` brand color scale, matching `design-system.md`.

---

## Design Tokens (from `_bmad-output/planning-artifacts/design-system.md`)

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        talentpilot: { 50: '#eff6ff', 100: '#dbeafe', 500: '#2563eb', 600: '#1d4ed8', 700: '#1e40af' }
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }
    }
  }
}
```

**Design-system note carried into this prototype:** the real codebase inconsistently mixes `talentpilot-*` and Tailwind's default `blue-*` for the same role. This prototype standardizes on `talentpilot-*` throughout, per the extracted design system's recommendation — a deliberate, documented deviation from the current production code, not an oversight.

---

## Folder Structure

**HTML Files** (root level — double-click to open):
```
hr-dashboard.html
```

**Supporting Folders**:
- `shared/` — shared JS (demo data loader, small API-simulation helpers)
- `components/` — none yet (single-page scenario; add if a section is extracted for reuse)
- `pages/` — none yet
- `data/demo-data.json` — employees, skills, existing assignment (for duplicate demo), matched content per skill
- `stories/` — created just-in-time per section
- `work/` — `hr-dashboard-Work.yaml`, created before building starts

---

## Demo Data

**Source: the real backend seed data** (`backend/app/core/seeds.py` + `seed_ids.py`), not invented — same UUIDs, names, skills, and content as the actual dev database, so this JSON is a drop-in stand-in for the live API responses.

### `data/demo-data.json`
- `currentUser` / `employees[]` — Rita the Recommender (HR_ADMIN) + Casey, Morgan, Jordan, Sam (EMPLOYEE). Rita is deliberately included in the employee list too — `list_employees()` isn't role-filtered in the real backend, so she genuinely appears in the wizard's own Employee combobox.
- `skills[]` — the 5 real seeded skills (Data Visualization, Salesforce Admin, Python Programming, SQL & Databases, Communication Skills)
- `contentMatches{}` — one representative video per skill, pulled from that skill's real seeded content catalog (`_CONTENT_SEED_DATA`). Not a live similarity computation — the real match comes from pgvector cosine ranking, which a static prototype can't reproduce.
- `existingAssignments[]` — intentionally empty. The real backend seeds no Assignment rows either (only Employees/Skills/Content are pre-seeded), so the duplicate-found interstitial has nothing to trigger on a fresh load — demo it by assigning the same pair twice within a session, same as production.
- **Known gap**: all 5 real skills have a content match, so the "no approved content found yet" branch (Step 3) can't be demoed from seed data as-is. Still a real, spec'd code path — build it, just don't expect seed data to trigger it automatically.

---

## Prototype Status

| Page | Status | Sections | Last Updated | Notes |
|------|--------|----------|--------------|-------|
| HR Dashboard (View 1) | ✅ Complete & Approved | 7/7 planned sections + 2 scope additions (Provenance Drill-Down, Delete Confirm) | 2026-09-03 | "Overall admin dashboard looks good for me" |
| Assign New Skill Modal (View 2) | ✅ Built | 3-step wizard + real dropdown comboboxes | 2026-09-03 | No further issues reported after dropdown fix |
| Skills View (View 3) | ✅ Built | Implements epic-skill-catalog-management.md | 2026-09-03 | Pending user review |
| Content Discovery Mockup | ⚠️ Superseded | See "Inline Content Search + Approval Gate" below — replaced via /bmad-correct-course | 2026-09-03 | — |
| API Keys View + Add Skill Gate | ✅ Built (mockup) | Implements epic Story 1 — shared org-level key (revised via /bmad-correct-course from per-admin) | 2026-09-03 | Pending user review |
| Inline Content Search + Approval Gate | ✅ Built (simulated) | Implements epic Stories 2-3 (revised via /bmad-correct-course) — search-before-create, approve-at-least-one gates skill creation | 2026-09-03 | Pending user review |

**Status Legend:** ✅ Complete · 🚧 In Progress · ⏸️ Not Started · 🔴 Blocked

---

## ⚠️ Known Pattern to Avoid

**Never combine the native `hidden` attribute with a `flex`/`block`/`grid`/`inline-*` Tailwind class on the same element.** CSS cascade resolves by *origin* before specificity: the browser's default `[hidden]{display:none}` lives in the user-agent stylesheet, which is always beaten by an author stylesheet rule (Tailwind's generated `.flex{display:flex}`, etc.) of equal or lower specificity — regardless of the `hidden` attribute's actual state. An element with both will render as visible from first paint, permanently, no matter what JS does to the `hidden` property.

**Found in this prototype** (`hr-dashboard.html`): `#hr-dashboard-pagination` and `#hr-dashboard-drilldown-backdrop` both had this bug — fixed by using `style="display: none"` + `element.style.display = 'none' / 'flex'` in JS instead of the `hidden` attribute/property.

**Applies directly to View 2** (Assign New Skill Modal, not yet built): its Dialog backdrop will need the same `flex items-center justify-center` centering pattern — build its show/hide with `style.display` toggling from the start.

---

## Change Log

### 2026-09-03
- Prototype environment created (folder structure, demo data, this roadmap)
- Scenario: Assign a New Skill · Devices: Fully Responsive · Fidelity: Design System Components
- Demo data corrected to use real backend seed data (backend/app/core/seeds.py) instead of invented names
- Logical View Map created: View 1 (HR Dashboard) + View 2 (Assign Modal, 1 view/9 states)
- HR Dashboard Section 1 (Page Shell & Header) implemented and user-approved
- HR Dashboard Section 2 (Toolbar & Title Row) implemented and user-approved
- HR Dashboard Section 3 (Loading/Empty/Error) implemented; empty-by-default surfaced a real gap (no sample data to review against) — fixed by adding `sampleAssignments` to demo-data.json
- HR Dashboard Sections 4-5 (Accordion + Table Rows) built together, ahead of the planned sequential order, after user shared a screenshot of the real production dashboard and asked for it directly — awaiting re-test/approval

---

**Last Updated**: 2026-09-03
**Version**: 1.0
**Status**: In Development
