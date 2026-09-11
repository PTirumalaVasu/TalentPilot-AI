# Edge Case Hunter Review — Employee Roster Management & HR Admin Nav Shell (§4.7–§4.8, FR-24–FR-28)

**Scope:** `prd.md` §4.7 (FR-24–FR-27) and §4.8 (FR-28), added 2026-09-11, plus their touch points into already-implemented behavior (Assignments, Watch Progress, HR Overrides, sessions/JWT). Cross-checked against `backend/app/assignments/service.py`, `backend/app/assignments/models.py`, `backend/app/dashboard/service.py`, and `backend/app/auth/service.py` / `repository.py` where the PRD's FR text made a claim the running code could confirm or contradict.

**Method:** exhaustive path enumeration over every branch and boundary FR-24–FR-28 introduce or touch. Only genuinely unhandled paths are listed — cases already named in the FR text, its Consequences bullets, its `[ASSUMPTION]`/`[NOTE FOR PM]` tags, or Open Questions 9/17 are excluded (e.g., FR-26's Email-edit/session `[ASSUMPTION]`, FR-27's un-archive `[ASSUMPTION]`, and FR-28's own Notes on narrow-viewport/responsive behavior are already flagged in-document and are not repeated here).

No severity labels are assigned in this list per the edge-case-hunter method; the accompanying summary ranks these separately for triage purposes.

---

1. **Location:** §4.7 FR-27 × §4.1 FR-1 (race)
   **Trigger condition:** A hard-delete request (zero-Assignment-history check passes) and a concurrent FR-1 Assignment-creation request for the same Employee are in flight at the same time.
   **Guard needed:** FR-27 should require the zero-history check and the delete to execute inside one serializable transaction/row lock (or rely on and gracefully translate a DB FK-violation into "switched to archive" rather than a raw error), not a check-then-delete read followed by a separate write.
   **Potential consequence:** The Employee row is hard-deleted just as a new Assignment referencing it commits — either an FK violation surfaces as a raw 500 to the HR Admin, or (if the constraint is looser) an Assignment is left pointing at a nonexistent Employee.

2. **Location:** §4.7 FR-27 (active session on archive)
   **Trigger condition:** An Employee holds an already-issued, unexpired JWT at the moment HR Admin archives (or role-changes were possible on) their record.
   **Guard needed:** FR-27 states "an archived Employee cannot authenticate" — this only governs new logins. `backend/app/auth/service.py` validates sessions purely by JWT signature plus a per-token (not per-user) revocation set (`_revoked_tokens`); there is no per-request check that the token's `user_id` still maps to an active Employee. The FR needs to state explicitly whether archiving must also invalidate any already-issued token for that identity, and if so, by what mechanism (the current design has no way to revoke "all sessions for user X," only a single known token).
   **Potential consequence:** An archived Employee's already-open tab keeps working — browsing Content Discovery, resuming video, posting Watch-Progress into now-invisible Assignments — until the token's natural expiry, contradicting the "no session obtainable once archived" intent.

3. **Location:** §4.7 FR-27 × §4.1 FR-1 (stale picker race)
   **Trigger condition:** HR Admin A has the Skill Assignment Flow's employee picker open (loaded before archival) while HR Admin B archives that same Employee; A then confirms an Assignment against the now-archived Employee.
   **Guard needed:** FR-1 or FR-27 should state that Assignment creation re-validates the target Employee's active/non-archived status server-side at confirm-time, not only at picker-load-time.
   **Potential consequence:** A new Assignment is created for an Employee who has already dropped off every picker per FR-25/FR-27 — the Assignment exists but its Employee is unreachable/unmanageable going forward.

4. **Location:** §4.7 FR-26 (concurrent edit)
   **Trigger condition:** Two HR Admins open the same Employee's edit form at the same time and both submit.
   **Guard needed:** FR-26 does not define a concurrency strategy (no optimistic-lock/version check mentioned, unlike a stated last-write-wins acceptance).
   **Potential consequence:** One Admin's edit (e.g., a Department transfer) is silently overwritten by the other's stale form submission with no conflict indication to either Admin.

5. **Location:** §4.7 FR-26 (name change vs. audit-record stability)
   **Trigger condition:** HR Admin renames an Employee who already has historical Assignment/Watch-Progress/Override records.
   **Guard needed:** FR-26 should state whether audit-facing views (drill-down, FR-9; override history, FR-12) must show the Employee's name as of the historical event (a snapshot) or the always-current name. Confirmed in code: `employee_name` is not a stored/denormalized column — `assignments/service.py` and `dashboard/service.py` both derive it live via `assignment.employee.name`/`.email` at read time — so a rename retroactively rewrites the name shown on every past Assignment/Override/drill-down record.
   **Potential consequence:** Records the PRD elsewhere calls immutable "for audit" (FR-15's language) silently change in appearance after a rename, undermining the audit trail's evidentiary value (e.g., "who was HR Override attributed to, under what name, at the time" can no longer be reconstructed).

6. **Location:** §4.7 FR-24 / FR-26 (uniqueness scope vs. archived records)
   **Trigger condition:** HR Admin creates a new Employee, or edits an existing Employee's Email, using an Employee ID/Code or Email value that belongs to an already-archived (soft-deleted) record.
   **Guard needed:** FR-24's "Employee ID/Code must be unique" and its Email-uniqueness consequence, and FR-26's Email re-validation, should state explicitly whether the uniqueness check is scoped to active (non-archived) records only, or to the entire roster including archived rows.
   **Potential consequence:** Either a departed employee's code/email is permanently unreusable for a rehire (if scoped roster-wide), or a new active record silently collides in reporting/lookup with an archived one sharing the same code/email (if scoped active-only with no de-dup safeguard against the archived match).

7. **Location:** §4.7 FR-24 (lost one-time password)
   **Trigger condition:** The HR Admin's browser/session is interrupted (crash, accidental navigation, network failure) after the Employee record is created server-side but before the one-time password is copied from the confirmation view.
   **Guard needed:** FR-24/FR-26 should define an admin-triggered "regenerate password" action — password is explicitly excluded from FR-26's editable-field list ("all fields from FR-24 except Employee ID/Code" does not obviously include a credential field), so no stated recovery path exists.
   **Potential consequence:** A newly-created Employee has a hashed password nobody possesses and no in-product mechanism to reset it, since the plaintext is stated as never re-displayable.

8. **Location:** §4.7 FR-27 (un-archive + stale one-time password)
   **Trigger condition:** HR Admin un-archives a previously-archived Employee (per FR-27's own `[ASSUMPTION]` that un-archive is possible) some time after the original one-time password was shown and shared out-of-band.
   **Guard needed:** State whether un-archiving reactivates the original password as-is or forces a fresh one-time password generation/redisplay, mirroring FR-24's creation pattern.
   **Potential consequence:** A reactivated Employee's only credential is a password shared once, an unknown time ago, that may no longer be known to anyone — reactivation restores an account nobody can actually log into.

9. **Location:** §4.7 FR-24 (forced credential rotation)
   **Trigger condition:** An Employee logs in for the first time using the HR-shared, system-generated password.
   **Guard needed:** FR-24 does not state whether first login forces a password change, despite the password having necessarily been seen and transmitted by a second party (HR Admin) out-of-band by design.
   **Potential consequence:** An Employee account's only long-term secret is a password a second person has also seen and possibly recorded/shared insecurely, with no stated rotation requirement.

10. **Location:** §4.7 FR-24 (Manager Name as free text, not a roster FK)
    **Trigger condition:** The Employee referenced by another Employee's freeform "Manager Name" field (FR-24's field list has no Manager-ID/FK, only a name string) is later renamed, archived, or deleted via FR-26/FR-27.
    **Guard needed:** State whether Manager Name should instead reference the manager's actual Employee record so downstream changes propagate, or explicitly accept it as an unmaintained text snapshot.
    **Potential consequence:** Other Employees' "Manager Name" field silently goes stale (points to a renamed or departed manager) with no update mechanism and no visible staleness indicator — unlike Employee ID/Code and Email, which at least have uniqueness/immutability rules defined.

11. **Location:** §4.7 FR-25 (roster search/filter vs. optional fields)
    **Trigger condition:** HR Admin filters the roster by Department or Position/Job Title while some Employees were created with those fields left blank (explicitly optional per FR-24).
    **Guard needed:** FR-25 should state how a blank/null Department or Position behaves under its own stated filter — excluded from every filter result, or surfaced under an explicit "Unassigned" bucket.
    **Potential consequence:** Employees with incomplete profiles become permanently unfindable through the exact mechanism FR-25 justifies as "find who you need fast," with no visible indication they've fallen out of filter results.

12. **Location:** §4.8 FR-28 × §4.6 FR-16 (relocated credential entry point)
    **Trigger condition:** FR-16's "account/settings surface reachable from the Skills tab" (for managing YouTube/Udemy API credentials) currently lives inside the top-header layout that FR-28 relocates into the left pane.
    **Guard needed:** FR-28 should confirm the credential-management entry point is explicitly preserved (or explicitly re-anchored) as part of the nav relocation, the same way it calls out the user-menu (avatar + Sign Out) staying put.
    **Potential consequence:** The only path to configuring content-source credentials (FR-16) could be inadvertently dropped or hidden during the header-to-left-pane refactor, silently blocking FR-17's live lookup with no FR calling this out as a migration risk.

---

## Notes on exclusions

The following were walked and found already handled or already named in-document, so are not repeated as findings:
- FR-27's hard-delete-vs-archive branch itself, and its "active or soft-deleted Assignment history" scope — explicitly defined.
- FR-26's Email-edit/session-invalidation ambiguity — already an `[ASSUMPTION]` in §4.7 and §12.
- FR-27's un-archive existence and hard-delete's no-restore-path — already an `[ASSUMPTION]`.
- FR-28's pane width/collapse/icon behavior on narrow viewports — already an open item in FR-28's own Notes.
- FR-28's "SkillsPage.tsx may duplicate the top-nav" implementation risk — already flagged in `addendum.md`'s architecture handoff notes.
- FR-24's required-vs-optional field split — already an `[ASSUMPTION]`.
