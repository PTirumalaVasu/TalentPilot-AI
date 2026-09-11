# PRD Quality Review — TalentPilot-AI (2026-09-11 update: §4.7 Employee Roster Management, §4.8 HR Admin Navigation Shell)

*Scope note: this review is weighted toward the material added 2026-09-11 — §4.7 (FR-24–FR-27), §4.8 (FR-28), the Open Question 9 update, the new addendum section, and the three new Assumptions Index entries. §1–§4.6 and the rest of §5–§12 were reviewed in prior sessions (see `review-rubric.md` history, `review-adversarial-general.md`, `review-edge-case-hunter.md`) and are not re-litigated here except where the new material touches them.*

## Overall verdict

The new material is well-built and integrates cleanly: FRs 24–28 carry testable consequences, correctly-indexed assumptions, and honest `[NOTE FOR PM]` flags at real tensions (HR_ADMIN provisioning is still ungoverned, no UX scenario covers the creation form). The one real hole is structural, not cosmetic: nothing in §4.7, §8, or the Open Questions addresses how an Employee's password is ever changed or recovered after the one-time reveal — a genuine gap given this stack has no email infrastructure and no SSO. The addendum's architecture handoff for §4.7 is also incomplete in a way worth catching before the next architecture pass: the codebase already has an `Account`/`accounts` table with a `password_hash` column, seeded but unused, that the handoff note never mentions despite being exactly the artifact FR-24's credential work would build on or against.

## Decision-readiness — adequate

The new FRs state real decisions, not smoothed-over considerations: FR-27's hard-delete-vs-archive branch is decided and tied to a concrete trigger (has this Employee ever had an Assignment); FR-21/22's Skill identity-lock is explicitly *not* extended to Employee records in FR-26, with the reasoning given ("locking them would block routine HR maintenance"). Open Question 9's update is a model of honest partial resolution — it says exactly what's now settled (roster origin, Employee login provisioning) and what's still open (HR_ADMIN account provisioning), rather than declaring victory prematurely.

### Findings
- **critical** No decision surfaced on password recovery/change after initial provisioning (§4.7, FR-24/FR-26, §8) — see Done-ness Clarity finding below; this is a decision that needed to be *stated* as open (or resolved) and instead isn't mentioned at all. *Fix:* add an FR or an explicit `[NOTE FOR PM]`/Open Question naming the gap and who owns closing it before build.

## Substance over theater — strong

No new personas, no new NFR boilerplate, no vision restatement. FR-24–27 read as genuine capability spec: concrete field lists, concrete uniqueness constraints (email, Employee ID/Code), concrete edge cases (duplicate email/name, immutable ID, archived-employee login deactivation). FR-28 resists over-specifying UI polish it doesn't own yet (explicitly punts pane width/responsive behavior to downstream UX rather than inventing throwaway detail).

## Strategic coherence — adequate

