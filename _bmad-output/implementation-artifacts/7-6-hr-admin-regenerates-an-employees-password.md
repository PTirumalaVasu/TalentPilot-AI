---
baseline_commit: 672d9d77
---

# Story 7.6: HR Admin Regenerates an Employee's Password

Status: done

## Story

As an **HR Admin**,
I want to generate a new password for an existing Employee,
So that a lost or forgotten password is a quick fix, not a dead end (FR-28).

## Scope Notes (read before starting)

1. **No new migration needed.** `accounts.password_hash` and `accounts.archived_at` already exist (Story 7.1/7.5). This story only ever calls `UPDATE accounts SET password_hash = ...` — no schema change.

2. **New route: `POST /api/admin/employees/{employee_id}/regenerate-password`**, mounted on the already-existing `employees_router` (no new `main.py` mount). POST, not PATCH/PUT, matching this codebase's established action-endpoint convention for a verb that isn't a plain field update (`skills/router.py`'s `/{skill_id}/content-lookup`, `assignments/router.py`'s `/{assignment_id}/override`) — mirrors those, not `update_employee_route`'s PATCH-a-resource shape. Response model is `EmployeeCreatedResponse` — **reused as-is, not a new schema** — per the epic AC's explicit instruction to reuse "the same response/display mechanism" as Story 7.2's creation flow. Status code 200 (default), not 201: no new resource is created.

3. **Password generation + hashing already has a home.** `employees/service.py::generate_password()`/`hash_password()` (Story 7.1/7.2) — call them, don't reimplement. `hash_password` must run via `asyncio.to_thread` (Story 7.2 code review's async-event-loop-blocking fix) — this story's new service function is the second caller of that pattern, so mirror it exactly, don't regress to a synchronous call.

4. **New repository/service write path: `auth/repository.py::update_account_password_hash`.** No function updates `Account.password_hash` after creation today (`create_account` only sets it once, at insert). Add it following the exact centralization pattern already established by `update_account_email`/`update_account_archived_at`/`delete_account` (Story 7.2/7.5 code reviews: "the sole write path... so Account's column shape stays known in exactly one place") — including the `None`-guard those two most recent additions were specifically reviewed to require (`update_account_email` is the one exception that still lacks it, a pre-existing deferred gap, unrelated to this story — do not fix it here, out of scope).

5. **Archived-employee rejection uses a plain lookup, not the `FOR UPDATE` row-lock mechanism Story 7.5 built.** Story 7.5's lock exists to make a *hard-delete-vs-archive decision* atomic against a concurrent Assignment-creation race — nothing analogous is being decided here. This story's AC2 is a simple point-in-time state check ("is this employee currently archived") with no check-then-act correctness requirement beyond it — use `employees/repository.py::get_employee_by_id` (already exists, Story 7.4), not `get_employee_for_update`. Don't invent lock-based atomicity this AC never asked for.

6. **New service-layer conflict helper, not a reuse of `_archived_conflict`.** `employees/service.py::_archived_conflict` (Story 7.5) is purpose-built for the Assignment-picker re-pick scenario — its message text ("please re-pick from the current roster") would be confusing here. Add a new `_archived_for_regenerate_conflict(employee_id) -> AppException` returning `409` with `error_code="EMPLOYEE_ARCHIVED"` (same error code, reused deliberately — both are "this employee is archived" conditions, just in different contexts) and a message specific to this action (e.g. "Employee '{employee_id}' is archived — password regeneration only applies to active employees").

