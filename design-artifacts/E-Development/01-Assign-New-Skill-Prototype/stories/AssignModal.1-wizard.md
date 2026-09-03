# Story AssignModal.1: Assign a New Skill — 3-Step Wizard

**View**: View 2 — Assign New Skill Modal (defined in `Logical-View-Map.md`, built now)
**Trigger**: "+ New Assignment" button (previously a placeholder toast, per user feedback: "New assignment button not functioning")

---

## 🎯 Goal

Build the full 3-step wizard defined in `Logical-View-Map.md` since it's this scenario's actual objective — matching real production `AssignmentModal.tsx` exactly, using this session's live `assignments` state for a real duplicate check and `DEMO_DATA.contentMatches` for content review.

---

## 📋 What Was Built

**Step 1 — Employee**: Searchable list (typed filter, not the real Combobox's full keyboard-nav — see Out of Scope) of `DEMO_DATA.employees` (includes Rita, HR_ADMIN, labeled accordingly — same fidelity note as the dashboard's own employee data). Continue disabled until selected.

**Step 2 — Skill**: Same pattern against `DEMO_DATA.skills`. On Continue: **real duplicate check** — `assignments.some(a => a.employee_id === X && a.skill_id === Y)` against this session's actual assignment state (seeded sample rows + anything created this session). If found → amber interstitial ("This skill is already assigned to {employee}.") with View/Assign Again, matching production exactly.

**Step 3 — Content Review + Confirm**: Simulated async fetch (400ms) of `DEMO_DATA.contentMatches[skillId]` — loading skeleton → found (thumbnail, title, source, duration, description, "✓ Approved") or not-found ("No approved content found yet"). Assignment Summary block (Employee/Skill/Content/Date/Status). Assign button submits (500ms simulated), pushes a new row into the live `assignments` array with `status: "Not Started"`, `provenance: "Not Started"`, closes the modal, refreshes the grid/count, and shows the exact real toast copy: `"✓ Skill assigned to {FirstName} — {SkillName}"`.

### Duplicate demo now reachable
`data/demo-data.json`'s `_existingAssignments_note` flagged that the duplicate interstitial had nothing to trigger against with an empty grid. Now that `sampleAssignments` seeds real rows (Casey already has Data Visualization and SQL & Databases), **selecting Casey + Data Visualization in the wizard genuinely triggers the duplicate interstitial** — no fabricated fixture needed, exactly as that note predicted.

---

## 🚫 Explicitly Out of Scope

- **No content match branch**: still unreachable from real seed data (all 5 skills have a match) — same documented gap as before, now genuinely testable only by editing `demo-data.json`.
- Built with `style.display` from the start (learned from the Section 8 bug) — no `hidden`+`flex` risk here.
- Full ARIA `role="combobox"`/`listbox`/`aria-activedescendant` wiring and Arrow-key option navigation are not implemented — the dropdown opens/closes/filters/selects correctly (see below) but isn't a byte-for-byte accessibility match to the real component yet.

## 🔄 Update: real dropdown behavior (user feedback: "we need a dropdown menu")

**Problem**: Initial build showed an always-visible filtered list under each input, never closing — not an actual dropdown.

**Fix**: Both Employee (Step 1) and Skill (Step 2) now behave as real comboboxes, matching `components/ui/combobox.tsx`:
- Closed by default; opens on focus or on typing
- Input displays the *selected* option's label once chosen (not raw search text), same as the real component's `value={selected ? selected.label : searchValue}`
- Selecting an option closes the dropdown and fills the input
- Clicking outside the combobox closes it (document-level listener, container-scoped via `.contains()`)
- Escape closes an open dropdown first, not the whole modal (matches the real component's `stopPropagation` behavior) — only closes the modal itself if no dropdown is open
- Options use `onmousedown` + `preventDefault()`, not `onclick` — same reason as the real component: mousedown fires before the input's blur, so the click actually registers instead of the list closing first

**Implementation note**: since `renderAssignModal()` replaces the modal body's `innerHTML` on every keystroke (destroying and recreating the `<input>`), a `refocusInput()` helper explicitly refocuses and restores cursor position after each re-render — without it, typing more than one character would lose focus after the first keystroke.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|---------------|
| 1 | Modal hidden via `style="display:none"`, not the `hidden` attribute | grep |
| 2 | "+ New Assignment" opens it | Code read: `handleNewAssignmentClick` → `openAssignModal` |
| 3 | Duplicate check reads from the live `assignments` array | Code read: `continueFromStep2` |
| 4 | Submit pushes a real row and triggers the exact production toast copy | Code read: `submitAssignment` |
| 5 | No duplicate object IDs anywhere in the file | Full-file uniqueness scan |
| 6 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative — this is the main ask)

- [ ] Full flow: Step 1 → Step 2 → Step 3 → Assign → toast → new row appears in the grid
- [ ] Duplicate path: try Casey the Continuer + Data Visualization → confirm the amber interstitial appears
- [ ] Cancel/Back at each step behaves sensibly

---

## 📊 Status Tracking

**Status**: ✅ Complete, pending user re-test
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Pending
**Notes**: This completes View 2 from the original Logical-View-Map.md — not a scope addition, the scenario's actual second planned view, built after View 1's sections and their follow-up fixes.
