---
baseline_commit: 48a11c48
---

# Story 6.7: Manual Content Link Entry (FR-17a)

Status: done

## Story

As an **HR Admin**,
I want to paste a content link directly, as an alternative to searching,
So that I can attach something I already have in mind without depending on either source's search API.

## Scope Notes (read before starting)

1. **This story is API + a standalone frontend component, by explicit user instruction (deviates from Story 6.6's API-only precedent).** Story 6.6 deferred all UI to Story 6.10 (the real Skills tab, not built yet). This story instead follows **Story 6.5's** precedent: build a self-contained component and exercise it via a temporary dev route (`frontend/src/pages/dev/ApiKeysModalDemo.tsx` is the template to mirror). Story 6.10 will later drop this component into the real Content Lookup Panel's "Paste a link" tab — nothing here should assume the panel exists.
2. **Backend mirrors Story 6.6's exact shape.** Route lives in `skills/router.py` (thin, same file/prefix as the existing `/content-lookup` route — both are `/api/admin/skills/{id}/...` sub-resources per the architecture spine's Consistency Conventions table), actual logic lives in `content/service.py` (AD-1). Reuses `skills_service.get_skill_by_id` for the 404 check (Story 6.6 Task 2, already exists) and `require_hr_admin` (Story 6.6 Task 7, already imported in `content/service.py`) — no new cross-cutting scaffolding needed.
3. **New schema, not a reuse of `ContentLookupCandidate`.** `content/schemas.py::ContentLookupCandidate` already carries a forward-looking docstring: *"shaped identically to Story 6.7's manual-entry candidate (source="MANUAL" there, no thumbnail_url)"*. "No thumbnail_url" means the field must not exist on this response at all (not just `None`) — add a new `ManualContentCandidate` schema: `{ title: str, source: Literal["MANUAL"], url: str, duration_hours: float | None }`. Do not widen `ContentLookupCandidate.source` to include `"MANUAL"` — that would let a `YOUTUBE`/`UDEMY`-shaped candidate from Story 6.6's endpoint silently claim `thumbnail_url` fields Story 6.7's candidates never have; two small schemas mirror this codebase's established per-branch-not-shared-abstraction convention (see Story 6.6 Dev Notes on `youtube_client`/`udemy_client`'s exception classes for the same reasoning).
4. **URL format validation is new — no existing helper to reuse.** `ManualContentCreate` (Story 2.3's CLI schema) never validates its `url` field at all (a human operator is trusted). This story's AC requires "a well-formed URL (client-side-equivalent format check only — no reachability/content check)". Add a small `_validate_url` field validator in `content/schemas.py` using `urllib.parse.urlparse` (stdlib, no new dependency): require `scheme in {"http", "https"}` and a non-empty `netloc`. Reject anything else with a `ValueError` (→ Pydantic 422).
5. **Zero calls to `youtube_client`/`udemy_client` — provable, not just true by omission.** The AC explicitly requires the same test-level guarantee `content/service.py::manual_seed_content()` already has (Story 2.3, see `backend/tests/test_content_ingestion.py::test_manual_seed_content_never_calls_youtube_client`, which monkeypatches `youtube_client.search_videos`/`get_video_durations` to raise `AssertionError` if called). Mirror that exact pattern for this story's new service function, extended to also monkeypatch `udemy_client.search_courses` to raise if called.
6. **No `content_catalog` row is written by this endpoint.** Matches Story 6.6's own "search-only" invariant (epics AC's explicit text: "same downstream review/approve treatment as a searched result (Story 6.8), never auto-attached"). The service function only validates + echoes back a candidate — no `repository.create_content` call anywhere in the new code path. Add an explicit test asserting this (mirrors Story 6.6's `test_search_content_for_skill_never_writes_content_catalog`).
7. **Frontend: the candidate card's [Approve] button is visibly present but disabled.** The UX spec (`04.1-skills-content-sourcing.md`, `content-lookup-btn-approve`) wires Approve to `POST /api/admin/content/attach` — that's Story 6.8, not built yet. Render the button with a `disabled` state and a `title="Available once Story 6.8 ships"` tooltip rather than omitting it entirely (keeps the object ID / layout stable for Story 6.10 to wire up later) or wiring it to a nonexistent endpoint. Do not stub a fake success path.
8. **Frontend: [View] opens a minimal, new, reusable preview modal — not `VideoPlayerDemo.tsx`.** `VideoPlayerDemo.tsx` bundles the YouTube IFrame **Adapter** + watch-progress **capture service** (Story 4.0/4.2-4.4's Employee-facing progress-tracking pipeline) — none of that applies to an HR Admin previewing an unapproved candidate. Build a small new `frontend/src/features/admin/ContentPreviewModal.tsx` matching the UX spec's "Watch Modal" section instead: a bare `<iframe src="https://www.youtube.com/embed/{id}">` (no adapter, no capture, no progress calls) when the URL is YouTube-recognizable (`watch?v=`, `youtu.be/`, or already `/embed/`), else an explicit "Preview not available for {source} in this prototype" state with an "Open in new tab ↗" link (`target="_blank" rel="noreferrer"` — this is the one place in this story a real new-tab link is correct, since it's the UX spec's own named fallback affordance, not a bare unexplained redirect).
9. **Duration input is free text on the frontend, a float on the backend — two different concerns, already anticipated by the epics AC's own type (`duration_hours: float | None`).** The UX spec's manual-entry duration field is free text (`"Duration (optional, e.g. 2h 30m)"`, parsed client-side "if supplied in a recognizable format, otherwise the days-estimate is simply omitted" — Form Validation section). Add a small `parseDurationToHours(text: string): number | null` in `frontend/src/lib/utils/duration.ts` (already home to `parseIso8601DurationSeconds`/`formatDurationMinutes`, Story 2.5) supporting `"2h 30m"`, `"2h"`, `"30m"`, and a bare number (`"2.5"` → 2.5 hours). Unparseable/empty → `null`, sent as `duration_hours: null` (never a guessed value, matching FR-17a's own "no data beats a guessed one" consequence).
10. **Days-to-complete is a pure display derivation, reusable ahead of Story 6.8/6.10.** `ceil(duration_hours / 5)` (FR-19) — add `estimateDaysToComplete(durationHours: number | null): number | null` alongside `parseDurationToHours` in the same `duration.ts` file. Shown only when non-null, exact copy from the UX spec: `"≈ {N} days to complete (at 5 hrs/day)"`.

## Acceptance Criteria

**Given** I am authenticated as HR_ADMIN
**When** I call `POST /api/admin/skills/{id}/content-manual` with `{ url: str, title: str, duration_hours: float | None }`
**Then**:
- `url` and `title` are required; `duration_hours` is optional
- **No call to `youtube_client.py` or `udemy_client.py` is made** — this path is proven to never touch either client (same test-level guarantee `content/service.py::manual_seed_content()` already has for the batch CLI's manual path, Story 2.3 Dev Notes: "a direct assertion... that the seed path works with `youtube_client` entirely unmocked/unpatched")
- `url` is validated as a well-formed URL (client-side-equivalent format check only — no reachability/content check; HR Admin is responsible for the link being correct, per FR-17a's consequence)
- The response is a candidate object shaped identically to Story 6.6's search results (`{ title, source: "MANUAL", url, duration_hours }`, no `thumbnail_url`) — same downstream review/approve treatment as a searched result (Story 6.8), never auto-attached

**Given** an EMPLOYEE session
**When** it calls this endpoint
**Then** `403 Forbidden` (AD-6)

**Given** the Skill referenced by `{id}` does not exist
**When** I call this endpoint
**Then** `404 Not Found` (mirrors Story 6.6's `content-lookup` 404 behavior for the same `{id}` sub-resource shape)

**Given** the UX spec's "Paste a link" tab (`04.1-skills-content-sourcing.md`, `content-lookup-manual-*` object IDs), built as a standalone frontend component per this story's Scope Note 1
**When** an HR Admin fills in URL/Title/optional-Duration and clicks "Review link" (`content-lookup-manual-btn-review`)
**Then** it calls this story's endpoint and renders the resulting candidate with the identical View treatment as a searched result (Scope Note 8) — the days-to-complete estimate is shown only when `duration_hours` is known (Scope Note 10), and [Approve] is visibly present but disabled pending Story 6.8 (Scope Note 7)

**Given** a malformed URL submitted via the frontend form
**When** "Review link" is clicked, or the backend rejects it with `422`
**Then** an inline error is shown on the form (no candidate card rendered) — mirrors the UX spec's general inline-error pattern for this panel, no epics-specified exact copy for this specific case

## Tasks / Subtasks

- [x] Task 1: `content/schemas.py` — `ManualContentEntryRequest` + `ManualContentCandidate` + URL validator (AC1, Scope Notes 3, 4)
  - [x] `ManualContentEntryRequest { url: str, title: str, duration_hours: float | None = None }`, `extra="forbid"`, `title` non-blank via `_reject_blank` (existing helper) + `max_length=255` (matches `content_catalog.title` convention, `skills.name`'s precedent), `url` non-blank + `max_length=2048` (generous URL bound, same reasoning as `CREDENTIAL_MAX_LENGTH`) + format-validated via `_validate_url`
  - [x] `_validate_url(value: str) -> str` — `urllib.parse.urlparse`, requires `scheme in {"http", "https"}` and non-empty `netloc`, else `ValueError`
  - [x] `ManualContentCandidate { title: str, source: Literal["MANUAL"], url: str, duration_hours: float | None }` — no `thumbnail_url` field at all
  - [x] Tests: extended existing `backend/tests/test_content_schemas.py` (a schemas test file already existed for this module — no new file needed): valid URL accepted; missing scheme/netloc/garbage string/empty string rejected (parametrized); blank title rejected; `extra="forbid"` rejects an unknown field; `ManualContentCandidate` has no `thumbnail_url` field
- [x] Task 2: `content/service.py` — `submit_manual_content` (AC1-AC3, Scope Notes 2, 5, 6)
  - [x] `async def submit_manual_content(db, *, current_user, skill_id, url, title, duration_hours) -> ManualContentCandidate`: `require_hr_admin` first; 404 via `skills_service.get_skill_by_id` (reuse `_not_found_skill()`); returns `ManualContentCandidate(title=title, source="MANUAL", url=url, duration_hours=duration_hours)` — no other logic, no repository writes
  - [x] Tests (extend `tests/test_content_service.py`): happy path (with and without `duration_hours`) returns the correct shape; nonexistent `skill_id` → 404 (`AppException`); EMPLOYEE `current_user` → `AppException`/403; **never calls `youtube_client.search_videos`/`get_video_durations` or `udemy_client.search_courses`** (monkeypatch all three to raise `AssertionError` if called, mirrors `test_manual_seed_content_never_calls_youtube_client`); **never calls `repository.create_content`** (explicit assertion, mirrors Story 6.6's `test_search_content_for_skill_never_writes_content_catalog`)
- [x] Task 3: `skills/router.py` — the route (AC1, AC2, AC3, Scope Note 2)
  - [x] `POST /{skill_id}/content-manual`, `response_model=ManualContentCandidate`, thin — one call into `content_service.submit_manual_content(...)`
  - [x] Tests (extend `tests/test_skills_router.py`, private-engine pattern per that file's existing convention): happy path 200 with real HTTP request/response shape; 403 for EMPLOYEE; 401 unauthenticated; 404 for a nonexistent skill; 422 for a malformed URL, blank title, and an extra/unknown field
- [x] Task 4: `frontend/src/lib/utils/duration.ts` — `parseDurationToHours` + `estimateDaysToComplete` (Scope Notes 9, 10)
  - [x] `parseDurationToHours(text: string): number | null` — supports `"2h 30m"`, `"2h"`, `"30m"`, bare numeric strings (interpreted as hours); `null` on empty/unparseable input
  - [x] `estimateDaysToComplete(durationHours: number | null): number | null` — `Math.ceil(durationHours / 5)`, `null` passthrough
  - [x] Tests (extend `frontend/src/lib/utils/staleness.test.ts`'s sibling pattern — new `duration.test.ts` if one doesn't already exist for `duration.ts`; check first): each duration format, invalid input, days-estimate rounding (e.g. 4.1 hours → 1 day, 5.0 → 1 day, 5.1 → 2 days), `null` passthrough
- [x] Task 5: `frontend/src/lib/api/adminContentApi.ts` (NEW) — API client (AC1)
  - [x] `reviewManualContent(skillId: string, body: { url: string; title: string; duration_hours: number | null }): Promise<ManualContentCandidate>` — `POST /api/admin/skills/{skillId}/content-manual`, mirrors `adminApiKeysApi.ts`'s shape (typed response interface, thin `apiClient` call)
- [x] Task 6: `frontend/src/features/admin/ContentPreviewModal.tsx` (NEW) — the "Watch Modal" (Scope Note 8, UX spec `watch-modal-*` object IDs)
  - [x] Props: `{ open: boolean; onClose: () => void; title: string; source: string; url: string; durationHours?: number | null }`
  - [x] YouTube-recognizable URL (regex extracting a video id from `watch?v=`, `youtu.be/`, or `/embed/` patterns) → `<iframe src="https://www.youtube.com/embed/{id}">`; otherwise → "Preview not available for {source} in this prototype. Use "Open in new tab" below to watch." + an `Open in new tab ↗` link (`target="_blank" rel="noreferrer"`)
  - [x] Built on the existing `Dialog` primitive (`components/ui/dialog.tsx`), same pattern as `ApiKeysModal.tsx`; closing tears down the iframe (unmounts, doesn't just hide) per the UX spec's "stops any playback" requirement
  - [x] Tests (new `frontend/src/tests/ContentPreviewModal.test.tsx`): YouTube URL → iframe rendered with correct `src`; non-YouTube URL → fallback text + external link rendered; closing removes the iframe from the DOM
- [x] Task 7: `frontend/src/features/admin/ManualContentEntryForm.tsx` (NEW) — the "Paste a link" tab component (Scope Note 1, 7; UX spec `content-lookup-manual-*` + result-card object IDs)
  - [x] Props: `{ skillId: string }` (self-contained otherwise, matches `ApiKeysModal.tsx`'s self-fetching convention — though this component has nothing to prefetch, it owns its own form/candidate/error state)
  - [x] Fields: URL input (`content-lookup-manual-url-input`, placeholder "Paste a content link…"), Title input (`content-lookup-manual-title-input`, placeholder "Title"), optional Duration input (`content-lookup-manual-duration-input`, placeholder "Duration (optional, e.g. 2h 30m)"), "Review link" button (`content-lookup-manual-btn-review`)
  - [x] On submit: parses duration via `parseDurationToHours`, calls `reviewManualContent`, renders the resulting candidate as a result card (title, "MANUAL" source badge, days-to-complete via `estimateDaysToComplete` — omitted if `null`, `[View]` opening `ContentPreviewModal`, `[Approve]` disabled per Scope Note 7) on success, or an inline `FormErrorText` on failure (a 422 from a malformed URL, or a network/other error) — no candidate card on error
  - [x] Tests (new `frontend/src/tests/ManualContentEntryForm.test.tsx`): happy path renders the candidate card with correct fields; duration omitted when not supplied; error response renders inline error, no card; View opens `ContentPreviewModal`; Approve button is disabled
- [x] Task 8: `frontend/src/pages/dev/ManualContentEntryDemo.tsx` (NEW) + `App.tsx` route (Scope Note 1)
  - [x] Mirrors `ApiKeysModalDemo.tsx`'s role exactly — a minimal dev-only page so this ahead-of-its-page component can be manually verified in a real browser. Since this component (unlike `ApiKeysModal`) needs a real `skillId`, the demo page includes a small Skill ID text input (defaulted empty, with a short note to paste in a real seeded Skill's UUID) feeding into `ManualContentEntryForm`
  - [x] Route: `/dev/manual-content-entry-demo`, added to `App.tsx` alongside the existing two dev routes, wrapped in `RequireAuth` (same pattern)
- [x] Task 9: Full regression + live verification
  - [x] Backend: `pytest` full suite, zero net-new regressions beyond the documented pre-existing 3 failures
  - [x] Frontend: `vitest` full suite, zero net-new regressions; `tsc --noEmit` — no new errors beyond the existing pre-existing count (check current baseline first via `git stash`/re-run if needed, or just diff the count before/after this story's changes)
  - [x] Live Docker verification (`curl` for the backend, matching Stories 6.2/6.4/6.5/6.6's precedent): as Rita (HR_ADMIN), call `content-manual` for a real seeded Skill with a valid URL — confirm 200 + shape; malformed URL — confirm 422; nonexistent skill — confirm 404; as Casey (EMPLOYEE) — confirm 403. Frontend: run the dev server, navigate to `/dev/manual-content-entry-demo`, paste in a real Skill ID, submit a real YouTube URL and a non-YouTube URL, confirm both preview states render correctly in a real browser.

### Review Findings

`bmad-code-review` (2026-09-10, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). Acceptance Auditor reported a fully clean pass (zero AC/Scope-Note violations). 0 decision-needed, 3 patches, 0 deferred, 15 dismissed.

- [x] [Review][Patch] `ManualContentEntryRequest.duration_hours` has no lower-bound (or NaN) validation — a direct API call (bypassing the frontend's numeric-only parser) can submit `-100` or `0`, which gets echoed straight back and, once rendered, produces a nonsensical "≈ -20 days to complete" / "≈ 0 days to complete" on the frontend. `Field(gt=0)` closes this (Pydantic's `gt` constraint rejects `NaN` too, since `NaN > 0` is always `False`); a plain `Infinity` value is not realistically reachable through this form (the client parser can never produce it) so is not separately guarded. [backend/app/content/schemas.py:200]
- [x] [Review][Patch] `MANUAL_URL_MAX_LENGTH` (2048) is defined but has no test asserting a URL over that length is actually rejected with `422` — the one length guard on this schema is unverified. [backend/tests/test_content_schemas.py]
- [x] [Review][Patch] `ContentPreviewModal`'s YouTube-URL detection (`YOUTUBE_ID_RE`) matches `youtube.com/watch?v=`/`youtu.be/`/`.../embed/` as a **substring anywhere in the URL**, not against the actual hostname — a non-YouTube URL that merely contains one of those substrings (e.g. in a query parameter, `https://example.com/redirect?to=youtube.com/watch?v=XXXXXXX`) is misidentified as embeddable, and the modal silently embeds an unrelated YouTube video instead of showing the correct "Preview not available for {source}" fallback + honest external link to the real destination. Fix: parse the URL and check `hostname` (`youtube.com`/`www.youtube.com`/`youtu.be`) rather than substring-matching the raw string. [frontend/src/features/admin/ContentPreviewModal.tsx:18]
- [x] [Review][Dismiss] `extractErrorMessage` in `ManualContentEntryForm.tsx` assumes an Axios-shaped `{response: {data: {message}}}` error body — verified against `backend/app/core/errors.py`'s centralized `validation_exception_handler`/`http_exception_handler`: **every** error response (422 validation, 403, 404, etc.) is normalized to `{status, code, message, timestamp}`, so `response.data.message` is the correct field for this codebase, not a mismatch. Live-verified via this story's own curl checks (422 body: `{"message":"The request body failed validation",...}`).
- [x] [Review][Dismiss] "Title is never trimmed before being echoed back" — false; `_reject_blank` (the shared helper `title_must_not_be_blank` calls) returns `stripped`, not the raw value, so surrounding whitespace is already stripped.
- [x] [Review][Dismiss] `submit_manual_content` doesn't check the Skill's lock/`ever_assigned` state — deliberate per the architecture spine's AD-11 point 5 ("FR-17/FR-18/FR-19/FR-23 are Skill-agnostic w.r.t. `ever_assigned`... the backend must not be built to artificially require `ever_assigned = false`"), and matches `search_content_for_skill`'s identical behavior (Story 6.6, also no such check).
- [x] [Review][Dismiss] Router docstring says "validation/logic lives in content/service.py" when URL/title format validation actually happens in `schemas.py`'s Pydantic validators — a wording nitpick on a comment, not a functional issue; matches `content_lookup_route`'s identical docstring phrasing (pre-existing pattern, not introduced by this story).
- [x] [Review][Dismiss] No audit trail (who/when) for a manual submission — out of scope; this endpoint writes nothing (`content_catalog` row creation, and its `attached_by`/`origin` audit fields, is explicitly Story 6.8's job per this story's own AC/Scope Note 6).
- [x] [Review][Dismiss] `ManualContentCandidate` carries no server-generated id/integrity token for a future Story 6.8 approve action to bind against — forward-looking design feedback for a not-yet-built story, not a defect in this one; `ContentLookupCandidate` (Story 6.6, the sibling schema this one mirrors) has the identical shape/gap.
- [x] [Review][Dismiss] `/dev/manual-content-entry-demo` is reachable by any authenticated user (only `RequireAuth`, no frontend role gate) — matches every existing dev route in this codebase (`ApiKeysModalDemo`, `VideoPlayerDemo`) exactly; the actual enforcement is server-side per AD-6 (`require_hr_admin` in `submit_manual_content`), which a non-admin would hit as a 403 on Review.
- [x] [Review][Dismiss] No client-side URL-format pre-validation before submit (a malformed URL round-trips to the server for its 422) — no spec requirement for eager client-side validation; cheap local round trip, correctly surfaced as an inline error either way.
- [x] [Review][Dismiss] No request-cancellation/stale-response guard against a rapid double-submit — false; the "Review link" button is `disabled={submitting || ...}`, so a second submit cannot be triggered while the first is in flight.
- [x] [Review][Dismiss] Unparseable duration text (e.g. "2 hrs") is silently dropped with no user-facing error — this is the UX spec's own explicitly stated behavior verbatim ("parsed... if supplied in a recognizable format, otherwise the days-estimate is simply omitted," Form Validation section), not a gap.
- [x] [Review][Dismiss] Candidate card stays visible (stale) if the admin edits URL/Title after a successful Review without resubmitting — minor UX nit on a standalone dev-precursor component (not Story 6.10's final panel), not specified either way by the UX spec; low value relative to scope.
- [x] [Review][Dismiss] Re-clicking Review while the preview modal is open could "auto-reopen" the modal for a new candidate — unreachable; `Dialog`'s full-screen backdrop overlay blocks interaction with the underlying "Review link" button while open, so a second submit can't be triggered mid-preview.
- [x] [Review][Dismiss] `_validate_url` permits URL userinfo (e.g. `https://youtube.com@evil.example/path`), which could read as a deceptive/phishing-style link — the exact `youtube.com@evil.example` netloc does not match `ContentPreviewModal`'s regex (no `youtube.com/` substring present), so this doesn't chain into the embed-substitution bug above; as a bare format concern it's consistent with FR-17a's own explicit "HR Admin is responsible for the link being correct, no reachability/content check" consequence.
- [x] [Review][Dismiss] `Open in new tab` link uses `rel="noreferrer"` rather than `rel="noopener noreferrer"` — functionally equivalent (`noreferrer` implies `noopener` in all modern browsers); not a live issue.
- [x] [Review][Dismiss] `ManualContentEntryDemo`'s Skill ID input does no UUID-format validation before enabling the form (a typo just produces a raw 404) — acceptable for a dev-only manual-verification page, consistent with this codebase's other dev routes.

## Dev Notes

- **Why this story's scope differs from Story 6.6's API-only precedent:** explicit user instruction for this story ("start development api and ui... refer the ux design if required"), not a re-litigation of Story 6.6's decision — Story 6.6 remains correctly scoped for its own kickoff. This story's frontend piece is deliberately built the same way Story 6.5's `ApiKeysModal.tsx` was: a real, testable component with 04.1's own object IDs, exercised via a temporary dev route, ready for Story 6.10 to drop in as-is.
- **Route/response-status precedent:** Story 6.6's `content-lookup` route uses FastAPI's default `200` (no explicit `status_code=`) since it's a read/search action, not a resource creation. This story's `content-manual` route follows the same precedent — it's a validate-and-echo action, not a `content_catalog` write (that's Story 6.8's `201 Created` via `POST /api/admin/content/attach`).
- **`ManualContentCandidate` vs `ContentLookupCandidate`:** deliberately two separate schemas (Scope Note 3) rather than a shared base/Union — matches this codebase's established preference for explicit per-branch schemas over premature shared abstraction (same reasoning Story 6.6 used for `youtube_client`/`udemy_client`'s independent exception classes, and Story 6.6's schema docstring already flagged this exact fork point).
- **Not this story's job:** `POST /api/admin/content/attach` (Story 6.8 — the actual write/approve action any candidate, searched or manual, eventually needs), the "Currently Approved" section, the Search tab, the Skills Card Grid, and the API Keys panel's integration into a real Skills tab (all Story 6.10). `ManualContentEntryForm.tsx`'s [Approve] button stays inert in this story by design (Scope Note 7) — wiring it up is explicitly Story 6.8/6.10's job, not a gap to silently fill here.
- **Testing standards (this codebase's established conventions, confirmed via Stories 6.2-6.6):** backend — pytest + httpx, TDD red-green-refactor, service-level tests via direct function calls + `db_session` fixture, router-level tests via the private-engine/`_login()` pattern in `test_skills_router.py`. Frontend — Vitest + React Testing Library, colocated in `frontend/src/tests/`.

### Project Structure Notes

New files:
- `frontend/src/lib/api/adminContentApi.ts`
- `frontend/src/features/admin/ContentPreviewModal.tsx`
- `frontend/src/features/admin/ManualContentEntryForm.tsx`
- `frontend/src/pages/dev/ManualContentEntryDemo.tsx`
- `frontend/src/tests/ContentPreviewModal.test.tsx`
- `frontend/src/tests/ManualContentEntryForm.test.tsx`
- `frontend/src/lib/utils/duration.test.ts` (no test file previously existed for `duration.ts`)

Modified files:
- `backend/app/content/schemas.py` — adds `ManualContentEntryRequest`, `ManualContentCandidate`, `_validate_url`, `MANUAL_URL_MAX_LENGTH`
- `backend/app/content/service.py` — adds `submit_manual_content`
- `backend/app/skills/router.py` — adds `POST /{skill_id}/content-manual`
- `backend/tests/test_content_schemas.py` — extended (existing file, not a new one)
- `backend/tests/test_content_service.py` — extended
- `backend/tests/test_skills_router.py` — extended
- `frontend/src/lib/utils/duration.ts` — adds `parseDurationToHours`, `estimateDaysToComplete`
- `frontend/src/App.tsx` — adds the new dev route

Not touched (out of scope, later stories): `content_catalog`/`ContentCatalog` writes (Story 6.8), the Skills tab / Content Lookup Panel / Skills Card Grid (Story 6.10), `content/admin_api_keys_router.py` (Story 6.5), Story 6.6's `content-lookup` endpoint and its Search tab UI (Story 6.10).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.7] — full AC text (lines 2309-2329)
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-17a] — full FR text/consequences (lines 292-299)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-1] — single-owner data module rule (route-in-skills/logic-in-content composition)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — role-gating requirement
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Consistency Conventions] — `/api/admin/skills/{id}/...` route grouping
- [Source: _bmad-output/C-UX-Scenarios/04-ritas-content-curation/04.1-skills-content-sourcing/04.1-skills-content-sourcing.md] — Content Lookup Panel's "Paste a link" tab (`content-lookup-manual-*`), result-card treatment, Watch Modal (`watch-modal-*`), Form Validation section (URL/Title/Duration rules)
- [Source: backend/app/content/schemas.py] — `ContentLookupCandidate`'s forward-looking docstring naming this story's exact candidate shape; `_reject_blank`, `CREDENTIAL_MAX_LENGTH` precedents
- [Source: backend/app/content/service.py:480-535] — `search_content_for_skill`, the exact shape this story's `submit_manual_content` mirrors (require_hr_admin → 404 check → response), and `_not_found_skill()`
- [Source: backend/app/skills/router.py] — thin-route convention, `content_lookup_route`'s exact shape to mirror
- [Source: backend/tests/test_content_ingestion.py:212-247] — `test_manual_seed_content_never_calls_youtube_client`, the pattern Task 2's "never calls youtube_client/udemy_client" test mirrors
- [Source: backend/tests/test_skills_router.py:1-53] — router test pattern (private engine, `_login` helper, 403/401/404/422 assertions)
- [Source: frontend/src/features/admin/ApiKeysModal.tsx] — self-contained-component-over-Dialog pattern this story's `ManualContentEntryForm`/`ContentPreviewModal` follow
- [Source: frontend/src/pages/dev/ApiKeysModalDemo.tsx] — the dev-route pattern Task 8 mirrors exactly
- [Source: frontend/src/lib/api/adminApiKeysApi.ts] — thin typed-API-client pattern Task 5 mirrors
- [Source: frontend/src/lib/utils/duration.ts] — existing duration-parsing home (Story 2.5's `parseIso8601DurationSeconds`/`formatDurationMinutes`), where Task 4's new functions are added
- [Source: _bmad-output/implementation-artifacts/6-6-live-content-search-youtube-and-udemy.md] — sibling story's full precedent (schema-fork reasoning, route/response-status convention, `_not_found_skill()`, `require_hr_admin` composition, its own explicit forward note about this story's candidate shape)
- [Source: _bmad-output/implementation-artifacts/6-5-per-admin-and-org-wide-credential-storage.md] — the dev-route-ahead-of-its-page precedent this story's frontend scope reuses

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- TDD throughout, RED confirmed before each GREEN: `content/schemas.py`'s `ManualContentEntryRequest`/`ManualContentCandidate` (16 tests, `ImportError` confirmed as RED), `content/service.py::submit_manual_content` (6 new tests, `ImportError` confirmed as RED), `skills/router.py`'s route (8 new HTTP-level tests, confirmed 404/401-mismatch as RED before the route existed), `frontend/src/lib/utils/duration.ts`'s `parseDurationToHours`/`estimateDaysToComplete` (11 tests, `TypeError: ... is not a function` confirmed as RED), `ContentPreviewModal.tsx` (6 tests, "Failed to load url" confirmed as RED), `ManualContentEntryForm.tsx` (5 tests, same RED pattern) — each confirmed failing for the right reason before implementation, then passing after.
- No new dependencies added; `_validate_url` uses stdlib `urllib.parse` only, matching Scope Note 4's "no new dependency" call.
- Full backend regression (`pytest`, no filters): `563 passed, 2 skipped, 3 failed` — the 3 failures are the same pre-existing ones documented since Story 6.4 (`test_find_existing_assignment_returns_empty_when_no_match`, `test_assignment_with_no_qualifying_content_has_null_content`, `test_content_match_returns_null_when_no_content_matches_the_skill`). Zero net-new regressions.
- Full frontend regression (`vitest run`): `296 passed` (up from Story 6.5's documented 274 baseline + this story's 22 new tests across `duration.test.ts`, `ContentPreviewModal.test.tsx`, `ManualContentEntryForm.test.tsx`), 0 failed.
- `tsc --noEmit`: 31 errors both before (verified via `git stash`) and after this story's changes — same pre-existing count, zero new TypeScript errors introduced by any new/modified file in this story.
- Live Docker verification: rebuilt both `talentpilot-ai-backend` and `talentpilot-ai-frontend` (`docker compose build backend frontend` + `up -d backend frontend`), both healthy. Backend, via `curl` against the running container as Rita (HR_ADMIN): created a real seeded Skill, called `content-manual` with a valid URL+title+duration — got back `200` with the exact expected shape (`{title, source: "MANUAL", url, duration_hours}`, no `thumbnail_url` key); malformed URL (`"not-a-url"`) — `422 VALIDATION_ERROR`; nonexistent skill UUID — `404 SKILL_NOT_FOUND`; as Casey (EMPLOYEE) — `403 FORBIDDEN_NOT_HR_ADMIN`. Cleaned up the test Skill via its own `DELETE` endpoint (`204`). Frontend: confirmed the rebuilt container serves `/dev/manual-content-entry-demo` (`200`). **Not performed:** interactive real-browser verification of the two Watch Modal preview states (YouTube embed vs. fallback) — no browser-automation tool (e.g. Playwright) was available in this session, unlike Story 6.5's ad-hoc Playwright session. This is covered instead by `ContentPreviewModal.test.tsx`'s 6 passing RTL tests, which directly assert the iframe `src` for a YouTube URL and the fallback text + external link for a non-YouTube URL — the same two states a manual browser check would have confirmed visually.

### Completion Notes List

- Implemented Story 6.7 end-to-end: `POST /api/admin/skills/{id}/content-manual` (FR-17a), mirroring Story 6.6's `content-lookup` composition exactly (thin route in `skills/router.py` → `content/service.py::submit_manual_content`, `require_hr_admin` → 404-via-`get_skill_by_id` → response). No source-client calls, no `content_catalog` write — both explicitly proven by tests (`test_submit_manual_content_never_calls_youtube_or_udemy_client`, `test_submit_manual_content_never_writes_content_catalog`), mirroring the exact test-level guarantees the epics AC calls out (`manual_seed_content`'s Story 2.3 precedent, Story 6.6's own search-only guarantee).
- **Deliberate deviation from Story 6.6's API-only scope, per explicit user instruction this session:** built a standalone frontend piece (`ManualContentEntryForm.tsx` + `ContentPreviewModal.tsx`) ahead of Story 6.10's real Skills tab, following Story 6.5's dev-route precedent (`ApiKeysModalDemo.tsx`) rather than Story 6.6's defer-everything-to-6.10 precedent. Exercised via a new `/dev/manual-content-entry-demo` route.
- **New schema, not a reuse of Story 6.6's `ContentLookupCandidate`:** added `ManualContentCandidate` with no `thumbnail_url` field at all (not just `None`) — matches that schema's own forward-looking docstring, avoids letting a manual candidate silently claim a field it never has.
- **New URL-format validator** (`content/schemas.py::_validate_url`, stdlib `urllib.parse` only) — no prior helper existed for this; `ManualContentCreate` (the CLI's manual-seed schema) never validated URLs at all since a human operator was trusted there. This story's HR-Admin-facing path needed the same "well-formed URL, no reachability check" bar the epics AC specifies.
- **Frontend `[Approve]` button is deliberately disabled, not wired or omitted:** it would call Story 6.8's `POST /api/admin/content/attach`, which doesn't exist yet. Rendered with a `disabled` state and an explanatory `title` attribute so Story 6.10 can wire it up later without a layout change, per this story's own Scope Note 7 — verified by an explicit test (`the Approve button on the candidate card is disabled`).
- **`ContentPreviewModal.tsx` is a new, minimal component — deliberately not `VideoPlayerDemo.tsx`:** that component bundles the Employee-facing YouTube Adapter + watch-progress capture service (Story 4.x), none of which applies to an HR Admin previewing an unapproved candidate. The new modal is a bare iframe embed (YouTube-recognizable URLs) or an explicit "Preview not available" fallback with an "Open in new tab" link, matching the UX spec's Watch Modal section exactly (`watch-modal-*` object IDs).
- Zero net-new regressions: backend 563 passed / 2 skipped / same 3 pre-existing failures since Story 6.4; frontend 296/296 passed (22 new tests); `tsc --noEmit` unchanged at 31 pre-existing errors (verified against the pre-story baseline via `git stash`). Live-verified via `curl` against rebuilt Docker containers (happy path, malformed-URL 422, nonexistent-skill 404, EMPLOYEE 403) plus a rebuilt-frontend-container route-serves check. Real-browser interactive verification of the two Watch Modal states was not performed this session (no Playwright/browser tool available) — covered instead by `ContentPreviewModal.test.tsx`'s passing automated tests for both states.

### File List

New files:
- `frontend/src/lib/api/adminContentApi.ts`
- `frontend/src/features/admin/ContentPreviewModal.tsx`
- `frontend/src/features/admin/ManualContentEntryForm.tsx`
- `frontend/src/pages/dev/ManualContentEntryDemo.tsx`
- `frontend/src/tests/ContentPreviewModal.test.tsx`
- `frontend/src/tests/ManualContentEntryForm.test.tsx`
- `frontend/src/lib/utils/duration.test.ts`

Modified files:
- `backend/app/content/schemas.py` -- adds `ManualContentEntryRequest`, `ManualContentCandidate`, `_validate_url`, `MANUAL_URL_MAX_LENGTH`
- `backend/app/content/service.py` -- adds `submit_manual_content`
- `backend/app/skills/router.py` -- adds `POST /{skill_id}/content-manual`
- `backend/tests/test_content_schemas.py` -- 6 new tests
- `backend/tests/test_content_service.py` -- 6 new tests
- `backend/tests/test_skills_router.py` -- 8 new tests
- `frontend/src/lib/utils/duration.ts` -- adds `parseDurationToHours`, `estimateDaysToComplete`
- `frontend/src/App.tsx` -- adds the `/dev/manual-content-entry-demo` route
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- story status tracking

Modified again by code review patches (2026-09-10):
- `backend/app/content/schemas.py` -- `duration_hours` gained `gt=0` (rejects negative/zero/NaN)
- `backend/tests/test_content_schemas.py` -- 4 new tests (non-positive-duration rejection x3 parametrized as 1, URL-over-max-length rejection, URL-at-max-length acceptance)
- `frontend/src/features/admin/ContentPreviewModal.tsx` -- `extractYoutubeId` rewritten from a substring regex to an actual hostname check via `new URL()`
- `frontend/src/tests/ContentPreviewModal.test.tsx` -- 1 new test (non-YouTube URL containing a `youtube.com/watch?v=` substring no longer misidentified as embeddable)

## Change Log

- 2026-09-10: Story 6.7 created (`bmad-create-story`, condensed given the story's tightly-scoped single-endpoint-plus-component shape). Unlike Story 6.6's API-only kickoff, this story deliberately includes both the backend endpoint and a standalone frontend component, per explicit user instruction, following Story 6.5's dev-route precedent instead.
- 2026-09-10: Story 6.7 implemented (`bmad-agent-dev`, TDD, same session as creation). `POST /api/admin/skills/{id}/content-manual` (FR-17a), mirroring Story 6.6's exact composition. New `content/schemas.py::ManualContentCandidate` (deliberately not a reuse of `ContentLookupCandidate` -- no `thumbnail_url` field) and `_validate_url` (stdlib `urllib.parse`, no new dependency). New `content/service.py::submit_manual_content`, proven by test to never call `youtube_client`/`udemy_client` or write `content_catalog`. New thin route in `skills/router.py`. Frontend: `ManualContentEntryForm.tsx` (the "Paste a link" tab, UX spec `content-lookup-manual-*` object IDs, `[Approve]` deliberately disabled pending Story 6.8) and `ContentPreviewModal.tsx` (a new, minimal Watch Modal -- explicitly not `VideoPlayerDemo.tsx`'s Employee-facing Adapter/capture-service machinery), exercised via a new `/dev/manual-content-entry-demo` dev route. 22 new frontend tests + 20 new backend tests, all passing on the RED→GREEN cycle. Zero net-new regressions: backend 563 passed / 2 skipped / same 3 pre-existing failures since Story 6.4; frontend 296/296; `tsc --noEmit` unchanged at 31 pre-existing errors (verified against the pre-story baseline via `git stash`). Live-verified via `curl` against rebuilt Docker containers (happy path, 422 malformed URL, 404 nonexistent skill, 403 EMPLOYEE) plus a rebuilt-frontend-container route-serves check; real-browser interactive verification of the two Watch Modal preview states was not performed (no Playwright/browser tool available this session) -- covered instead by `ContentPreviewModal.test.tsx`'s automated assertions of both states. Status -> review.
- 2026-09-10: `bmad-code-review` (3 parallel adversarial layers -- Blind Hunter, Edge Case Hunter, Acceptance Auditor; Acceptance Auditor reported a fully clean pass, zero AC/Scope-Note violations). 0 decision-needed, 3 patches applied, 0 deferred, 15 dismissed (including two false positives caught by reading code outside the diff: `extractErrorMessage`'s field assumption is actually correct per `core/errors.py`'s centralized error envelope, and "title never trimmed" was wrong -- `_reject_blank` already strips it). Patches (all TDD, 5 new tests, all passing): `ManualContentEntryRequest.duration_hours` gained `Field(gt=0)` -- a direct API call could previously submit a negative or zero duration, which would echo back and render as a nonsensical "≈ -20 days to complete" on the frontend (also rejects NaN, since `NaN > 0` is always `False`); added the missing test coverage for `MANUAL_URL_MAX_LENGTH`'s 2048-char boundary (the guard itself already existed, just untested); `ContentPreviewModal`'s YouTube-URL detection rewritten from a substring regex to an actual `new URL().hostname` check -- the most serious finding: a non-YouTube URL that merely *contained* a `youtube.com/watch?v=`-shaped substring (e.g. in a query parameter) was silently embedded as an unrelated YouTube video instead of showing the correct "preview not available" fallback. Dismissed findings included: a deliberate architectural choice (AD-11, not checking `ever_assigned`), several already-covered-by-spec behaviors (unparseable duration silently omitted per the UX spec's own wording), and a few unreachable-in-practice races (the Review button already disables during submission; the Dialog's backdrop already blocks re-triggering while the preview modal is open). Full regression re-verified: backend 568 passed (5 new) / 2 skipped / same 3 pre-existing failures; frontend 297/297 (1 new); `tsc --noEmit` unchanged at 31 pre-existing errors. Live-reverified via `curl` against rebuilt Docker containers (negative/zero duration now 422, positive duration still 200). Status -> done.
