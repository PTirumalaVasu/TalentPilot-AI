# Story 2-6: Empty & Error States for Content Discovery - Implementation Steps

**Date:** 2026-07-11
**Status:** COMPLETED ✅
**Test Results:** Frontend 156/156 passing (zero regressions); backend untouched (this story is 100% frontend)
**Ready for Merge:** YES

---

## Executive Summary

Story 2-6's epics.md text describes five UI edge-case states for Content Discovery. Direct source inspection at story-authoring time found that four of those five states were already built and already tested as side effects of Story 2.5 and Story 4.6 — so this story was scoped down to a verification pass for those four, not a rebuild. The one real gap was `VideoPlayer.tsx`'s video-load-failure handling: it had a bare, un-retriable error string and zero test coverage, a thread Story 2.5 had explicitly deferred and no later story had picked up.

Story authoring also surfaced a critical, unrelated, pre-existing bug blocking everything else: `assignmentsApi.ts` was syntactically broken from a bad `main` merge, breaking `npm run build` entirely. Fixing it (Task 0) then unmasked 25 further pre-existing `tsc` errors that had been silently hidden behind that one fatal parse failure — logged for later, not fixed here (out of scope).

Two rounds of adversarial code review followed. The first found and fixed 8 real gaps in the new retry UI. The second — a user-requested independent re-review of the round-1 patches — found that round 1's own fix had introduced a real regression: it broke silently under React StrictMode, the exact mode the real app renders under. That regression was reproduced empirically (not just theorized) and fixed with a permanent regression test proving it.

---

## What Was Implemented

**Backend:** None — this story touches no backend code.

