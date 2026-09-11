---
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
readinessStatus: 'READY (Epic 7/8 scope) -- all 3 fixable findings applied to epics.md same session (Open Question 17 callout added to Story 7.1, UX-DR42/43 ACs added to Story 7.3, Story 7.5 Dev Notes callout on cross-module blast radius). 2 items remain acceptable-as-scoped (AR-24, Open Question 9), not blockers.'
filesIncluded:
  prd: '_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md'
  prdAddendum: '_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md'
  architecture: '_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md'
  epics: '_bmad-output/planning-artifacts/epics.md'
  ux: '_bmad-output/C-UX-Scenarios/00-ux-scenarios.md (+ per-scenario page specs, notably 05-ritas-roster-management/)'
scope: 'Focused re-check of Epic 7 (Employee Roster Management, FR-24-29) and Epic 8 (Application Theming, FR-30) only -- Epics 1-6 already validated ready in the original 2026-07-09 readiness report and are fully implemented/done per sprint-status.yaml, not re-litigated here.'
---

# Implementation Readiness Assessment Report

**Date:** 2026-09-11
**Project:** TalentPilot-AI

## Document Discovery

**PRD:** `prds/prd-TalentPilot-AI-2026-07-09/prd.md` + `addendum.md` — single version, no duplicate sharded copy.

**Architecture:** `architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md` — single version.

**Epics & Stories:** `epics.md` — single version, no sharding. Extended 2026-09-11 with Epic 7 (7 stories) and Epic 8 (1 story).

**UX Design:** No file matches the generic `*ux*.md` pattern — this project uses the WDS pipeline, with UX living at `_bmad-output/C-UX-Scenarios/`. `epics.md`'s own `inputDocuments` frontmatter already references these paths directly, including the newly-added `05-ritas-roster-management/05-ritas-roster-management.md` scenario.

**Issues Found:** None — no duplicate whole+sharded conflicts on any document type.

**Scope of this run:** Focused on Epic 7/Epic 8 alignment only, per user request. Epics 1-6 were validated ready in the original 2026-07-09 report and are fully implemented (`sprint-status.yaml`: all `done`) — not re-assessed here.

## PRD Analysis (Epic 7/8 scope only — FR-1 through FR-23 already validated in the 2026-07-09 report)

### Functional Requirements Extracted

FR-24: HR Admin creates a new Employee-role record with Employee ID/Code, Name, Email required; Phone, Experience, Technologies, Position/Job Title, Project, Manager Name, Location, Department optional. Email unique (case-insensitive), ID/Code unique. System auto-generates an initial password, shown once via server-side one-time-reveal. Scoped to EMPLOYEE-role accounts only — does not provision HR_ADMIN accounts (PRD §4.7, Open Question 9 note).

FR-25: HR Admin views the Employee roster — searchable/filterable by Name, Department, Position; archived Employees excluded by default with an explicit toggle to reveal them.

FR-26: HR Admin edits any Employee's profile fields except Employee ID/Code (immutable). Always available regardless of Assignment history — no identity-lock like Skills have. Last-write-wins on concurrent edits (no optimistic locking).

FR-27: HR Admin deletes or archives an Employee. Hard-delete only if zero Assignment history ever existed; otherwise soft-archive (record + history retained, dropped from active roster/pickers). Zero-history check and the delete/archive action must be atomic. Archiving must revalidate sessions server-side per-request, not just block new logins.

FR-28: HR Admin regenerates an Employee's password at any time (lost password, suspected compromise, or re-activating an archived Employee). Same one-time-reveal pattern as FR-24; immediately invalidates the old password.

FR-29: HR Admin's primary navigation (Dashboard, Skills) relocates from a top-header bar to a persistent left-side pane, gaining a new Employees entry. Must preserve every existing entry point (notably FR-16's API-key settings surface) and collapse to a hamburger/backdrop pattern below 768px.

FR-30: Any user (HR Admin or Employee) can switch the app between Light and Dark theme. Defaults to OS preference; persists per-browser via `localStorage` once manually set; applies across every screen, HR and Employee shells alike.

