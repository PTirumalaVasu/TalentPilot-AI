---
story_key: 2-5-content-discovery-multi-assignment-grid-view
baseline_commit: b02a1fa
---

# Story 2.5: Content Discovery — Multi-Assignment Grid View

**Epic:** 2 (Content Catalog & Matching)
**Status:** ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **Employee**,
I want to see all my assigned Skills with their AI-recommended Content in one grouped list, without searching,
so that I can start or continue learning immediately with minimal friction.

## Scope Notes (read before starting)

1. **This story's scope was corrected during story authoring (2026-07-10).** `epics.md`'s Story 2.5 had been rewritten (2026-07-09, a "tier-2 fix") into a "Single Assignment Card View" citing UX spec `02.1-content-discovery.md`. That citation was itself stale — the implementation-readiness report had already flagged that UX spec doc as pre-pivot. The PRD's own **FR-4** (confirmed the same day, 2026-07-09, "the intended scope") and the actual shipped prototype (`_bmad-output/E-Development/02-Caseys-Resume-and-Watch-Prototype/02.1-Content-Discovery.html`) both describe a **multi-assignment grid** — Total/In Progress/To Start summary stats, two grouped sections, one card per assignment. `epics.md` has been corrected back to match; build against the corrected epics.md text and this story, not the old UX spec doc.

2. **No `GET /api/assignments` endpoint exists yet.** `assignments/router.py` has zero routes today (just the router-level auth gate from Story 1.6). Story 1.3's own binding Dev Notes forward-referenced this exact URL for employee-hard-scoped listing — this story is what finally builds it. `assignments/repository.py::list_assignments_for_employee` already exists (Story 3.1, hard-scoped per role) — reuse it, add eager-loading (see Task 1), don't duplicate its logic.

3. **`Assignment.content_id` is always `NULL` in real data today.** `assignments/service.py::create_assignment_service` hardcodes `content_id=None` — Story 3.4/3.5 (the assignment-creation flow that would populate it via a real match) are both still `backlog`. **Do not join through `assignment.content_id`.** Instead, call the already-built `content/service.py::match_content_for_skill(db, skill_id)` (Story 2.4, `done`) live, per assignment, to get the recommended Content. This is the exact same function Story 2.4's own Dev Notes forward-referenced for "a future assignment-creation flow" — this story is simply the first caller, from the read side instead of the write side. A `None` result means "no recommended content yet" (AC/UX empty state), not an error.

4. **No Status/Provenance derivation function exists anywhere yet** (Epic 5's Story 5.1 is the first story chartered to build the full AD-3 `(Status, Provenance)` derivation). This story needs a much narrower thing: bucketing an assignment into "In Progress" vs. "To Start" for grid grouping. To avoid a second, competing derivation of the `Status` half of AD-3 (which is explicitly the failure mode AD-3 exists to prevent), add a **narrow, reusable** helper now in `progress/service.py` — see Task 2. This becomes the seed of AD-3's single derivation authority; Story 5.1 will extend it with self-report staleness + HR override, not duplicate it.

5. **No `POST /api/assignments/{assignment_id}/progress` route exists yet either.** `progress/router.py` has zero routes (same as `assignments/router.py` — just the Story 1.6 auth gate). The frontend's `captureService.ts` (Story 4.2/4.3, both `done`) already POSTs to exactly this path — it has been doing so against a **404** since those stories shipped. This is a **pre-existing Epic 4 gap**, not something this story introduces or should fix — `Story 4-4: Server-side anti-spoofing` (`backlog`) is the story that wires in the real write-path route. When this story mounts the existing `<VideoPlayer>` component (Story 4.0, `done`) to satisfy the "click card → launch player" AC, its capture POSTs will silently 404 (the capture service already tolerates network/HTTP failures without crashing — Story 4.2's AC4/AC8). Do not attempt to build the missing route here; that is Story 4.4's job and touches `progress/router.py` + real anti-spoofing logic this story has no AC for.

6. **`SkillProgress` stores `watch_position` in seconds — no duration, no percentage.** The prototype's card UI shows `"{X}% watched"`, computed from a demo-data field the real backend doesn't have. A video's duration (when known) lives only in a matched Content row's `content_metadata.duration` — a raw YouTube-API ISO-8601 duration string (e.g. `"PT28M33S"`), set only for `source="YOUTUBE"` content (Story 2.3); manually-seeded content (`source="MANUAL"`) has `content_metadata=None`. **Percent-watched is best-effort display only** — compute it client-side when a matched video Content item has a parseable duration, and omit the percentage (show only the In Progress/To Start badge) when it can't be computed. No FR mandates an exact percentage; don't add a backend field or duration-parsing library for this.

7. **This story does not build the real video-watch experience.** Epic 4's remaining backlog stories (4.4 anti-spoofing, 4.5 event-time-ordering, 4.6 resume-position-retrieval, 4.7 continue-watching-card) own that. This story's job stops at: clicking a card navigates to a minimal watch route that mounts the already-built `<VideoPlayer assignmentId videoUrl startSeconds>` component (Story 4.0, `done`) — a thin wrapper page, not new polish. Use the assignment's own `watch_position` (already fetched for grid grouping) as `startSeconds`; don't add a second fetch for it (that's Story 4.6's dedicated resume-retrieval endpoint to build later).

8. **FR-4's "video couldn't be loaded → [Try again]" consequence is explicitly NOT built by this story.** `<VideoPlayer>` (Story 4.0) already surfaces a bare error string on player failure but has no retry CTA — that's Story 4.6/4.7's polish to add, not a silent gap this story is introducing. Do not add a "Try again" button to `<VideoPlayer>` itself (out of scope, that component is reused as-is per Dev Notes) or to the new watch-route wrapper (would be a one-off, inconsistent with wherever Epic 4 ultimately lands this).

## Acceptance Criteria

### AC1 — `GET /api/assignments` returns the Employee's own assignments, hard-scoped, EMPLOYEE-only

**Given** an authenticated EMPLOYEE session
**When** the frontend calls `GET /api/assignments`
**Then** the response contains only assignments where `employee_id` matches the calling Employee's own identity (reusing `assignments/repository.py::list_assignments_for_employee`'s existing hard-scoping — FR-14) — no request parameter can widen this scope for an EMPLOYEE session

**And** for an HR_ADMIN session calling this same route, the request is rejected with `403 FORBIDDEN_NOT_EMPLOYEE` — **do not** reuse `list_assignments_for_employee`'s existing HR_ADMIN-unrestricted branch here. This route's response composes per-assignment `watch_position` via `progress.service`'s single-assignment coaching-shaped read (Task 3) — looping that across an HR_ADMIN's org-wide, unrestricted assignment set would be a real AD-2 violation (bulk/cross-employee raw-progress exposure), not just a UI-scope gap. This route is Employee-only by design; an HR-facing assignments list (with different, non-coaching-shaped fields) is Epic 5's `dashboard` surface, not this one. Gate with a role check at the top of `list_my_assignments` (Task 3), mirroring the existing `require_hr_admin` pattern in reverse (see Dev Notes).

