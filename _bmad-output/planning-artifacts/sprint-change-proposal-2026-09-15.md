---
title: Sprint Change Proposal — Post-MVP Admin & Roster Refinements
date: 2026-09-15
status: approved
approved: 2026-09-15
author: John (PM) via bmad-correct-course
---

# Sprint Change Proposal — 2026-09-15

> **Addendum, same day, during mockup work (`wds-4-ux-design`):** Story 10.2's scope was corrected mid-mockup — the Employee grid drops the existing **Department** column (kept as a field/filter, just not displayed) and adds **Project** as a fourth new column, alongside the three already approved here (Location, Technologies, Days in Talent Pool). `prd.md` FR-34 and `epics.md` Story 10.2 have both been updated to match; this document's text below is left as originally approved, not retroactively rewritten.
>
> **Second addendum, same day, later in the session:** a new **Story 10.11** was added — the Skill Assignment Dashboard's Employee Segmentation pie chart (On Track/In Progress/Needs Attention) is fully retired and replaced by the Experience Distribution panel (FR-36) in the same primary position. This is **not** a scope refinement like the one above — it's a deliberate reversal of already-shipped, `done` Epic 9 work (Stories 9.2/9.3/9.4), confirmed via `AskUserQuestion` as a real product decision, not a mockup-only exploration. It was never part of this proposal's original 11-item trigger or its 10-story plan. See `prd.md` FR-32's superseded note and `epics.md` Story 10.11 for the full record; this document's original scope (§2's Story-Level Mapping table, listing only 10 stories) is left unchanged below.

## 1. Issue Summary

The project reached feature-complete on 2026-09-14 (all 9 epics, 30 FRs, done — see `sprint-status.yaml`). TalentPilot has since surfaced 11 post-launch change requests spanning the Employees roster, Skills/Skill-Assignments admin surfaces, content-sourcing credential handling, and seed data. None of these were discovered mid-story — they're new asks against a shipped system, evaluated here as a batch rather than 11 separate correct-course passes.

