# Logical View Map — Scenario 01: Rita's Trust Call

**Created:** 2026-07-08
**Confirmed by user:** 2026-07-08

---

## Views Identified

### View 1: Skills Dashboard

**File:** `01.1-Skills-Dashboard.html` (single file for the whole scenario)

**Scenario steps mapped to this view:**
- **01.1** (base page) — dashboard grid, provenance-labeled rows
- **01.2** (modal overlay) — Provenance Drill-Down, opened on top of 01.1 via JS, no page navigation

**Why combined:** 01.2's own spec declares "Type: Modal Overlay (no separate route)" and exits back to 01.1 on close (X / Escape / click-outside). Per the logical-view rule, an overlay/modal on an existing page is the same logical view as its host page, not a new one.

**States to implement:**
| State | Source | Trigger |
|---|---|---|
| Default/Loaded | 01.1 | Grid data fetched successfully |
| Loading | 01.1 | Page opens or pagination clicked, data not yet returned |
| Empty | 01.1 | No assignments exist |
| Error | 01.1 | Grid data fetch fails |
| Modal: Open | 01.2 | Drill-down arrow clicked on a row |
| Modal: Loading | 01.2 | Modal opens, raw signal data not yet returned |
| Modal: Error | 01.2 | Raw signal data fetch fails |
| Modal: Closed | 01.2 | X / Escape / click-outside |

**Object IDs involved:** `skills-dashboard-*` (dashboard) + `assignment-details-*` (modal) — see the retrofitted page specs for full tables.

**Design refs:**
- `../../C-UX-Scenarios/01-ritas-trust-call/01.1-assignment-dashboard/01.1-assignment-dashboard.md`
- `../../C-UX-Scenarios/01-ritas-trust-call/01.2-provenance-drill-down/01.2-provenance-drill-down.md`

---

## Build Order

1. **Skills Dashboard** (with embedded Provenance Drill-Down modal) — only view in this scenario

---

## Notes

- No second HTML file needed for this scenario — corrects the initial `PROTOTYPE-ROADMAP.md` draft, which listed 01.1 and 01.2 as two separate files.
- Scenarios 02 and 03 (not yet in scope for this prototype pass) will each introduce their own new logical views — Content Discovery, Continue Watching, Skill Assignment Flow (modal, but a *new* page's modal — not reusing this one), and the Assignment Confirmation view (an updated state of this same Skills Dashboard view, worth revisiting when that scenario is prototyped).