### AC2 — Each returned assignment includes skill name, recommended content (or null), watch status, and grid group

**Given** the Employee's assignments are fetched
**When** building each response item
**Then** it includes:
- `assignment_id`, `skill_id`, `skill_name` (via eager-loaded `Skill`, no N+1 lazy-load / `MissingGreenlet` risk — see Dev Notes)
- `content`: the live-matched `ContentResponse` from `content.service.match_content_for_skill(db, skill_id)`, or `null` if no Content clears the similarity threshold (Scope Note 3)
- `watch_position`: `0` if no `skill_progress` row exists yet for this assignment
- `status`: one of `NOT_STARTED` / `IN_PROGRESS` / `COMPLETED`, derived by the new `progress/service.py` helper (Scope Note 4) from `watch_position` — `0` → `NOT_STARTED`, `1-99` → `IN_PROGRESS`, `100` → `COMPLETED`
- `group`: `"TO_START"` when `status == NOT_STARTED`, else `"IN_PROGRESS"` — the two-section grid bucket (page-section grouping only; not a duplicate of `status`, which the frontend also needs for the completed-video badge)

### AC3 — Response includes summary counts

**Given** the full set of the Employee's own assignments
**When** the response is built
**Then** it includes `total`, `in_progress_count`, `to_start_count` — matching the counts of the `assignments` array's own `group` values (never independently computed, to avoid the counts and the list disagreeing)

### AC4 — Page loads and renders the grid (happy path)

**Given** I am authenticated as an Employee with one or more assignments
**When** I navigate to Content Discovery (`/employee/content` — the existing Story 1.8 route; this story replaces `ContentDiscoveryStub`, not a new URL)
**Then** I see:
- Header: Logo, navigation (Assignments, Continue Watching — both may be static/non-functional stubs; only the current page's own behavior is in scope), user menu, Sign Out (reuse Story 1.8's existing header/nav pattern, do not rebuild it)
- Summary stats: Total / In Progress / To Start counts
- Two grouped sections — "In Progress" and "To Start" — each rendering one card per assignment in that group
- Each card: Skill name, status badge (⊕ To Start / ⟳ In Progress / ✓ Completed — never color-only, paired with icon+text per NFR-A2), recommended Content's title/source/duration (best-effort, Scope Note 6)/description when `content` is non-null, and the "✓ Approved" provenance label (a fixed label per PRD §4.1 — no real approval gate exists in v1, do not make this conditional on any data field)

### AC5 — Per-card empty state: assignment exists, no matched Content yet

**Given** an assignment whose Skill has no Content clearing the similarity threshold
**When** its card renders
**Then** that specific card shows "No recommended content yet for this skill. [Contact Rita]" instead of a thumbnail/play control (UX-DR7) — this is a per-card state; other cards in the same grid with matched Content are unaffected

### AC6 — Page-level empty state: no assignments at all

**Given** the Employee has zero assignments
**When** the page loads
**Then** it shows "Nothing in progress right now. [View your assignments]" (UX-DR8) instead of the stats/grid — distinct from AC5's per-card state, not a shared generic empty view (FR-4 consequence, AR-14)

### AC7 — Page-level error state: API failure

**Given** `GET /api/assignments` fails (network error or non-2xx)
**When** the page attempts to load
**Then** it shows a distinct error state (e.g. "Couldn't load your assignments. [Try again]") — never a blank grid (UX-DR9/AR-14)

### AC8 — Loading state

**Given** the request is in flight
**When** the page is between navigation and data arrival
**Then** skeleton placeholders render in place of the stats/grid; the header remains interactive

### AC9 — Clicking a card launches the video player at the correct position

**Given** a card with matched Content
**When** I click the card (or its thumbnail)
**Then** I navigate to a watch route (e.g. `/assignments/:assignmentId/watch`) that mounts the existing `<VideoPlayer>` component (Story 4.0) with that assignment's Content URL and `startSeconds` = the card's already-fetched `watch_position` (0 for a never-started assignment) — no second network fetch for the resume position (Scope Note 7)

### AC10 — Accessibility

**Given** the rendered grid
**When** inspected for accessibility
**Then**: status badges are never color-only (icon + text, NFR-A2); thumbnail images have alt text including video title; all interactive elements (cards, buttons, links) have descriptive accessible labels; the grid is keyboard-navigable (cards are focusable and activatable via Enter/Space, not click-only)

## Tasks / Subtasks

