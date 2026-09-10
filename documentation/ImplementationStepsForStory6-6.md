# Implementation Steps for Story 6-6: Live Content Search — YouTube (Per-Admin) & Udemy (Org-Wide) (FR-17, AD-7 branches 2 & 3)

**Story Key:** 6-6-live-content-search-youtube-and-udemy
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.6 gives an HR Admin a live, on-demand search endpoint — `POST /api/admin/skills/{id}/content-lookup` — that searches YouTube (using the calling Admin's own stored key, Story 6.5) and Udemy (using the org-wide credential, Story 6.5) for content matching a Skill, returning unwritten candidate results for later review/approval (Story 6.8). A scope decision was made explicitly at kickoff: the epics file scopes this story as **API-only** — the search UI (tabs, result cards, "Search Results" labeling) is Story 6.10's job — so this story ships zero frontend code, unlike Story 6.5's API+UI pattern.

The work happened in three passes in the same overall session: (1) research into the existing codebase (YouTube client shape, Story 6.5's credential storage, architecture spine text) via a dedicated research subagent, followed by condensed story authoring and full TDD implementation, invoked via `/bmad-agent-dev`; (2) an adversarial code review pass (`/bmad-code-review`) that found and fixed 5 real issues, the most serious being a credential-decrypt failure that could 500 the whole request and discard the sibling source's already-computed results; (3) live Docker verification against the real YouTube Data API, both before and after the review's patches.

---

## Agents Invoked

### 1. **Research Agent (Explore)**

**Purpose:** Gather implementation context before writing the story — exact shapes of `youtube_client.py`, Story 6.5's credential storage/decrypt boundary, the architecture spine's AD-6/AD-7/AD-10 text, existing router/test conventions, and the `skills/router.py` composition question.

**When Invoked:** Immediately after the user confirmed the API-only scope decision
**Model Capability:** Sonnet 5 (session model)
**Input:** Six numbered research questions covering `youtube_client.py`'s exact function signatures and exception shape; `content/service.py`/router auth-gating conventions; Story 6.5's `admin_api_keys`/`org_api_credentials` schema and decrypt boundary; the architecture spine's AD-6/AD-7 text verbatim; existing router test patterns; and how `skills/router.py` should compose with `content/service.py`

**Key Findings Returned:**
- `youtube_client.search_videos`'s exact quota-detection shape (`_is_quota_exceeded`, 403 + reason `quotaExceeded`) and that no `udemy_client.py` existed yet
- Story 6.5's `get_admin_api_key`/`get_org_api_credential` return the **still-encrypted** ORM row — this story would be the first live caller of `decrypt_secret()`
- The AD-7 regression guard (`test_content_ad7_regression_guard.py`) was already stale relative to the architecture spine's own 2026-09-08 amendment — it still banned `search_videos`/`youtube_client` imports outright, which the spine text had already re-scoped away from
- The AD-6 role-gating pattern (service-layer `require_hr_admin(current_user)` as the first line, not a router-level `Depends`) and the exact test conventions (`_login` helper, private-engine pattern) to mirror
- Flagged, as an open question for the story itself to resolve: no existing precedent in the codebase has `skills/router.py` calling into `content/service.py` — a new cross-module composition

**Output:** A structured research report consumed directly into the story's Scope Notes — no code written

---

### 2. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, architectural/reliability concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model)
**Input:** Full diff (`git diff HEAD` against baseline `e09588d7`, with new files added via `git add -N` so they appear in the diff, ~1,400 lines across 16 backend files), instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (14 items):**
- Blocking synchronous I/O (`requests.get`) called directly inside the `async def search_content_for_skill` handler — every live search blocks the entire FastAPI event loop for up to ~30s
- Credential decrypt/parse failures (`_get_source_credential`) sit outside the per-source `try/except`, so a `decrypt_secret()`/`json.loads()` failure 500s the whole request and can discard the sibling source's already-computed results — directly contradicting the endpoint's own NFR-RES1 isolation guarantee
- `youtube_client._is_invalid_key()` overclassifies HTTP 400 + reason `badRequest` as an invalid API key
- Sequential rather than concurrent external calls (latency, not correctness)
- A malformed candidate (missing/`None` title or url) discards an entire source's results via an unhandled Pydantic `ValidationError`
- Unvalidated URL concatenation for Udemy results (`f"https://{subdomain}.udemy.com{result['url']}"` with no null check)
- The re-scoped AD-7 regression guard is a weaker literal-substring grep than the guard it replaced
- No router/HTTP-level tests for the `rate_limited`/`invalid_credential`/`source_error` response variants (only service-unit tested)
- Test-order/global-state fragility in one router test relying on another test's cleanup
- `CONTENT_LOOKUP_MAX_RESULTS` never enforced defensively client-side
- A duration-lookup failure after a successful search discards the already-fetched results
- The Udemy integration is entirely unverified against a real account
- Unguarded `UUID(current_user.user_id)` conversion
- No throttling against an admin rapidly burning their own YouTube quota
- Comment density reads as a defensive audit trail

**Output:** 14 findings; after triage, dedup with Edge Case Hunter, and direct code verification, the two most serious became patches at the top of the queue (credential-decrypt isolation, event-loop blocking), 3 more became patches, 6 routed to defer, 4 dismissed as matching established codebase precedent or explicit out-of-scope architecture decisions

---

### 3. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same full diff, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item):**
- `content/service.py` (~line 306, ~line 320): `_get_source_credential` calls for both YOUTUBE and UDEMY branches sit outside their `try/except` — independently confirmed the same credential-isolation bug Blind Hunter flagged
- `youtube_client.py` (~lines 473-490): `_is_invalid_key` only checks HTTP 400, missing 401/403 (asymmetric with `udemy_client`, which checks both)
- `youtube_client.py` (~lines 473-477): the 400/`badRequest` reason match is overbroad
- `content/service.py` (~line 279, ~line 258): a missing/null `url`/`video_id` in a source's result produces a malformed link with no error surfaced
- `content/service.py`: synchronous `requests.get()` calls inside the async route handler
- `test_content_ad7_regression_guard.py`: the prior ban on routers importing `youtube_client` directly was dropped with nothing narrower replacing it

**Output:** 7 structured findings; the two credential-isolation instances and the event-loop-blocking finding matched Blind Hunter's independently and were merged as the two highest-priority patches; the 401/403 and `badRequest`-overclassification findings were confirmed real but routed to defer (unverifiable without a live revoked YouTube key); the AD-7 guard deletion finding was dismissed as mandated by the architecture spine's own pre-existing amendment

---

### 4. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.6's literal Given/When/Then acceptance criteria and its 10 numbered Scope Notes.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers, background)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full, read directly) + the same diff

**Key Findings Identified:**
- **None requiring remediation.** Explicitly confirmed all 7 ACs (per-admin YouTube key never referencing `settings.YOUTUBE_API_KEY`, the `no_credential` case, the org-wide Udemy credential, per-source error isolation, the 429 rate-limit signal, the result shape with no `content_catalog` write, the blanket 403 for EMPLOYEE) and all 10 Scope Notes (the route/logic split, the repository decrypt functions, the `_get_source_credential` orchestrator, the Udemy endpoint/auth/rate-limit `[ASSUMPTION]`, the additive `youtube_client.InvalidCredentialError`, the flat response envelope, the always-both-sources request shape, the search-only guarantee, and the re-scoped AD-7 guard)
- Noted two minor, non-violating naming adjustments (a docstring-only `CREDENTIAL_SCOPE` mapping instead of a literal dict; `parse_content_info_to_hours` without a leading underscore since it's called cross-module) as sensible, not deviations

**Output:** A fully clean pass — zero findings

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development api and ui for the story 6-6-live-content-search-youtube-and-udemy refer the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, dispatched toward story 6.6 development. Before dispatching to implementation, surfaced a real scope question to the user (the epics file scopes 6.6 as API-only, with the search UI assigned to Story 6.10) via `AskUserQuestion` rather than assuming either direction — user chose "API only, per epics."

---

### 2. **`/bmad-dev-story` Skill (story creation condensed inline + implementation)**

**Purpose:** Create the story file and implement it in the same pass.

**When Invoked:** Immediately after the scope decision
**Workflow Steps Executed:**
1. Discovered no story file existed yet for `6-6-...` (sprint-status showed `backlog`) — pulled the full literal AC text from `epics.md` (Story 6.6, lines 2269-2306) and cross-referenced FR-17/FR-19 from the PRD
2. Delegated exhaustive codebase research to the Explore agent (see above) rather than duplicating that search inline
3. Read the actual current code directly: `content/service.py`/`repository.py`/`schemas.py`/`youtube_client.py` (full), `skills/router.py`/`service.py`/`repository.py`, `core/secrets.py`, `core/errors.py`, `test_content_ad7_regression_guard.py`, `test_youtube_client.py`, `test_skills_router.py`, `main.py` — to ground every design decision in the codebase's actual current conventions rather than guessing
4. Ran two `WebSearch`/`WebFetch` passes attempting to pull Udemy for Business's real Courses API v2.0 documentation (official PDF was unrenderable in this environment, the HTML support article returned 403) — settled for public search-result summaries and explicitly flagged the resulting endpoint/auth/rate-limit shape as an `[ASSUMPTION]` rather than presenting it as verified
5. Resolved 6 real design decisions during story-writing, written directly into 10 numbered Scope Notes: (a) the route lives in `skills/router.py`, the logic in `content/service.py` — the one new cross-module composition this codebase hadn't needed before; (b) two new decrypt-and-return repository functions rather than changing Story 6.5's existing (already-`done`) functions; (c) a `_get_source_credential` orchestrator named directly from AD-10's own forward-looking text; (d) two new **optional** `UDEMY_ORGANIZATION_SUBDOMAIN`/`UDEMY_ACCOUNT_ID` settings to resolve a real gap (Udemy's org-wide credential doesn't include the org's own portal subdomain/account id); (e) a purely-additive `InvalidCredentialError` on `youtube_client.py`; (f) a flat (not nested-per-source) response envelope
6. Generated the story file with 10 Scope Notes, then implemented it directly in the same session, task by task, TDD red-green-refactor: `core/config.py` settings → `skills/service.py::get_skill_by_id` wrapper → `youtube_client.InvalidCredentialError` → new `content/udemy_client.py` → `content/repository.py` decrypt functions → `content/schemas.py` → `content/service.py::search_content_for_skill` orchestrator → `skills/router.py` route → re-scoped `test_content_ad7_regression_guard.py`
7. Confirmed RED (import error / 404 / `ModuleNotFoundError`) before every implementation step, without exception
8. Full backend regression (532 passed, 2 skipped, same 3 pre-existing failures); rebuilt and redeployed the Docker backend image; live-verified via `curl`: no-credential state, EMPLOYEE 403, and a real, unmocked live search against the actual YouTube Data API (5 real results, correctly-computed durations) — Udemy left unverified live (no sandbox credential available)

**Output File:** `_bmad-output/implementation-artifacts/6-6-live-content-search-youtube-and-udemy.md`
**Sprint Status:** `6-6-...`: `backlog` → `ready-for-dev` → `review` (created and implemented in the same pass)

---

### 3. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-6-live-content-search-youtube-and-udemy"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from the explicit story name in the user's request (Tier 1). `baseline_commit` (`e09588d7`) confirmed to match current `HEAD` exactly, so diff source = uncommitted changes; new files (`udemy_client.py`, `test_udemy_client.py`) added to the diff via `git add -N` (intent-to-add, no content staged) so they appeared alongside the modified files. Diff saved to a scratchpad file (~1,400 lines) rather than inlined into subagent prompts. Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor as three parallel background subagents (`review_mode = "full"`, story file as spec), each given a file path to the saved diff to read directly. All three returned independently over the following ~2-4 minutes.
- **Step 03 (Triage):** Normalized 21 raw findings (14 Blind Hunter + 7 Edge Case Hunter; Acceptance Auditor returned zero) down to 15 distinct findings after dedup. Read the actual code at every finding's location before rating severity rather than trusting the diff hunk alone — e.g., confirmed `youtube_client.search_videos` already filters out items with a missing `video_id` before Edge Case Hunter's "missing video_id" sub-claim could be rated (found not reachable for YouTube, but genuinely reachable for Udemy's missing-`url` case, which has no equivalent upstream filter). Routed the result into 0 decision-needed, 5 patch, 6 defer, 4 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection and the 6 deferred items appended to `deferred-work.md` under a new dated heading. User chose "fix all of them" for the 5 patch findings.

**Patches Applied (all TDD — RED confirmed, then implemented, then GREEN):**
1. `_get_source_credential(...)` calls for both YOUTUBE and UDEMY moved inside their source's own `try/except`, so a `decrypt_secret()`/`json.loads()` failure is classified as `source_error` like any other search failure instead of 500ing the whole request and discarding the sibling source's results — the most serious finding, directly restoring the endpoint's own NFR-RES1 guarantee. 2 new tests, including one proving a Udemy decrypt failure (evaluated *after* YouTube's results are computed) no longer discards those already-successful results.
2. `_search_youtube`/`_search_udemy` now run via `asyncio.to_thread(...)` instead of calling `requests.get`-based clients directly inside the async handler, so a slow/hanging external API call no longer blocks the FastAPI event loop for every other concurrent request. Verified by the full existing test suite staying green plus a live re-verification (real YouTube search, ~1s wall time) against a rebuilt Docker container.
3. `get_video_durations`'s own `try/except` added inside `_search_youtube` — a duration-fetch failure now degrades gracefully to `duration_hours=None` for that batch instead of discarding the already-successful search results entirely. 1 new test.
4. `_search_udemy` now skips (with a logged warning) any result with a falsy `url` instead of interpolating `None` into the returned link (`https://sails.udemy.comNone`). 1 new test with a mixed good/broken result pair, asserting only the good one is returned.
5. 3 new router-level (`test_skills_router.py`) tests added, asserting the real HTTP response shape for the `rate_limited`, `invalid_credential`, and `source_error` variants — previously only exercised at the service-unit level with directly-mocked functions.

**Output:** Story status → `done`; full regression re-verified — backend 539 passed (7 net new) / 2 skipped / same 3 pre-existing failures. Docker backend image rebuilt and redeployed a second time with the patches applied, and a real live YouTube search re-verified via `curl` (confirming the `asyncio.to_thread` offload works correctly end-to-end), plus a fresh EMPLOYEE-403 check.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 6 deferred items logged to `deferred-work.md` under a new dated heading
- Sprint status synced (`6-6-...`: `backlog` → `ready-for-dev` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/app/content/udemy_client.py` | Thin REST wrapper mirroring `youtube_client.py`'s shape — `search_courses`, `RateLimitExceededError`, `InvalidCredentialError`, `parse_content_info_to_hours`; endpoint/auth/rate-limit shape documented as an `[ASSUMPTION]` |
| `backend/tests/test_udemy_client.py` | 10 tests — successful parse, 429/401/403 classification, unset-config failure, `content_info` parsing (hit/miss/None) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/core/config.py` | Adds `UDEMY_ORGANIZATION_SUBDOMAIN`, `UDEMY_ACCOUNT_ID` (both optional, default `None`) |
| `backend/.env.example` | Commented placeholders for the two new settings |
| `backend/app/content/youtube_client.py` | Adds `InvalidCredentialError`, `_is_invalid_key` (purely additive — `run_ingestion_job`'s existing catch-all is unaffected) |
| `backend/app/content/repository.py` | Adds `get_decrypted_admin_youtube_key`, `get_decrypted_org_udemy_credential` — the first live `decrypt_secret()` callers in this codebase |
| `backend/app/content/schemas.py` | Adds `ContentLookupRequest`, `ContentLookupCandidate`, `ContentLookupSourceError`, `ContentLookupResponse` |
| `backend/app/content/service.py` | Adds `search_content_for_skill`, `_get_source_credential`, `_search_youtube`, `_search_udemy`, `_parse_iso8601_duration_hours`, `_not_found_skill`, `CONTENT_LOOKUP_MAX_RESULTS`; code-review patches: credential fetches moved inside their `try/except`, `asyncio.to_thread` offload, graceful duration-lookup degradation, missing-url skip |
| `backend/app/skills/service.py` | Adds `get_skill_by_id` wrapper, mirroring `get_skill_embedding`'s existing shape |
| `backend/app/skills/router.py` | Adds `POST /{skill_id}/content-lookup` |
| `backend/tests/test_youtube_client.py` | 2 new tests (`InvalidCredentialError` classification) |
| `backend/tests/test_content_repository.py` | 4 new tests (decrypt-and-return round trips) |
| `backend/tests/test_content_service.py` | 13 new tests + 4 code-review-patch tests (17 total: happy path, no-credential combinations, both-directions NFR-RES1 isolation, invalid-credential/source-error/404/403, never-writes-`content_catalog`, decrypt-failure isolation x2, duration-lookup degradation, missing-url skip) |
| `backend/tests/test_skills_service.py` | 2 new tests (`get_skill_by_id` round trip / not-found) |
| `backend/tests/test_skills_router.py` | 7 new tests + 3 code-review-patch tests (10 total: happy path, no-credential, 403/401/404/422, plus the 3 new HTTP-level failure-shape tests) |
| `backend/tests/test_content_ad7_regression_guard.py` | Re-scoped per the architecture spine's 2026-09-08 amendment — now bans `run_ingestion_job`/`settings.YOUTUBE_API_KEY` from routers instead of `search_videos`/`youtube_client` imports |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-6-live-content-search-youtube-and-udemy.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-6-...`: `backlog` → `ready-for-dev` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 6 new items added under a new "Deferred from: code review of 6-6-..." heading |
| `documentation/ImplementationStepsForStory6-6.md` | This file |

### Not Changed (by design)

- Any frontend file — API-only per the confirmed kickoff scope decision; the search UI is Story 6.10's job
- `content/admin_api_keys_router.py` — Story 6.5's read-only status endpoint, untouched
- `content_catalog`/`ContentCatalog` — no write path exists in this story; writing happens only in Story 6.8's (not yet built) approve action

---

## Implementation Workflow Summary

### Phase 0: Scope Decision
**Skill:** `/bmad-agent-dev`
- User's initial message asked for "api and ui" for Story 6.6, but the epics file explicitly scopes 6.6 as API-only (search UI is Story 6.10's job) — surfaced this as a real, user-decidable scope question via `AskUserQuestion` rather than guessing; user confirmed "API only, per epics"

### Phase 1: Research + Story Creation
**Agent:** Explore (background research) · **Skill:** `/bmad-dev-story` (condensed story creation)
- Delegated exhaustive codebase research (YouTube client shape, Story 6.5's credential boundary, architecture spine text, router/test conventions) to a dedicated subagent rather than duplicating that search inline
- Attempted to pull real Udemy for Business API documentation via `WebSearch`/`WebFetch`; both the official PDF and the HTML support article were inaccessible in this environment — settled for public search-result summaries and explicitly flagged the resulting shape as an `[ASSUMPTION]`
- Resolved 6 real design decisions during story-writing, documented as 10 numbered Scope Notes, including the one new cross-module composition this codebase hadn't needed before (`skills/router.py` calling into `content/service.py`)

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, backend only)**
- 28 new backend tests across `skills/service.py`, `youtube_client.py`, the new `udemy_client.py`, `content/repository.py`, `content/service.py`, and `skills/router.py`
- RED confirmed (import error / 404 / `ModuleNotFoundError`) before every single implementation step
- One test-authoring bug caught immediately by the RED→GREEN cycle itself (a duration-hours expectation computed wrong by hand, fixed on the first failing run)
- Full regression pass — 532 passed, 2 skipped, same 3 pre-existing failures
- Live end-to-end verification via `curl` against a rebuilt Docker container, including one real, unmocked live search against the actual YouTube Data API (Udemy left unverified — no sandbox credential available)
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, all background subagents, single pass
- **Findings:** 21 raw → 15 after dedup → 0 decision-needed, 5 patch, 6 defer, 4 dismiss
- **Most serious finding, independently confirmed by two review layers:** credential-decrypt calls sat outside their source's `try/except`, so a decrypt failure could 500 the whole request and discard the sibling source's already-computed results — a direct contradiction of the endpoint's own advertised NFR-RES1 isolation guarantee
- **Action:** user chose "fix all of them" — all 5 patches applied with 7 new tests, re-verified live via a real post-patch YouTube search
- Output: 539 passed (up from 532 before review), 2 skipped, same 3 pre-existing failures; story marked `done`

---

## Test Coverage

### New/Extended Test Files (35 tests total from this story, post-review)
- `test_skills_service.py` — 2 new tests: `get_skill_by_id` round trip / not-found
- `test_youtube_client.py` — 2 new tests: `InvalidCredentialError` on a 400/`keyInvalid`-or-`badRequest` body; confirms an unrelated 400 reason still raises the generic exception
- `test_udemy_client.py` — 10 new tests: successful parse, 429/401/403 classification, unset-subdomain/account-id failure, `content_info`-to-hours parsing (decimal, singular, no-match, None)
- `test_content_repository.py` — 4 new tests: decrypt-and-return round trips for both credential types, `None` when not configured
- `test_content_service.py` — 17 new tests (13 original + 4 code-review patches): happy path both sources, YouTube-only/neither-configured combinations, both-directions NFR-RES1 isolation (YouTube quota doesn't block Udemy and vice versa), invalid-credential for both sources, generic source_error, 404/403, never-writes-`content_catalog`, decrypt-failure isolation (both directions), duration-lookup graceful degradation, missing-url skip
- `test_skills_router.py` — 10 new tests (7 original + 3 code-review patches): full HTTP-level matrix (both sources configured, no-credential, 403/401/404/422) plus the 3 new failure-shape tests (`rate_limited`/`invalid_credential`/`source_error` at the real HTTP layer)
- `test_content_ad7_regression_guard.py` — re-scoped (1 existing test re-asserted against the amended symbol set, not a net-new test)

### Regression Verification
- Full backend suite run after implementation (532 passed) and again after the code review's patches (539 passed) — same 3 pre-existing, unrelated failures at every stage (`test_find_existing_assignment_returns_empty_when_no_match`, `test_assignment_with_no_qualifying_content_has_null_content`, `test_content_match_returns_null_when_no_content_matches_the_skill`, documented since Story 6.4)
- Live-verified end-to-end via `curl` against a rebuilt/redeployed Docker container, both before and after the review's patches — including two separate real, unmocked live searches against the actual YouTube Data API (5 real results with correctly-computed durations each time)

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-7 branch 2: per-admin YouTube credential, never the shared batch key** | `_get_source_credential` dispatches to `get_decrypted_admin_youtube_key(admin_id=...)`, never reads `settings.YOUTUBE_API_KEY`; the AD-7 regression guard re-scoped to assert this explicitly | `content/service.py`, `content/repository.py`, `test_content_ad7_regression_guard.py` |
| **AD-7 branch 3: org-wide Udemy credential, mirroring `youtube_client.py`'s shape** | New `content/udemy_client.py` — a search function + a dedicated rate-limit exception, called with the org's decrypted `client_id`/`client_secret`, never a per-admin key | `content/udemy_client.py`, `content/service.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | `search_content_for_skill` calls `require_hr_admin(current_user)` first, before the 404 check — matching every other admin-gated function in this codebase | `content/service.py` |
| **AD-10: `CREDENTIAL_SCOPE` orchestration, decrypt boundary preserved** | `_get_source_credential` dispatches per source without decrypting itself; both new repository functions decrypt internally, preserving Story 6.5's repository-only decrypt boundary | `content/service.py`, `content/repository.py` |
| **AD-1: single-owner module, cross-module calls via Service API only** | The new route lives in `skills/router.py` (URL convention) but delegates all search/credential logic to `content/service.py`; a new `skills/service.py::get_skill_by_id` thin wrapper lets `content/service.py` do its 404 check without querying the `skills` table directly | `skills/router.py`, `skills/service.py`, `content/service.py` |
| **NFR-RES1: one source's failure never blocks the other** | Both YOUTUBE and UDEMY branches run in independent `try/except` blocks, each classifying failures into a 4-value error union; code review closed a real gap where a credential-decrypt failure could still violate this guarantee | `content/service.py` |

---

## Key Technical Achievements

✅ **Surfaced a real scope ambiguity to the user instead of guessing** — the epics file explicitly scopes Story 6.6 as API-only with the UI deferred to Story 6.10, contradicting the user's literal "api and ui" phrasing; asked rather than assumed, and got a clear, documented answer before writing any code
✅ **Delegated exhaustive research to a subagent rather than duplicating it inline** — a single Explore agent call returned exact function signatures, the decrypt boundary, and the amended AD-7 text, all consumed directly into the story's Scope Notes
✅ **Resolved a genuinely new architectural composition, not a copy-paste of an existing pattern** — `skills/router.py` calling into `content/service.py` had no prior precedent in this codebase; documented the reasoning (URL ownership vs. logic ownership) rather than silently picking a side
✅ **Documented an external-API assumption honestly instead of presenting an educated guess as fact** — Udemy for Business's real API docs were inaccessible in this environment (PDF unrenderable, HTML 403'd); the resulting endpoint/auth/rate-limit shape is explicitly flagged `[ASSUMPTION]` in the story, the code's docstrings, and the deferred-work ledger
✅ **Code review caught a bug that contradicted the code's own advertised guarantee** — the credential-decrypt-outside-try/except bug directly violated the endpoint's own docstring claim (NFR-RES1, "one source's failure never blocks the other"); independently confirmed by two separate adversarial review layers before being fixed
✅ **Live-verified twice with a real external API, not just mocked tests** — a genuine, unmocked search against the YouTube Data API both before and after the code review's patches, proving the `asyncio.to_thread` event-loop fix didn't silently break the live path
✅ **Zero regressions across both full-suite runs** — 532 → 539 passed, identical pre-existing failure count at every stage

---

## Deferred Items (Not Story 6-6 Scope)

1. **`youtube_client._is_invalid_key`'s 400/`badRequest` classification and its lack of 401/403 handling** — unverifiable without a live revoked YouTube key, already flagged `[ASSUMPTION]` in the story itself
2. **Sequential rather than concurrent external calls** — latency-only, subsumed by the `asyncio.to_thread` patch (sequential-within-a-thread is an acceptable pilot-scale tradeoff)
3. **One router test's credential-state cleanup relies on another test's `finally` block** — matches an already-accepted shared-singleton-row test fragility pattern from Story 6.5's own review
4. **Unguarded `UUID(current_user.user_id)` conversion** — pre-existing pattern from Story 6.5's `content/service.py` functions, not introduced by this story
5. **`CONTENT_LOOKUP_MAX_RESULTS` not defensively enforced client-side** — trivial, low realistic blast radius if a source ever ignores the parameter
6. **A missing/`None` title from either source still discards that source's whole result set** — same root-cause family as the missing-url patch, lower likelihood since both real APIs reliably populate title

---

## Conclusion

Story 6-6 is **✅ DONE** after a research-then-implement cycle (API-only, per an explicit kickoff scope decision) followed by one full adversarial code review pass:

- All 7 acceptance criteria satisfied, confirmed independently by a clean Acceptance Auditor pass
- A genuinely new architectural composition (`skills/router.py` → `content/service.py`) reasoned through and documented rather than forced into an ill-fitting existing pattern
- An inaccessible external API's documentation handled honestly — the resulting shape flagged as a documented assumption, not silently presented as verified fact
- 5 patches applied from this story's own code review, the most serious closing a real gap between the code's advertised reliability guarantee (NFR-RES1) and its actual behavior
- Zero regressions across every full-suite run
- 6 items explicitly deferred (all either pre-existing patterns, out-of-scope hardening, or genuinely unverifiable without a live external credential) rather than silently absorbed or ignored
- Live-verified twice with a real, unmocked YouTube Data API search — before and after the review's patches
- Not yet committed to git in this session

**Ready for:** Story 6.7 (Manual Content Link Entry, FR-17a), the next `backlog` story in Epic 6.