**Total FRs (this scope): 7** (FR-24 through FR-30)

### Non-Functional Requirements Extracted

NFR-SEC2: A new/regenerated Employee password is system-generated and shown exactly once via **server-side** one-time-reveal enforcement (a consumed/cleared flag on the credential record) — explicitly NOT client-side UI discipline alone, which the PRD's own post-review correction states cannot actually prevent re-access via the API directly.

**Total NFRs (this scope): 1**

### Additional Requirements / Constraints (from PRD §9, addendum.md's Architecture Handoff Notes, and Open Questions)

- **AR-24 trigger (unresolved in the PRD/addendum):** An existing-but-unused `Account`/`password_hash` model (`backend/app/auth/models.py`, seeded via `core/seeds.py::create_default_accounts`, never wired to `authenticate()`) is flagged as the likely migration target for Employee credential storage — but the addendum explicitly frames this as a decision for "the architecture pass," not something the PRD itself resolves.
- **Open Question 17 (unresolved):** No migration path is defined for the 5 already-shipped hardcoded demo employees (Rita, Casey, Morgan, Jordan, Sam) and their live Assignment/Watch-Progress/Override history, once Epic 7 becomes the roster's source of truth. Explicitly flagged as colliding with the PRD's stale "No data migration" constraint (§9), which predates this feature.
- **Open Question 18 (informational, not blocking):** Documents the `Account` model discovery itself — points the architecture pass at it, doesn't resolve AR-24.
- **Open Question 9 (partially resolved, partially still open):** FR-24 explicitly does not cover HR_ADMIN account provisioning — that remains on the pre-existing plaintext mock store (`auth/repository.py`), a live, day-one gap per the PRD's own strengthened language, not a someday-concern.
- **Zero-budget/no-email-infrastructure constraint (§9):** Binding on FR-24/FR-28's out-of-band password-sharing design — no story may introduce email-sending infrastructure to solve the recovery/sharing problem.

### PRD Completeness Assessment (Epic 7/8 scope)

The PRD is unusually explicit about its own open gaps here — Open Questions 17 and 18 are stated plainly rather than glossed over, and FR-24's note is direct about NOT covering HR_ADMIN provisioning. This is a **good** sign for traceability (nothing is silently assumed resolved), but it means genuine architectural decisions are still outstanding at the PRD layer and must be either resolved or explicitly and visibly carried forward into Epic 7's stories — not silently dropped during epic/story authoring. This is exactly the trace this report checks next.

## Epic Coverage Validation (Epic 7/8 scope)

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
|-----------|------------------|----------------|--------|
| FR-24 | HR Admin creates a new Employee record | Epic 7, Story 7.2 | ✓ Covered |
| FR-25 | HR Admin views the Employee roster | Epic 7, Story 7.3 | ✓ Covered |
| FR-26 | HR Admin edits an Employee record | Epic 7, Story 7.4 | ✓ Covered |
| FR-27 | HR Admin deletes or archives an Employee record | Epic 7, Story 7.5 | ✓ Covered |
| FR-28 | HR Admin regenerates an Employee's password | Epic 7, Story 7.6 | ✓ Covered |
| FR-29 | Left-pane navigation shell | Epic 7, Story 7.7 | ✓ Covered |
| FR-30 | Light/Dark theme | Epic 8, Story 8.1 | ✓ Covered |
| NFR-SEC2 | Server-side one-time password reveal | Epic 7, Stories 7.2 + 7.6 (both reuse the same reveal mechanism) | ✓ Covered |

### Missing Requirements

None — all 7 new FRs and the 1 new NFR have direct story coverage.

**However, two PRD-level open items are NOT "FRs" and therefore don't show up as coverage gaps in this matrix, but are real readiness risks — flagged explicitly rather than treated as resolved by omission:**

