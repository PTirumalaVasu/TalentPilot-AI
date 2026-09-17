---
baseline_commit: 60607d47
---

# Story 10.3: Delete/Archive Icon Reflects the Real Action Before the Click

Status: done

## Story

As an **HR Admin**,
I want the roster's Delete/Archive icon to visually show whether an Employee will be archived or truly removed before I click it,
So that I'm never surprised by which behavior happens (items #4/#5 of the Sprint Change Proposal, extends FR-27).

## Acceptance Criteria

1. **Given** `EmployeesPage.tsx`'s existing single Delete/Archive icon (currently one icon regardless of `has_assignment_history`)
   **When** this story ships
   **Then** the icon and its `aria-label`/`title` differ based on `employee.has_assignment_history` (already returned by the roster API, `EmployeeResponse.has_assignment_history`) — an Archive-style icon + "Archive {name}" label when `true`, a Delete-style icon + "Delete {name}" label when `false`, decided the same way `DeleteArchiveEmployeeModal.tsx` already branches its copy

2. **Given** `delete_or_archive_employee_service` (`backend/app/employees/service.py`) and `DeleteArchiveEmployeeModal.tsx`
   **When** this story is implemented
   **Then** neither's existing logic changes — `has_assignment_history` → archive, zero history → hard delete (FR-27) is already correct; this story is icon/label presentation only

3. **And** this story requires no new endpoint, schema, or migration — `has_assignment_history` is already present on every roster response row (confirmed: `employeesApi.ts::EmployeeResponse.has_assignment_history: boolean`, populated server-side by `employees/service.py::_build_employee_response`). **No backend code changes at all.**

4. **Given** the row-action icon-button set on the Employees, Skills, and Skill Assignments pages (Edit, Regenerate Password, View, Delete, Archive)
   **When** they render
   **Then** two visual tiers apply consistently across all three pages (locked during mockup-building, 2026-09-15, per direct request — "employee page delete button is not sync with the other pages and also show some difference between the Archive and Delete buttons"): routine/non-destructive actions (Edit, Regenerate Password, View) render as a neutral-gray `w-8 h-8` circular icon-button that only tints on hover; the two row-removing actions (Archive, Delete) render with a permanently-visible tinted pill instead of a hover-only cue — amber for Archive, red for Delete — so the two are distinguishable from each other and from the safe actions without requiring a hover

## Tasks / Subtasks

