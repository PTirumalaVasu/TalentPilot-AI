# Page Specification: HR Dashboard

## Overview
- **Purpose:** Let an HR Admin see, assign, monitor, and manage employee skill assignments.
- **URL:** `/hr/dashboard` (requires auth via `RequireAuth`)
- **Type:** Admin / data grid + modals
- **Source:** `frontend/src/pages/hr/Dashboard.tsx` + `frontend/src/features/dashboard/DashboardPage.tsx`

## Layout Structure (Desktop)

1. **Header** (`bg-white border-b`, sticky-feeling top bar)
   - Logo/wordmark "TalentPilot-AI"
   - Primary nav: "Dashboard" (active, blue underline) · "Skills" (dead link, `href="#"`)
   - User menu (right): avatar circle with initial + first name → click opens dropdown with "Sign Out"
2. **Main** (`px-6 pb-12`)
   - Toolbar: "+ New Assignment" button (opens AssignmentModal)
   - Title row: "Skill Assignments" (h2) + total count
   - Accordion grid grouped by employee name (alphabetical)
     - Each employee row: name + skill count, chevron toggle
     - Expanded panel: table (Assigned Skill, Status, Progress, Last Updated, Actions, Delete icon)
   - Pagination: Previous / current page / Next
   - Footer caption: "App v0.1.0"
3. **Modals** (portal-rendered, one at a time — mutually exclusive by design)
   - `AssignmentModal` — "Assign a New Skill" 3-step wizard
   - `ProvenanceDrillDownModal` — row detail + Mark-as-Ready / Reverse-Override
   - `DeleteAssignmentModal` — delete confirmation

## Component List

| Component | Location | Variant | Notes |
|---|---|---|---|
| User menu (inline, hand-rolled) | Header | open/closed | Duplicated implementation vs. Content Discovery's own copy — candidate for extraction |
| `Button` | Toolbar, modals | default/outline | |
| Accordion (hand-rolled, inline in `DashboardPage.tsx`) | Grid | expanded/collapsed per employee | Does **not** reuse the `ui/Accordion` primitive |
| `StatusBadge`-equivalent inline badges | Table rows | Not Started / In Progress(+%) / Completed | Table renders its own pill markup, not the shared `StatusBadge` component |
| `TrashIcon` (inline SVG) | Delete action | — | Hand-rolled, no icon library in the project |
| `AssignmentModal` | Toolbar trigger | 3-step + duplicate interstitial | See scenario-assign-new-skill.md |
| `ProvenanceDrillDownModal` | Row "View Details" | 4 provenance states + 2 confirm sub-views | See component notes below |
| `DeleteAssignmentModal` | Row delete icon | with/without recorded-progress warning | |
| `Toast` | Bottom-center | success messages | Fired from assignment created / deleted / provenance changed |
| aria-live region | Hidden, always mounted | — | Announces poll-driven row changes (status/provenance/percentage diffs) |

## Content Strategy
- Toolbar CTA: "+ New Assignment"
- Section title: "Skill Assignments", total shown as "Total: {n} assignment(s)"
- Employee group header: "{Name} ({n} skills)"
- Status pill text: "In Progress (n%)" / "Completed" / "Not Started"
- Staleness flag: red text + explicit day count (never color-only) when provenance is "Needs Attention"
- Success toasts: "✓ Skill assigned to {FirstName} — {SkillName}" (new assignment) · "{FirstName} — {SkillName} removed." (delete) · "{Name} marked as Ready for {Skill}." (override) · reversal-specific copy per underlying signal

## Responsive Behavior
Table/accordion layout has fixed column widths (`colgroup` with % widths) — no observed mobile-specific collapse; page assumes desktop/admin usage.

## Interactions
- Background poll every 12s (paused when tab hidden), diffs rows and announces changes via aria-live without disturbing loading/error UI
- Manual refetch on: New Assignment success, Delete success, Override change, page change, Retry
- Simultaneous-modal guard: opening one of the three modals force-closes the others
- Delete flow clamps pagination if the deleted row emptied the current page
- Row delete snapshot is captured at click time (not live-derived) so a concurrent poll/delete elsewhere can't blank the confirmation dialog

## Cross-References
Uses `Dialog`, `Combobox`, `FormErrorText`, `Toast`, `Button` from `ui/`. See `scenario-assign-new-skill.md` for the modal's full step flow.
