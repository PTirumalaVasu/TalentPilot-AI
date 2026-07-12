---
story_key: 5-4-dashboard-auto-update-live-row-refresh-on-watch-progress
epic: 5
story_num: 4
dependencies:
  - 5-1-assignment-dashboard-grid-status-badge-display
  - 5-2-provenance-drill-down-modal-trust-detail-and-raw-data
baseline_commit: 5fe6432fb041ac2e591c0033bfbc194c9bdc22cd
---

# Story 5-4: Dashboard Auto-Update — Live Row Refresh on Watch Progress

Status: done

**Epic:** 5 (Readiness Dashboard — Status, Provenance, Auto-Update & Override)
**Story ID:** 5.4
**Functional Requirements:** FR-11 (Dashboard rows update automatically as Watch Progress arrives, ≤30 seconds)
**Architecture Rules:** AR-21 (client polling for live dashboard updates, ≤30s, no WebSocket/SSE)
**NFRs:** NFR-L5 (row reflects a new watch-position update within 30 seconds), NFR-A4 (dynamic/live row updates announced to screen readers)
**UX Specs:** UX-DR22 (Status updates automatically as Watch Progress arrives), UX-DR24 (all dynamic updates announced to screen readers, not just visually rendered)

This story is **frontend-only**. `GET /api/dashboard` (Story 5.1) already returns everything needed — no backend changes, no new endpoint, no schema change.

---

## User Story

As an **HR Admin**,
I want the dashboard to automatically update as Employees watch content,
So that I see current readiness without manual refresh.

---

## ⚠️ Critical Pre-Implementation Findings (read before coding)

Found by reading the *actual current* `DashboardPage.tsx`/`DashboardRow.tsx`, not the epic text or Story 5.1's story file (which describes an earlier version of the grid, since rewritten twice — see Story 5.2's own Finding 1 for the first instance of this exact trap).

### Finding 1 — Reusing `fetchDashboard()` as-is for polling will violate this story's own "no full-page refresh" AC

`DashboardPage.tsx`'s current `fetchDashboard()` (lines 59–88) unconditionally does `setState(prev => ({ ...prev, loading: true, error: null, assignments: [] }))` at the start of every call. It is called today only on mount and on page/pageSize change, where the loading skeleton is correct UX. If a poll timer simply calls this same function every 10–15s, the entire grid will blank to the loading skeleton on every tick — the exact "full-page refresh" flicker this story's AC explicitly forbids ("updates the row (no full-page refresh)").

**Do not reuse `fetchDashboard()` unmodified for the poll path.** Add a separate, silent poll function that calls `dashboardApi.getDashboard(page, pageSize)` and, on success, replaces `state.assignments`/`state.totalCount` directly — without ever touching `state.loading` or clearing `state.assignments` first. Reuse the existing `requestId` staleness-guard pattern (lines 60, 66–69, 79–82) so a slow poll response can't clobber a newer manual fetch (page change, retry) that started after it, and vice versa.

### Finding 2 — The grid has no "Last Updated" column to update; this story's own AC has nothing to point at without restoring it

Story 5.1's original AC (epics.md lines 1631–1633) specifies a **Last Updated column** ("2 hours ago", red-highlighted when Self-reported data is >7 days stale). It does not exist in the live `DashboardRow.tsx` (confirmed by reading the file: columns are Employee, Skill, Status, Progress bar, Actions — no timestamp column anywhere) or in `AssignmentRow`'s consumption anywhere in the current grid. This is the same class of silent regression Story 5.2's Finding 1 caught for the View Details button (also dropped by the "align with Rita's prototype" rewrite, commits `77b798c`/`22a06d2`) — already logged in `deferred-work.md` under Story 5-2's review (item "DashboardPage.test.tsx has 3 pre-existing failures... 'displays relative timestamp' (the current grid has no Last Updated column at all)").

This story's own AC text says the poll behavior "Updates the 'Last Updated' timestamp" — there is nothing to update without a column displaying it. **In scope for this story:** add a Last Updated column to `DashboardRow.tsx` (plain relative time via `date-fns`'s `formatDistanceToNow`, matching `ProvenanceDrillDownModal.tsx:21`'s existing pattern — `AssignmentRow.last_updated` is already on the wire, just not rendered). **Out of scope, do not build:** the red-highlight-when-stale styling from Story 5.1's AC — that's a Story 5.1/5.3 concern (Needs Attention is already visually distinguishable via the Provenance drill-down, not this column), not needed to satisfy this story's own literal "updates the row / updates the timestamp" text. If you judge the stale-highlight worth adding while you're already touching this column, flag it as a deliberate addition in the Dev Agent Record rather than silently expanding scope.

### Finding 3 — NFR-A4/UX-DR24 bind this story even though epics.md's own AC bullets don't mention it