**Frontend:**
- `assignmentsApi.ts` — fixed a merge-corrupted `createAssignment`/`listMyAssignments` (missing closing brace had nested one function's export illegally inside the other), restoring a clean build
- `VideoPlayer.tsx` — the real new work: a video-load-failure state showing the literal copy "This video couldn't be loaded." with `role="alert"` and a working "Try again" button, backed by a per-attempt token guard (`attemptIdRef`/`isMountedRef`) so a stale async callback from a superseded or unmounted attempt can never overwrite newer state
- `VideoPlayer.test.tsx` — first-ever test file for this component (Story 4.0, previously untested), built via TDD
- Verification-only pass (no code changes) confirming `ContentDiscovery.tsx`, `AssignmentCard.tsx`, and `ContinueWatchingCard.tsx`'s existing empty/error states still match this story's AC text exactly

---

## Issues Faced and Fixes

### During Story Authoring (found before any code was written)

| # | Issue | Fix |
|---|-------|-----|
| 1 | `assignmentsApi.ts` was syntactically broken — a bad `main`-merge left `createAssignment`'s function body missing its closing brace, nesting `listMyAssignments` illegally inside it. `npm run build` was fully broken, invisible to `vitest` only because both consuming test files mock the module wholesale | Closed the function properly, restoring `listMyAssignments` as a valid top-level export (Task 0, done first as a blocking prerequisite) |

### During Implementation (Task 0's fix surfaced a second, deeper problem)

| # | Issue | Root cause | Fix |
|---|-------|-----------|-----|
| 1 | Fixing `assignmentsApi.ts` unmasked 25 pre-existing `tsc` errors that had never been visible before | TypeScript had been silently aborting diagnostic collection for the *entire* project because of that one file's fatal parse error — the errors (a `CaptureService`-used-as-a-type bug, a `UUID`-branded-type mismatch pattern) were real and pre-existing, just never reported | Confirmed via `git stash` that none were introduced by this story; logged to `deferred-work.md` rather than fixed (out of scope, a 3-story-old gap first flagged in Story 3.4); `vite build` used as the practical build-verification proxy in the meantime |
| 2 | The first draft of `handleRetry` didn't reset `playerRef.current` before calling `initPlayer()` again | `playerRef.current` is set synchronously inside `initPlayer`'s `try` block even for a player that only fails *later*, asynchronously — so a naive retry hit `initPlayer`'s own re-entry guard and silently did nothing | Caught by the retry test itself, not by reasoning about the code; fixed by resetting the relevant refs before re-invoking `initPlayer()` |

### During Code Review Round 1 (3 parallel adversarial layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor)

| # | Issue | Fix |
|---|-------|-----|
| 1 | No per-attempt guard on the new retry flow — a stale async callback from an abandoned attempt could overwrite state for a newer attempt, or fire after unmount | Added `attemptIdRef`/`isMountedRef`, checked at the top of every async callback |
| 2 | `handleRetry` never called the real `YT.Player`'s own `.destroy()` before discarding it, leaking a live player instance on every retry | `handleRetry` now calls `playerRef.current.destroy()` (guarded, since test mocks don't implement it) |
| 3 | The retry container reused the same DOM node the YouTube IFrame API had already replaced on the first load — risked attaching a new player into a detached element | Replaced with a stable `containerRef` plus a fresh child element created per attempt, matching the established pattern already used elsewhere in this codebase |
| 4 | `role="alert"` wrapped both the message text and the "Try again" button, nesting a focusable control inside a live region — a known screen-reader anti-pattern and a deviation from this project's own convention | Scoped `role="alert"` to the message text only; the button is now a sibling outside the alert region |
| 5 | No test proved the `onError` prop callback still fired on failure, despite the task checklist claiming it was verified | Added a dedicated test |
| 6 | No test covered the third failure path (`onPlayerReady_Internal`'s own construction failure) reaching the same error+retry UI | Added a dedicated test (mocks `CaptureService` to throw once) |
| 7 | A documentation ledger entry undercounted its own error breakdown | Corrected the prose to match the actual count |
| 8 | The error copy was duplicated as a separate hardcoded string in the test file, risking silent drift from the component's own text | Extracted a single exported `VIDEO_LOAD_FAILURE_MESSAGE` constant, imported by both |

### During Code Review Round 2 (user-requested independent re-review of the already-patched, already-committed diff)

| # | Issue | Root cause | Fix |
|---|-------|-----------|-----|
| 1 | **Critical: Round 1's own `.destroy()` fix (issue 2 above) broke the app under React StrictMode** | The real app renders under `<React.StrictMode>`, which double-invokes mount effects in dev (mount → unmount → remount). The unmount cleanup destroyed the player/adapter/capture-service but never *nulled* the refs afterward — so on the StrictMode remount, `initPlayer()`'s own re-entry guard saw a stale, already-destroyed player and silently did nothing. Watch-progress capture died permanently while the UI kept claiming "Capture service active." The reviewer reproduced this directly with a real probe test, not just by reading the code | Extracted a shared, exception-safe `destroyPlayerResources()` helper that destroys *and nulls* all four refs, used by both the unmount cleanup and `handleRetry`. Added a permanent regression test rendering under `<StrictMode>`, verified red (fails, player constructed only once) with the fix temporarily removed and green (constructed twice) with it restored |
| 2 | `handleRetry`'s and the unmount cleanup's teardown steps weren't exception-safe — one throwing `.destroy()` call could halt the rest, permanently disabling retry | Same as above | Each of the four teardown steps in the new shared helper is independently wrapped, so one failure can't block the others |
| 3 | This story's own round-1 review checklist had a stale, self-contradicting line claiming a listener-ordering fix was "unchanged," when the diff had actually already fixed it | A documentation bookkeeping slip, not a code defect | Corrected the checklist line in place to match reality and the separate deferred-work ledger, which already had it right |
| 4 | The per-retry DOM element reused the same id on every attempt, safe only by accident of execution order | — | Made the id unique per attempt |
| 5 | A retry-count test didn't actually verify a third construction attempt occurred, despite its name implying it did | — | Strengthened the assertion |
| 6 | A code comment overclaimed how closely the retry fix matched an existing pattern elsewhere in the codebase | — | Narrowed the comment to its accurate scope |

---

## Test Verification

- **Frontend:** 156/156 passing after both review rounds (was 148 before this story, 153 after round 1, 156 after round 2), zero regressions
- **Backend:** untouched, no backend tests run (this story has no backend scope)
- **TypeScript:** `tsc --noEmit` unchanged at 25 pre-existing errors throughout (none introduced by this story; the count is fully explained and itemized in `deferred-work.md`)
- **Build:** `vite build` clean at every checkpoint (used as the practical build-verification proxy since the pre-existing `tsc` errors keep the full `npm run build` gate red)
- **Regression proof, not just code review:** the critical round-2 fix was verified by temporarily removing it, confirming the new test failed for the right reason, then restoring it and confirming the test passed — the same discipline this project has repeatedly required for high-risk fixes

---

## Deferred (not fixed — logged for later, low severity)

- 25 pre-existing `tsc` errors in `VideoPlayer.tsx`, `VideoPlayerDemo.tsx`, `ContinueWatchingCard.tsx`, and `useResumePosition.test.ts` (a `CaptureService`-as-a-type bug and a `UUID`-branded-type mismatch pattern) — a 3-story-old gap, first flagged in Story 3.4, still open
- A theoretical double-firing of the player's own "ready" event for the same attempt — no established real-world trigger for this in the YouTube IFrame API
- The "Try again" button has no explicit accessible link back to the alert message text — a real but minor accessibility nice-to-have, beyond what this story's acceptance criteria require
- The `onError` prop callback still passes the raw, technical diagnostic message rather than the generic user-facing copy — no acceptance criterion requires sanitizing it, and no current caller consumes it

---

## References

- **Story File:** `_bmad-output/implementation-artifacts/2-6-empty-and-error-states-for-content-discovery.md`
- **Sprint Status:** `_bmad-output/implementation-artifacts/sprint-status.yaml`
- **Deferred Work Log:** `_bmad-output/implementation-artifacts/deferred-work.md`
- **Frontend:** `frontend/src/components/VideoPlayer.tsx`, `VideoPlayer.test.tsx`, `frontend/src/lib/api/assignmentsApi.ts`

---

**Document Status:** COMPLETE ✅
**Generated:** 2026-07-11
