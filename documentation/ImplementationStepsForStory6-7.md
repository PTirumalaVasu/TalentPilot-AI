# Implementation Steps for Story 6-7: Manual Content Link Entry (FR-17a)

**Story Key:** 6-7-manual-content-link-entry
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.7 gives an HR Admin a way to paste a content link directly — `POST /api/admin/skills/{id}/content-manual` — as an alternative to Story 6.6's live search, for a link they already have in mind. The endpoint validates the URL's format (no reachability/content check), never calls `youtube_client`/`udemy_client`, and never writes to `content_catalog` — it echoes the input back as an unwritten candidate, shaped for the identical downstream review/approve treatment Story 6.8 will eventually provide.

Unlike Story 6.6 (API-only by an explicit kickoff scope decision, search UI deferred to Story 6.10), this story deliberately included **both** the backend endpoint **and** a standalone frontend component, per the user's explicit instruction ("start development api and ui for the story"). The frontend piece follows Story 6.5's precedent instead: a real, testable component built to the UX spec's exact object IDs, exercised via a temporary dev route ahead of Story 6.10's real Skills tab.

The work happened in two passes in the same overall session: (1) story creation (condensed, reusing Story 6.6's proven composition as the backend template) followed by full TDD implementation of both the API and the frontend component, invoked via `/bmad-agent-dev` → `/bmad-dev-story` → `/bmad-create-story`; (2) an adversarial code review pass (`/bmad-code-review`) that found and fixed 3 real issues — the most serious being a YouTube-URL-detection bug that could silently embed the wrong video — plus caught two review-subagent false positives by reading code outside the diff before trusting the finding.

---

## Agents Invoked

No dedicated research subagent was used during story creation for this story — Story 6.6's own story file and the live codebase (`content/service.py`, `content/schemas.py`, `skills/router.py`, the UX spec, the PRD, and the architecture spine) were read directly to ground every design decision, since Story 6.6 had already established the exact composition this story needed to mirror.

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, reliability/security concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model)
**Input:** Full diff (`git diff HEAD` against baseline `48a11c48`, with new files added to the diff via `git add -N` so they appeared alongside modified files, ~1,239 lines across 15 files) saved to a scratchpad file and read directly by the agent, instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (16 items):**
- `duration_hours` had no lower-bound validation — a direct API call could submit a negative/zero value, echoed straight back
- No test exercised the `duration_hours` boundary at all
- `MANUAL_URL_MAX_LENGTH` (2048) was defined but never tested
- `extractErrorMessage` assumes an Axios-shaped `{response: {data: {message}}}` body, which looked like a mismatch against FastAPI's default `{detail: [...]}` validation-error shape
- Malformed duration input fails silently with no user feedback
- Title never trimmed before being echoed back
- `submit_manual_content` never checks the skill's lock/`ever_assigned` state
- The router's docstring overstates where validation lives
- No audit trail for manual submissions
- `ManualContentCandidate` carries no identifier/integrity token for a future approve action to bind against
- The dev demo route ships behind only `RequireAuth`, no frontend role gate
- No client-side re-validation before submit
- No request-cancellation/stale-response guard
- `_validate_url`'s host check is minimal (permits userinfo, bare IPs, etc.)
- `rel="noreferrer"` instead of `rel="noopener noreferrer"`
- The dev demo page does no UUID-format validation on the pasted Skill ID

