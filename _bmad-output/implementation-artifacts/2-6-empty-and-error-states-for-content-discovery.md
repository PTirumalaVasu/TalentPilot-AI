---
story_key: 2-6-empty-and-error-states-for-content-discovery
baseline_commit: af9e12a
---

# Story 2.6: Empty & Error States for Content Discovery

**Epic:** 2 (Content Catalog & Matching)
**Status:** done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to handle edge cases in Content Discovery,
so that the UI is always in a defined state.

## Scope Notes (read before starting — this story is 80% verification, not new UI)

1. **4 of this story's 5 AC states already exist and are already tested**, built incidentally by Story 2.5 (`done`) and Story 4.6 (`done`). Confirmed by direct inspection of the current source, not assumed from story titles:
   - "No assignments" page-level empty state → `frontend/src/pages/employee/ContentDiscovery.tsx:97-102`, tested at `frontend/src/tests/ContentDiscovery.test.tsx:159`.
   - "Assignments but no matched Content" per-card empty state → `frontend/src/components/AssignmentCard.tsx:106-113` ("No recommended content yet for this skill. [Contact Rita]" — exact epics.md copy), tested at `ContentDiscovery.test.tsx:171`.
   - "API error fetching content list" page-level error state → `ContentDiscovery.tsx:90-95` ("Couldn't load your assignments." + Try again), tested at `ContentDiscovery.test.tsx:182`.
   - "Continue Watching with no video watched" empty state → `frontend/src/components/ContinueWatchingCard.tsx:172-191` ("Start watching" + Play button, Story 4.6's AC1), tested in `ContinueWatchingCard.test.tsx` (12/12 passing).
   - **Do not rebuild any of these.** Task 1 below is a verification pass (re-run the existing tests, confirm the rendered copy/behavior still matches this story's AC text) — not new implementation. If verification finds a real gap in one of these four, fix only that gap; don't restructure working code.

2. **The 5th state — "Video load failure" — is the one real gap, and it's a bigger gap than the AC line makes it sound.** `frontend/src/components/VideoPlayer.tsx` (Story 4.0, `done`, reused as-is by every story since) has **zero test coverage** (no `VideoPlayer.test.tsx` exists anywhere in the repo — confirmed via glob) and its error UI (`VideoPlayer.tsx:169-181`) is a bare `⚠️ {error}` string with **no retry action at all** — just whatever raw message `onPlayerError_Internal`/`initPlayer`/`onPlayerReady_Internal`'s catch blocks produce (e.g. `"Video not found (removed or private)"`, `"Failed to initialize player: ..."`). This story's AC explicitly requires the literal copy **"This video couldn't be loaded. [Try again]"** with a working retry — that CTA does not exist today. This is the story's real scope: add a retry-capable error UI to `VideoPlayer.tsx` and write its first-ever test file.

3. **CRITICAL — found during story authoring, not part of this story's original scope, but blocks it and everything else:** `frontend/src/lib/api/assignmentsApi.ts` is currently **syntactically broken** on this branch. A bad merge (`1b3d8b8 Merge from Main`, combining Story 2.5's version of this file with Story 3.4's) left `createAssignment`'s function body missing its closing `return response.data;\n}` — `listMyAssignments` is nested *inside* `createAssignment` as an illegal nested `export`, and the file has a net +1 unclosed brace. Confirmed via `npx tsc --noEmit` → `error TS1005: '}' expected`. **`npm run build` is fully broken right now.** It's invisible in `npx vitest run` (148/148 currently pass) only because both files that import from this module (`ContentDiscovery.test.tsx`, `AssignmentModal.test.tsx`) `vi.mock()` it wholesale rather than executing the real file. **Task 0 fixes this first** — nothing in this story (or any future story) can claim a clean `npm run build`/`tsc --noEmit` until it's fixed, and it is a two-minute, mechanical fix (not a design decision).

4. **Do not touch `frontend/src/pages/dev/VideoPlayerDemo.tsx`.** It's a separate, self-contained implementation (Story 4.0's dev-only diagnostic route) that does **not** import or use the `<VideoPlayer>` component — it has its own inline `loadPlayer`/`onPlayerReady`. Story 4.0's own scope note (still binding, see `deferred-work.md`) requires it be preserved 1:1. Changes to `VideoPlayer.tsx` in this story cannot and must not touch it.

## Acceptance Criteria

### AC1 — No assignments (already built, verify only)

**Given** an Employee with zero assignments
**When** Content Discovery loads
**Then** it shows "Nothing in progress right now." (page-level empty state, not a blank grid) — already implemented and tested; re-run `ContentDiscovery.test.tsx` to confirm it still passes unmodified.

### AC2 — Assignments but no matched Content (already built, verify only)

**Given** an assignment whose Skill has no Content clearing the similarity threshold
**When** its card renders
**Then** it shows "No recommended content yet for this skill. [Contact Rita]" instead of a thumbnail/play control — already implemented and tested; re-run to confirm.

### AC3 — Video load failure (real gap — build this)

**Given** the YouTube player fails to load or errors during initialization (invalid/removed video, embed-disabled, network failure, or any of `VideoPlayer.tsx`'s existing catch paths)
**When** the failure occurs
**Then** the player area shows the literal text **"This video couldn't be loaded. [Try again]"** (not the current raw/technical error string) with a working **Try again** button, `role="alert"` on the message (matching this project's established a11y convention — `AssignmentModal.tsx`'s content-lookup error, Story 3.4 round 3 review)

**And** clicking Try again clears the error state and re-attempts player initialization from scratch (reset `playerRef`/`adapterRef`/`captureServiceRef`, call `initPlayer()` again) — it must not get silently blocked by `initPlayer`'s existing `if (playerRef.current) return;` guard, and must not re-inject a duplicate `<script>` tag if the YouTube IFrame API is already loaded (`window.YT` already truthy)

**And** a second, distinct retry can also fail (e.g. still-unavailable video) and re-render the same error+retry state — this is not a one-shot dismissal

### AC4 — Continue Watching with no video watched (already built, verify only)

**Given** an Employee has never recorded any watch progress for an assignment
**When** `<ContinueWatchingCard>` renders
**Then** it shows an explicit "Start watching" empty state, never blank space — already implemented (Story 4.6 AC1) and tested; re-run to confirm.

### AC5 — API error fetching content list (already built, verify only)

**Given** `GET /api/assignments` fails (network error or non-2xx)
**When** Content Discovery attempts to load
**Then** it shows a distinct error message with a Try again action, never a blank grid — already implemented and tested; re-run to confirm.

### AC6 — Each state is visually distinct, never color-only

**Given** all 5 states above
**When** inspected for accessibility
**Then** each is distinguishable by icon + text (or explicit copy), not color alone (WCAG 2.1 AA / NFR-A2) — already true for AC1/2/4/5 (existing icons/badges/button text); AC3's new error state must follow the same convention (keep the existing `⚠️` prefix, add the Try again button, add `role="alert"`).

## Tasks / Subtasks

- [x] **Task 0 (do first, blocking): Fix the broken `assignmentsApi.ts` merge damage** (Scope Note 3)
  - [x] Close `createAssignment`'s function body properly (`return response.data;` then `}`) before the `listMyAssignments` doc comment, restoring `listMyAssignments` as a proper top-level `export`, not a nested declaration
  - [x] Verify `npx tsc --noEmit` (frontend) has zero errors — **partially true**: fixing this specific file's syntax error unmasked 25 *pre-existing, unrelated* `tsc` errors that were dormant behind the fatal parse abort (confirmed via `git stash` against baseline — none introduced by this fix). Logged to `deferred-work.md` rather than fixed (out of scope, same bug class as an already-open Story 3.4 deferred item). `assignmentsApi.ts` itself now parses/type-checks cleanly.
  - [x] Verify `npm run build` (frontend) succeeds end-to-end — **the `tsc &&` gate still fails**, but only due to the pre-existing unmasked errors above, not this fix. Used `npx vite build` (bundler-level) as the practical proxy, matching Story 2.5's established precedent for this exact situation — succeeds cleanly.
  - [x] Re-run `npx vitest run` to confirm 148/148 still pass unaffected (this fix only touches dead/unreachable code paths from the test suite's perspective, since both consuming test files mock the module)

- [x] Task 1: Verification pass on the 4 already-built states (AC1, AC2, AC4, AC5)
  - [x] Run `npx vitest run src/tests/ContentDiscovery.test.tsx` — confirmed: empty-state, per-card-empty, and error+retry tests (12/12) pass, rendered copy matches AC1/AC2/AC5 exactly ("Nothing in progress right now.", "No recommended content yet for this skill. [Contact Rita]", "Couldn't load your assignments." + Try again)
  - [x] Run `npx vitest run src/components/ContinueWatchingCard.test.tsx` — confirmed: AC1 empty-state test (12/12 total) passes, "Start watching" copy matches AC4
  - [x] No drift found — no code changes made to these 3 components in this task, as scoped

- [x] Task 2: `VideoPlayer.tsx` — video-load-failure state with retry (AC3, AC6)
  - [x] Replace the bare `⚠️ {error}` render with the literal copy "This video couldn't be loaded." + a "Try again" button, `role="alert"` on the message container
  - [x] Add a `handleRetry` function: reset `error` to `null`, reset `playerRef.current = null` (and destroy/null `adapterRef.current`/`captureServiceRef.current`/`cleanupListenersRef.current`, mirroring the existing cleanup-on-unmount logic; also clear `iframeRef.current`'s DOM content defensively), then call `initPlayer()` again
  - [x] `initPlayer()` is called directly from `handleRetry` (not re-running the mount `useEffect`'s script-injection branch) — `window.YT.Player` is already available by the time any error/retry can occur, so no duplicate `<script>` tag risk
  - [x] Preserved the existing `onError` prop callback — still invoked with the same `Error` on every failure path, component's external contract unchanged
  - [x] Raw/technical error string kept for debugging via `console.error` (each of the 3 failure sites), never shown in the UI — user-facing text is always the literal AC3 copy

- [x] Task 3: `VideoPlayer.test.tsx` (NEW — first test file for this component) (AC3, AC6)
  - [x] Mocked `window.YT.Player` the same way `VideoPlayerDemo.test.tsx` mocks the YouTube IFrame API
  - [x] Test: `onPlayerError_Internal` (event.data 100) renders the literal copy, a "Try again" button, and `role="alert"`
  - [x] Test: clicking Try again clears the error UI and calls `window.YT.Player` a second time (asserted via mock call count, not just UI absence)
  - [x] Test: a second failed retry re-renders the same error+retry state
  - [x] Test: `initPlayer`'s own synchronous `try/catch` renders the same error+retry UI
  - [x] Bonus: a happy-path test confirming no error/retry UI renders on success (guards against a false-positive `role="alert"` always rendering)
  - [x] Added during patch remediation: `onError` prop callback fires on failure; `onPlayerReady_Internal`'s own try/catch (adapter/capture-service construction failure) reaches the same error+retry UI (Review patches 5, 6)
  - All 7 tests pass (5 original + 2 added during patch remediation); TDD red→green confirmed (4/5 failed before Task 2's implementation, 5/5 pass after, 7/7 pass after patch remediation)

- [x] Task 4: Full regression pass
  - [x] `npx vitest run` — 155/155 passing (148 baseline + 7 `VideoPlayer.test.tsx` tests), zero regressions
  - [x] `npx tsc --noEmit` — same 25 pre-existing errors as after Task 0 (one line number shifted from 115→146 in `VideoPlayer.tsx` due to Task 2's added code, not a new error — confirmed identical error messages/files), zero *new* errors introduced by Task 2/3 or patch remediation
  - [x] `npx vite build` — succeeds cleanly (used in place of the `tsc &&`-gated `npm run build`, per Scope Note 3/Task 0's finding)

### Review Findings

Code review completed 2026-07-11 (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor — run against the working-tree diff against baseline `af9e12a`). 0 decision-needed, 8 patches, 1 deferred, 6 dismissed as noise/already-verified/already-handled. All 8 patches applied 2026-07-11; verified against source rather than trusting prior checklist state (see Completion Notes).

- [x] [Review][Patch] No per-attempt token/mounted guard on the new retry flow — a stale async `onReady`/`onError` from an abandoned attempt can overwrite state for a newer attempt (or fire after unmount), and rapid double-clicks on "Try again" have no re-entrancy guard, orphaning multiple player instances [frontend/src/components/VideoPlayer.tsx: `handleRetry`, `onPlayerReady_Internal`, `onPlayerError_Internal`] — fixed via `attemptIdRef`/`isMountedRef`, checked at the top of every callback.
- [x] [Review][Patch] `handleRetry` never calls the real `YT.Player`'s own `.destroy()` before discarding it — confirmed by reading source that neither `YouTubeAdapter.destroy()` nor `CaptureService.destroy()` ever touches the underlying player object, so each retry abandons a live `YT.Player` instance (with its own iframe/listeners) [frontend/src/components/VideoPlayer.tsx:117-137] — fixed: `handleRetry` now calls `playerRef.current.destroy()` (guarded for the test mocks, which don't implement it) before nulling it out.
- [x] [Review][Patch] `iframeRef.current` likely becomes a stale/detached DOM reference after the first `YT.Player` construction (the YouTube IFrame API replaces the referenced container element with the generated `<iframe>`), so `handleRetry`'s reuse of the same ref for a second `new YT.Player(iframeRef.current, ...)` call risks attaching into a detached node — an established safe pattern (fresh child element per load attempt) already exists in this codebase at `VideoPlayerDemo.tsx`'s `loadPlayer()` [frontend/src/components/VideoPlayer.tsx: `handleRetry`] — fixed: `iframeRef` replaced with a stable `containerRef`; `initPlayer()` now clears it and appends a fresh child element per attempt, matching `VideoPlayerDemo.tsx`.
- [x] [Review][Patch] `role="alert"` wraps both the message text and the interactive "Try again" button, nesting a focusable control inside a live region — deviates from this project's own cited a11y precedent (`AssignmentModal.tsx`/`form-error-text.tsx` scope `role="alert"` to the message text only) [frontend/src/components/VideoPlayer.tsx: render, ~line 203] — fixed: `role="alert"` scoped to the `<p>` message only; the "Try again" `<button>` is a sibling outside the alert region.
- [x] [Review][Patch] No test asserts the `onError` prop callback still fires on failure, despite Task 2's checklist claiming this was verified — matches this project's repeated "a checked box isn't proof of coverage" lesson [frontend/src/components/VideoPlayer.test.tsx] — fixed: added "calls the onError prop with an Error on failure" test.
- [x] [Review][Patch] No test covers the third catch path (`onPlayerReady_Internal`'s own `try`/`catch`, e.g. a `CaptureService`/`YouTubeAdapter` construction failure) reaching the same error+retry UI — only `initPlayer`'s sync throw and `onPlayerError_Internal`'s async event are covered [frontend/src/components/VideoPlayer.test.tsx] — fixed: added "an adapter/capture-service construction failure ... renders the same error+retry UI" test (mocks `CaptureService` to throw once).
- [x] [Review][Patch] `deferred-work.md`'s new entry undercounts/mislabels its own breakdown — says "19 errors... plus one unused-import warning" but `useResumePosition.test.ts` actually has 20 `tsc` errors and the `ContinueWatchingCard.tsx` issue is a real `error TS6133`, not a warning (the total of 25 is correct; the prose breakdown isn't) [_bmad-output/implementation-artifacts/deferred-work.md] — fixed: prose now reads "20 errors" and "1 real `error TS6133`", matching the 25 total.
- [x] [Review][Patch] The literal error copy ("This video couldn't be loaded.") is duplicated as a separate hardcoded string in the test file instead of a shared constant — a future wording change in one place can silently desync from the other [frontend/src/components/VideoPlayer.tsx, VideoPlayer.test.tsx] — fixed: `VIDEO_LOAD_FAILURE_MESSAGE` exported from `VideoPlayer.tsx`, imported and asserted against in `VideoPlayer.test.tsx`.

- [x] [Review][Defer] `onPlayerReady_Internal` attaches `visibilitychange`/`beforeunload` listeners before `cleanupListenersRef.current` is assigned — if the `onPlayerReady?.()` prop callback throws, those listeners leak with no cleanup path [frontend/src/components/VideoPlayer.tsx:165-178] — deferred, pre-existing since Story 4.0, unchanged by this diff's edits to that function (only the catch block's error handling was touched); now more exercisable since retry allows multiple init attempts per session, but the root cause predates this story.

**Dismissed as noise or already-handled**: "duplicate deferred-work.md paragraph" (Blind Hunter) — verified against the real file on disk, only one occurrence exists; the duplication was an artifact of how the diff was pasted into the review subagent's prompt, not a real defect; `onError` prop callback still receiving the raw/technical error string (no AC requires sanitizing the programmatic callback, and there is no current consumer of `onError` anywhere in the codebase); "ships with the canonical `npm run build` command still broken" — already transparently documented in both this story's Task 0/Completion Checklist and `deferred-work.md`, not a hidden gap; `assignmentId: string` → `UUID` branded-type mismatch at the touched line — already captured as part of this same story's own Task 0 deferred-work entry, not a new/separate finding; `sprint-status.yaml`'s `last_updated` field being overwritten rather than appended — the established, consistent convention every prior story in this file already uses (history preserved in the trailing comment log); "diff excerpt given to the Acceptance Auditor was truncated" — a review-process artifact (intentionally trimmed in the prompt to save tokens), not a code defect, and the Auditor itself flagged it as such.

## Dev Notes

### Why this story is scoped as "verify 4, build 1," not "build 5"

Grepping the actual source (not trusting epics.md's story title) shows 4 of the 5 states already shipped as side effects of Story 2.5 (Content Discovery's own empty/error states, built because AC5-AC7 of that story required them) and Story 4.6 (`ContinueWatchingCard`'s own AC1 empty state). Re-implementing them here would be pure duplication — the actual gap epics.md's Story 2.6 line-item is pointing at is `VideoPlayer.tsx`'s error handling, which **every other story since Story 2.5** has explicitly deferred:
- Story 2.5's own Scope Note 8: *"FR-4's 'video couldn't be loaded → [Try again]' consequence is explicitly NOT built by this story... that's Story 4.6/4.7's polish to add."*
- Story 4.6 built `ContinueWatchingCard`'s own error state (a different component, fetching progress — not the video player itself) but did not touch `VideoPlayer.tsx`.

No later story picked it up either. This story is where that deferred thread finally gets closed.

### `initPlayer()`'s existing guard and why retry needs to reset `playerRef`

```js
const initPlayer = () => {
  if (!iframeRef.current || playerRef.current) return;
  ...
```

`playerRef.current` gets set synchronously inside the `try` block (`playerRef.current = new window.YT.Player(...)`) even on a call that will *later* fail asynchronously via `onError` (YouTube's IFrame API constructs the player object first, then may emit an error event once it discovers the video is unavailable). So after a failure, `playerRef.current` is non-null, and a naive second call to `initPlayer()` would hit the early-return guard and silently do nothing. `handleRetry` must null it out first.

### Established a11y/copy precedents to follow (from Story 3.4's review history, not invented here)

- `role="alert"` on inline error messages was a real AC gap found and fixed in Story 3.4 round 3 (`AssignmentModal.tsx`'s content-lookup error was missing it) — apply the same pattern here from the start rather than repeat that finding.
- Literal epics.md copy wins over a component's own ad hoc wording — Story 3.4/3.5 both had review findings where a component's error text didn't literally match the spec string. `VideoPlayer.tsx`'s current messages (`"Video not found (removed or private)"` etc.) are informative but must not be what the user sees for AC3; use the exact "This video couldn't be loaded." text.

### Project Structure Notes

Changes land in:
- `frontend/src/lib/api/assignmentsApi.ts` (MODIFIED — Task 0, mechanical fix, restores `listMyAssignments` as a valid top-level export)
- `frontend/src/components/VideoPlayer.tsx` (MODIFIED — error UI + retry)
- `frontend/src/components/VideoPlayer.test.tsx` (NEW)

No changes expected to:
- `frontend/src/pages/employee/ContentDiscovery.tsx`, `AssignmentCard.tsx` (AC1/AC2/AC5 already correct — Task 1 is verification, only touch if a real drift is found)
- `frontend/src/components/ContinueWatchingCard.tsx` (AC4 already correct)
- `frontend/src/pages/dev/VideoPlayerDemo.tsx` (Scope Note 4 — separate implementation, do not touch)
- `frontend/src/pages/employee/AssignmentWatch.tsx` (mounts `<VideoPlayer>` as-is; its own props/contract are unchanged by this story)
- Any backend file — this story is 100% frontend

## Library/Framework Requirements

- No new dependencies. `VideoPlayer.test.tsx` uses the existing `vitest` + `@testing-library/react` stack already used by every other frontend test in this repo — mock `window.YT` the same way `VideoPlayerDemo.test.tsx` does (check its mock setup first, reuse the pattern rather than inventing a new one).

## Testing Requirements

- Frontend only: `npx vitest run` for unit tests, `npx tsc --noEmit` for type-check, `npm run build` for the full build gate (Task 0 is what finally makes this last one meaningful again after the pre-existing multi-story gap tracked in `deferred-work.md`)
- No backend tests, no live-DB work — this story touches no backend code

## Previous Story Intelligence

From Story 2.5 (`2-5-content-discovery-multi-assignment-grid-view.md`, `done`):
- Built `ContentDiscovery.tsx`'s page-level empty/error states and `AssignmentCard.tsx`'s per-card empty state, all still current and correct (verified directly against source for this story, not assumed).
- Its own Scope Note 8 explicitly named `VideoPlayer.tsx`'s missing retry CTA as future work, not this story's — that "future work" is this story.
- Established pattern: literal epics.md/AC copy wins over ad hoc component wording; `role="alert"` on inline errors; keyboard-operable interactive elements checked via a real dispatched `KeyboardEvent` in tests, not just click simulation.

From Story 4.6 (`4-6-continue-watching-card-empty-and-loaded-states.md`, `done`):
- Built `ContinueWatchingCard.tsx`'s 4-state machine (empty/loading/loaded/error) with its own retry-with-max-attempts pattern (`retryCount`/`maxRetries`) — a reasonable reference for `VideoPlayer.tsx`'s simpler single-retry-button need, though `VideoPlayer.tsx`'s AC3 doesn't require a retry-limit/fallback (no epics.md text asks for one) — don't add one that isn't specified.

From Story 3.4 code review rounds 1-3 (`3-4-hr-assignment-flow-...md`, `done`):
- Recurring, hard-won lessons directly applicable here: unmemoized callbacks in `useEffect` dependency arrays can break re-render timing (the `Dialog` focus-trap bug); a "fix" that only runs against mocked tests can be dead against the real API/DOM (the `content_metadata` wire-key bug) — for `VideoPlayer.tsx`, this means actually exercising `window.YT.Player`'s mocked `onError` callback in a real test, not just asserting a `useState` value changed.

## Architecture Compliance

- **NFR-A2 (accessibility):** AC6 — icon+text/explicit copy on all 5 states, never color-only; `role="alert"` on the new error message.
- No AD-1/AD-2/AD-3/AD-6/AD-8 implications — this story touches no data-owning module, no backend route, no cross-module read composition. Pure frontend UI-state work plus one mechanical merge-conflict fix.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6] — AC text (5 states, WCAG 2.1 AA note)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5, "Page States"] — the original UX-DR7/DR8/DR9/AR-14 language AC1/AC2/AC5's already-shipped implementations were built against
- [Source: frontend/src/pages/employee/ContentDiscovery.tsx, components/AssignmentCard.tsx, components/ContinueWatchingCard.tsx] — the 4 already-built states, read directly this session to confirm current behavior
- [Source: frontend/src/components/VideoPlayer.tsx] — Story 4.0's component, AC3's target for modification
- [Source: frontend/src/lib/api/assignmentsApi.ts] — Task 0's broken file, confirmed via `npx tsc --noEmit`
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — prior `npm run build`/`tsc` gap history (now further extended by the Task 0 finding), `VideoPlayerDemo.tsx`'s "preserve 1:1" precedent
- [Source: _bmad-output/implementation-artifacts/3-4-hr-assignment-flow-multi-step-modal-employee-and-skill-selection.md] — `role="alert"`/literal-copy/mocked-vs-real-API review lessons carried forward

## Git Intelligence

Recent commits (`git log --oneline -6`):
```
af9e12a 2-5-content-discovery-single-assignment-card-view (#54)
1b3d8b8 Merge from Main
cc45d73 Story 3.5: Assignment Creation & Immediate Dashboard Appearance (#52)
afef45a Story 3.5: Assignment Creation & Immediate Dashboard Appearance
a2d6bd5 EPIC 4 RETROSPECTIVE & PR - COMPLETE WORKFLOW SUMMARY (#51)
3df2d02 Story 4-6: Continue Watching Card Component - Full Implementation + Code Review (#49)
```

Established conventions to follow:
- Current branch is `Story2.6`, already checked out (clean except an untracked `.claude/settings.json`, unrelated to this story) — implement directly on it.
- `1b3d8b8`'s "Merge from Main" is the commit that introduced Task 0's bug — it merged Story 2.5's freshly-created `assignmentsApi.ts` (which only had `listMyAssignments`) against `main`'s already-merged Story 3.4 version (`employees`/`skills`/`duplicate-check`/`createAssignment`) and the result is malformed. Worth a clean, isolated commit for Task 0's fix so it's reviewable on its own, separate from the AC3 feature work.
- PRs land on `main` with a `(#N)` suffix per every prior story.

## Completion Checklist

- [x] `assignmentsApi.ts` fixed; `npx tsc --noEmit` unmasked (not caused) 25 pre-existing unrelated errors, logged to `deferred-work.md`; `npx vite build` clean (used in place of the `tsc &&`-gated `npm run build`, see Scope Note 3)
- [x] AC1/AC2/AC4/AC5 re-verified passing, unmodified — no drift found, no copy fixes needed
- [x] `VideoPlayer.tsx` shows "This video couldn't be loaded." with `role="alert"` and a working "Try again" button that resets and re-attempts player init
- [x] `VideoPlayer.test.tsx` created, covering error-render, onError-callback, retry-clears-and-reattempts, repeat-failure, sync-construction-failure, adapter/capture-service-construction-failure, and happy-path-no-error paths (7/7 passing)
- [x] All 5 states confirmed icon/text-based, never color-only
- [x] Full `npx vitest run` — 155/155 passing, zero regressions
- [x] Project context (`_bmad-output/project-context.md`) updated per this project's mandatory-update rule
- [x] Sprint status updated to `review`
- [x] All 8 code-review Patch findings applied (per-attempt guard, `.destroy()` on retry, fresh-child-element pattern, `role="alert"` scoping, 2 new tests, `deferred-work.md` prose fix, shared error-copy constant) — verified against source, `npx vitest run` (155/155), `npx tsc --noEmit` (same 25 pre-existing errors), `npx vite build` (clean)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via `bmad-dev-story`.

### Debug Log References

- `npx tsc --noEmit` (before Task 0 fix) — 1 error: `assignmentsApi.ts(90,1): error TS1005: '}' expected.`
- `npx tsc --noEmit` (after Task 0 fix) — 25 errors, all confirmed pre-existing via `git stash`/`git stash pop` against baseline `af9e12a` (none introduced by this story) — logged to `deferred-work.md`.
- `npx vitest run` (before any change) — 148/148 passing.
- `npx vitest run src/components/VideoPlayer.test.tsx` (before Task 2's implementation, red phase) — 4/5 failed as expected (no `role="alert"`, no retry button, generic copy).
- `npx vitest run src/components/VideoPlayer.test.tsx` (after Task 2, green phase) — 5/5 passing.
- `npx vitest run` (final) — 153/153 passing (148 baseline + 5 new), zero regressions.
- `npx vitest run src/tests/ContentDiscovery.test.tsx src/components/ContinueWatchingCard.test.tsx` (Task 1 verification) — 24/24 passing, no copy drift from AC1/AC2/AC4/AC5's wording found.
- `npx tsc --noEmit` (final) — same 25 pre-existing errors as post-Task-0 (one line number shifted 115→146 in `VideoPlayer.tsx` due to Task 2's inserted code, same underlying error, not new).
- `npx vite build` (final) — succeeds cleanly, 205 modules transformed.

### Completion Notes List

- **This story was ~80% verification, not new implementation, as scoped during story authoring** — direct source inspection at story-creation time correctly found 4 of 5 AC states already built and tested (Story 2.5/4.6). No code changes were needed for AC1/AC2/AC4/AC5; Task 1 was a pure verification pass and found zero drift.
- **Task 0 (fixing `assignmentsApi.ts`'s merge-corrupted `createAssignment`/`listMyAssignments`) surfaced a second, deeper problem**: TypeScript had been silently aborting diagnostic collection for the *entire* project because of that one file's fatal parse error, hiding 25 genuinely pre-existing type errors (`CaptureService`-as-type, `UUID`-branded-type mismatches) in `VideoPlayer.tsx`, `VideoPlayerDemo.tsx`, `ContinueWatchingCard.tsx`, and `useResumePosition.test.ts`. Verified via `git stash` that none were introduced by this story — same bug class first flagged in Story 3.4's deferred-work entry, still unfixed after 2 more stories. Logged as a fresh, more specific deferred-work entry rather than fixed (out of this story's scope; `npx vite build` remains the practical build-verification proxy, matching Story 2.5's established precedent).
- **AC3's real gap matched the story's prediction closely**: `VideoPlayer.tsx` had zero test coverage and no retry mechanism at all. Built via TDD (wrote `VideoPlayer.test.tsx` first against the *pre-implementation* component, confirmed 4/5 tests failed for the right reasons, then implemented `handleRetry` + the new error UI, confirmed 5/5 green).
- **`handleRetry` needed to null out `playerRef.current` before calling `initPlayer()` again** — `playerRef.current` is set synchronously inside `initPlayer`'s `try` block even for a player that fails asynchronously via `onError` later, so a naive retry would hit `initPlayer`'s existing `if (playerRef.current) return;` guard and silently no-op. This was caught by writing the retry test against the real component (not by reasoning about it in isolation) — the first draft of `handleRetry` did in fact fail this exact test until the reset was added.
- No backend changes — this story is 100% frontend, as scoped.

### File List

**New:**
- `frontend/src/components/VideoPlayer.test.tsx`
- `_bmad-output/implementation-artifacts/2-6-empty-and-error-states-for-content-discovery.md` (this story file)

**Modified:**
- `frontend/src/lib/api/assignmentsApi.ts` (Task 0: fixed merge-corrupted `createAssignment`/`listMyAssignments`)
- `frontend/src/components/VideoPlayer.tsx` (Task 2: `handleRetry`, new error+retry UI with `role="alert"` and literal AC3 copy, `console.error` logging of raw diagnostic messages)
- `_bmad-output/implementation-artifacts/deferred-work.md` (logged the newly-unmasked 25 pre-existing `tsc` errors)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status transitions)
- `_bmad-output/project-context.md` (mandatory project-context update)

**Unchanged (as expected):**
- `frontend/src/pages/employee/ContentDiscovery.tsx`, `components/AssignmentCard.tsx`, `components/ContinueWatchingCard.tsx` (AC1/AC2/AC4/AC5 already correct — Task 1 verification found no drift)
- `frontend/src/pages/dev/VideoPlayerDemo.tsx` (Scope Note 4 — separate implementation, not touched)
- `frontend/src/pages/employee/AssignmentWatch.tsx` (mounts `<VideoPlayer>` as-is, contract unchanged)
- No backend files

## Change Log

- 2026-07-11: Story 2.6 created (`bmad-create-story`). Direct source inspection found 4 of the 5 AC states already built and tested by Story 2.5/4.6 (scoped down to verification-only), and one real gap (`VideoPlayer.tsx`'s video-load-failure retry, previously deferred by Story 2.5's own Scope Note 8 and never picked up since). Also found and scoped a critical, pre-existing, unrelated build-breaking bug in `assignmentsApi.ts` (a bad merge left `createAssignment`/`listMyAssignments` malformed, `npx tsc --noEmit` fails, invisible to `vitest` only because both consumers mock the module) as a blocking Task 0.
- 2026-07-11: Story 2.6 implemented (`bmad-dev-story`). Task 0 fixed `assignmentsApi.ts`, which unmasked (not introduced) 25 pre-existing `tsc` errors — confirmed via `git stash` against baseline and logged to `deferred-work.md` rather than fixed, following Story 2.5's established `vite build`-as-proxy precedent. Task 1 verified AC1/AC2/AC4/AC5 with zero drift, zero code changes. Task 2/3 built `VideoPlayer.tsx`'s missing video-load-failure retry UI via TDD (5 new tests, red confirmed before implementation, green after) — the literal "This video couldn't be loaded." copy, `role="alert"`, and a `handleRetry` that correctly resets `playerRef` before re-invoking `initPlayer()` (a bug the test suite itself caught on the first implementation draft). Final: 153/153 frontend tests passing (zero regressions), `npx vite build` clean, `tsc` error count unchanged (25, all pre-existing, one line-shifted). Status → `review`.
- 2026-07-11: All 8 code-review Patch findings applied — per-attempt token/mounted guard (`attemptIdRef`/`isMountedRef`) against stale async callbacks and double-click retry races; `handleRetry` now calls the real `YT.Player.destroy()` before discarding it; the reused-stale-DOM-node risk fixed by switching to a stable `containerRef` with a fresh child element per attempt (matching `VideoPlayerDemo.tsx`'s established pattern); `role="alert"` scoped to the message text only, no longer wrapping the "Try again" button; 2 new tests added (`onError` prop callback fires on failure; `onPlayerReady_Internal`'s own try/catch reaches the same error+retry UI); `deferred-work.md`'s prose breakdown corrected (20 errors / 1 real `error TS6133`, not "19... plus one warning"); error copy deduplicated behind the exported `VIDEO_LOAD_FAILURE_MESSAGE` constant, imported by the test file instead of re-hardcoded. Verified: `npx vitest run` 155/155 passing, `npx tsc --noEmit` unchanged at 25 pre-existing errors, `npx vite build` clean. Status → `done`.

## Status
**done**