- **AR-24 (Employee credential storage architecture decision)** is assigned to Story 7.1 to resolve ("the decision and its rationale are documented in this story's Dev Notes before any endpoint story is built") — this is a legitimate "decide during the foundation story" pattern, the same shape Epic 6's Story 6.1 used for the `skills/` module's own architecture questions. **Acceptable as scoped, not a blocker** — but it does mean Story 7.1 carries real architectural risk that a typical schema-migration story wouldn't, and should not be treated as routine/low-effort during estimation.
- **PRD Open Questions 17 and 18** are NOT restated anywhere inside Epic 7's story text itself — they exist only in the PRD and in `epics.md`'s Requirements Inventory "Additional Requirements" section (AR-24's note), not as an explicit callout inside any of Stories 7.1–7.7. Open Question 17 specifically (no migration path for the 5 existing demo employees) is a real gap: nothing in Story 7.1–7.7's acceptance criteria says what happens to Rita/Casey/Morgan/Jordan/Sam's *existing* records once Epic 7 ships. This is examined further under Findings below.

### Coverage Statistics

- Total new FRs (this scope): 7
- FRs covered in epics: 7
- Coverage percentage: 100%
- Non-FR open items requiring explicit story-level acknowledgment: 1 (Open Question 17 — not yet reflected in any story's AC)

## UX Alignment Assessment (Epic 7/8 scope)

### UX Document Status

**Found.** `_bmad-output/C-UX-Scenarios/05-ritas-roster-management/` — Scenario 05, fully specified (05.1 Employees Tab, 05.2 Create Employee, 05.3 Password Reveal), plus a working HTML prototype at `_bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html`. This is materially stronger UX grounding than several original epics had at their own readiness-check time (the 2026-07-09 report found FR-4/FR-8 UX specs actively stale against the shipped prototype) — Scenario 05 was authored and validated against a working prototype in the same session as Epic 7 itself, so no staleness risk of that kind exists here.

### UX ↔ PRD Alignment

Clean. Every interaction documented in 05.1–05.3 traces to a specific FR (FR-24 through FR-29), and every FR has a corresponding UX-documented interaction — no orphans in either direction.

### UX ↔ Epic/Story Alignment

Mapped each scenario step and on-page interaction to its story:

| UX Element | Epic 7 Story |
|---|---|
| 05.1 base state (roster list, Table/Card toggle, search/filter/archived-toggle, pagination) | 7.3 |
| 05.2 Create Employee panel | 7.2 |
| 05.3 Password Reveal panel (shared Create/Regenerate) | 7.2, 7.6 |
| 05.1's Edit Employee panel (on-page interaction) | 7.4 |
| 05.1's Regenerate Password confirmation (on-page interaction) | 7.6 |
| 05.1's Delete/Archive confirmation (on-page interaction) | 7.5 |
| FR-29 left-pane nav shell (introduced by 05.1) | 7.7 |

Every scenario step and on-page interaction has a story. No gaps in this direction.

### Alignment Issues Found

**Real gap — UX-DR42 and UX-DR43 are claimed as covered by Epic 7 but never appear in any story's acceptance criteria text:**

- Epic 7's header lists `UX-DR34 through UX-DR43` as bound, and UX-DR41 (status badges never color-only) is explicitly written into Story 7.3's AC — but **UX-DR42** (all row/card action icons carry descriptive `aria-label`s) and **UX-DR43** (Table view scrolls horizontally at narrow viewports rather than compressing columns) are not referenced in any story's AC text at all. A dev agent building strictly from Stories 7.1–7.7 as written could ship without either requirement and no AC would have been violated on paper.
- This is the same class of gap the original 2026-07-09 report's own methodology is designed to catch (claimed coverage vs. actual AC text) — worth fixing the same way that report's findings were fixed: add explicit AC lines to the responsible stories rather than leaving it to the epic-level "Binds" line alone.
- **Recommendation:** Add one AC line to Story 7.3 for UX-DR43 (horizontal scroll) since that story owns the Table view, and one AC line to whichever of 7.3/7.4/7.5/7.6 the team judges best (or a shared cross-cutting note) for UX-DR42 (aria-labels), since the action icons in question span all four of those stories' surfaces.

### Warnings

None beyond the gap above — UX documentation is present, current, and prototype-validated; this is not a "missing UX" situation.

## Epic Quality Review (Epic 7/8 scope)

### Epic Structure Validation

**User Value Focus:** Both epic titles/goals are user-centric ("HR Admin can onboard, view, edit, and offboard Employees...", "Any user can switch between Light and Dark mode..."). No technical-milestone epics. ✓

**Epic Independence:** Epic 8 requires nothing from Epic 7 (confirmed — no story in Epic 8 references any Epic 7 story or output). Epic 7 requires nothing from Epic 8. Both can ship in either order or in parallel. ✓

**Story 7.1 as a "foundation" story:** Story 7.1 (schema migration + credential-storage decision) has no direct end-user action — by this step's own red-flag list, a story like "Setup all models" would normally be a violation. However, this exact shape (`skills/` Module Foundation, Story 6.1) was already used and accepted for Epic 6 in this same project, and Epic 1's Stories 1.1/1.7 (project structure, schema init) are the original precedent. **Not flagged as a new violation** — consistent with this codebase's own established, already-accepted pattern for a schema/architecture-decision story preceding a set of user-facing endpoint stories within one epic.

### Story Quality & Dependency Analysis

**Forward dependencies:** None found. Checked every story against only earlier stories in its own epic — 7.7 (last) correctly depends on 7.3 (earlier), and no story assumes an unbuilt later story's output.

**🟠 Major — Story 7.5's cross-module blast radius is understated by its story size:** Story 7.5 (Delete/Archive) bundles three technically distinct surfaces: (a) the employee delete/archive endpoint itself, (b) archived-session revalidation, which requires modifying Epic 1's core session-validation path (`get_current_token_payload`/`get_current_user` — a cross-cutting mechanism every other protected endpoint in the app relies on), and (c) the stale-picker race fix, which requires modifying Epic 3's Assignment-creation service (already `done`, shipped code). This is not a *structural* rule violation (Epic 1 and Epic 3 are past, completed epics — not future ones, so the "no forward dependency" rule isn't broken), but it is real complexity this single story doesn't visibly size for. **Recommendation:** either explicitly note in Story 7.5's Dev Notes that it touches 3 modules across 2 other epics (so it isn't estimated like a typical single-module CRUD story), or split the session-revalidation piece into its own story if the team wants tighter single-responsibility sizing. Not a blocker, but should not be estimated as routine.

**Acceptance Criteria quality:** Given/When/Then format used consistently across all 8 new stories. Error/edge conditions are present in each story (Story 7.2: duplicate ID/Email 409; Story 7.4: email-collision rejection; Story 7.5: race condition, stale-picker; Story 7.6: archived-Employee rejection). No vague criteria found (e.g., no bare "user can create an employee" without a concrete Given/When/Then).

**Database/Entity Creation Timing:** Story 7.1 adds only the columns Stories 7.2–7.6 actually consume (no speculative/unused columns). ✓ Consistent with the "create only what's needed" principle.

**Starter Template / Greenfield-Brownfield:** N/A — this is an established brownfield codebase (Epics 1-6 already shipped); Epic 7/8 correctly include no redundant environment-setup stories, and Story 7.1 is framed as a migration onto an existing table, not a fresh-project setup.

### Best Practices Compliance Checklist

| Check | Epic 7 | Epic 8 |
|---|---|---|
| Delivers user value | ✓ | ✓ |
| Functions independently | ✓ | ✓ |
| Stories appropriately sized | ⚠️ (7.5 — see Major finding above) | ✓ |
| No forward dependencies | ✓ | ✓ |
| DB tables created when needed | ✓ | N/A (no DB) |
| Clear acceptance criteria | ✓ | ✓ |
| Traceability to FRs maintained | ✓ | ✓ |

### Findings Summary (this step)

- 🔴 Critical: none
- 🟠 Major: 1 (Story 7.5's understated cross-module blast radius)
- 🟡 Minor: none

## Summary and Recommendations

### Overall Readiness Status

**NEEDS WORK** — not a rebuild, but not a clean pass either. Epic 7/8's structure, FR coverage, and UX grounding are all fundamentally sound (100% FR coverage, no forward dependencies, epic independence holds, UX is current and prototype-validated — stronger footing than several original epics had at their own readiness check). The gaps found are real but narrow and fixable at the story-text level, not structural rework.

### Critical Issues Requiring Immediate Action

None. Nothing found here would produce incorrect or unsafe behavior if built exactly as currently written — the issues below are coverage/traceability gaps, not defects.

### Issues to Resolve Before Story 7.1 Begins

1. **PRD Open Question 17 (demo-employee data migration) has no home in any story's acceptance criteria.** Nothing in Stories 7.1–7.7 says what happens to Rita/Casey/Morgan/Jordan/Sam's existing records and live Assignment history once Epic 7 becomes the roster's source of truth. **Recommend:** add an explicit AC to Story 7.1 (or a dedicated migration task) stating the decision — migrate them into the new schema, leave them running unmigrated alongside new real employees, or another explicit choice — rather than leaving it to be discovered mid-implementation.
2. **UX-DR42 (action-icon `aria-label`s) and UX-DR43 (Table view horizontal scroll) are claimed as epic-level coverage but never appear in any story's AC text.** Recommend adding one AC line each to the responsible stories (7.3 for UX-DR43; 7.3/7.4/7.5/7.6 collectively, or a shared note, for UX-DR42) so a dev agent building strictly from the ACs doesn't miss them.
3. **Story 7.5's real cross-module blast radius (touches Epic 1's session-validation core and Epic 3's Assignment-creation service, on top of its own endpoint) isn't reflected in how the story reads.** Recommend adding a Dev Notes callout so it isn't estimated/reviewed like a routine single-module CRUD story.

### Acceptable-as-Scoped, Not Blocking

- **AR-24 (Employee credential storage vs. the existing unused `Account` model)** is explicitly assigned to Story 7.1 to resolve before any endpoint story is built — this mirrors Epic 6's Story 6.1 precedent for the `skills/` module's own architecture questions. Legitimate scope, not a gap, but real risk that should not be estimated as routine schema work.
- **PRD Open Question 9's HR_ADMIN-provisioning gap** is explicitly and correctly out of Epic 7's scope (FR-24 only provisions EMPLOYEE-role accounts) — the PRD already states this plainly; no epic action needed here, just don't let a future story quietly assume it was solved.

### Recommended Next Steps

1. Add the 3 story-text fixes above (Open Question 17 callout, UX-DR42/43 AC lines, Story 7.5 Dev Notes) directly to `epics.md` — all are text-only additions, no re-architecture needed.
2. Re-run this check (or just a quick self-review) after those edits if you want a clean "READY" before starting `bmad-create-story` for Story 7.1.
3. Proceed to `bmad-sprint-planning` (re-run, since it predates Epic 7/8) and then `bmad-create-story` for Story 7.1 — the foundation story that everything else in Epic 7 depends on.

### Final Note

This assessment identified 3 issues (1 Major, 2 traceability gaps) across 3 categories (Epic Coverage, UX Alignment, Epic Quality), plus 2 items explicitly judged acceptable-as-scoped. None are critical. These findings can be used to tighten the epics/stories, or you may choose to proceed as-is and catch them during story creation/dev instead.

## Resolution (2026-09-11, same session)

All 3 fixable findings were applied directly to `epics.md`:
1. Story 7.1 gained an explicit AC covering PRD Open Question 17 (demo-employee migration decision required before this story is done).
2. Story 7.3 gained explicit ACs for UX-DR42 (action-icon `aria-label`s) and UX-DR43 (Table view horizontal scroll).
3. Story 7.5 gained a Dev Notes callout naming its real cross-module blast radius (Epic 1's session-validation core, Epic 3's Assignment-creation service) and suggesting a split option.

**Status upgraded to READY** (Epic 7/8 scope). Next: re-run `bmad-sprint-planning` to add Epic 7/8 entries to `sprint-status.yaml`, then `bmad-create-story` for Story 7.1.