- [x] Task 1: Backend — `GET /api/assignments` repository + eager-loading (AC: #1, #2)
  - [x] `assignments/repository.py`: add `.options(selectinload(Assignment.skill))` to `list_assignments_for_employee`'s existing query (in-place edit — do not duplicate the function). This is required to avoid the exact `MissingGreenlet` async-lazy-load bug Story 2.3's code review already found and fixed once in this codebase (see Dev Notes) — accessing `assignment.skill.name` without eager-loading will reproduce it.
  - [x] Do not modify the function's hard-scoping logic (AC1 is already satisfied by the existing code) — this task only adds eager-loading.

- [x] Task 2: Backend — narrow Status derivation helper in `progress/` (AC: #2)
  - [x] `progress/service.py`: `ProgressService` is a class of `@staticmethod`s (existing style — `record_watch_progress`, `get_progress`) — add a new staticmethod to the same class, e.g. `ProgressService.derive_status(watch_position: int) -> Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]` — `0` → `NOT_STARTED`, `1-99` → `IN_PROGRESS`, `100` → `COMPLETED`. Do not add a bare module-level function; match the existing class-based convention exactly.
  - [x] This is deliberately narrow: it does not touch Provenance, self-report staleness, or HR override — those remain Story 5.1's job to add on top, extending this method rather than replacing it.
  - [x] Do not put this logic in `assignments/service.py` — AD-3 requires `progress/` to be the single place Status is derived from raw columns; a second derivation elsewhere is the exact divergence AD-3 exists to prevent.

- [x] Task 3: Backend — service composition + response schema (AC: #1, #2, #3)
  - [x] `assignments/schemas.py`: add `AssignmentContentItem` (assignment_id, skill_id, skill_name, content: `ContentResponse | None`, watch_position, status, group) and `MyAssignmentsResponse` (total, in_progress_count, to_start_count, assignments: `list[AssignmentContentItem]`)
  - [x] `assignments/service.py`: add `list_my_assignments(session, current_user) -> MyAssignmentsResponse`. **First**, raise `AppException(403, "FORBIDDEN_NOT_EMPLOYEE", ...)` if `current_user.role != Role.EMPLOYEE` (AC1 — this route is EMPLOYEE-only; do not let an HR_ADMIN session reach the per-assignment composition below). Then: call `assignments.repository.list_assignments_for_employee`, then for each assignment call `content.service.match_content_for_skill(session, skill.id)` and `ProgressService.get_progress(session, assignment.id)` (note: `get_progress` is a `ProgressService` staticmethod, not a bare function — `from app.progress.service import ProgressService`) — per-assignment, not a new bulk `progress/` read method (Dev Notes explain why this is still AD-2-safe once EMPLOYEE-only is enforced). Derive `status`/`group` via `ProgressService.derive_status`, and assemble counts from the assembled list (never independently recomputed — AC3).
  - [x] This is a deliberate, documented cross-module read composition (`assignments/` calling `content/`'s and `progress/`'s public service functions) — see Dev Notes' Architecture Compliance section before objecting to it as an AD-8 violation

- [x] Task 4: Backend — router (AC: #1)
  - [x] `assignments/router.py`: add `GET /` (mounts at `/api/assignments` via `main.py`'s existing prefix), `response_model=MyAssignmentsResponse`, calling `list_my_assignments`, using the existing `Depends(get_current_user)` already on the router (no new dependency needed — the EMPLOYEE-only role gate lives in the service function per Task 3, not a second router-level dependency)

- [x] Task 5: Backend tests (AC: #1, #2, #3)
  - [x] New test file, **private engine pattern only** (mandatory in this codebase — see Dev Notes; do not use `conftest.py`'s shared `db_session`/`test_engine` fixtures)
  - [x] Hard-scoping: EMPLOYEE session sees only own assignments; a spoofed/irrelevant query param doesn't widen scope
  - [x] Role gate (AC1): HR_ADMIN session calling `GET /api/assignments` gets `403 FORBIDDEN_NOT_EMPLOYEE`, not the assignment list — this is the regression guard that actually matters here (not "HR sees all," which this route deliberately no longer does)
  - [x] Content composition: assignment with a Skill that has matching Content → `content` populated; assignment with a Skill that has no qualifying Content → `content: null`
  - [x] Status/group derivation: watch_position 0/50/100 → NOT_STARTED/IN_PROGRESS/COMPLETED, and TO_START/IN_PROGRESS/IN_PROGRESS group respectively (verifies the COMPLETED→IN_PROGRESS-group folding decision from Dev Notes)
  - [x] Counts: `total`/`in_progress_count`/`to_start_count` always match a plain count of `assignments`' own `group` values, across at least one mixed-group fixture

- [x] Task 6: Frontend — API client + types (AC: #1, #2, #3)
  - [x] `frontend/src/lib/api/assignmentsApi.ts`: `listMyAssignments()` calling `GET /api/assignments` via the existing shared `apiClient` (`withCredentials: true` already baked in — reuse, don't rebuild)
  - [x] `frontend/src/types/assignments.ts` (new): TS interfaces mirroring the new backend schemas exactly (`AssignmentContentItem`, `MyAssignmentsResponse`)

- [x] Task 7: Frontend — Content Discovery page (AC: #4, #5, #6, #7, #8, #10)
  - [x] Replace `frontend/src/pages/employee/ContentDiscoveryStub.tsx`'s content with the real page (keep the file/route, or rename — either way `App.tsx`'s `/employee/content` route must render the real page, not the stub, when this story is done)
  - [x] Loading / loaded / page-empty / page-error states per AC6-AC8
  - [x] Per-card empty state per AC5
  - [x] Status badge rendering: icon + text, never color-only (AC10)
  - [x] Keyboard-operable cards (AC10)

- [x] Task 8: Frontend — watch route (AC: #9)
  - [x] New minimal page (e.g. `frontend/src/pages/employee/AssignmentWatch.tsx`) at route `/assignments/:assignmentId/watch`, mounting the existing `<VideoPlayer>` (Story 4.0) — receive `videoUrl`/`startSeconds` via router state from the card click (no second fetch, per Scope Note 7)
  - [x] Handle direct navigation / page refresh on this route (no router state present, e.g. `location.state` is `undefined`): redirect back to `/employee/content` rather than rendering `<VideoPlayer>` with an undefined `videoUrl` — this route is only ever meant to be reached via a card click, not bookmarked/refreshed (no AC requires persisting watch-route state across a refresh, matching this project's existing precedent for `/login`'s no-persistence stance)
  - [x] Wire the card click/thumbnail-click navigation in the Content Discovery page to this route

- [x] Task 9: Frontend tests (AC: #4-#10)
  - [x] Mock `assignmentsApi` at the module boundary (established Story 1.8/4.0 pattern — no real network calls in unit tests)
  - [x] Cover: loaded grid with mixed groups, page-empty state, per-card empty state, page-error state, loading state, card click navigates to the watch route with correct state, status badge never relies on color alone (assert text/icon presence, not just a CSS class)

### Review Findings

Code review completed 2026-07-11 (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed (resolved), 4 patches, 6 deferred, 8 dismissed.

- [x] [Review][Decision] AC6's empty state ("Nothing in progress right now. [View your assignments]") has no real link/action, unlike AC5's `[Contact Rita]` (a real `mailto:` link) and AC7's `[Try again]` (a real button) [frontend/src/pages/employee/ContentDiscovery.tsx:96-100] — **resolved 2026-07-11: keep as static text.** This page IS the assignments view — there is no separate "all assignments" destination to link to, so the bracket in the epics.md copy is descriptive framing carried over from the PRD's abstract UX-DR8 text, not a literal CTA requirement. No code change; `epics.md`'s copy is accurate as reference text, just not meant to imply every page necessarily wires up a link.

- [x] [Review][Patch] AC4: `content.description` is never rendered on the card, despite AC4 explicitly listing it among required card fields ("recommended Content's title/source/duration/description") [frontend/src/components/AssignmentCard.tsx:74-83] — fixed: card now renders `item.content.description` (line-clamped) when present
- [x] [Review][Patch] Task 5's `COMPLETED` status/group path has zero test coverage on either side, despite Task 5 explicitly requiring "watch_position 0/50/100 → NOT_STARTED/IN_PROGRESS/COMPLETED... verifies the COMPLETED→IN_PROGRESS-group folding decision" and being checked `[x]` [backend/tests/test_content_discovery.py:150-172, frontend/src/tests/ContentDiscovery.test.tsx] — fixed: added `test_completed_status_folds_into_in_progress_group` (backend) and a matching frontend test asserting the ✓ Completed badge renders under the In Progress section, not a third section
- [x] [Review][Patch] Nested `<a>` ("Contact Rita") inside a `role="button"` Card whose `onKeyDown` unconditionally calls `preventDefault()` on Enter/Space — keydown bubbles from the focused anchor to the ancestor handler before the browser's default mailto-navigation fires, breaking keyboard activation of the link and contradicting AC10's keyboard-operability requirement [frontend/src/components/AssignmentCard.tsx:39-51,99-104] — fixed: `onKeyDown` now checks `e.target !== e.currentTarget` and returns early for events from nested elements; added a regression test dispatching a real `KeyboardEvent` at the link and asserting it isn't prevented
- [x] [Review][Patch] `handleRetry` in the error state lacks the `cancelled`-guard the mount-time load path uses, risking a `setState` call after unmount if the user retries then navigates away before it resolves [frontend/src/pages/employee/ContentDiscovery.tsx:55-60] — fixed: `handleRetry` now bumps a `reloadToken` state value that re-triggers the same guarded `useEffect`, instead of duplicating the fetch/then/catch logic in a second, unguarded function

- [x] [Review][Defer] MANUAL-source (and non-YouTube) content can never derive `COMPLETED` status, since `duration_seconds` only resolves from YouTube's `content_metadata.duration` — beyond what Scope Note 6 licenses (which only excuses the missing *percentage display*, not an unreachable *status value*) [backend/app/assignments/service.py:93-97] — deferred, real gap but not a regression this story introduced (MANUAL content had no duration signal before this story either); revisit if MANUAL content becomes common enough for HR to notice assignments that never show Completed
- [x] [Review][Defer] `isWatchRouteState` accepts an empty-string `videoUrl` as valid router state, mounting `<VideoPlayer videoUrl="">` instead of redirecting [frontend/src/pages/employee/AssignmentWatch.tsx:10-17] — deferred, unreachable via the only real caller (`ContentDiscovery.tsx`'s `handleSelect` only navigates when `item.content` is non-null, and `content.url` is a required non-empty backend field)
- [x] [Review][Defer] `assignmentId` undefined + valid router state → renders a blank page instead of redirecting (asymmetric with the no-state case, which does redirect) [frontend/src/pages/employee/AssignmentWatch.tsx:33-41] — deferred, unreachable via the only real caller (the route param is always populated when reached via a card click)
- [x] [Review][Defer] No memoization/batching of per-assignment `match_content_for_skill`/`get_progress` calls — an Employee with N assignments triggers 2N sequential DB round-trips including a live embedding-similarity query per assignment [backend/app/assignments/service.py:88-96] — deferred, immaterial at this project's pilot scale (a handful of assignments per Employee, matching every other story's scale assumption); revisit if roster/assignment volume grows
- [x] [Review][Defer] `_parse_iso8601_duration_seconds` would raise `TypeError` on a non-string truthy `duration` value [backend/app/assignments/service.py:24-36] — deferred, unreachable today (every write path either sets `content_metadata=None` (MANUAL) or a real string from YouTube's API (Story 2.3's `get_video_durations`)); binding guidance for any future ingestion path that might store a non-string duration
- [x] [Review][Defer] No floor-at-0 guard for a hypothetical negative `watch_position` in `derive_status`/`duration.ts`'s percent computation [backend/app/progress/service.py:17-38, frontend/src/lib/utils/duration.ts:26-29] — deferred, `watch_position` is a server-validated `ge=0` field at the one write path that exists (`progress/schemas.py::RecordWatchProgressRequest`), and that write path's own route doesn't exist yet (Story 4.4, still `backlog`)

**Dismissed as noise or already-verified non-issues**: double `Depends(get_current_user)` at router + route level (correct pattern — router-level dependency gates access without exposing the value, route-level dependency retrieves it, FastAPI caches per-request, matches the existing `require_hr_admin` precedent) [backend/app/assignments/router.py:10,15]; story's "Project Structure Notes" omitting `content/schemas.py` from its "No changes" list while the diff touches it (already disclosed in the Dev Agent Record's File List and Change Log, just not reconciled back into that one stale sentence) [_bmad-output/implementation-artifacts/2-5-content-discovery-multi-assignment-grid-view.md]; `ContentResponse.metadata` alias fix changing the contract for other callers with "no audit shown" (independently verified — every existing caller constructs via `.model_validate()` from ORM, none via the serialized alias, and the full 179-test backend suite remains green) [backend/app/content/schemas.py:22-29]; `AppException`→JSON handler registration "not visible in this diff" (pre-existing, registered in `core/errors.py`, proven live via a direct `curl` test returning the correct `403 FORBIDDEN_NOT_EMPLOYEE` body during dev-story) [backend/app/core/errors.py:40-46]; the story's own AD-8 self-defense in Dev Notes "deserving independent verification" (already independently checked against `ARCHITECTURE-SPINE.md` during story authoring, not just self-asserted); a deleted-`Skill`-causes-`AttributeError` scenario [backend/app/assignments/service.py:104] (unreachable — no code path anywhere in this codebase deletes a `Skill` row); a malformed/broken thumbnail URL rendering a broken `<img>` [frontend/src/components/AssignmentCard.tsx:59-64] (cosmetic only, alt text still present, no functional break); a hypothetical third `group` value breaking the total/count invariant (impossible by construction — `group` is a 2-value `Literal`, covered by `test_summary_counts_match_assignment_groups`).

## Dev Notes

### Why the cross-module composition in `assignments/service.py` is not an AD-8 violation

AD-8's diagram shows `dashboard --> assignments` and `dashboard --> progress` as the only drawn cross-module read edges, but AD-8's own stated *purpose* is narrower than "no module may ever call another's service API": it exists to prevent "dependency cycles and back-references that let the **dashboard's** read shape leak into the write-owning modules." Content Discovery (FR-4) is not `dashboard` (which AD-8 itself scopes to the HR read surface, FR-8..FR-11) — it's a distinct Employee-facing read composition with no home of its own. Rather than invent a redundant `content-discovery/` module or route this through `dashboard/` (architecturally wrong — `dashboard` is explicitly HR-only per the Architecture Spine's module table), `assignments/service.py` composing `content/service.py::match_content_for_skill` (already forward-referenced by Story 2.4's own Dev Notes as a future caller) and `ProgressService.get_progress` (already the single-assignment coaching-shaped read AD-2 permits) is the minimal, precedent-consistent choice. Both calls go through the owning module's public Service API (AD-1), never touch another module's table directly, and `progress/`'s new `ProgressService.derive_status` (Task 2) keeps AD-3's single-derivation-authority intact rather than duplicating it. If this reasoning is later judged wrong during architecture review, the fix is moving `list_my_assignments` to a new thin module — not restructuring the underlying repository/service calls, which are correct regardless of which module hosts them.

### Per-assignment `ProgressService.get_progress()` call is AD-2-safe *only because* this route is EMPLOYEE-only (AC1) — this was tightened during story authoring

AD-2 says `skill_progress` is reachable "only through `progress/`'s coaching-shaped read methods — single-assignment status, and single-row drill-down. No bulk, cross-employee, raw-history, or export read method exists to call." Looping the single-assignment `get_progress()` call across an **Employee's own** handful of assignments is genuinely single-assignment-shaped, repeated — not what AD-2 is guarding against. But the same loop over an **HR_ADMIN's unrestricted, org-wide** assignment set (which `list_assignments_for_employee` would return unfiltered for that role) would functionally *be* the bulk/cross-employee raw-progress read AD-2 explicitly bans, even though each individual call is single-assignment-shaped — the aggregate behavior is what AD-2 cares about, not the call signature. This is why AC1/Task 3 gate `list_my_assignments` to EMPLOYEE sessions only (`403 FORBIDDEN_NOT_EMPLOYEE` for HR_ADMIN) rather than letting HR_ADMIN through with the existing unrestricted branch — do not remove that gate to "simplify" the route; it is load-bearing for AD-2 compliance, not incidental. An HR-facing, org-wide assignments view is Epic 5's `dashboard` surface (which reads via `progress/`'s coaching-shaped methods too, but is scoped/designed for that from the start) — not this route's job to also serve.

### `MissingGreenlet` risk — eager-load `Skill`, don't lazy-access it

This exact bug class (`sqlalchemy.exc.MissingGreenlet` from touching an async-lazy-loaded relationship attribute outside a greenlet context) was found and fixed once already in this codebase, in Story 2.3's code review (`run_ingestion_job`'s loop touching `skill.name` after a `db.rollback()` expired the ORM object). Task 1's `selectinload(Assignment.skill)` prevents the same failure mode here — a query for `assignment.skill.name` without it will not fail every time (only on the specific async-context edge the prior bug hit), so don't skip it just because a naive manual test happens to pass.

### `COMPLETED` status folds into the `"IN_PROGRESS"` grid group — a deliberate UI decision, not a reproduction of the prototype's bug

The shipped prototype's own JS buckets videos with `filter(v => watchProgress > 0 && watchProgress < 100)` for "In Progress" and `filter(v => watchProgress === 0)` for "To Start" — a completed (100%) video matches **neither** filter and silently vanishes from both sections. No FR/UX doc defines a third "Completed" section (only Total/In Progress/To Start summary counts are specified), so rather than reproduce the prototype's disappearing-video bug, this story folds `COMPLETED` into the `"IN_PROGRESS"` group for section placement while still exposing the finer-grained `status` field so the card can render its own "✓ Completed" badge (matching the prototype's card-rendering function, which does have that badge logic — it just never reaches it due to the filter bug). This is a strictly-better outcome than either reproducing the vanishing bug or inventing an unspec'd third section.

### Duration/percent-watched is best-effort, not a backend contract

`content_metadata.duration` (when present) is a raw ISO-8601 duration string from the YouTube API (e.g. `"PT28M33S"`) — parse it client-side for display (a handful of lines of regex, no new dependency) rather than adding a parsing library or a backend duration field. Manually-seeded Content (`source="MANUAL"`) has `content_metadata: null` — no duration, so no percent; show the status badge without a percentage in that case. Do not block on this — it's cosmetic, not gating any AC.

### The capture-service 404 you'll see when testing AC9 live is a pre-existing Epic 4 gap, not a regression

`POST /api/assignments/{assignment_id}/progress` has no backend route yet (Scope Note 5) — Story 4.4 (`backlog`) is what adds it. Mounting `<VideoPlayer>` from this story's new watch route will trigger that capture service's periodic POSTs, which will 404 until Story 4.4 ships. Story 4.2's own AC4/AC8 already require the capture service to tolerate network/HTTP failures without crashing, so this is silent and non-blocking — verify the watch page itself doesn't crash or show an error because of it, but do not attempt to build the missing route here (out of scope, and the real fix needs anti-spoofing logic this story has no AC for).

### Project Structure Notes

Changes land in:
- `backend/app/assignments/repository.py` (MODIFIED: eager-load added to existing function)
- `backend/app/assignments/schemas.py` (MODIFIED: two new response schemas)
- `backend/app/assignments/service.py` (MODIFIED: new `list_my_assignments`)
- `backend/app/assignments/router.py` (MODIFIED: first real route, `GET /`)
- `backend/app/progress/service.py` (MODIFIED: new `derive_status` helper)
- `backend/tests/test_assignments_content_discovery.py` or similar (NEW, private-engine pattern)
- `frontend/src/lib/api/assignmentsApi.ts` (NEW)
- `frontend/src/types/assignments.ts` (NEW)
- `frontend/src/pages/employee/ContentDiscoveryStub.tsx` → real implementation (MODIFIED, same route)
- `frontend/src/pages/employee/AssignmentWatch.tsx` (NEW)
- `frontend/src/App.tsx` (MODIFIED: add the new watch route)
- `frontend/src/tests/*` (NEW test files per Task 9)

No changes to:
- `content/repository.py`, `content/service.py`, `content/schemas.py` (Story 2.4's `match_content_for_skill` is called as-is, not modified)
- `progress/repository.py`, `progress/models.py` (Task 2's helper is pure logic in `service.py`, no new query)
- `frontend/src/components/VideoPlayer.tsx`, `frontend/src/lib/adapters/*`, `frontend/src/lib/services/captureService.ts` (Story 4.0/4.2/4.3's code — reused as-is, not modified)
- Epic 4's remaining backlog stories' scope (4.4 anti-spoofing route, 4.5 event-time-ordering, 4.6 resume-retrieval endpoint, 4.7 continue-watching-card polish)

## Library/Framework Requirements

- **No new backend dependencies.** `sqlalchemy.orm.selectinload` is already available (SQLAlchemy 2.0.51, already installed).
- **No new frontend dependencies.** Reuse the existing shared `apiClient` (axios), `react-router-dom` (already installed, Story 1.8), and the existing `<VideoPlayer>` component (Story 4.0).

## Testing Requirements

- Backend: `pytest` + `pytest-asyncio`, live database (Docker Compose Postgres, port 5433) — **must** use a private `create_async_engine` in the new test file, never `conftest.py`'s shared `db_session`/`test_engine` fixtures (the `Base.metadata.drop_all()` DB-wipe bug is still unfixed per `deferred-work.md`; every live-DB test file added since Story 3.1 follows the private-engine pattern — follow it here too)
- Frontend: `vitest` + `@testing-library/react`, mock the API client module boundary (established Story 1.8/4.0 pattern) — assert on rendered output for state tests (loading/empty/error), not just internal state
- Run the full backend suite afterward with the same exclusions prior stories have used (`test_database_schema.py`, `test_skill_progress.py` — known pre-existing cross-file live-DB engine-sharing issue, unrelated to this story) and confirm zero new regressions

## Previous Story Intelligence

From Story 2.4 (`2-4-semantic-content-matching-filter-then-rank.md`, status `done`):
- `content.service.match_content_for_skill(db, skill_id) -> ContentResponse | None` exists exactly as needed — its own Dev Notes explicitly forward-reference "a future assignment-creation flow (Story 3.4/3.5)" as the intended caller; this story is a different (read-side, not write-side) caller of the same function, which its docstring already anticipates in spirit.
- The `ivfflat` index on `content_catalog.embedding` lacks a cosine opclass (seq-scans instead of index-accelerated) — correct results, immaterial at this story's scale, not this story's fix (already deferred).

From Story 3.1 (`3-1-assignments-data-model-and-hr-admin-scope.md`, status `done`, re-reviewed):
- `list_assignments_for_employee` already exists with correct hard-scoping (EMPLOYEE forced to own `employee_id`, HR_ADMIN unrestricted-unless-filtered) — this story adds eager-loading only, does not touch the scoping logic.
- `core/db.py::get_db()` commits on success / rolls back on exception (fixed during Story 3.1's re-review) — this story's new router route is read-only, so no new commit-path risk, but don't assume a repository function needs its own `session.commit()` — the request-scoped `get_db()` dependency owns that.

From Story 2.3 (`2-3-batch-content-ingestion-job-youtube-search.md`, status `done`):
- The `MissingGreenlet` bug class (touching an expired/lazy-loaded ORM attribute outside a greenlet context) is real and has bitten this codebase once already — directly motivates Task 1's eager-loading requirement.
- `content_metadata.duration` is a raw ISO-8601 string from YouTube's API, only present for `source="YOUTUBE"` rows — confirms Scope Note 6's best-effort duration handling.

From Story 1.8 (`1-8-login-screen-ui.md`, status `done`):
- `/employee/content` already exists as a route, currently rendering `ContentDiscoveryStub` — this story's frontend work replaces that component's content, not the route.
- Shared `apiClient` (axios, `withCredentials: true`) and the 401-interceptor/`RequireAuth` guard are already wired at the app level — this story's new page inherits both for free, no new auth plumbing needed.
- Retrospective action item (Epic 1): UI stories must be visually validated against their matching HTML prototype before being marked `done` — this is the first story that action item explicitly named as applying (`02.1-Content-Discovery.html`). Do a visual comparison pass before completion, not just a functional/test-passing check.

From Story 4.2/4.3 (`4-2-...`, `4-3-...`, both status `done`):
- `captureService.ts` already POSTs to `/api/assignments/{assignmentId}/progress` on an interval/threshold and via `sendBeacon` on tab-close — confirms Scope Note 5's 404-until-Story-4.4 gap is real and pre-existing, not something to newly discover during this story's testing.
- `<VideoPlayer assignmentId videoUrl startSeconds onPlayerReady onError>` (Story 4.0) is the exact component to reuse for Task 8's watch route — its props already match what this story needs to pass.

## Architecture Compliance

**AD-1 — Single-owner data modules:** No new table access outside existing owners. `assignments/service.py` reads `content_catalog`/`skill_progress` only via `content/`'s and `progress/`'s public Service APIs (`match_content_for_skill`, `get_progress`), never their repositories/tables directly.

**AD-2 — Coaching-only is a read boundary:** Only the existing single-assignment `get_progress()` read is used, looped per assignment — no new bulk/export/cross-employee method is added to `progress/`. This is only AD-2-safe because `list_my_assignments` is gated to EMPLOYEE sessions only (AC1) — see Dev Notes; do not remove that gate.

**AD-6 — Server-side session/role/identity gate:** The new `GET /api/assignments` route inherits `assignments/router.py`'s existing `Depends(get_current_user)` (Story 1.6) for authentication — hard-scoping is enforced in the repository layer (AC1), matching Story 1.3's binding guidance exactly; the additional EMPLOYEE-only role check (AC1, Task 3) is enforced in the service layer, not a second router dependency.

**AD-3 — Single derivation authority for (Status, Provenance):** Task 2 adds `ProgressService.derive_status` to `progress/service.py`, not `assignments/` — the narrow Status-only slice of AD-3's rule, seeding (not duplicating) the fuller derivation Story 5.1 will build. This story computes no Provenance value at all (Content Discovery shows no Provenance Label — that's HR/Epic 5's surface).

**AD-8 — Module dependency direction:** See Dev Notes' dedicated explanation above — the new cross-module calls are read-only, go through public Service APIs, and don't route Content Discovery through `dashboard` (which is architecturally HR-only).

**NFR-A2 (accessibility):** Status badges in AC4/AC10 are icon+text, never color-only.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5] — corrected story text (this session)
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#4.2] — FR-4, the authoritative multi-assignment-list scope
- [Source: _bmad-output/E-Development/02-Caseys-Resume-and-Watch-Prototype/02.1-Content-Discovery.html] — shipped prototype, matches FR-4's grid model exactly (stats, In Progress/To Start sections, per-card ✓ Approved badge)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-1, AD-2, AD-3, AD-6, AD-8] — module boundary rules this story's composition decisions are reasoned against
- [Source: backend/app/assignments/repository.py, service.py, schemas.py, router.py] — existing Story 3.1/1.3 code this story extends
- [Source: backend/app/content/service.py::match_content_for_skill] — Story 2.4's matching function, reused as-is
- [Source: backend/app/progress/service.py, repository.py] — existing Story 4.1 code; `get_progress` reused as-is, `derive_status` added
- [Source: frontend/src/components/VideoPlayer.tsx, lib/services/captureService.ts] — Story 4.0/4.2/4.3 code reused as-is for Task 8
- [Source: frontend/src/pages/employee/ContentDiscoveryStub.tsx, App.tsx] — Story 1.8's existing stub/route this story replaces
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — `conftest.py` `drop_all()` DB-wipe bug (private-engine testing requirement), MissingGreenlet precedent
- [Source: _bmad-output/implementation-artifacts/epic-1-retro-2026-07-10.md] — prototype-fidelity action item naming this story

## Git Intelligence

Recent commits (`git log --oneline -6`):
```
b02a1fa Feature/story 2.4 (#45)
96c36c2 Merge branch 'main' into feature/story-2.4
8bcf056 Story 2.1 code review: fix shared-DB wipe bug and other findings
b40a42c Story 2.4: semantic content matching (filter-then-rank)
46834df Story 4-3: Tab-Close Flush via sendBeacon (Reliability) (#44)
0d10642 Merge from Main
```

Established conventions to follow:
- Branch naming: `feature/story-2.5` (matching `feature/story-2.4`'s exact pattern), merged to `main` via PR with `(#N)` suffix
- Current branch is `Story2.5`, already checked out, clean except this session's `epics.md`/`sprint-status.yaml` edits — implement directly on it or rename to match the `feature/story-N.N` convention, per user preference
- Sprint status transitions logged as dated comment lines in `sprint-status.yaml`'s header block, same as every prior story

## Completion Checklist

- [x] `GET /api/assignments` hard-scopes EMPLOYEE sessions; HR_ADMIN rejected with `403 FORBIDDEN_NOT_EMPLOYEE` (AD-2-safe by design, not "unrestricted for HR_ADMIN" — that draft assumption was corrected during story authoring, see AC1)
- [x] Response includes skill name, live-matched content (or null), watch_position, status, group, and self-consistent summary counts
- [x] `progress/service.py::ProgressService.derive_status` is the sole place Status is computed from `watch_position` in this story's code paths
- [x] Content Discovery page: loaded grid, page-empty, per-card-empty, page-error, loading states all render distinctly
- [x] Status badges never color-only
- [x] Card click navigates to `/assignments/:assignmentId/watch` with correct `startSeconds`, no extra fetch
- [x] Visual comparison pass against `02.1-Content-Discovery.html` completed (Epic 1 retro action item) — live browser verification via Playwright, see Dev Agent Record
- [x] Backend tests use the private-engine pattern, not the shared `conftest.py` fixtures
- [x] Frontend tests mock the API client, assert on rendered output
- [x] Full backend + frontend suites pass with zero new regressions (documented pre-existing exclusions unchanged)
- [x] Project context (`_bmad-output/project-context.md`) updated per this project's mandatory-update rule
- [x] Sprint status updated to `review`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via `bmad-dev-story`.

### Debug Log References

- `pytest tests/test_content_discovery.py -v` — 6/6 passing on first run.
- `pytest tests/ --deselect test_database_schema.py --deselect test_skill_progress.py --deselect test_content_repository.py --deselect test_content_service.py` — 179 passed (up from 175 pre-story + a net change accounting for the 6 new tests replacing older counts), zero regressions, matching the established exclusion pattern.
- `test_database_schema.py` (16/16), `test_skill_progress.py` (7/7), `test_content_repository.py`+`test_content_service.py` (10/10) — all re-confirmed passing in isolation, unrelated to this story.
- `npx tsc --noEmit` — 4 pre-existing errors (all in `VideoPlayer.tsx`/`VideoPlayerDemo.tsx`, Story 4.2/4.3's territory) confirmed present on the baseline commit via `git stash` before any of this story's changes — zero new type errors introduced.
- `npx vite build` — succeeds cleanly (bundler-level check, since `npm run build`'s `tsc &&` gate fails on the pre-existing errors above and can't reach `vite build` — this is a pre-existing project-wide gap, not something this story could fix within its own scope).
- `npx vitest run` — 83/83 passing (was 73 pre-story: -2 removed `ContentDiscoveryStub.test.tsx` tests, +12 new across `ContentDiscovery.test.tsx` (10) and `AssignmentWatch.test.tsx` (2)).
- Live end-to-end verification against the real stack (Docker Postgres, real `uvicorn`, real Vite dev server), driven by an ad hoc Playwright script (installed for this session, matching Story 1.8's precedent): logged in as Casey, verified the loaded grid (mixed In Progress/To Start groups, stats, ✓ Approved badge, duration, progress bar), the page-level empty state, per-card empty state (no matched content), and a full click-through to the watch route with a real `<VideoPlayer>` mount and zero console errors. Screenshots reviewed for visual comparison against `02.1-Content-Discovery.html` (Epic 1 retro action item) — close match: stats cards, grouped sections, card layout with thumbnail/badge/approval-label/progress-bar all present. All live-created fixture rows were cleaned up from the shared dev DB afterward (verified via a full regression re-run showing 179 passed, no count drift).

### Completion Notes List

- **Real, previously-undetected bug found and fixed during live verification, not by a reviewer**: `content/schemas.py`'s `ContentResponse.metadata` (Story 2.1, `done`) used a plain Pydantic `alias="content_metadata"`, which affects both validation *and* serialization. FastAPI's `response_model` serializes by alias by default, so every HTTP response leaked the DB-internal field name `content_metadata` instead of the schema's own documented public name `metadata`. This bug existed since Story 2.1 but was invisible until now — `content/router.py` had zero routes before this story, so `ContentResponse` had never actually been serialized over real HTTP. Fixed by switching to `validation_alias="content_metadata"` (accepts the ORM attribute name on input, serializes as `metadata` on output) — `populate_by_name=True` was already set, so direct `metadata=` construction still works unaffected. Verified live via `curl` before/after the fix.
- **Real UX bug found via the live-browser visual-comparison pass (Epic 1 retro action item), not caught by any unit test**: a never-started assignment's card showed "0% watched" instead of "Not started yet" — `computePercentWatched` correctly returns `0` (not `null`) when `watch_position` is 0 and a duration is known, but the card blindly rendered the percentage whenever it was non-null, without checking whether any watching had actually happened. Fixed by gating the progress-bar/percentage block on `watch_position > 0`, falling back to "Not started yet" otherwise — confirmed visually via a second screenshot pass. This is the kind of bug the retro action item ("live-browser smoke pass for auth/routing stories" precedent, extended here to a data-rendering story) exists to catch.
- **Live fixture data cleanup caused two transient regression-suite failures mid-session, root-caused and fixed, not just retried**: an early live-verification script created a real Assignment row via `session.commit()` (not rollback) directly against the shared dev DB to test the loaded-grid state. This polluted `test_assignments_service.py::test_employee_is_rejected_before_any_repository_call` and this story's own `test_employee_sees_only_own_assignments` (both assert exact counts/emptiness for Casey's assignments). Root-caused via the failing assertions' diffs (not guessed), cleaned up the specific rows via a targeted delete script (had to delete the child `skill_progress` row before the parent `Assignment`, per the FK), then re-ran the full suite to confirm 179/179 clean again before finalizing.
- **`GET /api/assignments` route path is `""`, not `"/"`**: FastAPI's default trailing-slash redirect behavior (307) on a router mounted at `/api/assignments` via `@router.get("/")` would have added an unnecessary redirect hop on every real request — caught live via `curl` (saw a raw `307` before following it), fixed to `@router.get("")`, reverified `200` directly with no redirect.
- **AD-3 derivation note**: `ProgressService.derive_status` was implemented duration-aware (`derive_status(watch_position, duration_seconds=None)`), not as the story's own draft signature (`derive_status(watch_position)` alone) — a percentage-style 0/1-99/100 bucketing of `watch_position` would have been wrong by construction, since `SkillProgress.watch_position` is stored in **seconds**, not a percentage (confirmed by re-reading the model comment before implementing). Without a known duration, any `watch_position > 0` derives as `IN_PROGRESS`, never `COMPLETED` — a raw seconds value carries no completion signal on its own. `assignments/service.py` resolves `duration_seconds` from a matched Content item's `metadata.duration` (best-effort ISO-8601 parse, Scope Note 6) before calling this method.
- Full task list matches the story file exactly — no scope creep, no task skipped. HR_ADMIN's rejection is enforced in the service layer (`list_my_assignments`), not a second router dependency, per Task 4's own instruction.

### Post-Review Patches (2026-07-11)

Code review (3 parallel adversarial layers) found 1 decision-needed and 4 patch findings; 6 deferred, 8 dismissed as noise/verified-safe. Decision resolved (AC6's empty state stays static text — no separate "all assignments" page exists to link to). All 4 patches applied:

- **`content.description` now renders on the card** (line-clamped, only when present) — a real AC4 gap: the story's own checklist had marked AC4 satisfied without this field ever being wired up in the frontend, despite the backend already returning it.
- **Real test-coverage gap closed for the `COMPLETED` status path**: neither the backend nor frontend test suite ever exercised `COMPLETED`, despite Task 5 explicitly requiring it and being checked off — a case where the story's own checklist claimed more than was actually verified. Added `test_completed_status_folds_into_in_progress_group` (backend, proves a watch_position at/above a matched Content's known duration derives COMPLETED and still groups under In Progress, not a phantom third section) and a matching frontend assertion on the ✓ Completed badge.
- **Real keyboard-accessibility bug fixed**: the per-card "Contact Rita" link (rendered when no Content is matched) is nested inside a `role="button"` Card whose `onKeyDown` unconditionally called `preventDefault()` on every Enter/Space keydown — since keydown bubbles, focusing the nested link and pressing Enter had its default mailto-navigation suppressed before it could fire, contradicting AC10's own keyboard-operability requirement. Fixed by checking `e.target !== e.currentTarget` and returning early for events that didn't originate on the Card itself — the standard fix for this exact "interactive element nested in a custom-role container" bug class. Added a regression test dispatching a real `KeyboardEvent` directly at the link and asserting the event was not prevented.
- **`handleRetry`'s missing unmount-guard fixed by consolidation, not duplication**: rather than copy-pasting the mount-effect's `cancelled` flag into a second function, `handleRetry` now just bumps a `reloadToken` state value that the existing guarded `useEffect` depends on — one fetch/guard implementation instead of two that could drift out of sync.

Re-verified after patches: backend 180/180 passing (was 179, +1), frontend 85/85 passing (was 83, +2), `tsc --noEmit` still shows only the same 4 pre-existing errors (confirmed unchanged), `vite build` still succeeds. Zero regressions.

### File List

**New:**
- `backend/tests/test_content_discovery.py`
- `frontend/src/lib/api/assignmentsApi.ts`
- `frontend/src/lib/utils/duration.ts`
- `frontend/src/types/assignments.ts`
- `frontend/src/components/AssignmentCard.tsx`
- `frontend/src/pages/employee/ContentDiscovery.tsx` (renamed from the deleted `ContentDiscoveryStub.tsx`, real implementation)
- `frontend/src/pages/employee/AssignmentWatch.tsx`
- `frontend/src/tests/ContentDiscovery.test.tsx` (renamed/rewritten from the deleted `ContentDiscoveryStub.test.tsx`)
- `frontend/src/tests/AssignmentWatch.test.tsx`

**Modified:**
- `backend/app/assignments/repository.py` (added `selectinload(Assignment.skill)` to `list_assignments_for_employee`)
- `backend/app/assignments/schemas.py` (added `AssignmentContentItem`, `MyAssignmentsResponse`)
- `backend/app/assignments/service.py` (added `list_my_assignments`, `_parse_iso8601_duration_seconds`)
- `backend/app/assignments/router.py` (added `GET ""` route, mounted at `/api/assignments`)
- `backend/app/progress/service.py` (added `ProgressService.derive_status`)
- `backend/app/content/schemas.py` (fixed pre-existing `ContentResponse.metadata` serialization bug — `alias` → `validation_alias`)
- `frontend/src/App.tsx` (swapped `ContentDiscoveryStub` for `ContentDiscovery`, added the `/assignments/:assignmentId/watch` route)

**Deleted:**
- `frontend/src/pages/employee/ContentDiscoveryStub.tsx` (superseded by `ContentDiscovery.tsx`)
- `frontend/src/tests/ContentDiscoveryStub.test.tsx` (superseded by `ContentDiscovery.test.tsx`)

**Unchanged (as expected):**
- `backend/app/content/service.py`, `content/repository.py` (Story 2.4's `match_content_for_skill` called as-is)
- `backend/app/progress/repository.py`, `progress/models.py` (Task 2's helper is pure logic, no new query)
- `frontend/src/components/VideoPlayer.tsx`, `lib/adapters/*`, `lib/services/captureService.ts` (Story 4.0/4.2/4.3 code reused as-is)

## Change Log

- 2026-07-10: Story 2.5 created (`bmad-create-story`). Preceded by a correction to `epics.md`'s own Story 2.5 text (reverting a stale "single-card" rewrite back to the PRD FR-4 / shipped-prototype multi-assignment grid model, per explicit user decision this session). Story key renamed from `2-5-content-discovery-single-assignment-card-view` to `2-5-content-discovery-multi-assignment-grid-view` in `sprint-status.yaml` to match the corrected scope.
- 2026-07-10/11: Story 2.5 implemented (`bmad-dev-story`) — new `GET /api/assignments` (EMPLOYEE-only), composing Story 2.4's content matching + Story 4.1's progress read + a new `ProgressService.derive_status`; real Content Discovery grid page + thin watch-route wrapper around the existing `<VideoPlayer>`. 6 new backend tests, 12 new frontend tests, zero regressions (179 backend / 83 frontend passing). Found and fixed one real pre-existing bug (`ContentResponse.metadata` serialization leaking the DB column name over HTTP, dormant since Story 2.1) and one real bug introduced by this story's own first draft (misleading "0% watched" on never-started assignments) — both caught via live browser verification, not unit tests alone. Status → `review`.
- 2026-07-11: Code review completed (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed resolved (AC6 empty state stays static text, no code change), 4 patches applied (render `content.description` on the card — a real AC4 gap; add missing `COMPLETED` status/group test coverage on both sides — Task 5 had claimed this was done when it wasn't; fix a real keyboard-accessibility bug where the Card's `onKeyDown` suppressed a nested link's own Enter-key activation; consolidate `handleRetry` into the existing guarded `useEffect` instead of a second, unmount-unsafe fetch), 6 deferred to `deferred-work.md`, 8 dismissed as noise/already-verified. Backend 180/180, frontend 85/85 passing after patches, zero regressions. Status → `done`.

## Status
**done**
