---
story_key: 5-5b-hr-override-reversal-undo-manual-confirmation
epic: 5
story_num: 5b
dependencies:
  - 5-2-provenance-drill-down-modal-trust-detail-and-raw-data
  - 5-5-hr-override-manual-readiness-confirmation
baseline_commit: d1b80a8
---

# Story 5.5b: HR Override Reversal — Undo Manual Confirmation

Status: ready-for-dev

**Epic:** 5 (Readiness Dashboard — Status, Provenance, Auto-Update & Override)
**Story ID:** 5.5b
**Functional Requirements:** FR-12 (HR Admin manually overrides an assignment's readiness status — reversal is the other half)
**Architecture Rules:** AD-4 (HR Override is a separate, coexisting record), AR-3 (single derivation authority — reuse, never re-derive), AD-6 (server-side role/identity gate, already enforced)
**NFRs:** NFR-A2 (Provenance never color-only), NFR-L5 (dashboard row reflects change within 30s)
**Data Model:** Table 7 `assignment_overrides` — write path (`action: 'unset'`) already built and tested by Story 5.5. This story builds no new backend mutation, only its missing UI trigger.

This story completes the `[Reverse Override]` half of the drill-down modal's Actions row that Story 5.5 deliberately left as a disabled stub. The backend endpoint, service method, repository methods, and frontend API client all already handle `action: 'unset'` end-to-end — this is a **frontend-only story** (plus one new backend test proving a concurrency edge case the epic's own AC calls out).

---

## User Story

As an **HR Admin**,
I want to reverse/remove an HR Override I previously set,
So that an Assignment returns to being based on its underlying signal (video progress or self-reported status).

---

## ⚠️ Critical Pre-Implementation Findings (read before coding)

Found by reading the actual current code — `ProvenanceDrillDownModal.tsx`, `DashboardPage.tsx`, `dashboardApi.ts`, `progress/service.py`, `test_override_endpoint.py` — not just the epic text.

### Finding 1 — The backend is already 100% done; do not touch it except for one new test

`POST /api/assignments/{id}/override { action: 'unset' }` is fully implemented and tested by Story 5.5: `assignments/router.py:103-117` (route), `assignments/service.py::set_override_service` (403/404 scoping), `progress/service.py::set_override` (`progress/service.py:449-503`, handles `action == "unset"` at lines 483-489, including the `NO_ACTIVE_OVERRIDE` 404), `progress/repository.py::deactivate_override`/`acquire_override_lock`. Existing test coverage already proves: `test_unset_with_no_active_override_returns_404`, `test_set_then_unset_deactivates_and_reverts_to_underlying_signal`, `test_employee_role_gets_403_for_set_and_unset` (`backend/tests/test_override_endpoint.py`). `dashboardApi.setOverride(assignmentId, action, reason?)` (`frontend/src/lib/api/dashboardApi.ts:41-51`) already accepts `"unset"` as a valid `action` value — **do not add a second API client method.** If you find yourself editing `progress/service.py`'s mutation logic, `progress/repository.py`, `assignments/router.py`'s route signature, or `dashboardApi.ts`, stop — you've misread the scope. The only backend change in this story is one new **test** (Finding 4).

### Finding 2 — `DashboardPage.tsx`'s toast/refresh wiring is already generic; do not touch `DashboardPage.tsx`

Story 5.5 built `onOverrideChanged?: (message: string) => void` as a generic string-message callback, not a Mark-as-Ready-specific one. `DashboardPage.tsx:344-351` already renders `<ProvenanceDrillDownModal onOverrideChanged={(message) => { setToastMessage(message); fetchDashboard(); }}>`. Calling `onOverrideChanged("Override removed. ...")` from the new reversal handler needs **zero changes to `DashboardPage.tsx`** — same `Toast` primitive, same `fetchDashboard()` refresh Story 5.5 already wired (not the silent `pollDashboard()` — this is a direct result of the HR Admin's own action, matching Story 5.5's Subtask 7.2 reasoning exactly). Do not add a second callback prop or a second `Toast` render.

