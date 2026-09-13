# Logical View Map — Scenario 06: Rita's Pulse Check

**Created:** 2026-09-13
**Confirmed by user:** 2026-09-13

**Note:** This folder hosts multiple scenarios (01/04/05/06) — see `PROTOTYPE-ROADMAP.md`'s 2026-09-13 update. This file is scenario-06-specific, named with the scenario prefix (unlike Scenario 01's un-prefixed `Logical-View-Map.md`, written before this folder became shared) to avoid collision.

---

## Views Identified

### View 1: Skill Assignment Dashboard

**File:** `06.1-Skill-Assignment-Dashboard.html` (single file for the whole scenario — only one page exists)

**Scenario steps mapped to this view:**
- **06.1** (the only step) — org-wide stats, Assignment Progress ring, Employee Segmentation pie chart, Needs Attention popover (on-page overlay, no separate route — same "overlay = same logical view" rule already established for 01.1/01.2)

**Why a single view:** Scenario 06 is deliberately a single-page scenario (see the scenario outline's Q8/Scenario Steps table) — the two drill-down exits (full grid, per-employee view) are owned by Scenario 01/page 01.1, not this view.

**States to implement:**
| State | Trigger |
|---|---|
| Default/Loaded | Data computed successfully from `demo-data.js` |
| Loading | Page opens, data not yet "returned" (simulated async, matches 01.1's pattern) |
| Empty | Zero active Employees or zero active Assignments in the dataset |
| Error | Simulated data-fetch failure |
| Needs Attention: Popover Open | Needs Attention segment clicked (only when count > 0) |
| Needs Attention: Popover Closed | Click outside, Escape, or navigate away |
| Needs Attention: Segment disabled | Count is 0 — not clickable, no popover |

**Object IDs involved:** `dashboard-*` (page content) + `app-nav-*` / `app-topbar-*` (shared shell, extended to 4 links) — see `06.1-skill-assignment-dashboard.md` for full tables.

**Design refs:**
- `../../../C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md`
- `../../../C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/Sketches/06.1-skill-assignment-dashboard-wireframe.png`

---

## Build Order

1. **Skill Assignment Dashboard** — only view in this scenario

---

## Notes

- Unlike Scenario 01, this scenario has no second page/modal to combine — it's genuinely one view, one state machine.
- The existing static HTML mock (built 2026-09-13, prior to this agentic-development pass) already has the correct structure/Object IDs/Tailwind classes; this pass replaces its hardcoded numbers and 3 static popover names with values computed from `data/demo-data.js`, and its `?demo_state=` URL toggle with real state logic (data-driven, matching 01.1's pattern — not a debug-only affordance).