Epic 5's binds list (epics.md line 1603) includes **NFR-A4** ("Dynamic updates (success toast, live row updates) are announced to screen readers") and **UX-DR24** ("All dynamic updates announced to screen readers... not just visually rendered") — both call out "live row updates" specifically, which is this story's entire feature. The Story 5.4 AC bullet list itself (epics.md lines 1769–1787) never mentions screen readers. Per this project's own convention (a story must leave the system correctly working end-to-end, not just satisfy its literal AC bullets when a binding NFR says otherwise): **add a visually-hidden `aria-live="polite"` region that announces when a poll detects a Status or Provenance change** (e.g. "Casey the Continuer's Data Visualization status updated to Completed"). Silent DOM updates with no announcement satisfy the AC's literal text but violate NFR-A4/UX-DR24, which are explicitly bound to this epic — do not skip this.

### Finding 4 — A directly-relevant sibling pattern already exists for interval + visibility lifecycle

`frontend/src/lib/services/captureService.ts` (Story 4.2/4.3) already implements `window.setInterval`-based periodic posting (`startBatchTimer()`, line 213) plus `visibilitychange`/`beforeunload` listener setup and teardown (`setupUnloadListeners()`/`removeUnloadListeners()`, lines 362–429) with a `listenersSetup` guard against duplicate registration. `frontend/src/lib/adapters/youtubeAdapter.ts` (line 70) uses the same `window.setInterval` pattern for its own position-polling. Match this codebase's established idiom (a ref-tracked interval id, explicit start/stop functions, guarded listener setup) rather than inventing a new one — this is a React function component, so wrap the equivalent lifecycle in a `useEffect` with a cleanup function instead of a class's manual setup/teardown methods, but the interval/visibility handling logic itself should mirror these two files' shape.

---

## Acceptance Criteria

_Verbatim from epics.md lines 1763–1788 (Story 5.4), numbered for traceability._