§4.7/§4.8 don't advance the PRD's core thesis (auto-captured trust signal for video) — they're enabling infrastructure, replacing the hand-seeded five-account demo store with a real roster. That's the right call for a capability-spec-shaped internal tool, and the PRD is honest about it being plumbing rather than dressing it up as a feature with its own Success Metric. No new SM was added for either addition, which is correct restraint (CRUD roster management and a nav relocation aren't outcome-bearing), but it's worth noting explicitly rather than leaving the reader to infer "no SM was intentional."

## Done-ness clarity — thin

This is where the new material is weakest, and per the rubric this dimension gets zero benefit of the doubt.

### Findings
- **critical** No path exists anywhere in the PRD for an Employee (or HR Admin on their behalf) to change or recover a password after the one-time reveal at creation (§4.7 FR-24: "shown once... never re-displayable after the confirmation view is dismissed"). FR-26 ("HR Admin edits any Employee's profile fields") explicitly scopes to "all fields from FR-24" — and password is not one of the listed profile fields (Name, Email, Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department) — so FR-26 does not obviously cover password reset either. §8's "Employee credential provisioning" NFR only restates the initial-generation constraint, not an ongoing recovery path. Given §9 confirms zero email-sending infrastructure and Open Question 9 confirms no SSO, an Employee who forgets their password (or an HR Admin who needs to reissue one) has no defined recourse. Verified against the actual codebase: no `reset_password`/`change_password`/`forgot_password` endpoint exists anywhere in `backend/app/`. *Fix:* add an explicit FR (HR Admin regenerates/reveals a new one-time password for an existing Employee) or, at minimum, log this as a launch-blocking Open Question — right now it's silently absent rather than honestly deferred.
- **medium** FR-24's consequences don't state a password generation policy (length/character set/expiry), and the addendum defers this to the architecture pass ("Auto-generated password mechanism is unspecified") — reasonable to defer, but the PRD itself doesn't flag it as an Open Question or NOTE FOR PM the way FR-19's fixed-pace constant or FR-16's credential model got flagged. Low cost to make it explicit at the PRD level rather than only in `addendum.md`.

## Scope honesty — adequate

The three new `[ASSUMPTION]` tags in §4.7 (FR-24's optional-fields assumption, FR-26's session-not-invalidated-on-email-edit assumption, FR-27's un-archive-permitted assumption) all round-trip correctly into §12's Assumptions Index — checked line-by-line, no drift. `[NOTE FOR PM]` callouts land on genuine open items (HR_ADMIN provisioning in FR-24's note and Open Question 9; missing UX scenario coverage for the creation/password-reveal flow in FR-24's Notes). The one omission that breaks the pattern is the password-reset gap above — everywhere else in this update, an unresolved decision gets a tag; this one doesn't.

## Downstream usability — strong, with one addendum-level accuracy gap

Glossary, ID continuity, and cross-references for the new material are clean: §3's Employee entry was updated in place with a dated tag pointing at §4.7; FR-24–28 are contiguous with no gaps or duplicates; every cross-reference (§4.1/FR-15, §4.6/FR-16, §4.6/FR-21/22, §6.2's Employee Profile View distinction) resolves to a real section. Brownfield accuracy spot-checked against the actual repo and holds: the addendum's claim that `app/assignments/models.py::Employee` has only `id, name, email, role, group, created_at` matches the code exactly, and the claim that `auth/repository.py` stores plaintext passwords in a dict compared via `secrets.compare_digest` also matches.

### Findings
- **medium** The addendum's "Employee Roster Management — Architecture Handoff Notes (2026-09-11)" section (addendum.md, lines ~29–37) says the `employees` table needs a new "password/credential column that does not exist today" and frames this as a migration onto the `Employee` model. It doesn't mention that the codebase already has a separate `Account` model (`backend/app/auth/models.py`) — table `accounts`, columns `id, email, password_hash, role, created_at` — that is already seeded (`backend/app/core/seeds.py::create_default_accounts`) for the five demo users but not yet wired into `authenticate()` (which still reads the plaintext `_MOCK_ACCOUNTS` dict in `auth/repository.py`). This looks like a half-finished migration path already sitting in the repo, directly relevant to how FR-24's login provisioning should be built (extend `Account` vs. bolt a column onto `Employee`), and the architecture pass shouldn't have to rediscover it from scratch. *Fix:* add one line to the addendum's handoff note pointing at `app/auth/models.py::Account` and `seeds.py::create_default_accounts` as the existing scaffold to reconcile with, not a green field.

## Shape fit — strong

Internal-tool, capability-spec shape held consistently: no UJs were added for §4.7/§4.8, matching the treatment already established for §4.6 (also UJ-less). This is the right call — an HR Admin CRUD screen and a nav relocation don't need named-protagonist journeys. Brownfield references check out (see Downstream Usability above), correctly distinguishing new capability from existing code rather than blurring the two.

## Mechanical notes

- Assumptions Index roundtrip: all three new `§4.7/...` entries in §12 have matching inline `[ASSUMPTION]` tags in §4.7, and vice versa — no drift found.
- ID continuity: FR-24–FR-28 contiguous, no gaps/duplicates against the existing FR-1–FR-23 sequence.
- Glossary: no new domain nouns introduced by §4.7/§4.8 that needed their own Glossary entries beyond the Employee entry's existing update; no drift observed.
- §4.8/FR-28 doesn't itself call out keyboard/ARIA behavior for the new left-pane nav; §8's accessibility NFR names "the full assignment and dashboard drill-down flows" specifically rather than nav chrome generally. Likely covered by the blanket WCAG 2.1 AA commitment, but worth a one-line addition to FR-28's consequences or the accessibility NFR so it isn't left to inference — low severity given the existing NFR's broad framing.
- MVP scope (§6.1) correctly lists FR-24–27 and FR-28 under new bullet items; no scope-list drift.