7. **`has_assignment_history` must still be populated correctly on the response**, exactly like `create_employee_service`/`update_employee_service` do (Story 7.5 Scope Note 4's "used consistently by all three service functions" — this is now the fourth). Since a real Employee already exists (unlike creation, which is always `False` by construction), use the single-employee check `_has_any_history_for_employee`, not the bulk roster-wide one — mirrors `update_employee_service`'s exact call shape.

8. **Frontend: this is the first time a Password Reveal panel is built in this codebase.** Story 7.2 shipped backend-only (`EmployeesPage.tsx`'s own header comment: "7.2's still-unbuilt frontend half") — no Create Employee modal or Password Reveal panel exists yet anywhere in `frontend/`. This story builds the Password Reveal UI for the **first** time, scoped only to the Regenerate flow (05.1/05.3's spec explicitly designs it to be shared with a future Create flow, but building that Create-flow frontend is not this story's scope — don't build it "while you're in there"). Keep the reveal UI self-contained inside the new Regenerate modal component rather than extracting a separate shared component nobody else calls yet.

9. **One new modal component, two-step flow, not two separate modals.** `frontend/src/features/admin/RegeneratePasswordModal.tsx` (new), structurally opened/closed the same way `DeleteArchiveEmployeeModal.tsx` is (a single `open`/`employee` prop pair from `EmployeesPage.tsx`), but internally manages its own step state: **Confirm** (05.1's Regenerate Password Panel copy) → **Regenerating** (inline spinner on the confirm button, per 05.1's Page States table) → **Revealed** (05.3's Password Reveal Panel copy, terminal — the modal transitions in place rather than closing-and-reopening) → **Error** (inline, per 05.1's Page States table: `"Couldn't regenerate — [Try again]"`, modal stays on the Confirm step). Reset all internal step state on `employee?.id`/`open` change, mirroring `DeleteArchiveEmployeeModal.tsx`'s existing `useEffect` reset pattern.

10. **Regenerate Password's icon button becomes real; Delete/Archive and Edit are untouched** (both already wired, Stories 7.4/7.5). `EmployeesPage.tsx`'s `RowActions` currently routes the key-icon button to the shared `onUnavailable` stub at **both** JSX call sites (table row and card view) — wire **only** that button to a new `onRegeneratePassword: (employee: EmployeeResponse) => void` prop, at both call sites.

11. **No roster refetch needed on completion.** Unlike Delete/Archive (which changes `archived_at`/roster membership) or Edit (which changes displayed fields), regenerating a password changes nothing visible in the roster table/card grid — `EmployeesPage.tsx`'s `employees` state needs no `refetch()` call when the modal's "Done" button closes it. Don't add one "for consistency" with the other two flows; there is nothing to refresh.

12. **The Copy button's toast is page-level, not a second modal-local toast mechanism.** `EmployeesPage.tsx` already owns one `<Toast/>` instance (Story 7.4-established `toastMessage` state) — reuse it via a new `onCopied: () => void` callback prop from the modal, exactly like `onCompleted`'s existing bubble-up shape, rather than inventing a modal-scoped toast/announcement of its own.

13. **Copy-to-clipboard has no existing precedent in this codebase** (confirmed: no `navigator.clipboard` usage anywhere in `frontend/src/`) — this is the first. Per 05.3's Design Constraints ("copy failures should fail silently to a manual-select fallback, not surface the password in a console/log message" — the password value is already rendered as selectable monospace text, satisfying the fallback): wrap `navigator.clipboard.writeText(password)` in `try { ...; onCopied(); } catch { /* silent */ }` — no error state, no console.error, no logging of the password value under any circumstance.

14. **Title is conditional per the UX doc's own flagged correction, not the HTML mock's shortcut.** 05.3 explicitly flags that the mock's "Employee created" title is wrong when opened via Regenerate and specifies "Password regenerated" as the correct title for this flow. Since this story only ever opens the panel via Regenerate (Create's frontend doesn't exist yet), hardcode `"Password regenerated"` directly — do not build a conditional `mode: 'create' | 'regenerate'` prop for a caller that doesn't exist yet (YAGNI; a future Create-flow story can add that branch when it actually needs it).

15. **UX copy is spec'd exactly — use verbatim** (`_bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md:166-175` for the confirm step, `05.3-password-reveal/05.3-password-reveal.md` for the reveal step):

    | `data-testid` | Step | Content (verbatim) |
    |---|---|---|
    | `regen-password-heading` | Confirm | "Regenerate password for {Employee name}?" |
    | `regen-password-summary` | Confirm | "Their current password will stop working immediately. You'll get a new one to share with them." |
    | `regen-password-btn-cancel` | Confirm | "Cancel" |
    | `regen-password-btn-confirm` | Confirm | "Regenerate Password" (label; shows a brief inline spinner state while the request is in flight, e.g. "Working…" matching `DeleteArchiveEmployeeModal.tsx`'s existing convention) |
    | `password-reveal-title` | Revealed | "Password regenerated" (per 05.3's flagged create-vs-regenerate title fix) |
    | `password-reveal-summary` | Revealed | "Share this password with {Employee name} — it won't be shown again." |
    | `password-reveal-value` | Revealed | The generated password, as selectable monospace text (not an input, not masked) |
    | `password-reveal-btn-copy` | Revealed | "Copy" — on click, copies to clipboard and fires `onCopied()` (Scope Note 12/13); panel stays open |
    | `password-reveal-recovery-note` | Revealed | "Lost this before sharing it? Use \"Regenerate Password\" from the employee's row — a lost password is a quick fix, not a dead end." |
    | `password-reveal-btn-done` | Revealed | "Done" — closes the modal (no refetch, Scope Note 11) |

    Page-level toast (via `onCopied`, Scope Note 12): `Password copied to clipboard` (reuses `EmployeesPage.tsx`'s existing `<Toast/>`/`toastMessage` mechanism, same one Stories 7.4/7.5 already use — don't invent a new one).

    Error state (Confirm step, on a failed regenerate call): inline error text via the standard `extractErrorMessage()` pattern (matches `DeleteArchiveEmployeeModal.tsx`'s `FormErrorText` usage) — modal stays on the Confirm step, per 05.1's Page States table.

16. **`aria-label` for the row action button already exists and is correct — do not change it.** `EmployeesPage.tsx`'s existing button already carries `aria-label={\`Regenerate password for ${employee.name}\`}` (added in Story 7.3 per UX-DR42, currently wired to `onUnavailable`) — this story only changes its `onClick` target, not its accessible name.

## Acceptance Criteria

**AC1 — Active Employee: regenerate, hash, store, one-time reveal:**
**Given** an active (non-archived) Employee
**When** I trigger "Regenerate Password"
**Then** a new password is generated server-side, hashed, and stored, immediately invalidating the previous one — shown to me exactly once, in the same one-time-reveal pattern as Story 7.2's creation flow (reusing the same response/display mechanism, UX-DR37: modal title reads "Password regenerated" here vs. "Employee created" on Story 7.2's path).

**AC2 — Archived Employee: unavailable/rejected:**
**Given** an archived Employee
**When** I attempt to regenerate their password
**Then** the action is unavailable/rejected — regeneration only applies to active Employees (un-archiving, if supported, is a separate action from this story's scope).

**AC3 — Credential operation, not a profile edit:**
**And** this is a credential operation, not a profile edit — it is not gated by or related to Story 7.4's field-edit scope, and Employee ID/Code is never involved.

## Tasks / Subtasks

- [x] **Task 1: Auth repository — password-hash write path** (`backend/app/auth/repository.py`) (AC1)
  - [x] `update_account_password_hash(db: AsyncSession, *, id: UUID, password_hash: str) -> None` — mirrors `update_account_archived_at`'s exact shape: `db.get(Account, id)`, guard `None` (return early — AR-24's 1:1 invariant makes a missing Account unreachable in normal operation, but the guard is free and matches the established pattern), `account.password_hash = password_hash`, `await db.flush()`.

- [x] **Task 2: Employees service — the regenerate service itself** (`backend/app/employees/service.py`) (AC1, AC2, AC3)
  - [x] `_archived_for_regenerate_conflict(employee_id: UUID) -> AppException` — `409`, `error_code="EMPLOYEE_ARCHIVED"`, message specific to this action (Scope Note 6).
  - [x] `regenerate_password_service(db, *, current_user, employee_id) -> EmployeeCreatedResponse`:
    1. `require_hr_admin(current_user)`.
    2. `employee = await repository.get_employee_by_id(db, employee_id)`; `404` (`_not_found`) if `None`.
    3. If `employee.archived_at is not None`: raise `_archived_for_regenerate_conflict(employee_id)` (AC2).
    4. `plaintext_password = generate_password()`.
    5. `password_hash = await asyncio.to_thread(hash_password, plaintext_password)` (Scope Note 3).
    6. `await auth_repository.update_account_password_hash(db, id=employee_id, password_hash=password_hash)`.
    7. `has_history = await _has_any_history_for_employee(db, employee_id)` (Scope Note 7).
    8. Return `EmployeeCreatedResponse(**_with_assignment_history(EmployeeResponse.model_validate(employee), has_history).model_dump(), generated_password=plaintext_password)` — same construction shape as `create_employee_service`'s return (Story 7.2).

- [x] **Task 3: Employees router** (`backend/app/employees/router.py`) (AC1, AC2)
  - [x] `POST "/{employee_id}/regenerate-password"` → `regenerate_password_route`, `response_model=EmployeeCreatedResponse`, same `Depends(get_current_user)`/`Depends(get_db)` shape as the other three routes, default 200 status.

- [x] **Task 4: Backend tests** (`backend/tests/test_employees_router.py`, extend — use the existing private-engine/`_login`/`_delete_employee_by_code` conventions in this file)
  - [x] AC1: create an active employee, `POST .../regenerate-password` → `200`, response includes `generated_password` (a new 12-char value, alphabet-matching `generate_password()`), `has_assignment_history` correctly reflects the employee's history.
  - [x] AC1/invalidation: after regenerating, `verify_password(old_plaintext, <fresh Account.password_hash read from DB>)` is `False` and `verify_password(new_plaintext, ...)` is `True` — confirms the previous password stops working, not just that a new one exists.
  - [x] AC1/no-leak: confirm the plaintext password never appears in any other endpoint's response (e.g. `GET /api/admin/employees` for that employee) — mirrors Story 7.2's equivalent no-leak test.
  - [x] AC2: create an employee, archive them (reuse the existing `DELETE` endpoint or direct repository archive call, matching this file's established setup conventions), `POST .../regenerate-password` → `409 EMPLOYEE_ARCHIVED`; confirm `Account.password_hash` is unchanged (the call had no side effect).
  - [x] AC3: confirm the request body is empty/no-op with respect to profile fields (no request schema needed — the endpoint takes no body) and that `employee_code`/other profile fields on the response are unchanged from before the call.
  - [x] 404: `POST` against a random non-existent UUID → `404 EMPLOYEE_NOT_FOUND`.
  - [x] Role gate: EMPLOYEE session → `403`; unauthenticated → `401`, matching every other route in this router.
  - [x] Full regression run; record before/after counts in the Dev Agent Record.

- [x] **Task 5: Frontend API client** (`frontend/src/lib/api/employeesApi.ts`, extend) (AC1)
  - [x] `RegeneratePasswordResponse` interface: `EmployeeResponse & { generated_password: string }`.
  - [x] `regeneratePassword(id: string): Promise<RegeneratePasswordResponse>` → `POST /api/admin/employees/${id}/regenerate-password` (no request body).

- [x] **Task 6: Regenerate Password modal — confirm + reveal, two-step** (`frontend/src/features/admin/RegeneratePasswordModal.tsx`, new file, Scope Notes 8-9)
  - [x] Props: `employee: { id: string; name: string } | null`, `open: boolean`, `onClose: () => void`, `onCopied: () => void`.
  - [x] Internal step state: `'confirm' | 'regenerating' | 'revealed'`; reset to `'confirm'` (plus clearing any error/password state) on `employee?.id`/`open` change, mirroring `DeleteArchiveEmployeeModal.tsx`'s existing reset `useEffect`.
  - [x] Confirm step: renders `regen-password-heading`/`regen-password-summary`/`regen-password-btn-cancel`/`regen-password-btn-confirm` per Scope Note 15's table; `handleConfirm` calls `regeneratePassword(employee.id)`, moves to `'revealed'` on success (storing the returned `generated_password`), shows inline error and stays on `'confirm'` on failure (via `extractErrorMessage()`, matching `DeleteArchiveEmployeeModal.tsx`'s pattern).
  - [x] Revealed step: renders `password-reveal-title`/`password-reveal-summary`/`password-reveal-value`/`password-reveal-btn-copy`/`password-reveal-recovery-note`/`password-reveal-btn-done` per Scope Note 15; Copy button calls `navigator.clipboard.writeText` per Scope Note 13 (silent catch, then `onCopied()` only on success); Done calls `onClose()` (no refetch, Scope Note 11).
  - [x] Guard against a stale in-flight request completing after the modal was closed/reopened for a different employee, using the same `requestIdRef` pattern as `DeleteArchiveEmployeeModal.tsx`.

- [x] **Task 7: Wire into `EmployeesPage.tsx`** (extend, Scope Notes 10, 12)
  - [x] New state: `const [regeneratingEmployee, setRegeneratingEmployee] = useState<EmployeeResponse | null>(null)`.
  - [x] `RowActions` gains `onRegeneratePassword: (employee: EmployeeResponse) => void`; wire **both** call sites' (table row + card view) Regenerate Password button to it — removed that button's `onUnavailable` wiring, and removed the now-dead `onUnavailable` prop from `RowActions` entirely (Edit/Delete-Archive untouched; "+ New Employee" still calls `showUnavailableToast` directly, unaffected).
  - [x] Render `<RegeneratePasswordModal ... />` alongside the existing `<EditEmployeeModal/>`/`<DeleteArchiveEmployeeModal/>`.
  - [x] `handlePasswordCopied`: `setToastMessage('Password copied to clipboard')` (reuses the page's existing `<Toast/>`, Scope Note 12).
  - [x] `onClose` for the new modal: `setRegeneratingEmployee(null)` — no `refetch()` call (Scope Note 11).

- [x] **Task 8: Frontend tests**
  - [x] `frontend/src/tests/RegeneratePasswordModal.test.tsx` (new, colocated under `frontend/src/tests/` per the established location convention): confirm step renders the correct copy/employee name; confirm calls the API and transitions to the revealed step with the returned password displayed; a failed confirm call shows an inline error and stays on the confirm step; Copy calls `navigator.clipboard.writeText` and fires `onCopied` on success, and does NOT throw/surface an error when clipboard access fails (mock a rejecting `navigator.clipboard.writeText` and assert no error is shown/thrown); Done calls `onClose`.
  - [x] `frontend/src/tests/EmployeesPage.test.tsx` (extend, per the Story 7.4/7.5-established split precedent): split the current combined stub-toast test into: (a) a test confirming only "+ New Employee" still shows the stub toast, (b) a new test confirming Regenerate Password now opens `RegeneratePasswordModal` pre-filled with that row's employee name, and that copying the revealed password shows the page-level "Password copied to clipboard" toast.
  - [x] `tsc --noEmit` and `vite build` clean; record before/after in the Dev Agent Record.

### Review Findings

_(`bmad-code-review`, 2026-09-12, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Reachability verified by direct code reading before rating, per this project's established review-quality standard.)_

- [x] [Review][Patch] TOCTOU: the archived-employee check has no row lock, so a concurrent archive can land between the check and the password write — `regenerate_password_service` reads `employee.archived_at` once via a plain `get_employee_by_id`, then awaits `asyncio.to_thread(hash_password, ...)` (~100-300ms) before writing the new hash; a concurrent `delete_or_archive_employee_service` call (which *does* take `FOR UPDATE`) can archive the employee inside that window, leaving them with a freshly-working password despite AC2's "regeneration only applies to active employees" guarantee. Currently inert in practice (no login path reads `Account.password_hash` yet — `authenticate()` is still `_MOCK_ACCOUNTS`-only, a pre-existing, separately-tracked Epic 7 gap), but the fix is free: swap to the already-existing `repository.get_employee_for_update`. [`backend/app/employees/service.py:380-389`]
- [x] [Review][Patch] Escape/backdrop-click during the `'regenerating'` step silently discards an already-completed password regeneration — `Dialog`'s `onClose` maps to `handleCancel` for every non-`'revealed'` step, including `'regenerating'`; the Cancel *button* is correctly disabled in-flight, but Escape/backdrop-click aren't gated the same way, so closing the modal mid-request bumps `requestIdRef` and the resolved response is silently dropped by the stale-request guard — the server-side regeneration already happened and the new plaintext is now unrecoverable except via a second regenerate. [`frontend/src/features/admin/RegeneratePasswordModal.tsx:89`]
- [x] [Review][Patch] Duplicated `"EMPLOYEE_ARCHIVED"` error-code string literal between `_archived_conflict` (Story 7.5) and this story's new `_archived_for_regenerate_conflict` — both in the same file with no shared constant, so the two can silently drift out of sync on a future edit. [`backend/app/employees/service.py:319,358`]
- [x] [Review][Patch] No test exercises `has_assignment_history: true` on the regenerate-password response — the one new AC1 test only covers a freshly-created employee (always `false` by construction); Scope Note 7 calls for the field to be "populated correctly," which the `true` branch never gets asserted for this endpoint. [`backend/tests/test_employees_router.py`]
- [x] [Review][Patch] No test verifies the confirm button is actually disabled during the `'regenerating'` step — the `disabled={step === 'regenerating'}` guard exists in the component but has no regression coverage. [`frontend/src/tests/RegeneratePasswordModal.test.tsx`]

Dismissed as spec-compliant, out of scope, or already-established precedent (verified by direct code/spec reading, not taken at face value): concurrent regenerate calls both succeeding with "last write wins" is the feature's own intended semantics (AC1 itself says regenerating "immediately invalidat[es] the previous one"), not a bug; no audit trail, no step-up re-authentication, no employee notification path, and no rate limiting are all real gaps but out of this story's AC/Scope-Note scope and consistent with equivalent gaps already accepted elsewhere in this app (e.g. Story 1.4's deferred no-rate-limiting item); reusing `EmployeeCreatedResponse` is Scope Note 2's explicit, spec-mandated choice, not an oversight; the duplicated `extractErrorMessage` helper and the no-auto-hide/silent-clipboard-failure behavior on the revealed password both match this codebase's and the UX spec's own explicit, pre-existing conventions (05.3's Design Constraints explicitly require silent clipboard-failure handling and a persistent, not auto-hidden, password value); the `None`-guard in `update_account_password_hash` mirrors `update_account_archived_at`'s identical, already-accepted unreachable-by-invariant guard shape; the role-gate test's use of a hardcoded `casey@sails.example.com` login matches the exact convention used by every other role-gate test in this file; a claimed router-docstring overclaim about session invalidation was verified false — the docstring only claims the *password* is invalidated, which the tests confirm, and never mentions sessions; a claimed missing client-side gate on the Regenerate Password button for archived employees was confirmed to satisfy the epic AC's disjunctive "unavailable/rejected" wording via server-side rejection, matching this page's existing pattern of never gating other row actions client-side either.

## Dev Notes

### Why this story is smaller than 7.4/7.5 despite touching the same modules

Unlike Story 7.5 (three separate correctness mechanisms across three modules) or Story 7.4 (email-sync + IntegrityError races), this story has exactly one real design decision (the archived-employee rejection, a plain point-in-time check) and otherwise composes entirely out of already-built pieces: `generate_password`/`hash_password` (Story 7.1/7.2), the `EmployeeCreatedResponse` schema and its exact-once-reveal contract (Story 7.2), `_has_any_history_for_employee` (Story 7.5), and the `update_account_*` centralization pattern (Story 7.2/7.4/7.5 code reviews). The only genuinely new backend code is one repository function and one thin service function. Don't over-build this story to match the shape of its two predecessors — there is no atomicity requirement, no cross-module history-check expansion, and no session-revalidation change needed here.

### `[RETRACTED 2026-09-12, code review]` Why AC2 doesn't need Story 7.5's row-lock mechanism

**This reasoning was wrong and has been reversed — `regenerate_password_service` now does use `repository.get_employee_for_update`'s `FOR UPDATE` lock.** The original argument ("is `archived_at` currently set" is read once and acted on once, with no multi-step decision a concurrent write could invalidate) missed that there *is* an await between the read and the write: `asyncio.to_thread(hash_password, ...)` takes ~100-300ms, during which a concurrent `delete_or_archive_employee_service` call could archive the employee and this call would still hand back a freshly-working password for a now-archived employee — a real, if currently inert (see below), AC2 violation. Code review caught this by asking what actually happens during the await window, not just re-reading the docstring's own claim. Left here, struck through in spirit rather than deleted outright, as a reminder that "no multi-step decision" needs to account for every `await` in the function, not just the ones between explicit branches — the same class of lesson Story 7.4's `MissingGreenlet` finding and Story 7.5's `IntegrityError`-backstop lock-reacquisition already taught this codebase.

**Why this was practically inert regardless (not an excuse to skip the fix, just context):** `authenticate()` still only reads `_MOCK_ACCOUNTS` (unchanged since Story 1.4, reconfirmed unrelated by every Epic 7 story since) — no login path anywhere in this app currently reads `Account.password_hash` at all, so the race's actual consequence (an archived employee holding a working `Account` password) has no live exploitation path today. This will change the moment a future story wires `authenticate()` to `Account` (the same "currently-unassigned gap" Story 7.1's Dev Notes originally flagged) — fixing the race now, while the cost is one line, avoids re-discovering it under time pressure later.

### The Password Reveal panel is genuinely new UI, not a refactor of existing code

Confirmed by reading `EmployeesPage.tsx`'s own header comment and Story 7.2's File List (backend-only): no Create Employee modal, no Password Reveal panel, and no clipboard-copy code exists anywhere in `frontend/src/` today. This story is what actually builds the UI half of the "one-time reveal" contract Story 7.2's backend already implemented five stories ago. Build it to the 05.3 spec's exact copy/testids/behavior (Scope Note 15) since a future Create-flow story, if ever built, is expected to reuse this same visual/interaction pattern (per 05.3's own "Entry Point: Automatic... Also reused by 05.1's 'Regenerate Password' action" framing) — even though this story deliberately does not build that shared-component extraction itself (Scope Note 8, YAGNI until a second real caller exists).

## Architecture Compliance

- **AD-1**: `auth/repository.py::update_account_password_hash` is the sole write path for `accounts.password_hash` post-creation, following the same centralization AD-1-adjacent pattern `update_account_email`/`update_account_archived_at`/`delete_account` already established — `employees/service.py` decides *when* to regenerate, `auth/repository.py` remains the only place that knows `Account`'s column shape.
- **AD-6/FR-14**: `POST /api/admin/employees/{employee_id}/regenerate-password` is HR_ADMIN-only via `require_hr_admin`, matching every other `/api/admin/employees/*` mutation in this codebase.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.6] — full AC text
- [Source: _bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md] — `generate_password()`, `hash_password()`/`asyncio.to_thread` offload pattern, `EmployeeCreatedResponse`'s exact-once-reveal contract this story reuses verbatim
- [Source: _bmad-output/implementation-artifacts/7-5-hr-admin-deletes-or-archives-an-employee-record.md] — `_has_any_history_for_employee`, `update_account_archived_at`'s `None`-guard precedent, the `DeleteArchiveEmployeeModal.tsx`/`requestIdRef`/`extractErrorMessage()` frontend shape this story's new modal mirrors
- [Source: _bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md] — `update_account_email`'s centralization precedent, the "split the combined stub-toast test" convention
- [Source: backend/app/employees/service.py, repository.py, router.py, schemas.py] — current module state, read in full during story authoring
- [Source: backend/app/auth/repository.py, models.py] — `Account.password_hash`/`archived_at` current shape; `update_account_email`/`update_account_archived_at`/`delete_account`'s established write-path pattern
- [Source: backend/app/skills/router.py::/{skill_id}/content-lookup, backend/app/assignments/router.py::/{assignment_id}/override] — the action-endpoint (POST, non-CRUD verb) routing convention this story's new route mirrors
- [Source: frontend/src/pages/hr/EmployeesPage.tsx, lib/api/employeesApi.ts] — `RowActions`' current stub wiring for Regenerate Password, `refetch()`/toast conventions
- [Source: frontend/src/features/admin/DeleteArchiveEmployeeModal.tsx, components/ui/dialog.tsx, components/ui/toast.tsx, components/ui/form-error-text.tsx] — the modal/error/toast primitives `RegeneratePasswordModal.tsx` reuses
- [Source: _bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md#Regenerate Password Panel] — confirm-step copy/testids/page-states (verbatim table, Scope Note 15)
- [Source: _bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.3-password-reveal/05.3-password-reveal.md] — reveal-step copy/testids/page-states/accessibility/security constraints (verbatim, Scope Note 15), including the flagged create-vs-regenerate title correction (UX-DR37)
- [Source: backend/tests/test_employees_router.py] — private-engine/`_login`/`_delete_employee_by_code` test conventions to follow

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `python -c "import app.main"` confirmed no circular-import regression before writing any tests (no new import edges were introduced — `regenerate_password_service` reuses `auth_repository`/`generate_password`/`hash_password`/`_has_any_history_for_employee`, all already imported by `employees/service.py`).
- Backend: all 7 new tests (`test_employees_router.py`) passed on first run, no red-phase fix needed — the story's Scope Notes matched the existing `create_employee_service`/`delete_or_archive_employee_service` patterns closely enough that the implementation matched the tests' expectations immediately.
- Full backend regression: 699 passed, 2 skipped, 0 failed (692-passed post-Story-7.5 baseline + 7 new), in 118.42s.
- Frontend: initial clipboard-mocking attempts in `RegeneratePasswordModal.test.tsx` failed twice before landing on the right approach — worth recording as a real trap for future tests touching clipboard: (1) `Object.assign(navigator, {clipboard: ...})` throws (`"Cannot set property clipboard of #<Navigator> which has only a getter"`) because `@testing-library/user-event` v14 installs its own getter-only Clipboard stub on `navigator.clipboard` the moment `userEvent.setup()` runs, and re-attaches it on every `setup()` call; (2) even `Object.defineProperty`/`vi.stubGlobal` calls made *before* `userEvent.setup()` get silently clobbered, since `setup()` always re-installs its own stub afterward. The fix: call `userEvent.setup()` first, then `vi.spyOn(navigator.clipboard, 'writeText')` on the real (now-installed) stub object to control/assert its behavior — not attempt to replace `navigator.clipboard` at all. Applied this pattern consistently in both `RegeneratePasswordModal.test.tsx` and (implicitly, via the working real stub) `EmployeesPage.test.tsx`'s new Story 7.6 test.
- Full frontend regression: 384 passed, 0 failed (375-passed post-Story-7.5 baseline + 9 new: 8 in the new `RegeneratePasswordModal.test.tsx`, +1 net in `EmployeesPage.test.tsx` from splitting the old combined stub-toast test into two and adding one new real-behavior test).
- `tsc --noEmit`: 73 pre-existing errors (down from 74 during an intermediate check — that 74th was a real regression this story introduced and fixed: `RowActions`' `onUnavailable` prop became fully unused once Regenerate Password was wired to a real handler, since Edit/Delete-Archive were already wired by Stories 7.4/7.5; removed the now-dead prop and its call-site wiring instead of leaving it declared-but-unused). Confirmed via diff that the remaining 73 are unchanged/pre-existing and none are in any file this story touched.
- `vite build`: clean, 533 modules (up from 532 pre-story, for the new `RegeneratePasswordModal.tsx`).
- Live-verified end-to-end via `curl` against a rebuilt Docker backend (`docker compose build backend && docker compose up -d --no-deps --force-recreate backend`): as Rita — created a test employee, regenerated their password (`200`, new password differs from the create-time password), archived the same employee directly via a `docker exec` Python/SQLAlchemy script (no un-archive path exists, so this is the only way to reach the archived state outside the UI), confirmed the same regenerate call now returns `409 EMPLOYEE_ARCHIVED` with the exact message text; confirmed a nonexistent employee_id returns `404 EMPLOYEE_NOT_FOUND` and an unauthenticated request returns `401`; confirmed an EMPLOYEE-role session (Casey) gets `403 FORBIDDEN_NOT_HR_ADMIN`. All live test data cleaned up from the dev DB afterward. A full ad hoc Playwright/Chromium browser smoke test (the pattern prior Epic 7 stories used) was not run this round — the combination of live `curl` verification against the real endpoint plus the full automated frontend test suite (which exercises the actual React component tree, not just the API contract) was judged sufficient coverage for a story this size; noted here as a deliberate scope call, not an oversight.

### Completion Notes List

- Backend: `auth/repository.py::update_account_password_hash` added (mirrors `update_account_archived_at`'s exact `None`-guard shape); `employees/service.py::regenerate_password_service` (HR-Admin-gated, 404 on missing employee, 409 `EMPLOYEE_ARCHIVED` on an archived one via a new `_archived_for_regenerate_conflict` helper, `asyncio.to_thread`-offloaded bcrypt hashing, correct `has_assignment_history` via the existing `_has_any_history_for_employee`); `POST /api/admin/employees/{employee_id}/regenerate-password` mounted, reusing `EmployeeCreatedResponse` as-is (no new schema), matching the epic AC's explicit "reusing the same response/display mechanism" instruction.
- Deliberately did **not** reuse Story 7.5's `get_employee_for_update`/`FOR UPDATE` row lock for the archived check — this story's Dev Notes explain why: there's no multi-step decision here that a concurrent write could invalidate mid-flight, just a point-in-time read, so a plain `get_employee_by_id` lookup is the correct (simpler) mechanism, not a missed opportunity to reuse Story 7.5's pattern.
- Frontend: `RegeneratePasswordModal.tsx` (new) is the first Password Reveal UI in this codebase — Story 7.2 shipped backend-only, so no Create-flow frontend existed to extend. Built as a single component with an internal confirm → regenerating → revealed step state, per 05.1/05.3's UX specs' verbatim copy and `data-testid`s, including 05.3's own flagged title fix ("Password regenerated," not the mock's "Employee created"). `EmployeesPage.tsx`'s previously-fully-stubbed Regenerate Password action (both table and card call sites) now opens it; the now-fully-unused `onUnavailable` prop was removed from `RowActions` rather than left as dead code (only "+ New Employee" still uses the stub toast directly, unaffected).
- Copy-to-clipboard (`navigator.clipboard.writeText`) is the first use of the Clipboard API in this codebase — implemented with a silent `catch` per the UX spec's security constraint (never logs/throws/surfaces the password on a copy failure; the value remains selectable as a manual-copy fallback).
- No roster `refetch()` is triggered on completion (Scope Note 11) — regenerating a password changes nothing visible in the roster table/card grid, unlike Edit or Delete/Archive.

### Test Results

```
Backend:  700 passed, 2 skipped  (699-passed post-implementation baseline + 1 new code-review test)
Frontend: 386 passed, 0 failed   (384-passed post-implementation baseline + 2 new code-review tests)
tsc --noEmit: 73 pre-existing errors, none in any file this story touched (unchanged post-patch)
vite build: clean, 533 modules
```

Live-verified end-to-end: `curl` against a rebuilt Docker backend confirmed all 3 ACs (200 with a genuinely new password on regenerate; 409 EMPLOYEE_ARCHIVED on an archived employee; profile fields unchanged) plus 404/403/401, with exact expected status codes and error bodies. Re-verified again after the code-review patches (the `FOR UPDATE` lock swap) against a rebuilt Docker backend — regenerate still returns 200 with a fresh password, confirming the lock introduced no regression to the happy path.

### File List

New files:
- `frontend/src/features/admin/RegeneratePasswordModal.tsx` — the Regenerate Password confirm + one-time reveal modal
- `frontend/src/tests/RegeneratePasswordModal.test.tsx` — 10 tests (8 implementation + 2 code-review regression tests)

Modified files:
- `backend/app/auth/repository.py` — `update_account_password_hash` added
- `backend/app/employees/service.py` — `_archived_for_regenerate_conflict`, `regenerate_password_service` added; code review: `regenerate_password_service` now uses `repository.get_employee_for_update`'s `FOR UPDATE` lock instead of a plain `get_employee_by_id` (closes a TOCTOU race against a concurrent archive); `_EMPLOYEE_ARCHIVED_ERROR_CODE` constant added, shared by `_archived_conflict` and `_archived_for_regenerate_conflict`
- `backend/app/employees/router.py` — `POST "/{employee_id}/regenerate-password"` route added
- `backend/tests/test_employees_router.py` — 7 new tests covering AC1 (incl. old-password-invalidation and no-plaintext-leak), AC2, AC3, 404, 403, 401; code review: +1 test covering `has_assignment_history: true` on this endpoint
- `frontend/src/lib/api/employeesApi.ts` — `RegeneratePasswordResponse`, `regeneratePassword()` added
- `frontend/src/pages/hr/EmployeesPage.tsx` — `regeneratingEmployee` state, `handlePasswordCopied`, `RowActions`' `onRegeneratePassword` prop wired at both call sites, `RegeneratePasswordModal` rendered, dead `onUnavailable` prop removed from `RowActions`
- `frontend/src/tests/EmployeesPage.test.tsx` — 1 pre-existing test split into 2 + 1 new test (net +2), `regeneratePassword` added to the module mock
- `frontend/src/features/admin/RegeneratePasswordModal.tsx` — code review: `Dialog`'s `onClose` is now a no-op during the `'regenerating'` step (previously mapped to `handleCancel`, letting Escape/backdrop-click silently discard an already-completed regeneration)
- `frontend/src/tests/RegeneratePasswordModal.test.tsx` — code review: +2 tests (confirm button disabled while in flight; Escape/backdrop-close no-ops while in flight)

No changes to:
- `backend/app/employees/models.py`, `schemas.py` — `EmployeeCreatedResponse` already existed (Story 7.2), reused as-is
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)
- `backend/alembic/versions/` — no schema change needed (Scope Note 1)
- `frontend/src/features/admin/EditEmployeeModal.tsx`, `DeleteArchiveEmployeeModal.tsx` — untouched, per Scope Note 10

## Completion Checklist

- [x] `update_account_password_hash` added to `auth/repository.py`, following the established centralization pattern with a `None`-guard
- [x] `regenerate_password_service` added: HR-Admin-gated, 404 on missing employee, 409 `EMPLOYEE_ARCHIVED` on an archived employee, `asyncio.to_thread`-offloaded hashing, correct `has_assignment_history` on the response
- [x] `POST /api/admin/employees/{employee_id}/regenerate-password` mounted and working, reusing `EmployeeCreatedResponse`
- [x] All 3 ACs covered by passing backend tests, including the old-password-invalidated and no-plaintext-leak checks
- [x] `RegeneratePasswordModal.tsx` implements the confirm → regenerating → revealed/error flow per the UX spec's verbatim copy/testids
- [x] `EmployeesPage.tsx`'s Regenerate Password row action (both table + card call sites) opens the real modal; Edit/Delete-Archive untouched
- [x] Copy-to-clipboard implemented with a silent failure fallback (never logs/throws the password)
- [x] Full backend + frontend regression run, zero new regressions
- [x] `tsc --noEmit` / `vite build` clean
- [x] Live-verified end-to-end via `curl` against a rebuilt Docker backend (all ACs + 404/403/401); a full browser smoke test was deliberately not run this round (see Debug Log)

## Change Log

- 2026-09-12: Story created (`bmad-create-story`/Amelia), building on Story 7.1 (`generate_password`/`hash_password`), 7.2 (`EmployeeCreatedResponse`'s one-time-reveal contract, the `Account`-write centralization pattern), 7.4 (`update_account_email` precedent, split-test convention), and 7.5 (`_has_any_history_for_employee`, `update_account_archived_at`'s `None`-guard precedent, `DeleteArchiveEmployeeModal.tsx`'s frontend shape). Verified current backend (`employees/`, `auth/` models/repository/service/router/schemas) and frontend (`EmployeesPage.tsx`, `employeesApi.ts`, `DeleteArchiveEmployeeModal.tsx`, `dialog.tsx`, `toast.tsx`) state directly rather than relying solely on prior story docs. Confirmed via direct code reading that Story 7.2 shipped backend-only — no Create Employee modal or Password Reveal panel exists in `frontend/` yet — so this story is the first to build the one-time password-reveal UI, scoped only to the Regenerate flow (Scope Note 8). Read both relevant UX scenario docs (05.1's Regenerate Password Panel, 05.3's Password Reveal Panel) directly and captured their verbatim copy/testids, including 05.3's own flagged title correction ("Password regenerated" vs. the mock's "Employee created", UX-DR37). Made explicit, load-bearing design decisions the epics text left open: reuse `EmployeeCreatedResponse` rather than a new schema; a plain point-in-time archived check rather than Story 7.5's `FOR UPDATE` lock (Dev Notes explain why that mechanism doesn't apply here); a new `_archived_for_regenerate_conflict` helper rather than reusing Story 7.5's assignment-specific `_archived_conflict`; and a self-contained two-step modal rather than a premature shared-component extraction for a Create-flow frontend that doesn't exist yet. Status → `ready-for-dev`.
- 2026-09-12: Implementation complete (`bmad-dev-story`/Amelia). Backend: `update_account_password_hash` (auth/repository.py), `_archived_for_regenerate_conflict`/`regenerate_password_service` (employees/service.py), `POST /{employee_id}/regenerate-password` (employees/router.py) — 7 new tests, all green first run. Full regression: 699 passed/2 skipped/0 failed (692 baseline + 7, zero regressions). Frontend: `RegeneratePasswordModal.tsx` added (the first Password Reveal UI in this codebase, confirm→regenerating→revealed flow per the UX spec's verbatim copy); wired into `EmployeesPage.tsx`'s previously-stubbed Regenerate Password action at both table and card call sites; removed the now-fully-dead `onUnavailable` prop from `RowActions` (a real `tsc` regression caught and fixed before completion, not left for review). 9 new/changed frontend tests, all green; full regression 384 passed/0 failed (375 baseline + 9, zero regressions); `tsc --noEmit` at 73 pre-existing errors (down from an intermediate 74, the one this story introduced and fixed), none in any touched file; `vite build` clean (533 modules, up from 532). A real testing pitfall was found and worked around, not just cited: `@testing-library/user-event`'s own Clipboard stub clobbers any manual `navigator.clipboard` override made before or via `userEvent.setup()` — fixed by spying on the real installed stub (`vi.spyOn(navigator.clipboard, 'writeText')`) after `setup()`, instead of trying to replace `navigator.clipboard` outright. Live-verified end-to-end: `curl` against a rebuilt Docker backend confirmed all 3 ACs with exact expected status codes/bodies (200 with a new password differing from the prior one; 409 EMPLOYEE_ARCHIVED on an archived employee; 404/403/401 on the usual edge cases), using a direct `docker exec` Python/SQLAlchemy script to reach the archived state (no UI un-archive path exists). All live test data cleaned up from the dev DB afterward. Status → `review`.
- 2026-09-12: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 0 decision-needed, 5 patches (all applied), 0 deferred, 14 dismissed as spec-compliant/out-of-scope/already-established precedent, verified by direct code and UX-spec reading rather than taken at face value. **Most consequential finding**: the story's own Dev Notes reasoning for skipping Story 7.5's `FOR UPDATE` row lock was wrong — it missed the await inside `asyncio.to_thread(hash_password, ...)` as a genuine TOCTOU window in which a concurrent archive could land between the archived-employee check and the password write, letting an about-to-be-archived employee end up with a freshly-working password. Fixed by switching to `repository.get_employee_for_update`; the retracted reasoning is preserved in Dev Notes (struck through, not deleted) as a lesson about accounting for every `await`, not just explicit branches, when arguing a lock is unnecessary. **4 other real issues fixed**: Escape/backdrop-close during the `'regenerating'` step silently discarded an already-completed regeneration (the Cancel button was correctly disabled in-flight, but Dialog's Escape/backdrop dismissal wasn't gated the same way) — fixed by making `onClose` a no-op during that step, with 2 new regression tests; a duplicated `"EMPLOYEE_ARCHIVED"` string literal between `_archived_conflict` (Story 7.5) and this story's `_archived_for_regenerate_conflict` — extracted to a shared `_EMPLOYEE_ARCHIVED_ERROR_CODE` constant; missing test coverage for `has_assignment_history: true` on this endpoint's response (the only existing test covered the trivial always-`false` freshly-created case) — added `test_regenerate_password_reflects_true_has_assignment_history`; missing regression coverage for the confirm button's in-flight `disabled` state — added `test('the confirm button is disabled while a regenerate request is in flight')`. Full regression re-verified: backend 700 passed/2 skipped/0 failed (699 + 1), frontend 386 passed/0 failed (384 + 2), `tsc --noEmit` unchanged at 73 pre-existing errors, `vite build` clean (533 modules). Live-re-verified against a rebuilt Docker backend: the `FOR UPDATE` lock introduced no regression to the regenerate happy path. Status → `done`.