**Output:** 16 findings; after triage, cross-checking against `core/errors.py`'s actual centralized error envelope, and direct code verification, 3 became real patches, the rest were dismissed as false positives, deliberate architecture decisions, or already-covered by the spec's own stated behavior

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same saved diff file, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item, 10 items):**
- `duration_hours` submitted negative/zero — independently confirmed the same gap Blind Hunter flagged
- `duration_hours` submitted as NaN/Infinity
- URL userinfo before an unrelated host (e.g. `https://youtube.com@evil.example/path`) — a deceptive-link-format concern
- **`ContentPreviewModal`'s `YOUTUBE_ID_RE` matches as a substring anywhere in the URL, not against the actual hostname** — a non-YouTube URL merely containing `youtube.com/watch?v=...` (e.g. in a query parameter) gets misidentified as embeddable and the wrong video is silently embedded
- `estimateDaysToComplete` at exactly `0` hours
- `estimateDaysToComplete` at a negative value (reachable only if the API ever returned one)
- `extractErrorMessage`'s FastAPI-shape mismatch — same claim as Blind Hunter, independently raised
- Malformed duration text silently dropped, no feedback
- Re-submitting while the preview modal is open could auto-reopen it for a new candidate
- Editing URL/Title after a successful review leaves a stale candidate card visible

**Output:** 10 structured findings; the substring-vs-hostname YouTube-detection bug was the one genuinely new, high-value finding from this layer (independently reproducible and reachable through ordinary use of the component) — it became this review's most serious patch

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.7's literal Given/When/Then acceptance criteria and its 10 numbered Scope Notes, and spot-check every cited precedent claim (e.g. "mirrors `search_content_for_skill`'s shape") against the actual current code.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers, background)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (read directly, full) + the same saved diff, plus direct reads of `content/service.py`, `test_content_ingestion.py`, `skills/router.py`, and the frontend primitives (`Dialog`, `Input`, `Button`, `Card`, `FormErrorText`, `ApiKeysModal.tsx`) to verify precedent claims against the real repository state, not just the diff

**Key Findings Identified:**
- **None requiring remediation.** Explicitly confirmed the request/response shape (including the genuine absence of `thumbnail_url`, not just a `None` value), the never-calls-youtube/udemy-client guarantee (verified the monkeypatch target actually matches how `submit_manual_content` calls through), the URL-format validator, the 403/404 ordering, every frontend object ID against the UX spec, the disabled-`[Approve]`-button Scope Note, the Watch Modal's fallback/embed states, the duration-parsing/days-estimate rounding cases, and the exact new-test-count bookkeeping the story file claimed for each task
- Confirmed the route's default `200` status code matches the cited `content_lookup_route` precedent

**Output:** A fully clean pass — zero findings

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development api and ui for the story 6-7-manual-content-link-entry: refer the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, recognized the request as a direct dispatch to the `DS` (dev-story) menu item, and proceeded straight into `/bmad-dev-story`.

---

### 2. **`/bmad-dev-story` → `/bmad-create-story` (story creation + implementation)**

**Purpose:** Discover story state, create the story file, and implement it in the same pass.