- [x] Task 1: Employees page — Archive-vs-Delete icon/label branch (AC: 1, 4)
  - [x] `frontend/src/pages/hr/EmployeesPage.tsx`'s `RowActions` component: replace the single `✕`/"Delete/Archive" button with a branch on `employee.has_assignment_history` — `true` renders an Archive icon (🗄) button with `aria-label={\`Archive ${employee.name}\`}` `title="Archive"`; `false` renders a Delete icon (✕) button with `aria-label={\`Delete ${employee.name}\`}` `title="Delete"`. Both call the existing `onDeleteOrArchive(employee)` handler unchanged — only the icon/label differ, never the click behavior (AC2).
  - [x] Same component: convert all three action buttons (Edit, Regenerate Password, Archive/Delete) to the shared two-tier circular style (AC4) — Edit/Regenerate Password become `w-8 h-8 rounded-full` neutral-gray buttons that only tint on hover (kept this file's existing blue hover-tint convention: `hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-600`); Archive/Delete become permanently-tinted `w-8 h-8 rounded-full` pills — amber for Archive, red for Delete. Extracted as three shared class constants (`NEUTRAL_ICON_BTN`/`AMBER_PILL_BTN`/`RED_PILL_BTN`) at module scope.
  - [x] Kept the existing `isSelf` → `(you)` label branch exactly as-is (Story 10.2 AC6) — it still fully replaces the Archive/Delete button, unaffected by this story.

- [x] Task 2: Skills page — matching two-tier icon-button style (AC: 4)
  - [x] `frontend/src/features/admin/SkillCard.tsx`: converted the existing text-link-style Edit (`✎ Edit`) and Delete (`🗑 Delete`) buttons into the same `w-8 h-8 rounded-full` circular icon-button pair — Edit stays neutral-gray hover-tint-only (icon glyph only, `aria-label`/`data-testid` unchanged, a new `title="Edit"` added for tooltip parity with the other pages' buttons); Delete became a permanently-tinted red pill (icon glyph only, `aria-label`/`data-testid` unchanged, a new `title="Delete"` added). No other SkillCard behavior changed (the `ever_assigned` lock still hides both buttons entirely, unchanged).

- [x] Task 3: Skill Assignments (Readiness Dashboard) grid — View + Delete icon-button conversion (AC: 4)
  - [x] `frontend/src/features/dashboard/DashboardPage.tsx`: converted the "View Details" text-link button into a neutral-gray `w-8 h-8 rounded-full` icon-only button — added a hand-rolled `EyeIcon()` component (same convention as the existing `TrashIcon()`, exact path data reused verbatim from the locked mockup), kept `aria-label`/`onClick` unchanged, added `title="View Details"`. The existing `TrashIcon`/delete button resized from `w-9 h-9` (hover-only red text) to a permanently-tinted `w-8 h-8` red pill, matching Employees/Skills exactly. `aria-label`/`onClick`/`title="Delete"` unchanged.
  - [x] Confirmed `frontend/src/features/dashboard/DashboardRow.tsx` is dead code (`grep -r "import.*DashboardRow"` returns only its own test file) — left untouched, out of scope.

- [x] Task 4: Frontend tests — update assertions broken by the icon-only conversion (AC: 1, 4)
  - [x] `frontend/src/tests/EmployeesPage.test.tsx`: updated every `'Delete/Archive {name}'` label assertion to `'Delete {name}'` (fixture default `has_assignment_history: false`); added two new tests — one asserting the Archive-branch icon/label for `has_assignment_history: true`, one asserting clicking Archive opens the same `DeleteArchiveEmployeeModal` with the archive copy/button-text, unchanged behavior (AC2). Also updated the AC6 self-row test to assert neither `Delete` nor `Archive` labels exist for the acting admin's own row.
  - [x] `frontend/src/features/dashboard/DashboardPage.test.tsx`: line 179's `screen.getAllByText("View Details")` changed to `screen.getAllByRole("button", { name: /View details/i })`. The two other existing assertions (lines 318/384) already used `getByRole(..., { name: /View Details/i })` against the aria-label and needed no change.
  - [x] `frontend/src/features/dashboard/DashboardPage.polling.test.tsx`: both `screen.getByText("View Details")` occurrences changed to `screen.getByRole("button", { name: /View details/i })`.
  - [x] `frontend/src/tests/SkillCard.test.tsx`: no assertion changes needed (confirmed — all 5 tests pass unmodified, `data-testid`-based clicks are visual-content-agnostic).
  - [x] Full regression: `npm run test` (vitest) — 432/432 passed, 41/41 files, 0 failed. `tsc --noEmit` — 31 errors, identical to the pre-existing documented baseline (all in `useResumePosition.test.ts`, an unrelated UUID-branding issue), zero new errors and none in any file this story touched.

### Review Findings

- [x] [Review][Patch] Dashboard's red Delete pill hover-state diverges from the shared `RED_PILL_BTN` pattern used on Employees/Skills [frontend/src/features/dashboard/DashboardPage.tsx:611] — rest-state pill colors matched exactly across all three files, but Dashboard's hover classes carried leftover Story 5.7 styling (`hover:text-red-700 dark:hover:bg-red-950 dark:hover:text-red-300`) not reconciled with the new shared pattern. **Fixed:** Dashboard's Delete button className now matches `RED_PILL_BTN` exactly (`hover:bg-red-100 dark:hover:bg-red-900/40`, no hover text-color change).
- [x] [Review][Patch] Completion Notes/Task 2 wording inaccurately claimed SkillCard's Edit/Delete `title` attributes were "unchanged" — `title="Edit"`/`title="Delete"` were newly added in this diff (the pre-story buttons had no `title` attribute at all, only `aria-label`). **Fixed:** Task 2's wording corrected to say the `title` attributes were newly added, not preserved.
- [x] [Review][Patch] No test asserted the tinted-pill vs. neutral-hover-only visual distinction that is AC4's core deliverable — every prior assertion checked `aria-label`/`role`/text content only; a future regression flipping or removing `AMBER_PILL_BTN`/`RED_PILL_BTN` classes would have left the suite green. **Fixed:** added `toHaveClass('bg-red-50'/'bg-amber-50')` assertions (Archive/Delete carry the tint, Edit/Regenerate don't) in both `EmployeesPage.test.tsx` and `SkillCard.test.tsx`.
- [x] [Review][Defer] `employee.has_assignment_history` can go stale between the roster fetch and the row click (e.g. a new assignment is created concurrently), so the icon/label and the confirm modal's copy can transiently predict the opposite of what the server actually does — deferred, this is a pre-existing trade-off from Story 7.5 (the modal's own copy already had this exact staleness characteristic before this story added a second UI surface with the same property), and the final outcome is always correct because `handleDeleteOrArchiveCompleted` already drives the toast off the server's real response `action`, never the client's prediction. Fixing would require a live re-check round-trip, out of scope for a presentation-only story.