1. **Given** the HR Admin has the Assignment Dashboard open, **when** an Employee posts a watch-progress update, **then** the frontend polls `GET /api/dashboard` every 10–15 seconds (interval is a named constant, not a magic number, so it's easy to adjust — mirrors this project's established config-constant convention, e.g. `NEEDS_ATTENTION_STALENESS_DAYS` in Story 5.3, `SIMILARITY_THRESHOLD` in Story 2.4). [epics.md:1771–1774]
2. Each poll response is compared to current local state; if any Assignment's Status or Provenance changed, that row updates in place — **no full-page refresh** (Finding 1). [epics.md:1776]
3. The "Last Updated" timestamp updates on the affected row(s) (Finding 2 — column must exist first). [epics.md:1777]
4. Polling is client-driven only — no WebSocket/SSE (AR-21, already the architecture's locked decision; nothing to newly decide here). [epics.md:1779]
5. New rows (newly created Assignments) also appear on subsequent polls. Since each poll re-fetches the full current page via the existing paginated endpoint, this is a natural side effect of Finding 1's replace-in-place approach — no special-case code needed, just don't filter the poll response down to only "changed" rows. [epics.md:1781]
6. A dashboard row reflects a new watch-position update within 30 seconds (NFR-L5) — satisfied by the 10–15s interval (AC1) with margin. [epics.md:1783]
7. Polling stops when the tab is hidden (`document.visibilitychange`, `document.hidden === true`) and resumes when visible again (Finding 4). [epics.md:1785]
8. If a poll request fails (network error), log a warning to the console — **do not** set the page-level error state or interrupt the visible grid; polling continues on the next interval regardless (non-blocking). This is a deliberately different failure path from the existing manual/initial `fetchDashboard()`, which is allowed to show the full error state. [epics.md:1787]

**Also binding (not in the epics.md bullet list, see Finding 3):** live row changes are announced via an `aria-live="polite"` region (NFR-A4, UX-DR24).

---

## Tasks / Subtasks

- [x] Task 1: Add the Last Updated column (AC: 3; Finding 2)
  - [x] Subtask 1.1: Add a "Last Updated" `<th>`/`<td>` to `DashboardRow.tsx`, rendering `formatDistanceToNow(new Date(row.last_updated), { addSuffix: true })` (reuse the exact `date-fns` import/pattern already in `ProvenanceDrillDownModal.tsx:2,21` — do not add a second relative-time helper).
  - [x] Subtask 1.2: Update `DashboardRow.test.tsx` to assert the new column renders a relative-time string (`/ago$/`), matching the assertion style `DashboardPage.test.tsx`'s already-broken "displays relative timestamp" test attempted (see Known Issues — do not fix that stale test, add fresh coverage in `DashboardRow.test.tsx` instead, consistent with how Story 5.2 put new View-Details coverage there rather than patching the old file).
- [x] Task 2: Silent poll fetch path, decoupled from `fetchDashboard()`'s loading/blanking behavior (AC: 1, 2, 4, 5; Finding 1)
  - [x] Subtask 2.1: Add a `POLL_INTERVAL_MS` constant (10000–15000 range; pick one value, e.g. `12000`, and comment why — matches this project's "config constant, not a magic number" convention) at module scope in `DashboardPage.tsx`.
  - [x] Subtask 2.2: Add `pollDashboard()`: calls `dashboardApi.getDashboard(state.page, state.pageSize)` (same call `fetchDashboard` makes), and on success replaces `state.assignments`/`state.totalCount` via the existing `requestId` guard pattern — **without** setting `loading: true` or clearing `assignments` first. On failure, `console.warn` and return (AC8) — never touch `state.error`.
  - [x] Subtask 2.3: Before replacing state, diff the incoming `assignments` array against the current one (by `assignment_id`, comparing `status`/`provenance`/`status_percentage`/`last_updated`) to build the list of changed rows — needed for Task 3's announcement and useful for an optional visual highlight if you choose to add one (not required by any AC).
- [x] Task 3: Interval lifecycle + tab-visibility handling (AC: 1, 7; Finding 4)
  - [x] Subtask 3.1: `useEffect` that starts a `window.setInterval(pollDashboard, POLL_INTERVAL_MS)` on mount, stores the id in a `useRef`, and clears it on unmount. Do **not** tie this to the existing page/pageSize `useEffect` (line 51–57) — that one is for the debounced manual fetch; polling must run independently and continue across page changes (polling the *current* page).
  - [x] Subtask 3.2: Add a `document.visibilitychange` listener (mirror `captureService.ts`'s `setupUnloadListeners`/`removeUnloadListeners` guard-and-cleanup shape, adapted to a `useEffect`): on `document.hidden`, `clearInterval`; on visible again, restart the interval. Register/deregister in the same `useEffect` as Subtask 3.1, cleaned up together.
  - [x] Subtask 3.3: Guard against overlapping polls — if a poll is already in-flight when the interval fires again (e.g. a slow network), skip starting a second one (simple `isPollingRef` boolean ref checked at the top of `pollDashboard()`).
- [x] Task 4: Screen-reader announcement of live changes (Finding 3, NFR-A4/UX-DR24; user decision 2026-07-12: build now in 5.4 using Story 5.6's exact wording, see Debug Log)
  - [x] Subtask 4.1: Add a visually-hidden `<div aria-live="polite" className="sr-only">` in `DashboardPage.tsx`'s render, holding the most recent poll-driven change summary (e.g. built from Task 2.3's diff: `"{employee_name}'s {skill_name} status updated to {status}"`, joined if multiple rows changed in one poll). Only update this text when a real change is detected — do not re-announce identical content every poll (screen readers should stay silent on no-op polls).
  - [x] Subtask 4.2: Confirm (or add, if missing) a `.sr-only` utility class — check `frontend/src/index.css`/Tailwind config first; Tailwind ships `sr-only` as a built-in utility class (no custom CSS needed if Tailwind is already configured, which it is per `tailwind.config.js`).
- [x] Task 5: Tests
  - [x] Subtask 5.1: New `frontend/src/features/dashboard/DashboardPage.polling.test.tsx` (see Testing Strategy) using `vi.useFakeTimers()`/`vi.advanceTimersByTimeAsync()` (established pattern: `frontend/src/tests/youtubeAdapter.test.ts:23,147`). **Deviation from the sketch, documented in Debug Log:** RTL's `waitFor()` does not resolve under `vi.useFakeTimers()` (its own internal retry loop uses the now-faked `setTimeout`) — every test using it timed out at 5000ms. Rewrote all assertions to run directly after `act(async () => { await vi.advanceTimersByTimeAsync(ms) })` instead, matching `src/tests/Toast.test.tsx`'s already-working fake-timer + RTL pattern (which also avoids `waitFor`). 7/7 passing.
  - [x] Subtask 5.2: Verified `DashboardRow.test.tsx` (7/7 passing, including Task 1's new column test) and re-ran `DashboardPage.test.tsx`. **Finding, not assumed:** the pre-existing failure count dropped from 3 to 2, not "unchanged" — Task 1's restoration of the Last Updated column incidentally satisfies the old "displays relative timestamp (not ISO-8601)" test's assertion, which previously failed because no such column existed. The other 2 pre-existing failures ("renders loading state on mount", "pagination shows correct page numbers and total") are untouched and still fail for the same pre-existing reasons (stale copy/format assertions unrelated to this story).
- [x] Task 6: Full regression pass
  - [x] Subtask 6.1: `npm run test` full suite: 205 passed, 2 failed (both pre-existing, unrelated — see Task 5 finding). `tsc --noEmit` diffed before/after via `git stash`: baseline 85 errors, after 85 errors, **byte-for-byte identical diff output** — zero new type errors. One real type error was caught and fixed during this pass (not left in): `window.setInterval(...)`'s return type conflicted with the `ReturnType<typeof window.setInterval>` ref typing under this project's mixed Node/DOM ambient types; fixed by matching `captureService.ts`'s own established `as unknown as number` cast pattern for the exact same issue.
  - [x] Subtask 6.2: Real-browser smoke test via a one-off Playwright script (not added as a project dependency — installed only in the session scratchpad, `package.json`/`package-lock.json` untouched) against the live running app (Docker Postgres + `uvicorn` + `vite`, already running). Logged in as `rita@sails.example.com`/`demo123`, loaded the dashboard, inserted a real `skill_progress` row directly via `psql` for Casey/Salesforce Admin (previously "Not Started"), and observed: row updated to "In Progress" with "Last Updated: less than a minute ago" within ~15s, **no page reload, no loading-skeleton flash**; the `aria-live="polite"` region's text read exactly `"Casey the Continuer Salesforce Admin status updated to In Progress"` (Story 5.6's literal wording, confirmed real); poll requests observed at the correct ~12s cadence; **0 new `/api/dashboard` requests during 13s of simulated tab-hidden**, **1 new request within 13s after simulated visibility resume** — AC7 confirmed working in a real browser, not just under jsdom's fake timers. Screenshot confirms the rendered grid visually. Test data cleaned up afterward (`DELETE FROM skill_progress ...`) to restore the dev DB's original state.
  - [x] Subtask 6.3: Dev Agent Record + File List updated below.

### Review Findings

- [x] [Review][Patch] Poll responses bypass the `requestId` staleness guard — a slow poll can silently overwrite a newer page's/manual-fetch's data, the exact race Finding 1/Subtask 2.2 says the guard must prevent; no test covers it [frontend/src/features/dashboard/DashboardPage.tsx:116-122]
- [x] [Review][Patch] `diffAssignments()` omits `status_percentage` (Subtask 2.3 specifies it), so a percentage-only progress bump (e.g. "In Progress (20%)" → "In Progress (45%)", confirmed visible via `StatusBadge.tsx`) updates the grid but is never announced to screen readers — a real violation of the binding NFR-A4/UX-DR24 requirement for this feature's most common real-world scenario [frontend/src/features/dashboard/DashboardPage.tsx:27-33]
- [x] [Review][Patch] Poll interval starts unconditionally on mount with no check of `document.visibilityState` — if the dashboard mounts already in a hidden/background tab, polling begins immediately instead of waiting for the tab to become visible, violating AC7's intent [frontend/src/features/dashboard/DashboardPage.tsx:140]

**Patch notes:** Fixing the `requestId` guard surfaced a second bug introduced by the fix itself: `pollDashboard`'s closure captured `state.requestId` once at mount and never refreshed it (the polling effect's dependency array was `[state.page, state.pageSize]` only), so the snapshot went stale the instant the mount's own `fetchDashboard()` bumped `requestId` from 0→1 — causing the new guard to discard *every* poll response, not just stale ones (4 of 7 polling tests failed on first patch attempt). Fixed by adding `state.requestId` to the effect's dependency array, matching the same "closure trap" reasoning already documented in this file for `state.page`/`state.pageSize`. Re-verified after the fix: 205/207 frontend tests passing (same 2 pre-existing unrelated `DashboardPage.test.tsx` failures), `tsc --noEmit` diffed byte-identical against a `git stash` baseline (85 lines both times) — zero new type errors.

---

## Developer Context & Implementation Notes

### `DashboardPage.tsx` — sketch of the additions (Task 2 + 3)

```tsx
const POLL_INTERVAL_MS = 12000; // within the 10-15s AC range (epics.md:1774)

// ... inside the component, alongside existing state/refs:
const pollIntervalRef = useRef<ReturnType<typeof window.setInterval> | null>(null);
const isPollingRef = useRef(false);
const [liveAnnouncement, setLiveAnnouncement] = useState("");

async function pollDashboard() {
  if (isPollingRef.current) return; // Subtask 3.3
  isPollingRef.current = true;
  try {
    const response = await dashboardApi.getDashboard(state.page, state.pageSize);
    setState((prev) => {
      const changes = diffAssignments(prev.assignments, response.assignments); // Subtask 2.3
      if (changes.length > 0) {
        setLiveAnnouncement(describeChanges(changes)); // Task 4
      }
      return { ...prev, assignments: response.assignments, totalCount: response.total_count };
    });
  } catch (err) {
    console.warn("Dashboard poll failed, will retry on next interval", err); // AC8
  } finally {
    isPollingRef.current = false;
  }
}

useEffect(() => {
  function startPolling() {
    if (pollIntervalRef.current !== null) return;
    pollIntervalRef.current = window.setInterval(pollDashboard, POLL_INTERVAL_MS);
  }
  function stopPolling() {
    if (pollIntervalRef.current === null) return;
    window.clearInterval(pollIntervalRef.current);
    pollIntervalRef.current = null;
  }
  function handleVisibilityChange() {
    if (document.hidden) stopPolling();
    else startPolling();
  }

  startPolling();
  document.addEventListener("visibilitychange", handleVisibilityChange);
  return () => {
    stopPolling();
    document.removeEventListener("visibilitychange", handleVisibilityChange);
  };
}, [state.page, state.pageSize]); // deliberately NOT []: pollDashboard closes over state.page/pageSize
```

**Closure trap to avoid:** `pollDashboard` reads `state.page`/`state.pageSize` from the render it was defined in. If the `useEffect` above used an empty dependency array (`[]`) for a "set up once" interval, `startPolling` would capture that *first* render's `pollDashboard` forever, and every subsequent poll would silently keep hitting the page the user was on at mount — even after they navigate to page 2. Depending on `[state.page, state.pageSize]` (as sketched) makes the effect re-run — tearing down and restarting the interval with a fresh `pollDashboard` closure — whenever the page changes, which is the correct fix, not just a caveat to note and ship around. The small cost (interval resets, so the next poll is up to `POLL_INTERVAL_MS` later than it would've been) is negligible next to silently polling the wrong page.

### `DashboardRow.tsx` — Last Updated column (Task 1)

```tsx
import { formatDistanceToNow } from "date-fns"; // same import ProvenanceDrillDownModal.tsx already uses

// new <td> between Progress and Actions (or wherever fits the existing column order):
<td className="px-4 py-3 text-gray-500 text-sm">
  {formatDistanceToNow(new Date(row.last_updated), { addSuffix: true })}
</td>
```

Add the matching `<th>Last Updated</th>` to `DashboardPage.tsx`'s table header (line ~193, alongside the existing `Employee/Assigned Skill/Status/Progress/Actions` headers).

### Diffing helper (Task 2.3 / Task 4)

Keep it simple — a plain function, not a library:

```ts
function diffAssignments(prev: AssignmentRow[], next: AssignmentRow[]) {
  const prevById = new Map(prev.map((r) => [r.assignment_id, r]));
  return next.filter((row) => {
    const before = prevById.get(row.assignment_id);
    return !before || before.status !== row.status || before.provenance !== row.provenance;
  });
}
```

This intentionally does not diff `last_updated` alone (a timestamp can tick forward on every poll even with no status change once relative-time rendering is added — you don't want a screen-reader announcement firing every 12 seconds for a row that hasn't actually changed).

---

## Testing Strategy

### Frontend only (no backend tests — this story adds no backend code)

New file `frontend/src/features/dashboard/DashboardPage.polling.test.tsx` (kept separate from the already-partially-broken `DashboardPage.test.tsx` — see Known Issues; new fake-timer setup/teardown is cleaner isolated, and this avoids conflating this story's pass/fail counts with pre-existing unrelated failures):

- Mock `dashboardApi.getDashboard`; `vi.useFakeTimers()` in `beforeEach`, `vi.useRealTimers()` in `afterEach` (or per-test) — mirror `youtubeAdapter.test.ts`'s setup.
- **No full-page refresh on poll:** render with initial data, `vi.advanceTimersByTime(POLL_INTERVAL_MS)`, resolve a second `getDashboard` mock with changed data, assert the loading skeleton never re-appears (e.g. assert the grid `<table>` stays in the DOM throughout, never unmounted) and the changed row's new value renders.
- **Row updates without full remount:** two consecutive polls with different `status` for the same `assignment_id`; assert the displayed Status badge text changes between polls.
- **New row appears on a later poll:** second poll response includes an extra `assignment_id` not in the first; assert it renders after the poll.
- **Poll failure is non-blocking (AC8):** mock a rejected poll after a successful initial load; assert the grid remains visible (no error state shown) and `console.warn` was called; advance timers again with a successful mock and assert normal operation resumes.
- **Visibility pause/resume (AC7):** stub `document.hidden`/dispatch `visibilitychange`; assert `getDashboard` is not called while hidden even after advancing timers past the interval, and is called again once visibility is restored.
- **Screen-reader announcement (Finding 3):** assert the `aria-live="polite"` region's text changes only when a poll detects a Status/Provenance diff, and stays unchanged across a no-op poll (identical data).
- **Last Updated column (Task 1, can live in `DashboardRow.test.tsx` instead):** row renders a string matching `/ago$/` for a given `last_updated` ISO timestamp.

Do not extend the fake-timer/polling assertions into the existing `DashboardPage.test.tsx` — keep that file's scope as-is (it already has 3 known-broken, out-of-scope tests; see Known Issues) and put all new coverage in the new file plus `DashboardRow.test.tsx`.

---

## Architecture Compliance Checklist

- **AR-21 (client polling, ≤30s, no WebSocket/SSE):** satisfied by construction — `window.setInterval` polling `GET /api/dashboard`, 10–15s interval.
- **NFR-L5 (≤30s freshness):** 10–15s interval gives ~2x margin.
- **NFR-A4 / UX-DR24 (live updates announced to screen readers):** `aria-live="polite"` region, Task 4.
- **AD-6 (server-side role gate):** no new endpoint added; existing `GET /api/dashboard` already requires `require_hr_admin` (Story 5.1) — nothing to change here.
- **No new backend surface:** this story must not add a route, service method, or repository method — if you find yourself doing so, stop and re-read the AC; the feature is entirely client-side diffing of an existing response.

---

## Known Issues & Deferrals

- **`DashboardPage.test.tsx` has 3 pre-existing, unrelated failures** (loading-state text, relative-timestamp text — Task 1 of this story finally makes a real "Last Updated" column exist, but that old test's specific assertion text may still not match; verify but do not feel obligated to make that specific stale test pass — and pagination "Page X of Y" text) — logged in `deferred-work.md` under Story 5-2's review. Not this story's job to fix; put new coverage in the new `DashboardPage.polling.test.tsx` / `DashboardRow.test.tsx` files instead (Testing Strategy).
- **Backend transaction/snapshot race between assignment+progress+override reads** (`dashboard/service.py`, `deferred-work.md`, Story 5-1/5-2 reviews) — those deferred items explicitly say "revisit... Story 5.4," but this story's actual AC scope is client-side polling only, with zero backend changes. **This story does not close that deferred item** — flag it as still-open in the Dev Agent Record rather than assuming client polling incidentally fixes a backend read-consistency gap (it doesn't; a torn read would just get polled again and self-correct on the next tick, which is a reasonable mitigation but not the same as fixing the race). If the user wants this story to also touch backend snapshot consistency, that's a scope decision to surface explicitly, not silently absorb.
- **No exponential backoff on repeated poll failures** — AC8 only requires "log a warning, continue on next interval," which a plain fixed-interval retry already satisfies. `deferred-work.md`'s existing "Error Retry Lacks Exponential Backoff" item (Story 5-1 review, about the manual Retry button) is a related-but-distinct surface; do not conflate the two or feel obligated to add backoff to the poll loop — not required by any AC.
- **`npm run build`'s `tsc &&` gate has pre-existing, unrelated failures** (branded `UUID` type mismatches, `CaptureService`-as-type errors — `deferred-work.md`, Story 2.6 entry) — use `tsc --noEmit` diffed before/after (git stash) to prove no *new* errors, matching Story 5.2's own established verification method for this exact gap, not a clean full `npm run build` pass.

---

## Success Criteria

1. Dashboard grid updates a row's Status/Provenance/Last-Updated in place within ~10–15s of a real change, with zero loading-skeleton flash (Finding 1).
2. Last Updated column exists and renders relative time (Finding 2, Task 1) — the AC this story is nominally about has something real to point at.
3. Polling stops while the tab is hidden and resumes on return (AC7); a poll failure never shows the page-level error state (AC8).
4. Live row changes are announced to screen readers via `aria-live="polite"` (Finding 3, NFR-A4/UX-DR24) — silent-but-visible updates are not sufficient.
5. Zero new backend code. Zero new type errors (`tsc --noEmit` diff). All new tests pass; pre-existing unrelated failures are unchanged in count.

---

## Dev Notes

### Project Structure Notes

- Files expected to change: `frontend/src/features/dashboard/DashboardPage.tsx` (poll loop, visibility handling, `aria-live` region, Last-Updated `<th>`), `frontend/src/features/dashboard/DashboardRow.tsx` (Last-Updated `<td>`).
- New test file: `frontend/src/features/dashboard/DashboardPage.polling.test.tsx`.
- `DashboardRow.test.tsx` gets one new test (Last Updated column), no other changes.
- No backend files touched. No Alembic migration. No new API client method (`dashboardApi.getDashboard` already exists and is reused as-is).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4] (lines 1763–1788) — full AC text this story implements, verbatim
- [Source: _bmad-output/planning-artifacts/epics.md] — FR-11 (line 60), AR-21 (line 137), NFR-L5 (line 76), NFR-A4 (line 99), UX-DR22/UX-DR24 (lines 173, 175), Epic 5 binds list (line 1603)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md:123] — "Real-time: Live dashboard row updates (FR-11, ≤30s) via client polling of the dashboard read endpoint — no WebSocket/SSE"
- [Source: frontend/src/features/dashboard/DashboardPage.tsx] — current implementation; Finding 1's `fetchDashboard()` blanking behavior (lines 59–88), existing `requestId` staleness-guard pattern to reuse
- [Source: frontend/src/features/dashboard/DashboardRow.tsx] — current implementation, confirms no Last Updated column exists (Finding 2)
- [Source: frontend/src/lib/services/captureService.ts:213-219,362-429] — sibling `setInterval` + `visibilitychange` lifecycle pattern to mirror (Finding 4)
- [Source: frontend/src/lib/adapters/youtubeAdapter.ts:70] — second sibling polling-interval precedent
- [Source: frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:2,21] — existing `date-fns` `formatDistanceToNow` relative-time pattern to reuse for the new Last Updated column, not reinvent
- [Source: frontend/src/tests/youtubeAdapter.test.ts:23,147] — working `vi.useFakeTimers()`/`vi.advanceTimersByTime()` test pattern for polling-interval behavior in this exact codebase
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — Story 5-1 review (dashboard transaction/snapshot race, explicitly deferred "to Story 5.4" — see Known Issues for why this story doesn't close it), Story 5-2 review (same race item, `DashboardPage.test.tsx`'s 3 pre-existing unrelated failures, the "align with Rita's prototype" regression pattern this story's Finding 2 is a second instance of)
- [Source: _bmad-output/implementation-artifacts/5-2-provenance-drill-down-modal-trust-detail-and-raw-data.md] — Finding 1 (View Details regression) is the direct precedent for this story's Finding 2 (Last Updated regression) — same rewrite, same failure mode, same "read the actual current code, not the story history" lesson
- [Source: _bmad-output/implementation-artifacts/5-3-needs-attention-flagging-7-day-staleness-threshold.md] — precedent for "config constant, not a magic number" (this story's `POLL_INTERVAL_MS`)
- [Source: _bmad-output/project-context.md] — Epic 5 architecture-spine summary; confirms `progress/` is the single derivation authority this story's client-side diffing must not duplicate (this story only compares already-derived `status`/`provenance` values, never re-derives them)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- **Scope decision (2026-07-12, user-confirmed via AskUserQuestion before implementation began):** Task 4 (aria-live announcement) duplicates part of Story 5.6's ("Accessibility & Real-Time Announcements", still `backlog`) own literal AC text — Story 5.6's own spec (epics.md:1964) specifies the exact same announcement: `"{Employee} {Skill} status updated to {Status}"`. This was missed during story creation (didn't scan far enough into epics.md to see Story 5.6 exists). User decision: build it now in 5.4 using Story 5.6's exact wording, so 5.6 can verify/extend (badge-focus, modal-focus, toast announcements) rather than rebuild the live-row-update announcement from scratch. Implemented `describeChanges()` to produce that exact string format.
- **RED phase confirmed before each implementation:** `DashboardRow.test.tsx`'s new Last Updated test failed with `getByText(/ago$/)` finding no match before Task 1's column existed; all 7 new `DashboardPage.polling.test.tsx` tests timed out at 5000ms before Tasks 2-4 existed (no interval was ever scheduled, so the mocked `getDashboard` was never called a second time).
- **Test-infrastructure finding, not an implementation bug:** RTL's `waitFor()` does not resolve under `vi.useFakeTimers()` — its internal retry loop uses the now-faked global `setTimeout`, so it polls forever without the outer fake-timer clock ever advancing it, producing a real 5000ms wall-clock timeout regardless of `vi.advanceTimersByTimeAsync()` calls elsewhere in the test. Confirmed this is a known interaction hazard, not specific to this story's code, by checking this codebase's own existing fake-timer tests (`src/tests/Toast.test.tsx`, `src/tests/youtubeAdapter.test.ts`) — neither uses `waitFor`, both assert directly after advancing timers. Rewrote all 7 polling tests to match that established pattern (`act(async () => { await vi.advanceTimersByTimeAsync(ms) })` followed by direct synchronous assertions, no `waitFor`). All 7 then passed in 93ms (down from 5x 5000ms timeouts).
- **Real type error caught and fixed during Task 6's `tsc --noEmit` pass:** `pollIntervalRef` typed as `useRef<ReturnType<typeof window.setInterval> | null>` produced `Type 'number' is not assignable to type 'Timeout'` — this project's mixed Node/DOM ambient types make `window.setInterval`'s inferred return type ambiguous at the assignment site. Fixed by typing the ref as `number | null` and casting `window.setInterval(...) as unknown as number`, matching `captureService.ts`'s (`postInterval`) already-established fix for the identical issue in this codebase.
- **`tsc --noEmit` diffed via `git stash`:** baseline (pre-story) = 85 errors; after this story's full diff = 85 errors; `diff` between the two captured outputs was empty (byte-identical) — confirms zero new type errors, not just "same count by coincidence."
- **Full frontend suite:** 205 passed / 2 failed both before and after this story's changes were the *only* two remaining pre-existing `DashboardPage.test.tsx` failures ("renders loading state on mount", "pagination shows correct page numbers and total"). A third previously-logged pre-existing failure ("displays relative timestamp (not ISO-8601)") now passes as an incidental, correct side effect of Task 1 restoring the Last Updated column — not something this story set out to fix, but a real, verified improvement worth recording accurately rather than either claiming credit for a "fix" or leaving the failure-count claim stale.
- **Real-browser verification (Task 6, Subtask 6.2):** one-off Playwright script (Chromium, already cached in this environment from a prior session; installed only in the session scratchpad — did not modify `frontend/package.json`/`package-lock.json`, avoiding an unapproved new project dependency per this workflow's "new dependencies need user approval" rule). Logged in as `rita@sails.example.com` (seeded HR Admin), loaded `/hr/dashboard`, inserted a real `skill_progress` row via `psql` directly against the running Postgres container for a genuinely "Not Started" assignment (Casey the Continuer / Salesforce Admin — confirmed via `SELECT` it had no existing progress row), then observed over ~15s: Status badge changed "Not Started" → "In Progress" in place, Last Updated changed "about 17 hours ago" → "less than a minute ago", no page navigation/reload occurred, the `aria-live="polite"` region's `textContent` read exactly `"Casey the Continuer Salesforce Admin status updated to In Progress"`. Separately verified AC7 in the same real browser (not just jsdom): 0 new `/api/dashboard` network requests over 13s after dispatching `visibilitychange` with `document.visibilityState = "hidden"`, then 1 new request within 13s after switching back to `"visible"`. Test data cleaned up afterward.
- **Confirmed still-broken, unrelated, not touched:** `progress/router.py`'s double-prefix bug (logged Story 5-2 review, `deferred-work.md`) — `POST /api/assignments/{id}/progress` still 404s at its documented URL; had to use the actual live double-prefixed path for an earlier attempt at posting progress via the API before switching to a direct DB insert for the smoke test instead. Re-confirms the bug is still open; out of this story's scope to fix (different feature surface, zero backend files touched by this story).

### Completion Notes List

- All 6 tasks complete, all 8 literal ACs + the Finding-3 binding NFR-A4/UX-DR24 requirement satisfied. Purely frontend: `frontend/src/features/dashboard/DashboardPage.tsx` and `DashboardRow.tsx` modified, one new test file added, two existing test files extended. Zero backend files touched, confirmed by `git status` and by the unchanged backend test run.
- **Task 1 (Last Updated column):** restored the column Story 5.1 originally specified but a later "align with Rita's prototype" rewrite silently dropped (Finding 2) — reused the exact `date-fns` `formatDistanceToNow` pattern already established in `ProvenanceDrillDownModal.tsx`, no new relative-time helper invented.
- **Tasks 2-3 (silent poll + interval/visibility lifecycle):** `pollDashboard()` is fully decoupled from `fetchDashboard()`'s loading/blanking behavior (Finding 1) — never sets `state.loading` or clears `state.assignments`, reuses the diff-based `setState` update instead. Interval effect depends on `[state.page, state.pageSize]` (not `[]`) specifically to avoid a stale-closure bug where `pollDashboard` would keep polling whatever page the user was on at mount forever, even after navigating — documented explicitly in the story file's "Closure trap" note and implemented as specified. Overlapping-poll guard (`isPollingRef`) and non-blocking failure handling (`console.warn`, never `state.error`) both implemented per AC8.
- **Task 4 (aria-live announcement):** built now per user decision (see Debug Log) using Story 5.6's exact wording. `diffAssignments()`/`describeChanges()` only compare `status`/`provenance` (not `last_updated`, which ticks forward on every poll regardless of a real change) — verified via the "does not re-announce anything on a poll with no actual Status/Provenance change" test.
- **No backend changes, no new dependencies added to `package.json`** — both explicitly confirmed, matching the story's own Architecture Compliance Checklist and this workflow's dependency-approval rule.

### File List

**Frontend (modified):**
- `frontend/src/features/dashboard/DashboardPage.tsx` — added `POLL_INTERVAL_MS` constant, `diffAssignments()`/`describeChanges()` helpers, silent poll loop + `useRef`-tracked interval, `visibilitychange` listener, `aria-live="polite"` region (rendered in all 4 state branches), Last Updated `<th>`
- `frontend/src/features/dashboard/DashboardRow.tsx` — added Last Updated `<td>` using `date-fns`'s `formatDistanceToNow`
- `frontend/src/features/dashboard/DashboardRow.test.tsx` — added Last Updated column test

**Frontend (new):**
- `frontend/src/features/dashboard/DashboardPage.polling.test.tsx` — 7 new tests covering AC1/2/4/5/7/8 and the aria-live announcement, kept separate from the pre-existing partially-broken `DashboardPage.test.tsx`

**Docs/tracking:**
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status transitions (`ready-for-dev` → `in-progress` → `review`) and dated log entry
- `_bmad-output/project-context.md` — story creation entry (from `bmad-create-story`) plus a new implementation-completion entry added by this `bmad-dev-story` pass, per the project's mandatory Project Context Maintenance rule

## Change Log

| Date | Change |
|------|--------|
| 2026-07-12 | Implemented all 6 tasks. Restored the Last Updated column (Finding 2 regression), added a silent background poll loop decoupled from the existing loading/blanking fetch path (Finding 1), interval + tab-visibility lifecycle matching `captureService.ts`'s established pattern (Finding 4), and an `aria-live="polite"` announcement region using Story 5.6's exact wording per an explicit user scope decision (Finding 3). 7 new frontend tests (`DashboardPage.polling.test.tsx`) + 1 new test in `DashboardRow.test.tsx`, all passing. Full frontend suite: 205 passed / 2 failed (both pre-existing, unrelated — one previously-pre-existing failure now incidentally passes as a side effect of Task 1). `tsc --noEmit` diffed byte-identical before/after via `git stash` — zero new type errors (one real type error was caught and fixed during this same pass, not shipped). Real-browser Playwright smoke test against the live running app confirmed all of AC1-AC8 plus the aria-live announcement working end-to-end, not just under jsdom. Zero backend files touched. Status → review. |