### Finding 3 — `[Mark as Ready]`'s visibility is already correct; only `[Reverse Override]`'s needs the same treatment

`ProvenanceDrillDownModal.tsx:209` already renders `[Mark as Ready]` only when `data.provenance !== "HR Override"` — this is already the correct half of epics.md:1849-1851's mutual exclusivity and needs no change. The gap is entirely on the other button: `[Reverse Override]` (current lines 217-224) is an **unconditional** disabled stub with no visibility check at all (`aria-label="Available once HR Override reversal is built — Story 5.5b"`). Fix: wrap it in `{data.provenance === "HR Override" && (...)}`, remove the `disabled`/`aria-label`/`title` stub attributes, wire a real `onClick`.

### Finding 4 — The epic's "concurrent reversal + fresh watch progress" AC has zero test coverage, and writing it correctly means routing around a known-broken endpoint

Story 5.5b's own AC ("State Management During Reversal", epics.md:1899-1908) requires proving that an `unset` completing concurrently with a fresh watch-progress write loses no data. **`progress/router.py`'s two routes are still live-broken** — double-prefixed (`backend/app/main.py:40` mounts `progress_router` at `prefix="/api/progress"`, but the router's own routes already declare the full `/api/assignments/{id}/progress` path, so the real reachable URL is `/api/progress/api/assignments/{id}/progress`). This is a pre-existing, already-tracked `deferred-work.md` item (Story 5-2 review) — **not this story's job to fix.** Story 5.5's own `test_fresh_watch_progress_after_override_shows_both_signals` (`test_override_endpoint.py:267-296`) already sidesteps it by inserting a `SkillProgress` row directly via a raw `_session_factory()` session instead of going through the broken HTTP route — **copy that exact technique** for the new test, combined with `test_concurrent_set_calls_leave_exactly_one_active_override_row`'s `asyncio.gather` pattern (`test_override_endpoint.py:357-395`) to fire the `unset` HTTP call and the direct `SkillProgress` insert genuinely concurrently (not sequentially), then assert a following drill-down GET shows both: the reversal took effect (`provenance != "HR Override"`) and the fresh signal is visible (`provenance == "Verified"`, correct percentage).

### Finding 5 — Confirmation view's fields are already on `DrillDownResponse`; reuse `UnderlyingSignal`'s label logic, don't reinvent it

Everything the confirmation view's AC text asks for is already present on the existing response shape (`frontend/src/types/dashboard.ts:34-53`): `override_set_by_name`, `override_set_at`, `status` (→ override status), and the four `underlying_*` fields for the "signal that will take effect" preview. `ProvenanceSection`'s existing `UnderlyingSignal` helper (`ProvenanceDrillDownModal.tsx:302-333`) already implements the exact per-branch Verified/Self-reported/Needs-Attention/Not-Started label mapping this preview needs — but it currently early-returns `null` when `underlying_provenance` is falsy (line 303), which is wrong for the confirm view: the epic explicitly wants a "Not Started · No signal" line shown even when there's no underlying signal at all, not a blank space. **Extract the label-computation switch (lines 311-326) into a standalone `describeUnderlyingSignal(data: DrillDownResponse): string`** (always returns a string, covering the `null`/`"Not Started"` case in one `default` branch exactly as the existing switch already does) — have `UnderlyingSignal` call it after its existing early-return guard (unchanged rendering, zero behavior change, verify its existing tests still pass), and have the new confirm view call it directly (bypassing the early return, since the confirm view needs the string unconditionally).

### Finding 6 — The epic's literal reversal-toast text is a one-size-fits-all string that doesn't match every underlying signal; verified as an actual mismatch, not assumed

epics.md:1878 hardcodes: *"Success toast appears: 'Override removed. Status now based on video progress.'"* — literally true only when `underlying_provenance === "Verified"`. If the underlying signal is Self-reported, Needs Attention, or nothing at all (Not Started — a real, reachable case: an HR Admin can mark Ready on an assignment with zero prior activity), the literal toast text would misdescribe the new state as "video progress" when none exists. This is the same class of imprecise-literal-AC-text issue Story 5.5's own Debug Log documents for its `??`/`||` finding (Finding 3 there) and Story 5.2's mislabeled "Underlying Signal" line — verify before trusting the literal string. **Build the toast message from the response's `underlying_provenance` instead of hardcoding the epic's exact string**: `"Verified"` → `"Override removed. Status now based on video progress."` (matches the epic's literal text for this one real case); `"Self-reported"` / `"Needs Attention"` → `"Override removed. Status now based on self-reported progress."`; `null` / `"Not Started"` → `"Override removed. No prior progress recorded — status now shows Not Started."` Document this as a deliberate, verified deviation in the Dev Agent Record (same pattern as Story 5.5's own `??`-deviation entry), not a silent change.

### Finding 7 — AC's "Last Updated timestamp is current" claim is not what `get_provenance_detail` actually does, and this story must not "fix" it

epics.md:1895 states post-reversal: *"Last Updated timestamp is current (shows reversal just happened)."* Reading `get_provenance_detail` directly (`backend/app/progress/service.py:390-446`) shows this is **not** how `last_updated` is derived: once `override` is `None`/inactive, the function returns the plain `underlying` `ProvenanceDetail`, whose `last_updated` is `assignment.assigned_at` (no progress ever recorded) or `progress.updated_at` (the video/self-report's own timestamp) — **never** the moment of the reversal itself. A reversal on a long-stale assignment will correctly show an old "Last Updated," not "just now." This is deliberate, correct-by-design behavior (the whole point of AR-3's single derivation authority is that `last_updated` always reflects the *signal's* freshness, not administrative actions on it) — **do not attempt to make `last_updated` reflect the reversal time**; that would require touching `progress/service.py`'s core derivation function used by every other consumer in the app (dashboard grid, drill-down GET, Mark-as-Ready), directly violating Finding 1's scope boundary. Treat the epic's parenthetical as imprecise color, not a literal requirement — same judgment call this project has made repeatedly (Story 5.2's shared-403-message decision, Story 5.5's `??` deviation).

---

## Acceptance Criteria

_Verbatim intent from epics.md lines 1830-1946 (Story 5.5b), numbered for traceability._

1. **Reversal button visibility:** an assignment with an active HR Override shows, in the drill-down: Provenance "🔒 HR Override" (already rendered, `ProvenanceSection`'s existing `case "HR Override"` branch), override status/by/at (already rendered), and a `[Reverse Override]` button — visible and enabled (not the current disabled stub). An assignment with **no** active override hides `[Reverse Override]` and shows `[Mark as Ready]` instead (already true, Finding 3). [epics.md:1838-1851]
2. **Confirmation flow:** clicking `[Reverse Override]` opens a confirmation view: "Remove this HR Override?", current override summary (e.g. "Status: Completed (set by Rita on 2026-07-09)"), the underlying signal that will take effect (e.g. "In Progress · Video progress: 65%", or the no-signal case if none exists — Finding 5), and `[Remove Override]` (red/confirm) / `[Cancel]` buttons. [epics.md:1857-1863]
3. **Cancel:** closes the confirmation view with no API call, no state change; the override remains active; returns to the detail view. [epics.md:1865-1870]
4. **Remove Override (confirm):** `POST /api/assignments/{assignment_id}/override { action: 'unset' }` (already implemented, Finding 1); on success the drill-down updates immediately from the response (no extra GET round-trip, same pattern Mark-as-Ready already uses); a success toast appears (Finding 6's corrected, signal-aware text); the confirm view closes back to the (now-updated) detail view. [epics.md:1872-1879]
5. **Post-reversal display:** the drill-down now shows the new Provenance derived from the underlying signal (Verified/Self-reported/Not Started, per `get_provenance_detail`'s existing logic — zero new derivation code, Finding 1); `[Mark as Ready]` is now visible (Finding 3's existing condition already handles this automatically once `provenance !== "HR Override"`); `[Reverse Override]` is hidden (this story's new condition, Finding 3); the dashboard row updates on the next refresh (Finding 2, already wired). [epics.md:1883-1895] — **Note:** "Last Updated timestamp is current" is not literally true by design; see Finding 7.
6. **Concurrent reversal + fresh watch progress:** an `unset` completing at the same time as a fresh watch-position write for the same assignment must not lose either change — the reversal completes, the fresh `skill_progress` write persists, and a following drill-down shows the newest signal with the override no longer shadowing it. New test required (Finding 4) — no implementation change expected (this is a proof, not a fix; `set_override`'s advisory lock only serializes concurrent override mutations against each other, and `skill_progress` writes are a structurally independent table/row, so no conflict is expected — the test exists to verify that assumption directly, not assume it).
7. **Access control:** an EMPLOYEE session calling `{ action: 'unset' }` gets 403 (already implemented and tested by Story 5.5's `test_employee_role_gets_403_for_set_and_unset`; Employees also cannot reach the drill-down modal at all per Story 5.2's AC6, so there is no new Employee-facing UI path in this story). No new test required.
8. **Dashboard integration:** after a reversal, the next dashboard poll/refresh shows the row's Status badge reflecting the new underlying signal and an updated Last Updated — already true via the existing `get_provenance_detail`-backed read path (Finding 1) plus Finding 2's existing `fetchDashboard()` wiring; no new code, verified by this story's frontend test (Task 3).

---

## Tasks / Subtasks

- [ ] Task 1: Frontend — `[Reverse Override]` visibility + shared confirm-mode branching (AC: 1, 5; `ProvenanceDrillDownModal.tsx`, Finding 3)
  - [ ] Subtask 1.1: Replace the unconditional disabled stub (current lines 217-224) with a button rendered only `{data.provenance === "HR Override" && (...)}`; remove `disabled`, `aria-label`, `title`; `onClick={() => setConfirming(true)}` — **reuses the existing `confirming` boolean** (do not add a second state flag: since `[Mark as Ready]` and `[Reverse Override]` are already mutually exclusive by `data.provenance`, whichever button is visible when `confirming` becomes `true` unambiguously determines which confirm sub-view to render — branch on `data.provenance === "HR Override"` inside the existing `confirming` block, not on a new mode variable).
  - [ ] Subtask 1.2: Style the new button distinctly from `[Mark as Ready]`'s blue text-link style — e.g. `text-sm font-medium text-red-600 hover:underline` — first destructive-styled interactive element in this codebase (no existing red *button* precedent to copy; `Login.tsx`'s `bg-red-50`/`text-red-700` is an error banner, not a button — establish the pattern here).

- [ ] Task 2: Frontend — reversal confirmation view (AC: 2, 3; `ProvenanceDrillDownModal.tsx`, Finding 5)
  - [ ] Subtask 2.1: Extract `describeUnderlyingSignal(data: DrillDownResponse): string` above `UnderlyingSignal` (move the existing switch body from lines 311-326 verbatim, drop the `label` variable name if you like but keep all 4 branches' exact wording unchanged) — `UnderlyingSignal` becomes `if (!data.underlying_provenance) return null; return <p ...>Original signal: {describeUnderlyingSignal(data)}</p>;` (unchanged rendered output — verify `UnderlyingSignal`'s existing call sites/tests still pass byte-for-byte after the extraction, this is a pure refactor).
  - [ ] Subtask 2.2: Inside the existing `{!loading && !error && data && confirming && (...)}` block (current lines 158-192), branch the rendered content on `data.provenance === "HR Override"`:
    - **Reversal branch** (new): heading `Remove this HR Override?`; a summary paragraph: `Status: {STATUS_DISPLAY[data.status]} (set by {data.override_set_by_name ?? "Unknown"} on {data.override_set_at ? new Date(data.override_set_at).toLocaleDateString() : "Unknown"})`; a second line: `Currently: {describeUnderlyingSignal(data)}` (Finding 5 — always renders a string, including the no-signal case); no textarea (a reversal carries no reason field, unlike Mark-as-Ready); `submitError && <p>...</p>` (reuse as-is); buttons `[Cancel]` (`onClick={handleCancelOverride}`, unchanged — already has no side effects) and `[Remove Override]` (`onClick={handleConfirmReversal}`, Task 3 — red styling per Subtask 1.2's palette, e.g. `bg-red-600 hover:bg-red-700` mirroring the existing `[Confirm]` button's exact shape/sizing classes at lines 183-189 with the color swapped).
    - **Mark-as-Ready branch** (existing): unchanged.
  - [ ] Subtask 2.3: `handleCancelOverride` (existing, lines 87-91) needs no changes — it already just resets `confirming`/`reason`/`submitError` with no API call, which is correct for both confirm sub-views (the reversal view never sets `reason`, so resetting it is a harmless no-op there).

- [ ] Task 3: Frontend — reversal submit handler (AC: 4, 6 [UI half], 8; `ProvenanceDrillDownModal.tsx`, Finding 2, Finding 6)
  - [ ] Subtask 3.1: Add `handleConfirmReversal`, mirroring `handleConfirmOverride`'s exact structure (`requestIdRef` staleness guard, `setSubmitting(true)`/`setSubmitError(null)`, try/catch/finally) but calling `dashboardApi.setOverride(assignmentId, "unset")` (no reason argument — `unset` rejects a non-blank `reason` with a 422 per Story 5.5's backend validation, so never pass one).
  - [ ] Subtask 3.2: On success: `setData(response)`, `setConfirming(false)`, call `onOverrideChanged?.(<Finding 6's signal-aware message>)` computed from `response.underlying_provenance` (not the request's own prior state — use the fresh response, which already reflects the post-reversal derivation).
  - [ ] Subtask 3.3: On failure: same pattern as `handleConfirmOverride`'s catch — `setSubmitError(message)`, stay in the confirm view (don't lose the user's place, though there's no typed input to preserve here since there's no textarea).
  - [ ] Subtask 3.4: No changes to `DashboardPage.tsx` (Finding 2 — the existing `onOverrideChanged` prop already does everything needed).

- [ ] Task 4: Backend — concurrency test only (AC: 6; `test_override_endpoint.py`, Finding 4)
  - [ ] Subtask 4.1: `test_concurrent_reversal_and_fresh_watch_progress_no_data_loss` (or similar name) — create an assignment, `POST .../override {action:'set'}` to establish an active override, then `asyncio.gather` two concurrent operations: (a) `client.post(.../override, json={"action": "unset"})`, (b) a raw `SkillProgress` insert via `_session_factory()` (copy `test_fresh_watch_progress_after_override_shows_both_signals`'s exact insert shape, `watch_position=120, verified=True, event_time=now`). Assert both succeed, then `GET .../progress/drill-down` and assert `provenance == "Verified"` (override no longer shadowing) and the watch data is reflected (`status_percentage` matches the fresh position, not stale/lost).
  - [ ] Subtask 4.2: No other backend file changes (Finding 1).

- [ ] Task 5: Frontend tests (extend `ProvenanceDrillDownModal.test.tsx`, no new file — matches Story 5.5's established one-file-per-component convention)
  - [ ] Subtask 5.1: `[Reverse Override]` renders and is enabled when `provenance === "HR Override"`; is absent entirely when `provenance !== "HR Override"` (mirrors Story 5.5's existing Subtask 9.1 pattern for the opposite button).
  - [ ] Subtask 5.2: Click `[Reverse Override]` → confirm view renders "Remove this HR Override?", the override summary line, and the underlying-signal preview line — for both a case with an underlying signal (`underlying_provenance: "Verified"`) and a case with none (`underlying_provenance: null`), asserting the no-signal case still renders a real string, not a blank/missing line (Finding 5).
  - [ ] Subtask 5.3: `[Cancel]` in the reversal confirm view → returns to detail view, `dashboardApi.setOverride` never called.
  - [ ] Subtask 5.4: `[Remove Override]` → calls `dashboardApi.setOverride(assignmentId, "unset")` (assert no third `reason` argument passed), updates `data` from the response, closes the confirm view, calls `onOverrideChanged` — assert the message text varies correctly across at least two `underlying_provenance` fixtures (`"Verified"` vs `null`), proving Finding 6's dynamic message actually branches rather than hardcoding one string.
  - [ ] Subtask 5.5: `[Remove Override]` failure (rejected promise) → shows an error, stays in the confirm view.
  - [ ] Subtask 5.6: A stale-response guard test for `handleConfirmReversal`, mirroring the existing pattern already covering `handleConfirmOverride` (Story 5.5's code review added this for the Mark-as-Ready path — the new reversal handler must have the same `requestIdRef` protection, Subtask 3.1).

- [ ] Task 6: Full regression pass
  - [ ] Subtask 6.1: Backend — run `test_override_endpoint.py` (full file, including the new test) in isolation, plus `test_drill_down_endpoint.py`/`test_provenance_detail.py` (shared import surface) — known pre-existing cross-file asyncpg pool-corruption pattern still open (`deferred-work.md`, Epic 4 retro action item), do not attempt to fix it here.
  - [ ] Subtask 6.2: Frontend — `npm run test` full suite; `tsc --noEmit` diffed via `git stash` against baseline (Story 5.2/5.4/5.5's established method) — assert **zero new** type errors, not a clean full-build pass.
  - [ ] Subtask 6.3: Update Dev Agent Record + File List (below) with actual results.

---

## Developer Context & Implementation Notes

### Why this story has almost no backend work

Story 5.5 deliberately built the shared `set`/`unset` endpoint as one mechanism up front (see that story's own "Why the endpoint handles both set and unset now" note) specifically so this story wouldn't need to reopen the router/service/repository trio. That decision paid off: this story's only backend change is a new **test** proving an edge case, not new production code.

### Reversal confirm-view sketch (`ProvenanceDrillDownModal.tsx`, inside the existing `confirming` block)

```tsx
{confirming && data.provenance === "HR Override" ? (
  <div className="space-y-4">
    <h2 id={titleId} className="text-lg font-bold text-gray-900">
      Remove this HR Override?
    </h2>
    <p className="text-sm text-gray-700">
      Status: {STATUS_DISPLAY[data.status]} (set by {data.override_set_by_name ?? "Unknown"} on{" "}
      {data.override_set_at ? new Date(data.override_set_at).toLocaleDateString() : "Unknown"})
    </p>
    <p className="text-sm text-gray-700">Currently: {describeUnderlyingSignal(data)}</p>
    {submitError && <p className="text-red-600 text-sm">{submitError}</p>}
    <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
      <button disabled={submitting} onClick={handleCancelOverride}
              className="text-sm font-medium text-gray-600 hover:underline disabled:opacity-50">
        Cancel
      </button>
      <button disabled={submitting} onClick={handleConfirmReversal}
              className="bg-red-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50">
        Remove Override
      </button>
    </div>
  </div>
) : confirming ? (
  /* existing Mark-as-Ready confirm view, unchanged */
) : (
  /* existing detail view, only the [Reverse Override] button's condition changes (Task 1) */
)}
```

### `handleConfirmReversal` sketch (mirrors `handleConfirmOverride`, `ProvenanceDrillDownModal.tsx:93-120`)

```tsx
function describeReversalToastMessage(underlying: DrillDownResponse["underlying_provenance"]): string {
  switch (underlying) {
    case "Verified":
      return "Override removed. Status now based on video progress.";
    case "Self-reported":
    case "Needs Attention":
      return "Override removed. Status now based on self-reported progress.";
    default:
      return "Override removed. No prior progress recorded — status now shows Not Started.";
  }
}

async function handleConfirmReversal() {
  if (!assignmentId) return;
  const requestIdAtSubmit = requestIdRef.current;
  setSubmitting(true);
  setSubmitError(null);
  try {
    const response = await dashboardApi.setOverride(assignmentId, "unset");
    if (requestIdRef.current !== requestIdAtSubmit) return;
    setData(response);
    setConfirming(false);
    onOverrideChanged?.(describeReversalToastMessage(response.underlying_provenance));
  } catch (err) {
    if (requestIdRef.current !== requestIdAtSubmit) return;
    const message = err instanceof Error ? err.message : "Couldn't remove override. Try again.";
    setSubmitError(message);
  } finally {
    if (requestIdRef.current === requestIdAtSubmit) {
      setSubmitting(false);
    }
  }
}
```

---

## Testing Strategy

**Backend:** one new integration test added to the existing `test_override_endpoint.py` (Task 4) — do not create a new test file. Real Postgres + `ASGITransport`, copying `_client`/`_login`/seed-constant/cleanup scaffolding already in that file verbatim.

**Frontend:** extend `ProvenanceDrillDownModal.test.tsx` (already has the `dashboardApi` mock + `baseResponse` fixture pattern, and already mocks `setOverride`) — add cases, do not create a second test file.

Do **not** re-test anything Story 5.5 already covers (Mark-as-Ready flow, `set` action's backend behavior, at-most-one-active-override invariant, `unset`-with-nothing-active 404) — this story's tests are additive, scoped to the reversal UI and the one new concurrency case.

---

## Architecture Compliance Checklist

- **AD-4 (HR Override is a separate, coexisting record):** unchanged by this story — the reversal flow calls the same `set_override(action="unset")` Story 5.5 already built correctly against this rule.
- **AR-3 (single derivation authority):** the reversal's UI response comes from the same `POST .../override` → `get_provenance_detail()` path as Mark-as-Ready (Finding 1); no new derivation code anywhere in this story.
- **AD-6 (server-side role/identity gate):** unchanged, already enforced and tested (AC7).
- **No new backend table/migration/endpoint:** if you find yourself adding one, stop — you've misread the scope (Finding 1).

---

## Known Issues & Deferrals

- **Finding 6's toast-message deviation from epics.md's literal string** is a deliberate, verified correction (not all reachable underlying-signal states are "video progress") — document in Dev Agent Record, don't silently diverge.
- **Finding 7's "Last Updated is current" AC text is not literally implemented** — `last_updated` continues to reflect the underlying signal's own freshness, not the reversal action's timestamp, by the existing (correct) design of `get_provenance_detail`. Not fixed by this story; flagged so nobody "fixes" it later without re-deriving why it's actually correct as-is.
- **`progress/router.py`'s double-prefix bug** (Finding 4) remains open, tracked in `deferred-work.md` since Story 5-2's review — this story routes around it for its one new test but does not fix it.
- **`conftest.py` cross-file asyncpg pool corruption** (open since the Epic 4 retro action item) — run touched test files in isolation per Subtask 6.1, same as every recent story.
- **Toast auto-dismiss doesn't reset for two identical back-to-back messages** (`deferred-work.md`, Story 5.5 review, `components/ui/toast.tsx`) — Finding 6's varied message text actually reduces the odds of hitting this pre-existing gap in practice (a reversal's message differs from a Mark-as-Ready message), but it's still open for the case of two reversals in a row with the same underlying-signal category. Not this story's scope to fix.

---

## Success Criteria

1. `[Reverse Override]` is visible and enabled only when `provenance === "HR Override"`; hidden otherwise — mirrors `[Mark as Ready]`'s existing opposite condition exactly (AC1).
2. Clicking it opens a confirmation view (same single-`Dialog`, no nested modal) showing the current override summary and the underlying signal that will take effect, including the explicit no-signal case (AC2, Finding 5).
3. Cancel makes no API call and leaves the override active (AC3).
4. Confirm calls the existing `unset` endpoint, updates the modal from the response with no extra round-trip, and shows a toast whose text correctly varies by the new underlying signal (AC4, Finding 6) — not a copy-pasted literal string that's wrong for 3 of its 4 possible states.
5. Post-reversal: `[Mark as Ready]` becomes visible, `[Reverse Override]` hides, dashboard row reflects the change on next refresh — all via already-existing machinery, zero new derivation code (AC5, AC8).
6. A new backend test proves a concurrent reversal and a concurrent fresh watch-progress write both persist correctly with no data loss (AC6).
7. Zero new type errors (`tsc --noEmit` diff); all new backend/frontend tests pass; pre-existing unrelated failures unchanged in count.

---

## Dev Notes

### Project Structure Notes

- Frontend files expected to change: `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` (reversal confirm view, `handleConfirmReversal`, `describeUnderlyingSignal`/`describeReversalToastMessage` extraction, `[Reverse Override]` condition), `frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx` (new cases, no new file).
- **No changes** to `DashboardPage.tsx` (Finding 2), `dashboardApi.ts` (Finding 1), any backend file except `backend/tests/test_override_endpoint.py` (one new test, Finding 4).
- No Alembic migration. No new endpoint. No new component/primitive beyond the red-button styling variant (Task 1.2).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5b] (lines 1830-1946) — full AC text this story implements
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5] (lines 1791-1828) — the sibling story that already built the shared endpoint this story's UI calls
- [Source: _bmad-output/implementation-artifacts/5-5-hr-override-manual-readiness-confirmation.md] — direct predecessor; the confirm-flow pattern (single-Dialog step-switch, `requestIdRef` staleness guard, `onOverrideChanged` contract) this story mirrors for the reversal half; its Known Issues & Deferrals section explicitly names this story as owner of the reversal UI, confirmation modal, toast copy, and race-condition test
- [Source: backend/app/progress/service.py:356-446] — `get_provenance_detail()`, confirms Finding 7's `last_updated` derivation and Finding 1's "no new derivation code" boundary
- [Source: backend/app/progress/service.py:449-503] — `set_override()`, confirms the `unset` action is fully implemented (Finding 1)
- [Source: backend/app/main.py:36-41] — router mount prefixes, confirms Finding 4's double-prefix bug is still present
- [Source: backend/tests/test_override_endpoint.py] — existing `unset`/concurrency test patterns to copy (`test_fresh_watch_progress_after_override_shows_both_signals`, `test_concurrent_set_calls_leave_exactly_one_active_override_row`)
- [Source: frontend/src/types/dashboard.ts:34-53] — `DrillDownResponse` shape, confirms all fields the confirm view needs already exist (Finding 5)
- [Source: frontend/src/lib/api/dashboardApi.ts:36-51] — `setOverride`, confirms `"unset"` is already a supported action (Finding 1)
- [Source: frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:93-120,209-224,302-333] — `handleConfirmOverride` (pattern to mirror), the two Action buttons (only one changes), `UnderlyingSignal` (label logic to extract, Finding 5)
- [Source: frontend/src/features/dashboard/DashboardPage.tsx:344-351] — existing generic `onOverrideChanged` wiring, confirms Finding 2 (no changes needed)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — Story 5-2 review's still-open `progress/router.py` double-prefix item (Finding 4), Story 5.5 review's Toast dedup item (Known Issues)
- [Source: _bmad-output/project-context.md] — Epic 5 architecture-spine summary; confirms `progress/` is the sole mutation authority for overrides, already fully exercised by the `unset` action this story only adds a UI trigger for

## Dev Agent Record

### Agent Model Used

_To be filled by dev-story._

### Debug Log References

_To be filled by dev-story._

### Completion Notes List

_To be filled by dev-story._

### File List

_To be filled by dev-story._

## Change Log

| Date | Change |
|------|--------|
| 2026-07-13 | Story created via bmad-create-story. Scoped as a frontend-only completion of the `[Reverse Override]` UI (visibility, confirmation view, submit handler) against the already-built-and-tested `unset` backend endpoint (Story 5.5), plus one new backend test proving the concurrent-reversal-vs-fresh-watch-progress race the epic's own AC calls out. Seven findings documented, most notably: the epic's literal reversal-toast text only fits one of four possible underlying-signal states (Finding 6, corrected to a signal-aware message) and its "Last Updated is current" claim doesn't match `get_provenance_detail`'s existing (correct) design (Finding 7, explicitly not "fixed"). |