**When Invoked:** Immediately after Amelia activation
**Workflow Steps Executed:**
1. `/bmad-dev-story` discovered no story file existed yet for `6-7-...` (sprint-status showed `backlog`, not `ready-for-dev`) — routed to `/bmad-create-story` per its own halt-and-offer-options branch
2. Pulled the full literal AC text for Story 6.7 from `epics.md` (lines 2309-2329) and FR-17a's full text/consequences from the PRD (lines 292-299); read the relevant architecture spine sections (AD-1, AD-6, AD-10, the Consistency Conventions route table) and the full UX spec (`04.1-skills-content-sourcing.md`) for the "Paste a link" tab's exact object IDs, copy, and validation rules
3. Read the actual current code directly (no subagent): `content/schemas.py`, `content/service.py` (specifically `search_content_for_skill`/`_not_found_skill`, the exact composition to mirror), `skills/router.py`, `skills/schemas.py`, `test_content_ingestion.py`'s `test_manual_seed_content_never_calls_youtube_client` (the precedent for this story's own never-calls-clients test), `test_skills_router.py`'s router-test pattern, and the frontend precedents (`ApiKeysModal.tsx`, `ApiKeysModalDemo.tsx`, `adminApiKeysApi.ts`, `VideoPlayerDemo.tsx`, `Dialog`/`Card` primitives)
4. Resolved 10 real design decisions during story-writing, written directly into 10 numbered Scope Notes: (a) API + a standalone frontend component this time, by explicit user instruction, deviating from Story 6.6's API-only precedent; (b) the exact route/service composition to mirror from Story 6.6; (c) a new `ManualContentCandidate` schema rather than widening `ContentLookupCandidate` — no `thumbnail_url` field at all, not just `None`; (d) a new stdlib-only `_validate_url` (no prior URL-format helper existed); (e) the never-calls-youtube/udemy-client test pattern to mirror; (f) no `content_catalog` write, matching Story 6.6's search-only invariant; (g) the `[Approve]` button stays visibly present but disabled, since it needs Story 6.8's not-yet-built attach endpoint; (h) a new, minimal `ContentPreviewModal` rather than reusing `VideoPlayerDemo.tsx`'s Employee-facing progress-tracking machinery; (i) duration is free text on the frontend, a float on the backend — two different parsing concerns; (j) days-to-complete is a pure, reusable display derivation
5. Generated the story file with 10 Scope Notes, then implemented it directly in the same session, task by task, TDD red-green-refactor: `content/schemas.py` (`ManualContentEntryRequest`/`ManualContentCandidate`/`_validate_url`) → `content/service.py::submit_manual_content` → `skills/router.py`'s route → `frontend/src/lib/utils/duration.ts` (`parseDurationToHours`/`estimateDaysToComplete`) → `adminContentApi.ts` → `ContentPreviewModal.tsx` → `ManualContentEntryForm.tsx` → `ManualContentEntryDemo.tsx` + `App.tsx` route
6. Confirmed RED (import error / `ImportError` / "Failed to load url" / `TypeError: ... is not a function`) before every implementation step, without exception
7. Full backend regression (563 passed, 2 skipped, same 3 pre-existing failures); full frontend regression (296/296); `tsc --noEmit` baseline-checked via `git stash`/re-run (31 errors both before and after — zero new); rebuilt and redeployed both Docker images; live-verified via `curl`: happy path 200, malformed-URL 422, nonexistent-skill 404, EMPLOYEE 403, plus a rebuilt-frontend-container route-serves check
8. Noted honestly, rather than overclaiming: interactive real-browser verification of the two Watch Modal preview states was not performed (no Playwright/browser-automation tool available this session) — covered instead by `ContentPreviewModal.test.tsx`'s automated assertions of both states

**Output File:** `_bmad-output/implementation-artifacts/6-7-manual-content-link-entry.md`
**Sprint Status:** `6-7-...`: `backlog` → `ready-for-dev` → `review` (created and implemented in the same pass)

---

