# Story HR-Dashboard.10: Skills View (implements epic-skill-catalog-management.md)

**View**: HR Dashboard — new third view (Dashboard / Skills), reached via the header's "Skills" nav
**Implements**: `_bmad-output/planning-artifacts/epics/epic-skill-catalog-management.md` — Story 0 (Skills Tab Navigation, added retroactively — see Update below), Story 1 (View the Skill Catalog), and Story 2 (Add a New Skill, since superseded by `HR-Dashboard.13-inline-content-approval.md`)

---

## 🔄 Update: Story 0 added retroactively

The `mainView` state variable + `switchMainView()` function built here (originally described only as part of Story 1's "click Skills, see the catalog" AC) was later split out into its own explicit **Story 0: Add a Working Skills Tab to the Header Navigation** in the epic — the navigation/view-switching mechanism is a distinct enough unit of work (and the foundation every other Skills-tab story depends on) to warrant its own AC, rather than staying implicit inside Story 1's scope. No code changed for this — it's the same implementation, just now explicitly documented as its own story.

---

## ⚠️ Process Note

The "Skills" nav link was a deliberate dead link (`href="#"`, no destination) — captured that way from real production during Reverse Engineering, and explicitly documented in `HR-Dashboard.1-page-shell-header.md`'s edge cases as "not a bug to fix in this prototype." The user later asked to build it out for real; that request was first turned into an Epic + 2 Stories (`epic-skill-catalog-management.md`) before implementation, per explicit instruction to plan before coding. This story implements both.

---

## 📋 What Was Built

**Third page mode**: `#hr-dashboard-view-dashboard` (existing Sections 2-7, now wrapped in a container) and `#hr-dashboard-view-skills` (new), toggled by `switchMainView('dashboard' | 'skills')` — same single-page-swap pattern already used in Content Discovery's grid/video modes. Nav active/inactive classes swap between "Dashboard" and "Skills" to match.

**Story 1 (View the Skill Catalog)**: Skills view shows a card grid of every skill (name + description) and a live total count. Empty state ("No skills yet — add one above") if the catalog is ever emptied — not reachable today since it starts with the 5 real seeded skills, but handled rather than left to break.

**Story 2 (Add a New Skill)**: name + optional description inputs, "+ Add Skill" button. Validates a non-empty name (inline error, matches the FormErrorText pattern used elsewhere in this prototype), pushes the new skill into the **shared `skills` array**, re-renders the list + count, shows the same toast/aria-live pattern as every other action in this file.

**Shared catalog (Story 2, AC3)**: `let skills` is now the single source read by both the Skills view and the Assign modal's `filteredSkills()` / skill lookups (previously those read `window.DEMO_DATA.skills` directly) — a skill added via the Skills tab is immediately selectable in "+ New Assignment" without a page reload.

---

## 🚫 Explicitly Out of Scope (per the epic's own Notes)

- **No persistence** — `skills` is an in-memory array; added skills vanish on refresh. No backend to persist to.
- **No edit or delete** of skills — matches the epic's literal scope (view + add only).
- **No duplicate-name validation** — not specified in the epic; flagged there as a decision needed before real implementation.

---

## ✅ Acceptance Criteria (traced to the epic)

| # | Criterion (from epic) | Result |
|---|---|---|
| 1 | Clicking "Skills" shows the catalog, "Dashboard" no longer active | ✓ `switchMainView` toggles both view containers and nav classes |
| 2 | Total skill count shown | ✓ `renderSkillsCount()` |
| 3 | Clicking "Dashboard" returns to the assignment grid, active state restored | ✓ same function, `view === 'dashboard'` branch |
| 4 | Adding a skill with a name shows it immediately + updates count | ✓ `addNewSkill()` → `renderSkillsList()` |
| 5 | Empty name blocked with a validation message | ✓ inline error, no push to `skills` |
| 6 | New skill selectable in the Assign wizard | ✓ `filteredSkills()`/`submitAssignment()`/`renderAssignModal()` all now read the shared `skills` array |
| 7 | No `hidden`+`flex` bug, no duplicate IDs, no syntax errors | ✓ full-file scan clean |

### User-Evaluable (Qualitative — needs your eyes)

- [ ] Skills view layout looks consistent with the rest of the dashboard
- [ ] Add-a-skill flow feels smooth (focus returns to the name field after adding, ready for the next one)
- [ ] Try adding a skill, then immediately open "+ New Assignment" → Step 2 → confirm it's in the list

---

## 📊 Status

**Status**: ✅ Built, pending user review
**Started / Completed**: 2026-09-03
