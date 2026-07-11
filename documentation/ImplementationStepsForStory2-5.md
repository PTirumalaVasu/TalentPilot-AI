# Story 2-5: Content Discovery — Multi-Assignment Grid View - Implementation Steps

**Date:** 2026-07-10 / 2026-07-11
**Status:** COMPLETED ✅
**Test Results:** Backend 180/180, Frontend 85/85 passing (zero regressions)
**Ready for Merge:** YES

---

## Executive Summary

Story 2-5 implements the real Content Discovery page: a new `GET /api/assignments` endpoint (EMPLOYEE-only) that composes Story 2.4's semantic content matching with Story 4.1's progress data into a grouped grid (Total / In Progress / To Start), plus a thin watch-route page that mounts the existing `<VideoPlayer>` component.

The story's own scope had to be corrected before implementation began — `epics.md` had drifted to describe a stale "single assignment card" model citing a pre-pivot UX spec, when the PRD (FR-4) and the shipped prototype both specify a multi-assignment grid. This was fixed during story authoring, not discovered mid-build.

Implementation followed TDD discipline; adversarial code review then found and fixed 4 real issues, plus live browser verification caught 2 additional real bugs no automated test had surfaced.

---

## What Was Implemented

**Backend:**
- `GET /api/assignments` — first real route on `assignments/router.py`, EMPLOYEE-only (HR_ADMIN gets `403 FORBIDDEN_NOT_EMPLOYEE`)
- `assignments/service.py::list_my_assignments` — composes `content.service.match_content_for_skill` (Story 2.4) + `ProgressService.get_progress` (Story 4.1) per assignment
- `progress/service.py::ProgressService.derive_status` — new, narrow Status-derivation helper (NOT_STARTED / IN_PROGRESS / COMPLETED), seeding the architecture's single-derivation-authority rule
- Eager-loading added to the existing `list_assignments_for_employee` query to avoid an async lazy-load crash

**Frontend:**
- Real `ContentDiscovery.tsx` page replacing the `ContentDiscoveryStub` — grouped grid, summary stats, per-card and page-level empty/error/loading states
- `AssignmentWatch.tsx` — thin watch-route wrapper mounting the existing `<VideoPlayer>` at the card's last watched position
- New API client, TypeScript types, and a duration-parsing utility (client-side, best-effort percent-watched display)

---

## Issues Faced and Fixes

### During Code Review (3 parallel adversarial layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor)

| # | Issue | Fix |
|---|-------|-----|
| 1 | AC4 required rendering the recommended content's description on each card, but it was never wired into the frontend despite the backend already returning it | Card now renders `content.description` (line-clamped) when present |
| 2 | The `COMPLETED` status/group path had zero test coverage on either backend or frontend, despite the task list claiming it was done | Added a backend test proving COMPLETED folds into the "In Progress" section (not a phantom third section), plus a matching frontend assertion |
| 3 | A real keyboard-accessibility bug: the "Contact Rita" link inside a card was nested in a custom `role="button"` container whose keydown handler unconditionally blocked Enter/Space — breaking the link's own keyboard activation | Handler now checks whether the event originated on the card itself vs. a nested element, and only intercepts the card's own keypresses |
| 4 | The retry button on the error state duplicated the mount-time fetch logic without the same "component unmounted" safety guard, risking a state update after the user navigated away | Consolidated into the existing guarded effect instead of a second, unguarded copy |

One decision-needed finding (AC6's empty-state copy referencing a `[View your assignments]` link with no real destination) was resolved as: keep it as static text — this page already *is* the assignments view, so there's no separate page to link to.

### During Live Browser Verification (not caught by any automated test)

| # | Issue | Root cause | Fix |
|---|-------|-----------|-----|
| 1 | Every API response leaked the internal database column name `content_metadata` instead of the documented public field name `metadata` | A pre-existing bug from Story 2.1, dormant since then because no route had ever actually serialized `ContentResponse` over real HTTP until this story added the first one | Changed the Pydantic field from `alias` to `validation_alias`, so it still accepts the ORM's internal name on the way in but serializes with the correct public name on the way out |
| 2 | A never-started assignment's card displayed "0% watched" instead of a clearer "Not started yet" | The percentage calculation correctly returns `0` when nothing has been watched, but the card blindly rendered that number without checking whether the number was meaningful | Card now only shows a percentage when `watch_position > 0`, falling back to plain text otherwise |

### Mid-Session Test Pollution (self-inflicted, root-caused and fixed)

A live-verification script committed a real Assignment row directly to the shared dev database instead of rolling it back, which broke two unrelated tests that assert exact counts. Root-caused via the failing assertions (not guessed), the specific rows were deleted in the correct order (child row before parent, respecting the foreign key), and the full suite was re-run to confirm a clean pass before finalizing.

---

## Test Verification

- **Backend:** 180/180 passing after review patches (was 179 pre-patch), zero regressions
- **Frontend:** 85/85 passing after review patches (was 83 pre-patch), zero regressions
- **Live end-to-end pass:** logged in as a real Employee against the actual running stack (Docker Postgres, real backend, real frontend dev server) — confirmed the loaded grid, both empty states, the error state, and a full click-through to the video watch route with no console errors
- **Visual comparison** against the shipped HTML prototype completed, per this project's standing rule that UI stories must be visually validated before being marked done

---

## Deferred (not fixed — logged for later, low severity)

- Manually-entered (non-YouTube) content can never reach "Completed" status, since only YouTube content carries a known duration
- Two narrow, currently-unreachable edge cases in the watch-route page's state handling
- No batching of the per-assignment database calls — immaterial at this project's current small scale
- A theoretical non-string duration value would crash the duration parser — unreachable via any real data-write path today

---

## References

- **Story File:** `_bmad-output/implementation-artifacts/2-5-content-discovery-multi-assignment-grid-view.md`
- **Sprint Status:** `_bmad-output/implementation-artifacts/sprint-status.yaml`
- **Backend:** `backend/app/assignments/service.py`, `router.py`, `schemas.py`, `repository.py`; `backend/app/progress/service.py`
- **Frontend:** `frontend/src/pages/employee/ContentDiscovery.tsx`, `AssignmentWatch.tsx`, `frontend/src/components/AssignmentCard.tsx`

---

**Document Status:** COMPLETE ✅
**Generated:** 2026-07-11