### 3. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-7-manual-content-link-entry: refer t[he UX design]"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from the explicit story name in the user's request (Tier 1). `baseline_commit` (`48a11c48`) confirmed to match current `HEAD` exactly, so diff source = uncommitted changes; new files added to the diff via `git add -N` (intent-to-add, no content actually staged, reset immediately after) so they appeared alongside the modified files without touching working-tree state. Diff saved to a scratchpad file (~1,239 lines, 15 files) rather than inlined into subagent prompts. Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor as three parallel background subagents (`review_mode = "full"`, story file as spec), each given the saved diff's file path to read directly. All three returned independently.
- **Step 03 (Triage):** Normalized 26 raw findings (16 Blind Hunter + 10 Edge Case Hunter; Acceptance Auditor returned zero) down to 18 distinct findings after dedup. Read the actual code at every finding's location before rating severity rather than trusting the diff hunk alone — most notably, verified `core/errors.py`'s centralized `validation_exception_handler`/`http_exception_handler` actually normalizes every error response (422/403/404) to `{status, code, message, timestamp}`, which flipped two "real" findings (`extractErrorMessage`'s field-shape assumption, and "title is never trimmed" — `_reject_blank` already strips it) to false positives. Routed the result into 0 decision-needed, 3 patch, 0 defer, 15 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection (no items qualified for `deferred-work.md` this time — 0 deferred). User chose "apply every patch."

**Patches Applied (all TDD — RED confirmed, then implemented, then GREEN):**
1. `ManualContentEntryRequest.duration_hours` gained `Field(gt=0)` — a direct API call could previously submit a negative or zero duration, which would echo back and render as a nonsensical "≈ -20 days to complete" on the frontend (also rejects NaN, since `NaN > 0` is always `False`). 3 new tests (negative, small-negative, zero).
2. Added the missing test coverage for `MANUAL_URL_MAX_LENGTH`'s 2048-char boundary — the guard itself already existed (`Field(max_length=MANUAL_URL_MAX_LENGTH)`), it was just untested. 2 new tests (over-limit rejected, at-limit accepted).
3. **The most serious finding:** `ContentPreviewModal`'s YouTube-URL detection (`extractYoutubeId`) was rewritten from a substring regex to an actual `new URL(url).hostname` check — a non-YouTube URL that merely *contained* a `youtube.com/watch?v=`-shaped substring (e.g. in a query parameter) was previously silently embedded as an unrelated YouTube video instead of showing the correct "preview not available" fallback + honest external link. 1 new test proving the substring case now correctly falls through to the fallback state.

**Output:** Story status → `done`; full regression re-verified — backend 568 passed (5 net new) / 2 skipped / same 3 pre-existing failures; frontend 297/297 (1 net new); `tsc --noEmit` unchanged at 31 pre-existing errors. Docker backend and frontend images rebuilt and redeployed a second time with the patches applied; negative/zero-duration now correctly 422, positive duration still 200, re-verified via `curl`.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection (3 patches, 15 dismissals each with a one-line reason)
- Sprint status synced (`6-7-...`: `backlog` → `ready-for-dev` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

None — this story extends existing modules only (`content/schemas.py`, `content/service.py`, `skills/router.py`), no new backend files.

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/content/schemas.py` | Adds `ManualContentEntryRequest`, `ManualContentCandidate`, `_validate_url`, `MANUAL_URL_MAX_LENGTH`; code-review patch: `duration_hours` gained `Field(gt=0)` |
| `backend/app/content/service.py` | Adds `submit_manual_content` — `require_hr_admin` → 404-via-`get_skill_by_id` → echo back as `ManualContentCandidate`, no client calls, no `content_catalog` write |
| `backend/app/skills/router.py` | Adds `POST /{skill_id}/content-manual` |
| `backend/tests/test_content_schemas.py` | 11 new tests (6 initial: valid URL, optional duration, malformed-URL rejection ×5 parametrized, blank-title rejection, unknown-field rejection, no-`thumbnail_url`-field; 5 code-review patches: non-positive-duration rejection ×3 parametrized, URL-over-max-length rejection, URL-at-max-length acceptance) |
| `backend/tests/test_content_service.py` | 6 new tests: happy path with/without duration, nonexistent-skill 404, EMPLOYEE 403, never-calls-youtube/udemy-client, never-writes-`content_catalog` |
| `backend/tests/test_skills_router.py` | 8 new tests: HTTP-level happy path, duration-omitted-defaults-null, EMPLOYEE 403, unauthenticated 401, nonexistent-skill 404, malformed-URL 422, blank-title 422, unknown-field 422 |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/adminContentApi.ts` | `reviewManualContent(skillId, body)` — thin typed POST client, mirrors `adminApiKeysApi.ts`'s shape |
| `frontend/src/features/admin/ContentPreviewModal.tsx` | The UX spec's "Watch Modal" — YouTube iframe embed (hostname-checked, post-review fix) or an explicit "preview not available" fallback + external link; built on the existing `Dialog` primitive |
| `frontend/src/features/admin/ManualContentEntryForm.tsx` | The Content Lookup Panel's "Paste a link" tab — URL/Title/Duration inputs, "Review link" button, resulting candidate card with `[View]` (opens the preview modal) and a disabled `[Approve]` (pending Story 6.8) |
| `frontend/src/pages/dev/ManualContentEntryDemo.tsx` | Dev-only page exercising `ManualContentEntryForm` ahead of Story 6.10's real Skills tab, mirroring `ApiKeysModalDemo.tsx`'s role; adds a Skill ID text input since (unlike `ApiKeysModal`) this component needs a real skill to act against |
| `frontend/src/tests/ContentPreviewModal.test.tsx` | 7 tests (6 initial + 1 code-review patch): closed state, `watch?v=`/`youtu.be` embed, fallback + external link, duration/days meta, iframe teardown on close, non-YouTube URL containing a `youtube.com/watch?v=` substring no longer misidentified |
| `frontend/src/tests/ManualContentEntryForm.test.tsx` | 5 tests: candidate card renders on success, days-estimate omitted without duration, inline error + no card on failure, `[Approve]` disabled, `[View]` opens the preview modal |
| `frontend/src/lib/utils/duration.test.ts` | 11 tests: `parseDurationToHours` (5 formats + empty/unparseable), `estimateDaysToComplete` (rounding boundaries + `null` passthrough) — first test file for `duration.ts`, which previously had none |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/utils/duration.ts` | Adds `parseDurationToHours`, `estimateDaysToComplete` alongside the existing ISO-8601 duration helpers |
| `frontend/src/App.tsx` | Adds the `/dev/manual-content-entry-demo` route, wrapped in `RequireAuth` |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-7-manual-content-link-entry.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-7-...`: `backlog` → `ready-for-dev` → `review` → `done` |
| `documentation/ImplementationStepsForStory6-7.md` | This file |

### Not Changed (by design)

- `content/admin_api_keys_router.py` — Story 6.5's read-only status endpoint, untouched
- `content_catalog`/`ContentCatalog` — no write path exists in this story; writing happens only in Story 6.8's (not yet built) approve action
- The real Skills tab / Content Lookup Panel / Skills Card Grid — Story 6.10's job; this story's frontend is a standalone precursor component only
- `VideoPlayerDemo.tsx` — deliberately not reused for the preview modal; that component's Adapter/capture-service machinery is Employee-facing progress-tracking, not applicable here

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skills:** `/bmad-agent-dev` → `/bmad-dev-story` → `/bmad-create-story`
- Discovered no story file existed yet (`backlog`, not `ready-for-dev`) — routed into story creation
- Reused Story 6.6's exact route/service composition as the template, adapted for a validate-and-echo action instead of a multi-source search
- Resolved 10 real design decisions during story-writing, documented as 10 numbered Scope Notes, including the deliberate deviation from Story 6.6's API-only scope (this story's frontend piece, per explicit user instruction) and the new `ManualContentCandidate` schema fork (no `thumbnail_url` field at all)

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, both backend and frontend)**
- 24 new backend tests (schemas, service, router) + 22 new frontend tests (duration utils, preview modal, entry form)
- RED confirmed (import error / "Failed to load url" / `TypeError`) before every single implementation step
- Full regression pass — backend 563 passed / 2 skipped / same 3 pre-existing failures; frontend 296/296; `tsc --noEmit` verified unchanged (31 pre-existing errors, baseline confirmed via `git stash`)
- Live end-to-end verification via `curl` against rebuilt Docker containers (happy path, 422, 404, 403) plus a rebuilt-frontend-container route-serves check
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, all background subagents, single pass
- **Findings:** 26 raw → 18 after dedup → 0 decision-needed, 3 patch, 0 defer, 15 dismiss
- **Two review-subagent claims flipped to false positives by reading code outside the diff:** `extractErrorMessage`'s Axios-shape assumption (actually correct — `core/errors.py` normalizes every error to `{message: ...}`) and "title is never trimmed" (`_reject_blank` already strips it)
- **Most serious finding:** `ContentPreviewModal`'s YouTube-URL detection used a substring match instead of a hostname check, letting a non-YouTube URL that merely contained a YouTube-shaped substring get silently embedded as the wrong video
- **Action:** user chose "apply every patch" — all 3 patches applied with 5 new tests, re-verified live via `curl` against a rebuilt Docker container
- Output: 568 passed backend (up from 563 before review) / 297 passed frontend (up from 296); story marked `done`