## Dev Notes

**No backend work in this story (AC3).** `has_assignment_history` already flows end-to-end: `employees/service.py::_build_employee_response` (added in Story 7.5, still correct) → `EmployeeResponse.has_assignment_history` → `employeesApi.ts::EmployeeResponse.has_assignment_history` → already read directly by `DeleteArchiveEmployeeModal.tsx`. This story only changes which icon/label `RowActions` renders and the shared visual styling of action buttons across three pages — zero service/repository/router/schema edits, no migration.

**Icon glyphs (matches the locked mockup exactly, no icon library in this codebase — confirmed via `package.json`, no lucide-react/heroicons/etc.):**
- Archive: `🗄` (already used in the mockup's `tintedBtn('🗄', 'Archive', ...)`) — Unicode glyph is fine here since it's inside a colored circular pill, not relying on `currentColor` fill the way `DashboardPage.tsx`'s hand-rolled `TrashIcon` SVG does (that file's Story 5.7 review comment explains why emoji + `text-{color}` doesn't reliably tint — but `EmployeesPage.tsx`/`SkillCard.tsx` already use `✎`/`✕`/`🗑` emoji glyphs today inside colored text classes without a prior bug report, so this story keeps using the same emoji-glyph convention already established in those two files rather than introducing SVGs there; only `DashboardPage.tsx`'s new View icon needs a hand-rolled SVG, matching its own file's existing precedent).
- View (`DashboardPage.tsx` only): hand-rolled inline `<svg>` eye icon, `viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5" aria-hidden="true"`, exact path data from the locked mockup (`_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/01.1-Skills-Dashboard.html` lines 462-465) — reuse verbatim so the rendered shape matches the approved design pixel-for-pixel.

**Color tokens:** use this codebase's existing plain Tailwind palette (`amber-*`, `red-*`, `blue-*` + `dark:` variants) already in use in `EmployeesPage.tsx`/`SkillCard.tsx`/`DashboardPage.tsx` today, **not** the mockup's `talentpilot-*` custom token for the neutral-hover tint — the neutral/routine-action hover color is not specified by the AC (only Archive=amber/Delete=red are named), and switching three files' existing blue hover convention to a differently-defined custom color (`tailwind.config.js`'s `talentpilot-600` = `#1d4ed8`, one shade darker than Tailwind's default `blue-600` = `#2563eb`) is an unnecessary, unrequested visual change with no AC basis — keep the existing blue.

**Architecture compliance (`ARCHITECTURE-SPINE.md`):** No AD is touched — this is presentation-only, no table/service/router changes in any module. `employees/`'s AD-1 ownership of the `has_assignment_history` derivation is unaffected (still computed once, server-side, in `employees/service.py`).

**Testing standard:** Frontend `vitest` only — no backend test changes (no backend code changes). This project's convention (per Story 10.2) is to fix every test call site broken by a visual/text change as part of the same story, not defer it.

### Project Structure Notes

Frontend only: `frontend/src/pages/hr/EmployeesPage.tsx`, `frontend/src/features/admin/SkillCard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx`, plus their test files (`frontend/src/tests/EmployeesPage.test.tsx`, `frontend/src/features/dashboard/DashboardPage.test.tsx`, `frontend/src/features/dashboard/DashboardPage.polling.test.tsx`). No backend files. No new files.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.3` (lines 2992-3013)] — canonical AC text this story implements.
- [Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-09-15.md` lines 48, 86] — originating item #4/#5, confirms "no service-layer change" and build-order sequencing after 10.2.
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html` lines 505-552] — locked mockup reference for the `neutralBtn`/`tintedBtn` two-tier pattern and the Archive(amber)/Delete(red) branch logic (`emp.hasAssignments ? tintedBtn('🗄', 'Archive', ...) : tintedBtn('✕', 'Delete', ...)`).
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/04.1-Skills-Tab.html` lines 603-604, 639-642] — locked mockup reference for the Skills page's Edit/Delete icon-button pair (identical `w-8 h-8` two-tier pattern).
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/01.1-Skills-Dashboard.html` lines 458-486] — locked mockup reference for the Skill Assignments grid's View (eye SVG, neutral) / Delete (trash SVG, permanent red pill) icon-button pair, including the exact SVG path data to reuse for the new View icon.
- [Source: `_bmad-output/implementation-artifacts/10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool.md`] — Story 10.2 (done), immediately prior in build order per the Sprint Change Proposal; this story builds on its `EmployeesPage.tsx` `RowActions`/`isSelf` shape without altering it beyond the Archive/Delete branch and styling.
- [Source: `CLAUDE.md`#Invariants] — no AD applies to this presentation-only change; confirmed no AD-1/AD-6/AD-11 code is touched.

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- `npx vitest run` (full suite, pre-review): 432 passed, 0 failed, 41 files.
- `npx tsc --noEmit`: 31 pre-existing errors (baseline unchanged), all in `useResumePosition.test.ts` (unrelated UUID-branding type issue), 0 new.
- `npx vitest run` (full suite, post-review-patches): 434 passed (432 + 2 new tint-class tests), 0 failed, 41 files. `tsc --noEmit` re-checked: still 31 pre-existing errors, 0 new.

### Completion Notes List

- All 4 ACs implemented and verified: Archive-vs-Delete icon/label branch driven by `employee.has_assignment_history` with zero service/modal logic changes (AC1/AC2), no backend touched at all (AC3), and a consistent two-tier action-icon style (neutral-gray hover-only `w-8 h-8` circles for Edit/Regenerate Password/View; permanently-tinted `w-8 h-8` pills — amber/Archive, red/Delete) applied identically across `EmployeesPage.tsx`, `SkillCard.tsx`, and `DashboardPage.tsx` (AC4).
- Scope decision (documented in Dev Notes, followed exactly): kept the existing codebase's plain `blue-*` hover-tint convention for neutral/routine actions rather than switching to the mockup's `talentpilot-*` custom token — the AC only names colors for the two destructive actions (amber/red), so the neutral tint color was not a spec requirement and changing it across three files would have been an unrequested visual change.
- `DashboardPage.tsx`'s "View Details" text link became an icon-only button (new hand-rolled `EyeIcon()`, path data copied verbatim from the locked mockup) — this required updating 3 test assertions across two test files that asserted on the visible text node rather than the (unchanged) `aria-label`; the two assertions already using `getByRole(..., { name: /View Details/i })` against the aria-label needed no change since the regex substring-matches unaffected by the visible-text removal.
- Confirmed `DashboardRow.tsx` is dead code (not part of the live app tree, only referenced by its own test) — left untouched, out of this story's scope.
- Full regression green: frontend 432/432 passed (41 files); `tsc --noEmit` unchanged at the documented 31 pre-existing errors, none in touched files. No backend tests run or affected (zero backend files touched).

### File List

- `frontend/src/pages/hr/EmployeesPage.tsx`
- `frontend/src/features/admin/SkillCard.tsx`
- `frontend/src/features/dashboard/DashboardPage.tsx`
- `frontend/src/tests/EmployeesPage.test.tsx`
- `frontend/src/tests/SkillCard.test.tsx`
- `frontend/src/features/dashboard/DashboardPage.test.tsx`
- `frontend/src/features/dashboard/DashboardPage.polling.test.tsx`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/deferred-work.md`

