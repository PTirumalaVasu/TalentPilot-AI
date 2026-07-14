---
title: Sprint Change Proposal — Delete Assignment Capability
date: 2026-07-13
status: approved-pending-story-creation
---

# Sprint Change Proposal: Delete Assignment from the Assignment Dashboard

## 1. Issue Summary

**Trigger:** Not a story defect — a capability gap surfaced from actually using the shipped Assignment Dashboard (Epic 3 + Epic 5 are done through Story 5.6). HR Admins have no way to remove a Skill Assignment. The `assignments` table (Story 3.1) was designed as **accumulating, immutable history**: `epics.md:968` — "(employee_id, skill_id) may have multiple rows (same skill can be intentionally re-assigned), but each row is a distinct Assignment." That design choice is exactly why today a duplicate (Employee, Skill) pair creates a second row (Story 3.4's duplicate-detection flow surfaces the existing row and lets HR create another) instead of editing or removing the first. There has never been a delete path, because none was ever specified.

**New requirement (this proposal):** HR Admin can remove a Skill Assignment from the Assignment Dashboard via a delete icon (red bin) on each row, gated by a confirmation step before the delete executes.

**Category:** New requirement emerged from stakeholder (HR Admin) use of the live product — not a technical limitation, not a misunderstanding, not a strategic pivot.

## 2. Decisions Locked This Session

These were open design questions the trigger explicitly called out as needing resolution now, not deferral. Resolved with the user (TalentPilot) before drafting stories:

| Decision | Resolution | Why |
|---|---|---|
| Hard delete vs. soft delete | **Soft delete.** Add `active` (boolean, default `true`) + `deleted_at` + `deleted_by` to `assignments`, mirroring `assignment_overrides.active`/`reversed_at`/`reversed_by` (Story 5.5b). No row is physically removed. | Consistency with the 5.5b precedent already in the codebase, and the product's coaching-only / nothing-quietly-erased privacy stance (PRD §9). `skill_progress` and `assignment_overrides` rows survive untouched for audit. |
| Confirmation copy for assignments with real watch-progress vs. Not Started | **Escalated copy when a `skill_progress` row exists.** Not Started gets a plain "Remove this assignment?" Anything with recorded progress gets explicit progress-loss framing, e.g. "This assignment has recorded watch progress (65%). Removing it will take it off the dashboard; the history is retained for audit." | Recorded progress represents real signal HR should be made aware they're hiding, even though nothing is destroyed. |
| Assignment with an ACTIVE HR Override (Story 5.5) | **Allowed, no special-case.** Soft-delete stamps the assignment; the `assignment_overrides` row is left untouched (`active` unchanged) — it simply becomes irrelevant once the parent assignment is hidden. | Keeps this change additive and non-branching; the override row remains intact audit history if the assignment is ever inspected directly. |
| Restore/undo | **One-way from the UI in this change.** No "Deleted Assignments" view, no undo affordance. Data is preserved at the DB layer for audit but there is no in-product recovery path. | Keeps this change's scope to the requested capability (delete + confirm). A restore flow is a natural fast-follow if HR asks for it, symmetric with 5.5b's reversal pattern, but is not requested here. |
| Employee-side visibility (Content Discovery / Continue-Watching) | **Disappears for the Employee too.** The `active` flag is the single source of truth read by both the HR dashboard composition and the Employee's Content Discovery list. | One flag, one meaning, everywhere — avoids the two read paths (`dashboard`'s `list_assignments_for_dashboard`, `content`'s `list_assignments_for_employee`) silently diverging on what "deleted" means. |
| Delete eligibility by status | **No restriction.** Not Started, In Progress, Completed, and HR-Overridden assignments are all deletable through the same red-bin icon + confirmation. | Simplest rule; HR owns this data and no status is treated as "protected" from removal. |

## 3. Impact Analysis

### Epic Impact

- **Epic 3 (Skill Assignment Flow & Content Review)** — the epic that owns the `assignments` table (Story 3.1) is **done**, but is not closed to schema evolution. This change adds a new story to Epic 3 (data model + delete endpoint) rather than reopening Story 3.1 itself, and a companion story to Epic 5 (Readiness Dashboard) for the UI (icon, confirmation modal, row removal). No existing Epic 3 or Epic 5 story's acceptance criteria are invalidated or need rewriting — this is additive.
- **No other epic is invalidated.** Epic 4 (Watch Progress) and Epic 5's other stories (5.2 drill-down, 5.3 staleness, 5.5/5.5b override, 5.6 accessibility) are unaffected in their own logic; they only need the `active = true` filter applied at their assignment-read call sites (see Technical Impact) so a deleted assignment doesn't resurface progress/override data for a row that's no longer visible.
- **No resequencing needed.** This slots in as new stories appended to Epic 3/Epic 5; nothing ahead of it in the sprint plan depends on it.

### Story Impact (new)

**Numbering correction:** `epics.md` and `sprint-status.yaml` both confirm Epic 3 already runs through **Story 3.6** ("Cancel Assignment Flow Leaves No Orphaned Record") and Epic 5 already runs through **Story 5.6** ("Accessibility & Real-Time Announcements"). The next available numbers are **3.7** and **5.7** — an earlier draft of this proposal mistakenly used "3.5" for the new backend story, which collides with the existing, already-done "Assignment Creation & Immediate Dashboard Appearance." Corrected below.

- **New Story — Epic 3, Story 3.7: "Assignment Soft-Delete — Data Model & API"** (developer-facing, mirrors Story 3.1's framing): adds `active`/`deleted_at`/`deleted_by` columns + index to `assignments`, a `DELETE /api/assignments/{id}` endpoint (HR-Admin-only, scoped to `assigned_by == caller`, same 403-on-mismatch pattern as `get_assignment_scoped_to_hr_admin`), and updates every existing assignment-read call site to filter `active = true`.
- **New Story — Epic 5, Story 5.7: "Delete Assignment — Dashboard Row Action"** (HR-Admin-facing): red bin icon per row in `DashboardPage.tsx`'s Actions cell (the live grid, routed via `Dashboard.tsx` at `/hr/dashboard` — not the dead `DashboardRow.tsx`/`AssignmentsList.tsx` stub), confirmation modal (progress-aware copy per the table above), success toast, row disappears + pagination/count updates without a full page reload.

### Artifact Conflicts

**PRD (`prds/prd-TalentPilot-AI-2026-07-09/prd.md`):**
- §3 Glossary — **Assignment** definition ("A record linking one Employee to one Skill... Carries a Status badge... and a Provenance Label") should gain one sentence noting an Assignment can be removed by an HR Admin (soft-deleted) and no longer appears on either the Dashboard or the Employee's Content Discovery list.
- §4.1 Skill Assignment Flow — needs a new FR (**FR-15**, next available number) for delete, consequences drawn from the Decisions table above.
- §4.4 Readiness Dashboard — cross-reference FR-15 the same way FR-12 (HR Override) is cross-referenced today.
- §6.1 MVP Scope — add FR-15 to the in-scope FR list.
- No Non-Goal, Success Metric, or NFR in the current PRD conflicts with this addition; §9's coaching-only/privacy constraint is actually reinforced by choosing soft delete.

**Epics (`epics.md`):**
- Table 5 (`assignments`, line ~495) gains three columns and one index — documented in the new Epic 3 story, not a rewrite of Story 3.1's original AC (that AC remains historically accurate to what shipped; the new columns are additive).
- New stories appended under Epic 3 and Epic 5 per Story Impact above.

**Architecture (`ARCHITECTURE-SPINE.md` / `SOLUTION-DESIGN.md`):**
- Entity diagram: `assignments` gains `active`, `deleted_at`, `deleted_by`.
- AD-3 ("Single derivation authority for Status/Provenance," owned by `progress/`) is unaffected — delete is an existence/visibility concern, not a derivation concern, so it doesn't belong in `progress/`. It belongs in `assignments/` (the module that already owns the table, per AD-1's single-owner rule) and must be respected by both `dashboard/`'s read-composition and `content/`'s FR-4 discovery-list read.
- New architectural note: any future assignment-read call site (present or added later) must filter `active = true` — this is now a spine-level invariant for the `assignments` table, the same way `assignment_overrides` already has a plain (non-partial) `idx_overrides_active` index on its `active` column. [Corrected 2026-07-14 per Story 3.7 code review: the original text here described this as a partial index (`WHERE active = true`); the actual `AssignmentOverride.__table_args__` defines `Index("idx_overrides_active", "active")` with no `postgresql_where` clause — a plain index, not partial. The new `idx_assignments_active` correctly mirrors the real, non-partial definition; only this rationale doc's description was wrong.]

**Technical Impact (concrete call sites, verified against current code — corrected after tracing actual routing, not assumed from file names):**

Backend:
- `backend/app/assignments/models.py:79` — `Assignment` ORM model: add `active` (Boolean, default `True`), `deleted_at` (DateTime, nullable), `deleted_by` (UUID, nullable, FK→`employees.id`) + `Index("idx_assignments_active", "active")`.
- New Alembic migration adding the 3 columns + index to `assignments`.
- `backend/app/assignments/repository.py:111` `list_assignments_for_dashboard` — add `.where(Assignment.active.is_(True))`. (Feeds the legacy `/api/dashboard/assignments` endpoint via `service.py:223 list_assignment_rows_for_dashboard_service` — see routing note below.)
- `backend/app/assignments/repository.py:89` `list_assignments_for_employee` — add the same filter; feeds Content Discovery via `service.py:262 list_my_assignments` (FR-4), per the locked "disappears for Employee too" decision.
- `backend/app/assignments/repository.py:146` `list_assignments_for_hr` (paginated) — add the same filter to both the `count_stmt` and the page `stmt`. **This is the real production path**: `dashboard/router.py`'s `GET /api/dashboard` → `DashboardService.get_dashboard_assignments` → `AssignmentsService.list_assignments_for_hr` (`service.py:46`) → this repository function. This is what the live dashboard grid actually calls (`dashboardApi.getDashboard`, used by `DashboardPage.tsx`), so this filter is the one that matters most for pagination counts and grid correctness.
- `backend/app/assignments/repository.py:76` `find_existing_assignment` (Story 3.4 duplicate-detection) — **resolved with the recommended default**: filter to `active = true` here too, so a soft-deleted prior assignment no longer surfaces as a "duplicate" when HR re-assigns the same (employee, skill) pair — a deleted assignment shouldn't block or clutter that flow. Consistent with every other read call site above.
- New: `soft_delete_assignment` repository function + `delete_assignment_service` in `service.py` (mirrors `set_override_service`'s HR-scoping pattern via `get_assignment_scoped_to_hr_admin`, same uniform 403 on not-found/not-owned) + new `DELETE /{assignment_id}` route in `backend/app/assignments/router.py` (mounted under `/api/assignments`, alongside the existing `/override` and `/progress/drill-down` routes).

Frontend — **corrected after tracing the actual mounted route, not just filename matching:**
- `App.tsx` mounts `/hr/dashboard` → `pages/hr/Dashboard.tsx` → `features/dashboard/DashboardPage.tsx`. This is the only live HR grid.
- `frontend/src/features/dashboard/DashboardRow.tsx` and `frontend/src/features/dashboard/AssignmentsList.tsx` (rendered only via `pages/hr/DashboardStub.tsx`) are **dead/unreachable code** — confirmed by a comment in `Dashboard.tsx:78-79`: "App.tsx no longer routes to DashboardStub.tsx (Story 3.5), which is now dead/unreachable." These are **not** touched by this feature.
- **Real target: `frontend/src/features/dashboard/DashboardPage.tsx`**, the inline `<tr>`/`<td>` Actions cell at ~lines 421-429 (where "View Details" currently renders) — add the red-bin delete button here.
- New confirmation modal component (progress-aware copy per the locked decisions) — can extend `ProvenanceDrillDownModal.tsx`'s modal primitive or the 5.5b reversal-confirmation pattern.
- `frontend/src/lib/api/dashboardApi.ts` — new `deleteAssignment(id)` client call.
- `frontend/src/types/dashboard.ts` — type updates if the delete response returns a body (vs. 204 No Content).

**UI/UX:** No existing UX spec covers this (same situation Story 5.5's Notes flagged for HR Override: "No existing UX scenario or prototype covers this interaction"). The confirmation modal copy is specified directly in the Decisions table above in lieu of a separate UX artifact, following the precedent Story 5.5b set (copy specified inline in the story's AC).

**Other artifacts:** No deployment/IaC/CI impact (local-only build, OQ7). Test suites need new coverage: soft-delete endpoint (HR-only, 403 for Employee and for HR Admin who doesn't own the assignment), post-delete invisibility on both dashboard and Content Discovery reads, confirmation-modal copy branching (progress vs. no-progress), and a regression check that `assignment_overrides`/`skill_progress` rows are untouched after a delete.

## 4. Recommended Approach

**Option 1 — Direct Adjustment.** Add two new stories (one Epic 3 backend story, one Epic 5 frontend story) plus the PRD/epics.md documentation deltas above. No rollback, no MVP scope reduction.

- Effort: **Low–Medium** (one additive migration, one new endpoint, filter additions at four existing read call sites, one new UI affordance + modal).
- Risk: **Low.** The soft-delete pattern is not new to this codebase — it's a direct extension of the `assignment_overrides.active` precedent from Story 5.5b, so there's no novel architectural risk, and it touches no derivation logic (AD-3 is untouched).

Option 2 (Rollback) and Option 3 (MVP Review) were not seriously in contention: nothing needs to be reverted, and the MVP's existing scope/goals aren't threatened by adding a delete capability. **Recommended: Option 1.**

## 5. Detailed Change Proposals

### PRD — new FR

> **FR-15: HR Admin removes an Assignment from the Dashboard**
> HR Admin can remove an Assignment from the Readiness Dashboard via a delete control on the row, after confirming the action. Realizes a capability gap surfaced from live dashboard use (not tied to an original UJ).
>
> **Consequences (testable):**
> - Deletion is soft: the Assignment row is hidden from the Dashboard and from the Employee's Content Discovery list; the underlying `assignments`, `skill_progress`, and `assignment_overrides` records are retained for audit, never physically removed.
> - A confirmation step is always required before delete executes; canceling leaves the Assignment untouched.
> - If the Assignment has recorded watch progress, the confirmation copy explicitly names the recorded percentage before HR confirms; a Not Started Assignment gets plain confirmation copy.
> - Any Assignment is deletable regardless of Status (Not Started / In Progress / Completed) or whether it carries an active HR Override.
> - No restore/undo path exists in the product UI for this capability; recovery, if ever needed, is a database-level operation outside product scope.

### Epics.md — new stories (drafted at handoff, not yet written into epics.md)

- **Epic 3, new Story 3.7: "Assignment Soft-Delete — Data Model & API"**
- **Epic 5, new Story 5.7: "Delete Assignment — Dashboard Row Action"**

Confirmed against the current state of both `epics.md` and `sprint-status.yaml`: Epic 3 ends at Story 3.6, Epic 5 ends at Story 5.6 — so 3.7/5.7 are the correct next numbers (an earlier draft of this proposal mistakenly used 3.5, which collides with the existing, already-done "Assignment Creation & Immediate Dashboard Appearance").

## 6. Implementation Handoff

**Change scope classification: Moderate.** This is backlog reorganization (two new stories added to already-"done" epics) plus documentation updates to the PRD and epics.md — not a fundamental replan (no PM/Architect-level strategic decision remains open; all of it was resolved in Section 2 above), but more than a single Developer-agent edit since it spans PRD + epics.md + two stories.

**Handoff:**
1. **Product Owner / Developer** — write the two story files (Story 3.7 backend, Story 5.7 frontend) using `bmad-create-story`, using the FR-15 text and Technical Impact call-site list above as the seed content.
2. **Developer agent** — implement Story 3.7 first (schema + API + call-site filters), then Story 5.7 (UI), consistent with backend-before-frontend sequencing already used for the override feature (5.5 before 5.5b's UI-facing reversal work).
3. **PRD/epics.md updates** — apply the FR-15 addition and Glossary note to the PRD, and append the two new stories to `epics.md`, before or alongside story-file creation (whichever the user prefers at handoff).

**Success criteria:** HR Admin can remove any Assignment row via the red bin icon + confirmation; the row disappears from both the HR dashboard and the affected Employee's Content Discovery list; `skill_progress` and `assignment_overrides` history for that assignment is unchanged in the database; no restore control is exposed in the UI; Employee sessions cannot call the delete endpoint (403).