None of the 11 items require rolling back completed work or reducing MVP scope. All are additive/corrective and fit within the existing modular-monolith architecture (`ARCHITECTURE-SPINE.md`) without violating any AD. **Recommended path: Direct Adjustment** — a new Epic 10 with 10 stories (two items each bundled into one story where they're the same surface — #2+#3 into 10.2, #4+#5 into 10.3), built the same way Epics 6–9 were.

**Approved 2026-09-15.** `sprint-status.yaml` has been updated with Epic 10 and its 10 stories (all `backlog`). Next step: author each story's full ACs in `epics.md` (via `bmad-create-epics-and-stories` or per-story `bmad-create-story`), then implement via `bmad-dev-story`, per the build order in §3.

**Scope addendum (confirmed 2026-09-15, after initial approval discussion):** item #1's "ID not roles/names" requirement was tightened to mean *no identity reference* (display, attribution, seed data) should key off a name or role string — role-based *authorization* (AD-6) is unaffected. Audited the codebase directly: zero hardcoded name/role identity comparisons exist anywhere; the one attribution surface that shows a name (`admin_api_keys_router.py`'s Udemy "connected by {name}") already stores and looks up by `employee.id`, resolving the display name live — already the correct pattern (matches FR-26). Story 10.1's scope is therefore just the rename itself; see its updated description below.

Four items carried real ambiguity and were resolved with the user via `AskUserQuestion` before drafting this proposal (all "Recommended" options chosen):

| # | Ambiguity | Resolution |
|---|---|---|
| 4/5 | Delete vs. archive semantics for an Employee with assigned skills | Keep the existing silent-archive behavior (already correct per FR-27); tighten the icon/label so it's visibly "Archive" before the click, not just in the confirm dialog |
| 6 | "Employee Segmentation" already names FR-32's On Track/In Progress/Needs Attention chart | The experience-bucket widget is a new, separately-named panel — FR-32 is untouched |
| 9 | YOUTUBE_API_KEY → admin_api_keys seeding | Seed an encrypted copy for the one seeded HR Admin; the batch ingestion job keeps reading `settings.YOUTUBE_API_KEY` unchanged (AD-7 boundary preserved) |
| 11 | Seed reduction breaks ~10 regression tests | Reduce to 1 HR Admin + 1 Skill and rewrite the affected tests |

One item (#8) was investigated and is very likely **not** a RAG/embedding defect — see §2, Story 10.8.

## 2. Impact Analysis

### Epic Impact

No existing epic (1–9) needs reopening or AC changes — all are `done` and none of these 11 items contradict their shipped scope. This is genuinely new scope: **new Epic 10 — "Post-MVP Admin & Roster Refinements."**

### Story-Level Mapping

| Story | Covers item(s) | New FR(s) | Notes |
|---|---|---|---|
| 10.1 | #1 — Seeded HR Admin's login/display identity + ID-only identity references | Glossary/seed change, no new FR | **Scope corrected 2026-09-15 (user clarification):** the PRD's narrative persona name "Rita" stays untouched in §2.1/UJ-1/UJ-3 — this is illustrative storytelling, not a system identifier, and is not being renamed. What changes is the **actual seeded account**: login email `rita@sails.example.com` → `admin@sails.example.com`, and its in-product display name → "Sails Admin". §3 Glossary now documents this split (persona name vs. account identity) explicitly. Role-based access control (AD-6, `Role.HR_ADMIN`/`Role.EMPLOYEE` checks) is authorization, not an identity reference, and stays as-is. Audited the codebase for hardcoded name/role identity comparisons and found **zero** instances. The one attribution surface that resolves a name (`content/admin_api_keys_router.py`'s `configured_by_name = employee.name if employee else None`, backing AD-10's "connected by {name}" Udemy credential display) already stores and looks up by `employee.id` (the FK), resolving the display name live at read time — the same pattern FR-26 already established as correct, not a violation. **Story 10.1's actual work:** `core/seeds.py`'s seeded account (email + `name` field), and ~15 test files' `rita@sails.example.com` login fixtures. |
| 10.2 | #2, #3 — Employee grid columns + red flag | FR-34, FR-35 | Split `name` into `first_name`/`last_name` (migration); grid adds Location, Technologies, Days in Talent Pool; display name format; row turns red when Days in Talent Pool > 90. |
| 10.3 | #4, #5 — Delete/Archive icon clarity | Extends FR-27 (no renumber) | Icon/label reflects Archive vs. Delete *before* the click, based on `has_assignment_history` (field already returned by the API). No service-layer change — `delete_or_archive_employee_service` is already correct. |
| 10.4 | #6 — Experience Distribution widget | FR-36 | New panel, new endpoint, numeric `experience_years` field (see Open Item below), 6(+1) buckets, click-through to a paginated (15/page) employee list. |
| 10.5 | #7 (Skills) — search + pagination | FR-37 | Mirrors Story 7.3's Employees search/pagination pattern. |
| 10.6 | #7 (Skill Assignments) — search + pagination | FR-38 | Same pattern applied to the Readiness Dashboard grid (Epic 5). |
| 10.7 | #8 — New-skill content not visible at assignment time | FR-39 | See investigation below — likely a wiring/UX gap in FR-20's "content lookup auto-opens on skill creation," not a matching-algorithm defect. |
| 10.8 | #9 — Seed `admin_api_keys` from `YOUTUBE_API_KEY` | AD-10 addendum note, no new FR | Encrypted copy written at seed time for the one seeded HR Admin; batch job unchanged. |
| 10.9 | #10 — Disable "New Skill" without a configured credential | FR-40 | Reads the existing FR-16 "configured" boolean; disabled state + tooltip. |
| 10.10 | #11 — Seed-data minimization | §9 Constraints amendment, no new FR | `seeds.py` → 1 HR Admin (Sails Admin) + 1 Skill; all other employees/skills/content created live via existing CRUD (FR-24, FR-20) going forward, not pre-seeded. |

(10.1 and 10.10 are sequenced together — the seeded HR Admin's identity is renamed *and* becomes the only seeded account in the same pass.)

### Investigation: Item #8 ("RAG implementation missing?")

Traced the actual code path: `assignments/service.py::create_assignment_service` calls `content.service.match_content_for_skill(session, skill_id)`, which ranks only against rows that already exist in `content_catalog` for that skill (pgvector filter-then-rank, AD-7). A brand-new Skill has **zero** `content_catalog` rows until either the scheduled batch job runs, or an HR Admin uses the "search & attach" panel (FR-17/18) to add one directly.

FR-20 already specifies: *"the Content Lookup panel (FR-17) opens automatically for it [a newly-created Skill], with the search term pre-filled."* If that auto-open didn't fire, or the Admin closed it without attaching anything, the Skill genuinely has no content — and `match_content_for_skill` returning nothing is the **correct, designed** behavior (FR-3: "no match beats a bad match"), not a broken embedding pipeline.

**Story 10.7 scope:** (a) verify/fix that the content-lookup panel reliably auto-opens per FR-20, and (b) add a clearer empty state in the assignment flow's content-review step specifically for "this Skill has no content yet" (distinct from FR-2's existing generic no-content copy), pointing the Admin back to the Skills tab's search-and-attach flow. This is **not** a RAG/embedding rebuild — no change to `content/repository.py`'s matching query is anticipated. If the dev-story investigation finds the panel genuinely isn't auto-opening, that's the bug; if it finds Admins are closing it without attaching, that's a UX-copy fix.

### Artifact Conflicts

- **PRD** (`prd.md`): needs §3 Glossary update (persona rename), §4.7 amendments (FR-24/25/26 gain First/Last Name + grid columns; FR-27 gains the icon-clarity consequence), a new §4.11 for FR-34–FR-40, and a §9 Constraints amendment for the seed-data minimization. None of this contradicts an existing FR — all are additive amendments in the PRD's own established style (matching how FR-24–FR-33 were added).
- **Architecture** (`ARCHITECTURE-SPINE.md`): one addendum note to **AD-10** — seed-time credential provisioning is a new (but consistent) credential-entry path alongside the existing admin-submitted-via-UI path; still Fernet-encrypted via `core/secrets.py`, still never returned in plaintext. **No AD is violated.** AD-7's batch/live-lookup separation is explicitly preserved per the user's confirmed answer.
- **UI/UX**: no formal UX-scenario doc covers any of these 11 items (consistent with FR-24–FR-33, which also shipped without upfront UX artifacts) — story files will spec the UI detail directly, per this project's established pattern.
- **Other artifacts**: `sprint-status.yaml` needs a new Epic 10 block (10 stories, `backlog`) -- already added. `backend/tests/`: ~10 files keyed to the current multi-employee/multi-skill seed (`test_seed_employee_identity_alignment.py`, `test_seed_skill_data_quality.py`, and the `_login()` helpers using `rita@sails.example.com` across ~15 test files) need updating for the persona rename and seed reduction — scoped into Stories 10.1/10.10, not left implicit.

### Path Forward Evaluation

- **Option 1 — Direct Adjustment (recommended):** all 11 items fit as new stories in a new epic, no rollback, no MVP change. Effort: **Medium** overall (mostly standard CRUD/UI extension work); two stories carry more weight — 10.2 (schema migration + widely-referenced `name` field) and 10.10 (seed reduction's test blast radius). Risk: **Medium** — concentrated entirely in 10.1/10.2/10.10 touching identity fields and seed data that many existing tests assume; 10.3–10.9 are low-risk, additive, isolated.
- **Option 2 — Rollback:** not viable — nothing here is better solved by reverting shipped work.
- **Option 3 — MVP Review:** not applicable — no MVP goal is invalidated; this is pure post-launch enhancement.
- **Selected: Option 1, Direct Adjustment**, organized as Epic 10.

## 3. Recommended Approach

Create Epic 10 with the 10 stories mapped in §2, in this build order (dependency-driven, not numeric-only):

1. **10.1 + 10.10 together** (persona rename + seed minimization) — do first, since 10.2's grid work and most test fixtures should be written against the *final* seed shape, not the old one.
2. **10.2, 10.3** (Employee grid/schema) — the widest-blast-radius schema change; sequence before 10.4 (icon depends on the same roster data) and 10.4 (Experience widget depends on 10.2's schema touch-point if `experience_years` lands in the same migration).
3. **10.5, 10.6** (search/pagination) — independent of everything else, can run any time, in parallel with 10.7–10.9 if desired.
4. **10.7** (content-visibility investigation/fix) — independent.
5. **10.8, 10.9** (credential seeding + button gating) — sequence 10.8 before 10.9 so the "disabled without a key" state can be verified against both the seeded-key and no-key cases.

Rationale: minimizes rework (schema/identity changes land before the UI that displays them), and keeps the two higher-risk stories (10.2, 10.10) earliest so any surprises surface before the rest of the epic is built on top.

## 4. Detailed Change Proposals

### PRD (`prd.md`)

**§3 Glossary** — OLD: *"HR/L&D Admin ("Rita the Referee")"* → NEW: *"HR/L&D Admin ("Sails Admin")"*; every `rita@sails.example.com` reference → `admin@sails.example.com`.
Rationale: user-requested rebrand away from a named-persona convention toward a role-generic one; reduces the temptation for code to key off a hardcoded name.

**New §4.11 "Employee Roster Enhancements & Content-Sourcing Guardrails"** with FR-34 through FR-40 (full text to be drafted during story creation, not here — matching this PRD's own pattern of writing FR consequence-lists alongside the story, e.g. FR-31/32/33's authorship). Stub summary:
- FR-34: Employee record split into `first_name`/`last_name`; roster grid adds Location, Technologies, Days in Talent Pool columns; display name = `{last_name} {first_name}` **[OPEN — see below]**.
- FR-35: A roster row with Days in Talent Pool > 90 renders with a red visual flag (paired with text, per this PRD's existing non-color-only rule, §8).
- FR-36 (extends FR-27): the Delete/Archive row action's icon and label reflect which behavior will occur *before* the click.
- FR-37: Employee Experience Distribution — a headcount-by-experience-bucket panel with click-through to a paginated (15/page) roster filtered to that bucket.
- FR-38: Skills tab gains search + pagination (15/page), mirroring FR-25's Employee roster pattern.
- FR-39: Skill Assignments (Readiness Dashboard) grid gains search + pagination (15/page).
- FR-40: The "+ New Skill" action is disabled with an explanatory tooltip when no content-source credential is configured for the acting HR Admin.

**§9 Constraints** — add: *"Seed data is minimized to exactly one HR Admin account and one Skill; all other Employees, Skills, and Content are created through the product's own CRUD flows (FR-20, FR-24) rather than pre-seeded, as of the 2026-09-15 seed-reduction change."* This actually **reinforces** the PRD's own pre-existing "no data migration, clean launch" constraint (§9) rather than conflicting with it.

**AD-10 addendum** (`ARCHITECTURE-SPINE.md`) — append: *"[ADDED 2026-09-15] Seed-time credential provisioning: `core/seeds.py` may write one encrypted `admin_api_keys` row for the seeded HR Admin, sourced from `settings.YOUTUBE_API_KEY`, using the same `core/secrets.py` Fernet encryption as the admin-submitted-via-UI path. This is a second entry point for the same encrypted-at-rest guarantee, not a new credential shape — AD-7's batch-vs-live-lookup key separation is unchanged; the batch ingestion job continues reading `settings.YOUTUBE_API_KEY` directly."*

### Decisions Locked 2026-09-15 (confirmed via AskUserQuestion)

1. **Experience bucket boundaries (FR-37).** Resolved as **7 contiguous, exhaustive buckets**: 0–4, 5–7, 8–9, 10–11, 12–14, **15–19 (new)**, 20+. One more segment than the 6 originally listed, to close the 15–19 gap without silently absorbing it into a neighboring bucket.
2. **Display name format (FR-34).** Resolved as **`"{last_name}, {first_name}"`** (e.g., "Martinez, Rita") — conventional HR-roster comma format, not the literal no-comma concatenation.
3. **"Days in Talent Pool" basis.** Resolved as **`now() − employees.created_at`** (days since the Employee record was created in this system) — no new hire-date field added; no schema addition beyond FR-34's own First/Last Name split.

## 5. Implementation Handoff

**Scope classification: Moderate.** Requires backlog reorganization (new Epic 10 + 10 stories) and PO/Dev coordination — not a fundamental replan, since no existing epic, architecture decision, or MVP goal is being reversed.

- **Product Owner / this PM (Alice/John role):** finalize the 3 Open Items above with TalentPilot, then run `bmad-create-epics-and-stories` (or `bmad-create-story` per-story) to formally add Epic 10 to `epics.md`, and update `sprint-status.yaml` with the 11 new story entries (all `backlog`), per this proposal's build order.
- **Developer agent (Amelia / `bmad-dev-story`):** implements each story once created, in the sequence given in §3. Story 10.10 (seed reduction) should explicitly enumerate every test file it touches before starting, given the ~10-file blast radius identified here.
- **Architect:** no dedicated architecture pass needed — the AD-10 addendum above is small enough to fold into Story 10.8's own Dev Notes, matching how prior single-paragraph AD amendments (e.g., AD-7's extensions) were handled inline rather than via a full `bmad-architecture` re-run.

**Success criteria:** all 11 original change requests traced to a specific story with a testable AC; zero existing (Epic 1–9) regression tests broken outside the ones explicitly scoped for rewrite in Stories 10.1/10.10; `sprint-status.yaml` and `project-context.md` updated per this project's own mandatory-update convention (per the epic-8 retro's blocking-gate decision).