---

## Test Coverage

### New/Extended Test Files (52 tests total from this story, post-review)

**Backend (29 new):**
- `test_content_schemas.py` — 11 new: valid URL, optional duration, malformed-URL rejection (5 parametrized cases), blank-title rejection, unknown-field rejection, no-`thumbnail_url` field, non-positive-duration rejection (3 parametrized cases), URL-over-max-length rejection, URL-at-max-length acceptance
- `test_content_service.py` — 6 new: happy path with/without duration, nonexistent-skill 404, EMPLOYEE 403, never-calls-youtube/udemy-client, never-writes-`content_catalog`
- `test_skills_router.py` — 8 new: HTTP-level happy path, duration-omitted-defaults-null, EMPLOYEE 403, unauthenticated 401, nonexistent-skill 404, malformed-URL 422, blank-title 422, unknown-field 422

**Frontend (23 new):**
- `duration.test.ts` — 11 new: 5 duration-format cases, empty/unparseable input, 3 days-estimate rounding boundaries, `null` passthrough
- `ContentPreviewModal.test.tsx` — 7 new (6 initial + 1 patch): closed state, `watch?v=` embed, `youtu.be` embed, fallback + external link, duration/days meta, iframe teardown, substring-vs-hostname fix
- `ManualContentEntryForm.test.tsx` — 5 new: candidate card on success, days-estimate omitted without duration, inline error on failure, `[Approve]` disabled, `[View]` opens the preview modal