## Change Log

- 2026-09-17: Story created via `bmad-create-story` (Amelia/dev agent) — derived directly from `epics.md`'s existing Story 10.3 AC text (no elicitation needed; AC was already fully specified), cross-referenced against the locked UX mockups for exact icon/color/SVG specs.
- 2026-09-17: Story implemented via `bmad-dev-story` — Archive/Delete icon-label branch on `EmployeesPage.tsx`, two-tier icon-button style applied across `EmployeesPage.tsx`/`SkillCard.tsx`/`DashboardPage.tsx`, `DashboardPage.tsx`'s View Details converted to an icon-only button. Test fallout fixed in the same story (2 new tests added, several label assertions updated). Full regression green (432 frontend tests, `tsc --noEmit` baseline unchanged). Zero backend changes. Status → `review`.
- 2026-09-17: Code-reviewed via `bmad-code-review` (3-layer adversarial review — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 0 decisions needed, 3 patches applied, 1 deferred, 8 dismissed after verification. Patches: aligned Dashboard's Delete-pill hover classes to the shared `RED_PILL_BTN` pattern, corrected Task 2's inaccurate "title unchanged" wording, added `toHaveClass` tint-assertions guarding AC4's visual distinction (2 new tests). Deferred: `has_assignment_history` staleness between roster fetch and click (pre-existing Story 7.5 trade-off, final outcome always server-driven). Full regression re-verified green: 434 frontend tests (432 + 2 new), `tsc --noEmit` unchanged at 31 pre-existing errors. Status → `done`.
