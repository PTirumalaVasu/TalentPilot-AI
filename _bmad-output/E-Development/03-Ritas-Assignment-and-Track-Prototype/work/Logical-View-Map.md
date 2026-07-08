# Logical View Map — Scenario 03: Rita's Assignment & Track

**Created:** 2026-07-08
**Confirmed by user:** 2026-07-08

---

## Views Identified

### View 1: Skills Dashboard (continued from Scenario 01)

**File:** `03-Skills-Dashboard.html` (duplicated starting point from Scenario 01's finished dashboard)

**Scenario steps mapped to this view:**
- **03.1** (new modal overlay) — Skill Assignment Flow, 3-step form, opens via `[+ New Assignment]`
- **03.2** (new states on existing view) — Toast/Confirmation + New Row Highlight after a successful assignment

**Why reused, not new:** 03.2's own spec says "Same as 01.1 - Skills Dashboard, plus..."; 03.1's entry/exit points are both the dashboard itself (modal, not a route change) — both are the "overlay/modal on existing page" reuse case, same rule that combined 01.1+01.2 in Scenario 01.

**States to implement (new, on top of the ones already built in Scenario 01):**
| State | Source | Trigger |
|---|---|---|
| Assignment Modal: Step 1 (Employee) | 03.1 | `[+ New Assignment]` clicked |
| Assignment Modal: Step 2 (Skill) | 03.1 | Employee selected |
| Assignment Modal: Step 3 (Content Review) | 03.1 | Skill selected, content auto-linked |
| Assignment Modal: Loading | 03.1 | Employee/skill/content lists fetching |
| Assignment Modal: Empty (no content match) | 03.1 | No approved content found for skill |
| Assignment Modal: Error | 03.1 | List fetch fails |
| Dashboard: Toast confirmation | 03.2 | After successful [Assign] |
| Dashboard: New row highlight | 03.2 | New row rendered |

**Already built (Scenario 01, carried over via duplication):** Dashboard Loaded/Loading/Empty/Error, Provenance Drill-Down modal Open/Loading/Error/Closed.

**Design refs:**
- `../../C-UX-Scenarios/03-ritas-assignment-and-track/03.1-skill-assignment-flow/03.1-skill-assignment-flow.md`
- `../../C-UX-Scenarios/03-ritas-assignment-and-track/03.2-assignment-confirmation-and-auto-update/03.2-assignment-confirmation-and-auto-update.md`

---

## Build Order

1. **Skill Assignment Flow modal** (03.1) — the new interaction that everything else depends on
2. **Toast + New Row Highlight** (03.2) — the result of completing step 1

---

## Notes

- This is the third and final scenario in the POC scope — once this view's new sections are built, all 3 scenarios (01, 02, 03) will have working prototypes.
- No new HTML files needed — everything extends `03-Skills-Dashboard.html`.
