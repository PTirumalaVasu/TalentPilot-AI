# Logical View Map — Scenario 01: Assign a New Skill

**Confirmed by user**: 2026-09-03
**Source specs**: `_bmad-output/planning-artifacts/scenarios/scenario-assign-new-skill.md`, `_bmad-output/planning-artifacts/specs/page-hr-dashboard.md`, verified directly against `frontend/src/features/dashboard/DashboardPage.tsx` and `frontend/src/features/assignments/AssignmentModal.tsx`

---

## View 1: HR Dashboard (Grid)

**Purpose**: Host page — browse and manage skill assignments; entry point and landing point for this scenario.

**Structure** (from `page-hr-dashboard.md`): Header (logo, nav, user menu) → Toolbar ("+ New Assignment") → Title/count row → employee-grouped accordion+table → pagination.

**States**:
| State | Trigger | Notes |
|---|---|---|
| Loading | Initial mount / manual retry | Skeleton rows |
| Loaded (with data) | Default | Accordion grid, grouped by employee |
| Empty | Zero assignments | Dashed-border empty message |
| Error | Fetch failure | Error message + Retry |
| Assignment-created (toast) | After Assign New Skill Modal succeeds | "✓ Skill assigned to {FirstName} — {SkillName}", grid refetches |

**Scenario steps mapped here**: Entry (before "+ New Assignment" click), Exit (after Step 3 "Assign" succeeds and modal closes)

---

## View 2: Assign New Skill Modal

**Purpose**: 3-step wizard for creating a new assignment, overlaying View 1.

**Why one view, not three**: Confirmed directly from `AssignmentModal.tsx` source — a single `Dialog`-based component driven by one `step: 1 | 2 | 3` state variable, not three separate modal components. All sub-states below are conditional renders inside the same component.

**Structure** (base): `Dialog` shell (focus-trap, Esc, backdrop-click) → step-conditional content → footer action buttons (Cancel/Back/Continue vary per step)

**States**:
| State | Step | Trigger | Notes |
|---|---|---|---|
| Employee selection | 1 | Modal opened | `Combobox` — loading / populated from `employees[]` (incl. Rita, HR_ADMIN, per real `list_employees()` behavior) |
| Skill selection | 2a | [Continue] from Step 1 | `Combobox` — loading / populated from `skills[]` |
| Duplicate-found interstitial | 2b | Duplicate check returns a match | Amber warning + [View] / [Assign Again] |
| Content loading | 3a | Advancing past Step 2 (no duplicate, or Assign Again) | Skeleton |
| Content-fetch error | 3b | `matchContentForSkill` fails | Error + [Retry] |
| Content found (review) | 3c | Match returned | Thumbnail/title/source/duration/description + Assignment Summary |
| No content found | 3d | Match returns null (not reachable with current seed data — see `demo-data.json`'s `noContentMatchCase` note) | "No approved content found yet" + [Assign without content] |
| Submitting | 3 (any) | [Assign] clicked | Buttons disabled, label → "Assigning…" |
| Submit error | 3 (any) | `createAssignment` fails | Inline error, stays on Step 3 |

**Scenario steps mapped here**: All three steps of `scenario-assign-new-skill.md` (Step 1, Step 2, Step 3) map to this one logical view, differentiated by state, not by separate views.

---

## Build Order

1. **View 1 — HR Dashboard shell** first: gives the modal a trigger ("+ New Assignment") and a place to land the success toast + refreshed grid. Built to Loaded/Empty/Error states; the "Assignment-created" toast state is wired once View 2 exists.
2. **View 2 — Assign New Skill Modal**, state-by-state in this order (matches the wizard's own natural sequence, each state buildable/testable independently):
   1. Step 1 (Employee)
   2. Step 2a (Skill)
   3. Step 2b (Duplicate interstitial)
   4. Step 3a/b (Content loading/error)
   5. Step 3c/d (Content found / no content)
   6. Submit (loading/error/success → closes modal, hands off to View 1's toast state)

## View 3: Provenance Drill-Down Modal (added 2026-09-03, scope addition)

**Not part of the original plan.** Added mid-build after the user shared a reference screenshot of the real `ProvenanceDrillDownModal.tsx` and asked for it directly — see `stories/HR-Dashboard.8-provenance-drilldown.md` for full detail. Opened from View 1's "View Details" link (previously a console-only placeholder).

**States built**: read-only detail view only, across 5 provenance branches (Verified / Self-reported / Needs Attention / HR Override / Not Started). Mark-as-Ready/Reverse-Override confirm sub-states are explicitly not built yet (see that story's Out of Scope section).

## View 4: Delete Confirmation Modal (added 2026-09-03, scope addition)

**Not part of the original plan.** Added after user feedback that delete had no confirmation step, matching real production's `DeleteAssignmentModal.tsx` — see `stories/HR-Dashboard.9-delete-confirmation.md`. Opened from a row's trash icon (previously an immediate, unconfirmed delete).

## Notes

- No third logical view was originally needed for "duplicate interstitial" or any Step 3 sub-state — all are states of View 2, not new views, per the workflow's own "overlay/modal on existing page = same view, different state" rule extended here to sub-states within one already-overlaid modal. View 3 above is a genuine addition, not a reclassification of an existing view.
- Demo data gaps (no seeded Assignments → duplicate case must be produced interactively; no skill lacks a content match → state 3d needs a manual data tweak to demo) are already documented in `data/demo-data.json` and `PROTOTYPE-ROADMAP.md` — carried forward here so Step 3 (section breakdown) doesn't re-discover them.