### Regression Verification
- Full backend suite run after implementation (563 passed) and again after the code review's patches (568 passed) — same 3 pre-existing, unrelated failures at every stage (`test_find_existing_assignment_returns_empty_when_no_match`, `test_assignment_with_no_qualifying_content_has_null_content`, `test_content_match_returns_null_when_no_content_matches_the_skill`, documented since Story 6.4)
- Full frontend suite run after implementation (296 passed) and again after patches (297 passed), zero failures at either stage
- `tsc --noEmit` explicitly baselined via `git stash`/re-run before trusting the count — 31 pre-existing errors, unchanged by this story's changes at every stage
- Live-verified end-to-end via `curl` against a rebuilt/redeployed Docker backend container, both before and after the review's patches — happy path, malformed-URL 422, nonexistent-skill 404, EMPLOYEE 403, and (post-patch) negative/zero-duration 422
- Frontend dev-route (`/dev/manual-content-entry-demo`) confirmed served (`200`) by the rebuilt frontend container; the two Watch Modal preview states were verified via `ContentPreviewModal.test.tsx`'s automated assertions rather than an interactive browser session — honestly noted as not performed, since no Playwright/browser-automation tool was available this session

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: single-owner module, cross-module calls via Service API only** | The new route lives in `skills/router.py` (URL convention, same prefix as Story 6.6's `content-lookup`) but delegates all logic to `content/service.py::submit_manual_content`, reusing the existing `skills.service.get_skill_by_id` wrapper for its 404 check | `skills/router.py`, `content/service.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | `submit_manual_content` calls `require_hr_admin(current_user)` first, before the 404 check — same ordering as `search_content_for_skill` | `content/service.py` |
| **AD-11 point 5: content-sourcing is Skill-agnostic w.r.t. `ever_assigned`** | Deliberately does **not** check the Skill's lock/assignment state — confirmed correct during code review triage against the architecture spine's explicit text, not a gap | `content/service.py` |
| **FR-17a: never validated against a source, no reachability check** | `_validate_url` checks format only (`scheme in {http, https}` + non-empty `netloc`) via stdlib `urlparse` — no network call, no content check | `content/schemas.py` |
| **FR-17a: identical review/approve treatment as a searched result, never auto-attached** | `ManualContentCandidate` deliberately shares `ContentLookupCandidate`'s downstream shape (minus `thumbnail_url`); no `content_catalog` row is ever written by this endpoint | `content/schemas.py`, `content/service.py` |
| **FR-19: days-to-complete, client-side, never persisted** | `estimateDaysToComplete` (`ceil(duration_hours / 5)`) lives entirely on the frontend; the backend only ever stores/echoes `duration_hours` | `frontend/src/lib/utils/duration.ts` |

---

## Key Technical Achievements

✅ **Deliberately deviated from the prior story's scope precedent, with the reasoning written down, not silently** — Story 6.6 was API-only by an explicit kickoff decision; this story's Scope Note 1 documents exactly why this one instead follows Story 6.5's API+UI pattern (explicit user instruction), rather than leaving future readers to wonder why two adjacent stories in the same epic look structurally different
✅ **Reused an existing composition instead of inventing a new one** — `submit_manual_content` mirrors `search_content_for_skill`'s exact `require_hr_admin` → 404-check → response shape, verified line-for-line by the Acceptance Auditor against the live code, not just the diff
✅ **Proved a negative, not just implemented a feature** — the "never calls `youtube_client`/`udemy_client`" requirement is backed by an explicit test that monkeypatches all three functions to raise `AssertionError` if called, mirroring Story 2.3's `manual_seed_content` precedent exactly
✅ **Code review caught a real bug through independent confirmation** — the substring-vs-hostname YouTube-detection flaw was raised by Edge Case Hunter with a concrete reproduction, verified by reading the actual regex before rating it, reproduced with a RED test, then fixed
✅ **Two review findings were caught as false positives by reading code outside the diff, not accepted at face value** — `extractErrorMessage`'s field-shape assumption and the "title never trimmed" claim both looked plausible from the diff alone but were refuted by `core/errors.py`'s actual centralized handler and `_reject_blank`'s actual return value, respectively
✅ **Honest gap disclosure instead of a false completeness claim** — explicitly recorded that the two Watch Modal preview states were verified via automated component tests, not an interactive browser session, because no Playwright/browser tool was available this session, rather than silently marking that verification task done
✅ **Zero regressions across both full-suite runs, on both stacks** — backend 563 → 568 passed, frontend 296 → 297 passed, `tsc --noEmit` unchanged at 31 pre-existing errors, identical pre-existing failure set at every stage

---

## Deferred Items (Not Story 6-7 Scope)

None — this review's triage routed zero findings to `defer`; every real finding was either patched immediately (3 items) or dismissed with a documented reason (15 items, including deliberate architecture decisions and already-covered spec behaviors). Forward-looking design feedback about Story 6.8's not-yet-built approve action (e.g. whether a candidate needs a server-generated integrity token) was dismissed as out-of-scope for this story rather than deferred, since it names a future story's design surface rather than an unresolved issue in this one.

---

## Conclusion

Story 6-7 is **✅ DONE** after a story-creation-then-implement cycle (API + a standalone frontend component, per explicit user instruction) followed by one full adversarial code review pass:

- All acceptance criteria satisfied, confirmed independently by a clean Acceptance Auditor pass that also verified every cited precedent claim against the live code
- A deliberate scope deviation from the immediately preceding story, reasoned through and documented as a Scope Note rather than left unexplained
- 3 patches applied from this story's own code review, the most serious closing a real YouTube-URL-misidentification bug in the preview modal
- Two review findings correctly identified and dismissed as false positives after reading code outside the diff — precision, not just volume, in the triage
- Zero regressions across every full-suite run, on both the backend and frontend stacks
- Zero items deferred — every real finding was resolved in this same pass
- Live-verified via `curl` against rebuilt Docker containers, both before and after the review's patches
- One honestly-disclosed verification gap (interactive browser check of the two preview states) rather than an overclaimed "done"
- Not yet committed to git in this session

**Ready for:** Story 6.8 (Review, Approve & Estimate Days-to-Complete, FR-18/FR-19), the next `backlog` story in Epic 6 — the first story that will actually write to `content_catalog` for an admin-sourced candidate.
