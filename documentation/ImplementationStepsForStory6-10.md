# Implementation Steps for Story 6-10: Skills Tab Frontend — Card Grid, Content Lookup, API Keys, Watch Modal

**Story Key:** 6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal
**Epic:** 6 (Admin-Assisted Content Sourcing) — **final story, epic now complete**
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.10 is the epic's capstone: the real Skills tab an HR Admin actually uses — a card grid of every Skill, a Content Lookup panel for sourcing or rejecting Content, an API Keys modal, and an in-app Watch Modal. Every backend endpoint it needed already existed from Stories 6.1–6.9 (create/edit/delete, live search, manual entry, attach, reject, credential management), and three frontend pieces had already been deliberately built "ahead of" this story's real panel by earlier stories (`ApiKeysModal`, `ManualContentEntryForm`, `ContentPreviewModal`, `CurrentlyApprovedContent`) — so the honest scope of this story was composition, not invention, for most of it.

The one genuine exception, found only by reading the actual current backend source rather than trusting the epics text: **`GET /api/admin/skills` — the list endpoint the Skills Card Grid needs — did not exist anywhere in the codebase.** The epics AC assumed it as a given ("`GET` over Story 6.1's `skills.service.list_all_skills()`, extended to also return each Skill's current approved Content and `ever_assigned` status"), but no route, service function, or schema for it had ever been written. Building it — a new `SkillWithContentResponse` schema, a bulk repository query picking each Skill's most-recently-admin-approved Content in one round trip, and an HR_ADMIN-gated service composer — became this story's own backend scope, composed the same cross-module way Stories 6.6/6.7's existing Skill sub-routes already cross into `content/service.py`.

The work happened in three passes in one session: (1) exhaustive research via three parallel background agents — the UX spec plus its HTML/CSS mock for exact visual and copy fidelity, the actual current backend API contracts (which surfaced the missing-endpoint gap), and the existing frontend conventions plus an inventory of what Stories 6.5/6.7/6.9 had already built ahead of this story — followed by direct reads of the live skills/content source files to confirm the gap and design the fix; (2) full TDD implementation across both stacks, composing rather than rebuilding wherever a prior story had already shipped a piece; (3) an adversarial code review pass that found and fixed four real frontend bugs — a lock-bypass path, a concurrency race on Approve, and two stale-async-state races in the New Skill modal — while correctly dismissing fourteen other findings as either pre-existing codebase-wide patterns or a reviewer's factual mix-up between two unrelated foreign keys.

---

## Agents Invoked

### 1. **UX Spec & Mock Research Agent (Explore)**

**Purpose:** Extract the complete, exact UX specification and its HTML/CSS prototype for visual and copy fidelity — the single largest source of ground truth this story needed.

**When Invoked:** Immediately after story-creation kickoff, in parallel with the two agents below
**Model Capability:** Sonnet 5 (session model)
**Input:** `04.1-skills-content-sourcing.md` (the full UX spec) and `04.1-Skills-Tab.html` (the E-Development HTML/Tailwind mock), plus a check of the sibling `01.1-Skills-Dashboard.html` for shared header/modal conventions

**Key Findings Identified:**
- The complete page anatomy: header/toolbar/Skills Card Grid/New Skill Panel/Content Lookup Panel/Watch Modal/API Keys Panel/footer, with every UX-spec object ID (`skills-tab-*`, `content-lookup-*`, `watch-modal-*`, `api-keys-modal-*`) and its exact required copy
- The UX spec's own same-day revision history: the Content Lookup Panel's *only* entry point for an unassigned Skill is its card's Edit icon — no separate "Find Content" button exists, and none should be built
- The explicitly-flagged, intentionally-unresolved gap (UX-DR33/PRD Open Question 17): a locked (assigned) Skill has no entry point into content-sourcing anywhere on this page, by design, not an oversight to fix
- Exact HTML/Tailwind structure, icon characters (`✎`✎/`🗑`/`🔒`/`✓`/`⚠`), and interaction JavaScript from the mock — card anatomy, the Watch Modal's YouTube-embed-or-fallback behavior, the API Keys modal's Udemy row restructuring (Client ID on its own row, Client secret + Save/Remove below it, matching YouTube's shape)

**Output:** A single exhaustive report covering every object ID, every required copy string, and the mock's exact DOM/class conventions — used directly to build `SkillCard`, `NewSkillModal`, and `ContentLookupPanel` with matching `data-testid`s and copy, without needing to re-open either source file during implementation.

---

### 2. **Backend API Contracts Research Agent (Explore)**

**Purpose:** Determine the *actual current* backend contracts for every endpoint this story's frontend would need to call — not what the planning docs said, but what the real source code does today.

**When Invoked:** In parallel with the UX research agent
**Model Capability:** Sonnet 5 (session model)
**Input:** `backend/app/skills/` (router/service/schemas/repository), `backend/app/content/` (admin router/service/schemas), `backend/app/main.py`'s router mounts, and the relevant test files

**Key Findings Identified:**
- **The critical gap:** `skills/router.py` has only `POST ""`, `PATCH "/{id}"`, `DELETE "/{id}"`, and the two Skill-sub-resource content routes — **no `GET` (list or single) route exists anywhere**, confirmed by reading the full router file and grepping the whole backend
- `SkillResponse` already carries `ever_assigned` but never a Skill's approved Content — no schema anywhere embeds the two together
- No route ever returns "all content for a skill" — `content.service.list_content_for_skill` exists but was never wired to any router
- Every other Epic 6 endpoint's exact contract (request/response field names, status codes, error codes), verified field-for-field against the real Pydantic schemas rather than paraphrased

**Output:** A complete, verified API reference plus an explicit flag: *"Story 6.10's list/detail view has no backend endpoint to consume yet — that's a gap the frontend work will hit immediately."* This became the trigger for scoping the new `GET /api/admin/skills` endpoint as this story's own backend work.

---

### 3. **Frontend Conventions Research Agent (Explore)**

**Purpose:** Establish exact existing frontend conventions (routing, API client shape, modal/toast primitives, testing style) and inventory what earlier stories had already built ahead of this one.

**When Invoked:** In parallel with the two agents above
**Model Capability:** Sonnet 5 (session model)
**Input:** `App.tsx`, `adminContentApi.ts`, `frontend/src/features/admin/*`, `frontend/src/pages/dev/*`, `frontend/src/components/ui/*`, and the existing test suite

**Key Findings Identified:**
- No `/skills` route existed, but `Dashboard.tsx` already had a **dead** `<a href="#">Skills</a>` nav link waiting to be wired up
- `ApiKeysModal.tsx`, `ContentPreviewModal.tsx`, and `CurrentlyApprovedContent.tsx` (from Stories 6.5, 6.7, and 6.9 respectively) were already fully built and explicitly documented in their own code as "ahead of Story 6.10's real panel" — reuse directly, do not rebuild
- `ManualContentEntryForm.tsx` (Story 6.7/6.8) already implemented the entire "Paste a link" tab, including Approve
- Story 6.6's `content-lookup` search endpoint had **no frontend client function anywhere in the repo** — a second real gap this story needed to close
- The exact API-client convention (one function per endpoint, snake_case fields mirroring the Pydantic schema, a shared `apiClient` axios instance with no per-call base URL) and the exact modal/toast/error-handling primitives (`Dialog`, `Toast`, `FormErrorText`, a duplicated-per-component `extractErrorMessage` helper) to match

**Output:** A precise map of what to reuse verbatim, what to compose, and what was genuinely still missing — directly shaped the story's Scope Notes on reuse (Scope Note 5) and the two real new-code gaps (Scope Notes 1–4 for the backend list endpoint, Scope Note 6 for `searchContentForSkill`).

---

### 4. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, reliability/security concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model), general-purpose background agent
**Input:** Full diff (uncommitted changes against `HEAD`, reconstructed via `git add -N` intent-to-add on the 11 new untracked files so they appeared in `git diff HEAD`, then reset), ~2278 net new lines across 24 files, instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (15 items):**
- Duplicate/colliding `data-testid`s across a mapped result list and across two composed components rendered together
- `DeleteSkillModal`'s confirmation copy claimed to contradict the data model (later disproven — see Triage)
- `NewSkillModal`'s duplicate notice goes stale after the name is edited post-409
- **No lock check anywhere in `ContentLookupPanel`, and the "Use existing skill" hand-off opens it for *any* skill by id — bypassing `SkillCard`'s own lock gate entirely**
- `SkillsPage`'s `onUseExisting` fallback fabricates unlocked/empty skill state when the conflicting skill isn't in the local cache
- Most-recent-content tie-breaking, imperative-not-declarative authorization, no client-side role gate, duplicated duration-extraction logic, dead state writes in a composed `ManualContentEntryForm`, a narrowed `useEffect` dependency array, a silent no-op on blank name, no pagination, and a router-test coverage gap for the multi-row tie-break

**Output:** 15 findings; after triage — including verifying the `DeleteSkillModal` cascade claim directly against a passing test and the imperative-authorization/no-role-gate findings against this router's and codebase's own established, identical pattern elsewhere — 1 became a real patch (merged with Edge Case Hunter's overlapping finding below into the lock-bypass fix), 6 became deferred items, 8 were dismissed as pre-existing precedent or a factual error.

---

### 5. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model), general-purpose background agent
**Input:** Same diff, targeting the `bmad-review-edge-case-hunter` skill's exhaustive-path-enumeration methodology

**Key Findings Identified (structured JSON, location/trigger/guard/consequence, 13 items):**
- **Approve clicked on candidate B while candidate A's `attachContent` is still in flight — only A's own button was disabled, so two concurrent approves could both succeed**
- **`NewSkillModal` closed while `createSkill()` is still pending, then it resolves — `onCreated` fires anyway, unexpectedly reopening `ContentLookupPanel` after the admin believed they'd cancelled**
- The same lock-bypass path Blind Hunter found (independently converged on from a different angle — race-condition framing rather than access-control framing)
- `refetch()` failure after a successful mutation masks the just-updated grid behind a full error banner
- `getApiKeysStatus()` fetch failure indistinguishable from "not configured"; results-and-error rendered together for one source (later disproven as unreachable); no message when both source checkboxes are unchecked; `DeleteSkillModal` has no distinct handling for a concurrent lock; no Enter-to-submit; sign-out doesn't guard in-flight modal requests

**Output:** 13 structured findings; the two genuinely new, high-value findings (concurrent double-approve, and the New-Skill-Modal close-race) became this review's second and third patches; the shared lock-bypass finding merged with Blind Hunter's into one combined patch; the rest were verified and either deferred or dismissed as unreachable/pre-existing.

---

### 6. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.10's literal Given/When/Then acceptance criteria (AC1–AC10, AC1a) and its 12 numbered Scope Notes.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers)
**Model Capability:** Sonnet 5 (session model), general-purpose background agent
**Input:** The full story spec file (read directly, in full) plus the same diff

**Key Findings Identified:**
- **Zero violations of substance.** Every AC and every Scope Note's specific technical decision was verified directly against the actual shipped code: Scope Note 2's `origin="ADMIN_LOOKUP"`-only definition, Scope Note 3's exact schema/repository/service composition, Scope Note 4/AC1a's HR_ADMIN gating (confirmed via the router-level 403/401 tests), Scope Note 9's client-side-only source filter (no backend param added), Scope Note 11's two-different-409-behaviors distinction (verified against `skills/service.py`'s actual `_conflict` vs. `_rename_conflict`), AC7/UX-DR29's uniform "approve closes the panel" rule across both tabs, and AC10/Scope Note 8's locked-skill gap
- **One informational, non-code note:** Scope Note 10's own prose describes a two-argument `onApproved(skillId, skillName)` callback, while Task 11's own Props checklist specifies the one-argument form the code actually ships — a self-contradiction in the spec text itself, not a defect, since the shipped code correctly matches the Task 11 checklist item that was actually marked done

**Output:** Zero AC/Scope-Note violations; the one informational note was dismissed as a spec-text inconsistency rather than a code issue.

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development api and ui for the story 6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, recognized no story file existed yet for `6-10-...` (sprint-status showed `backlog`, the last story in Epic 6), and dispatched into `/bmad-create-story` before implementation — with the added step of launching three parallel research agents first, given the scale of what this story needed to get right (UX fidelity, real API contracts, existing reusable components).

---

### 2. **`/bmad-create-story` → `/bmad-dev-story` (story creation + implementation)**

**Purpose:** Ground the story in the real spec/architecture/UX/code (via the three parallel research agents above plus direct source reads), create the story file, then implement it in the same pass.

**When Invoked:** Immediately after Amelia activation
**Workflow Steps Executed:**
1. Launched the three parallel research agents described above; while waiting, independently confirmed the missing-list-endpoint gap by reading `backend/app/skills/service.py`/`router.py` and `backend/app/content/service.py`/`repository.py`/`schemas.py` directly
2. Verified `content_catalog.ingested_at`'s exact column definition (`nullable=False, server_default=func.now()`) and `origin`'s default (`'BATCH'`), and confirmed via `content/service.py::attach_content`/`reject_content` that `origin="ADMIN_LOOKUP"` is the only correct filter for "approved" in this epic's sense
3. Read every reusable frontend piece in full (`ApiKeysModal.tsx`, `ContentPreviewModal.tsx`, `CurrentlyApprovedContent.tsx`, `ManualContentEntryForm.tsx`, `DeleteAssignmentModal.tsx`, `Dialog`/`Card`/`Toast` primitives) to confirm exact props, copy, and composition shape before writing a line of new code
4. Wrote 12 numbered Scope Notes into the story file resolving every real design decision: the missing-endpoint gap and its exact fix (schema/repository/service/router composition, Scope Notes 1–4); the `origin="ADMIN_LOOKUP"`-only "approved" definition (Scope Note 2); which existing components to reuse verbatim vs. compose (Scope Notes 5–7); the client-side-only source-filter rule for Search (Scope Note 9); the two-different-409-behaviors distinction between `NewSkillModal` and `ContentLookupPanel`'s own rename conflict (Scope Note 11); and the deliberately-unresolved locked-skill gap (Scope Note 8, later revisited by code review from a different angle)
5. Implemented directly in the same session, task by task, TDD red-green-refactor: `content/schemas.py::SkillWithContentResponse` → `content/repository.py::list_admin_lookup_content_for_skills` (bulk query, 2 new tests) → `content/service.py::list_skills_with_content` (5 new tests) → `skills/router.py`'s new `GET ""` route (3 new tests) → `skillsApi.ts` → `adminContentApi.ts`'s new `searchContentForSkill` → `ManualContentEntryForm.tsx`'s additive `onApproved` hook (2 new tests) → `SkillCard.tsx` (5 new tests) → `NewSkillModal.tsx` (4 new tests) → `DeleteSkillModal.tsx` (3 new tests) → `ContentLookupPanel.tsx` (9 new tests) → `SkillsPage.tsx` (7 new tests) → routing (`App.tsx`, `Dashboard.tsx`)
6. **Self-caught and fixed one editing mistake during test authoring**, the same category Story 6.9's own Dev Notes had already flagged as a recurring risk: an `Edit` tool call's `old_string` boundary matched an earlier test with an identical ending line instead of the true end-of-file test (a prior `Read` call's `offset`/`limit` window had cut off one line before the file's actual last line), orphaning that test's final assertion onto the new one — caught immediately by the first test run's `NameError`, fixed by restoring the assertion to its original location
7. Full backend regression (631 passed, 2 skipped, 1 pre-existing failure — exact match to the documented 621-passed baseline + 10 new tests); full frontend regression (337 passed, exact match to 307-passed baseline + 30 new tests); `tsc --noEmit` unchanged at 31 pre-existing errors, none touching this story's files; rebuilt and redeployed both Docker images; live-verified via `curl` the complete create → attach → list-reflects-it → reject → list-clears cycle, plus 403 (EMPLOYEE) and 401 (unauthenticated) gating on the new endpoint
8. Noted honestly, rather than overclaiming: interactive real-browser click-through of the full UI flow was not performed (no Playwright/browser-automation tool available this session) — covered instead by the 30 new RTL tests exercising the real component tree

**Output File:** `_bmad-output/implementation-artifacts/6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal.md`
**Sprint Status:** `6-10-...`: `backlog` → `ready-for-dev` → `review` (created and implemented in the same pass)

---

### 3. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for s story 6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from the explicit story name in the user's request (Tier 1). The story's own `baseline_commit` frontmatter (`786b1aa4`) turned out to be stale relative to actual `HEAD` (`80fdb17d`, Story 6.9's own commit) — a bookkeeping artifact of having been copied from the 6-9 story file as a template rather than freshly captured via `git rev-parse HEAD`, but harmless for review purposes since nothing had been committed since `HEAD` and "uncommitted changes" (`git diff HEAD`) correctly captured exactly this story's diff regardless. Reconstructed the diff including the 11 new untracked files via `git add -N` (intent-to-add, non-destructive) → `git diff HEAD` → `git reset --` (restoring the untracked state exactly), producing a 2556-line diff across 24 files. Checkpoint presented (diff stats, review mode) and confirmed before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor as three parallel background subagents, each independently reconstructing the same diff via the identical `git add -N`/`git diff`/`git reset` sequence and reading the story spec file directly (`review_mode = "full"`). All three returned independently.
- **Step 03 (Triage):** Normalized 15 Blind Hunter + 13 Edge Case Hunter + 1 Acceptance Auditor findings (29 raw) down to a unified list, merging the two independently-converged lock-bypass findings into one. Read the actual code at every finding's location before rating severity — most consequentially, re-read `SkillsPage.tsx`'s `onUseExisting` line-by-line and confirmed the lock-bypass was real even in the common case (an `existing` skill *found* in cache still had no `ever_assigned` check), not just the rarer cache-miss fallback; separately confirmed via the passing `test_delete_skill_cascades_attached_content_catalog_rows` test that Blind Hunter's `DeleteSkillModal`-copy finding was a factual mix-up between two unrelated foreign keys (`content_catalog.skill_id`'s real CASCADE vs. `assignments.content_id`'s unrelated SET NULL from Story 6.9); confirmed `content_catalog.ingested_at` is a NOT NULL column, disproving one edge case entirely; confirmed the results-and-error-together finding was unreachable per `search_content_for_skill`'s own mutually-exclusive-per-source contract. Routed the result into 0 decision-needed, 4 patch, 6 defer, 14 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection; 6 deferred items also logged to `deferred-work.md`. User chose "apply every patch."

**Patches Applied (all frontend, all TDD — implemented, then re-verified GREEN):**
1. `SkillsPage.tsx`'s `onUseExisting` opened `ContentLookupPanel` for the conflicting existing Skill with **no `ever_assigned` check at all**, directly contradicting AC10/UX-DR33's "no entry point for a locked Skill" invariant — reachable whenever a new-Skill name collides case-insensitively with an already-assigned Skill's name. The same path also fabricated `{ever_assigned: false, approved_content: null}` when the conflicting Skill wasn't in the local cache. Fixed: the hand-off now declines (shows a toast) when the resolved Skill is locked or genuinely not found, instead of ever opening the panel with unlocked/empty state. 3 new tests (unlocked/locked/not-found).
2. `ContentLookupPanel`'s Search-tab result cards only disabled the *specific* candidate's own `[Approve]` button while its `attachContent` call was in flight — every other candidate's button stayed clickable, letting two concurrent approves both succeed and write two `content_catalog` rows for one Skill. Fixed: `ResultCard` gained a separate `disabled` prop (`approvingUrl !== null`) disabling every card's Approve button while *any* approve is in flight, distinct from the `approving` prop that still drives the per-card "Approving…" label. 1 new test.
3. `NewSkillModal`'s async `handleCreate` had no request-identity guard — closing the modal (or it reopening for a different flow) while `createSkill` was still pending let the eventual resolution still call `onCreated`, unexpectedly reopening `ContentLookupPanel`. Fixed: added the identical `requestIdRef` guard `DeleteSkillModal`/`ApiKeysModal` already use elsewhere in this codebase. 1 new test (resolves a pending create after close, asserts `onCreated` never fires).
4. `NewSkillModal`'s duplicate-conflict notice was never cleared when the name was edited after a 409 — its "Use existing skill" link kept pointing at the original, now-stale conflicting Skill. Fixed: the name input's `onChange` now also clears the duplicate state. 1 new test.

One test-authoring type error was caught and fixed during this pass: a deferred-promise mock in the new concurrency test needed explicit typing (`Awaited<ReturnType<typeof attachContent>>`) to avoid a transient 32nd `tsc` error; corrected before final verification.

**Output:** Story status → `done`; **epic-6 marked complete** in `sprint-status.yaml` (all 10 stories 6-1 through 6-10 now `done`, only the optional retrospective remains); full regression re-verified — frontend 343/343 (up from 337); `tsc --noEmit` back to the exact 31-error baseline; backend untouched (all 4 patches were frontend-only).

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection (4 patches, 6 deferrals, 14 dismissals each with a one-line reason)
- 6 deferred items appended to `deferred-work.md` under a new "Deferred from: code review of 6-10-..." heading
- Sprint status synced (`6-10-...`: `backlog` → `ready-for-dev` → `review` → `done`; `epic-6`: `in-progress` → `done`)

---

## Files Created/Updated

### Backend — Modified Files (no new backend files — the gap was closed inside existing modules)

| File | Purpose |
|------|---------|
| `backend/app/content/schemas.py` | Adds `SkillWithContentResponse` (id, name, description, ever_assigned, approved_content) |
| `backend/app/content/repository.py` | Adds `list_admin_lookup_content_for_skills` — one bulk query across all Skills, `origin="ADMIN_LOOKUP"` only, ordered `(skill_id, ingested_at, id)` |
| `backend/app/content/service.py` | Adds `list_skills_with_content` — HR_ADMIN-gated, composes `skills_service.list_all_skills` with the bulk content query, picks the most-recent row per Skill |
| `backend/app/skills/router.py` | Adds `GET ""` → `list_skills_with_content`, the same cross-module composition pattern the existing `content_lookup_route`/`content_manual_route` already use |
| `backend/tests/test_content_repository.py` | 2 new tests: empty `skill_ids` short-circuits; excludes BATCH-origin and other-Skill rows |
| `backend/tests/test_content_service.py` | 5 new tests: ADMIN_LOOKUP content returned as approved; BATCH-only ignored; most-recent-of-two picked; `ever_assigned` passes through; EMPLOYEE 403 |
| `backend/tests/test_skills_router.py` | 3 new tests: extended shape for a mix of unassigned/locked/batch-only Skills; EMPLOYEE 403; unauthenticated 401 |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/skillsApi.ts` | `listSkillsWithContent`/`createSkill`/`updateSkill`/`deleteSkill` — one function per `skills/router.py` endpoint |
| `frontend/src/features/admin/SkillCard.tsx` | One Skills Card Grid card — name, Approved/None-yet badge, Edit/Delete or 🔒 lock text, approved-link row |
| `frontend/src/features/admin/NewSkillModal.tsx` | The "New Skill" panel — create-only, 409-duplicate "Use existing skill" hand-off |
| `frontend/src/features/admin/DeleteSkillModal.tsx` | Delete-confirmation modal, mirrors `DeleteAssignmentModal.tsx`'s exact structure |
| `frontend/src/features/admin/ContentLookupPanel.tsx` | The composite panel — edit fields, Currently-Approved slot, Search/Paste-a-link tabs, fresh Search-tab result cards |
| `frontend/src/pages/hr/SkillsPage.tsx` | The real Skills tab page — header, toolbar, grid, and every modal wired together |
| `frontend/src/tests/SkillCard.test.tsx`, `NewSkillModal.test.tsx`, `DeleteSkillModal.test.tsx`, `ContentLookupPanel.test.tsx`, `SkillsPage.test.tsx` | 5/6/3/10/10 tests respectively (post-review counts) |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/adminContentApi.ts` | Adds `searchContentForSkill` + `ContentLookupCandidate`/`ContentLookupSourceError`/`ContentLookupResponse` types — Story 6.6's endpoint had no frontend client anywhere until now |
| `frontend/src/features/admin/ManualContentEntryForm.tsx` | Adds optional `onApproved` prop, called after a successful attach so a real panel can close immediately (UX-DR29) |
| `frontend/src/tests/ManualContentEntryForm.test.tsx` | 2 new tests: `onApproved` called when provided; omitting it doesn't throw |
| `frontend/src/App.tsx` | Adds the `/skills` route, `RequireAuth`-wrapped like every other protected route |
| `frontend/src/pages/hr/Dashboard.tsx` | The previously-dead `<a href="#">Skills</a>` now `<Link to="/skills">` |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal.md` | Story file — ACs, 12 Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-10-...`: `backlog` → `ready-for-dev` → `review` → `done`; `epic-6`: `in-progress` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 6 deferred findings logged under a new heading |
| `documentation/ImplementationStepsForStory6-10.md` | This file |

### Not Changed (by design)

- `ApiKeysModal.tsx`, `ContentPreviewModal.tsx`, `CurrentlyApprovedContent.tsx` — reused exactly as Stories 6.5/6.7/6.9 built them, no rewrite
- Story 6.6's `ContentLookupRequest` schema — no source-selection parameter added; the Search tab's YouTube/Udemy toggles are a client-side display filter over the always-full response (Scope Note 9)
- PRD Open Question 17 / UX-DR33 (locked-Skill content-sourcing entry point) — the review's lock-bypass patch closed an *unintended* back door into the panel, but did not invent the *intended* entry point the UX spec itself still leaves open; that remains a deliberate, tracked gap

---

## Implementation Workflow Summary

### Phase 1: Research & Story Creation
**Skills:** `/bmad-agent-dev` → `/bmad-create-story` (3 parallel Explore agents + direct source reads)
- Three parallel background agents covered the UX spec + HTML mock, the real current backend API contracts, and the existing frontend conventions/already-built components simultaneously
- **Found a real, undocumented backend gap before writing any code:** `GET /api/admin/skills` never existed, despite the epics AC assuming it — scoped as this story's own Task 1–4 backend addition
- Confirmed via direct source reading that `origin="ADMIN_LOOKUP"` (not any BATCH-ingested row) is the correct "approved" definition, by reading `reject_content`'s own 404 condition
- Resolved 12 real design decisions during story-writing, documented as 12 numbered Scope Notes, including exactly which existing components to reuse verbatim vs. build fresh

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, both backend and frontend)**
- Backend: schema → bulk repository query → HR_ADMIN-gated service composer → router route, 10 new tests
- Frontend: 2 new API-client additions, 5 new components, 1 additive hook on an existing component, 30 new tests
- One self-caught and immediately-fixed editing mistake during test authoring (an orphaned assertion from an imprecise `Edit` match), the same category of risk Story 6.9's own Dev Notes had flagged
- Full regression pass — backend 631 passed / 2 skipped / 1 pre-existing failure (exact match to documented baseline + new tests); frontend 337/337; `tsc --noEmit` unchanged (31 pre-existing errors)
- Live end-to-end verification via `curl` against rebuilt Docker containers: the full create → attach → list-reflects-it → reject → list-clears cycle, plus 403/401 gating
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, all background subagents, single pass, each independently reconstructing the diff via a non-destructive `git add -N`/`git diff`/`git reset` sequence
- **Findings:** 29 raw → merged/deduped → 0 decision-needed, 4 patch, 6 defer, 14 dismiss
- **Two independent review layers (Blind Hunter and Edge Case Hunter) converged on the same real defect from different angles** — a locked-Skill lock-bypass via the "Use existing skill" hand-off — merged into one combined patch
- **Most dismissed findings were correctly identified as pre-existing, codebase-wide patterns, not new defects introduced by this story** — imperative HR_ADMIN gating (matches every sibling route), no client-side role gate (matches `/hr/dashboard`'s own precedent), a narrowed `useEffect` dependency array (matches `ApiKeysModal`'s identical pattern) — and one finding was a reviewer's factual mix-up between two unrelated foreign keys, disproven by re-reading a passing test
- **Four genuinely real, small-to-moderate correctness fixes applied:** the lock-bypass, a concurrent double-approve race, and two stale-async-state races in `NewSkillModal`
- **Action:** user chose "apply every patch" — all four applied with 6 new tests, full regression re-verified
- Output: frontend 343/343 (up from 337); `tsc --noEmit` back to the exact 31-error baseline; story marked `done`; **epic-6 marked complete**

---

## Test Coverage

### New/Extended Test Files (46 tests total from this story, post-review)

**Backend (10 new):**
- `test_content_repository.py` — 2 new: empty `skill_ids` short-circuits; excludes BATCH-origin and other-Skill rows
- `test_content_service.py` — 5 new: ADMIN_LOOKUP content as approved; BATCH-only ignored; most-recent-of-two picked; `ever_assigned` passthrough; EMPLOYEE 403
- `test_skills_router.py` — 3 new: extended shape for a mix of skills; EMPLOYEE 403; unauthenticated 401

**Frontend (36 new, post-review):**
- `ManualContentEntryForm.test.tsx` — 2 new (the `onApproved` hook)
- `SkillCard.test.tsx` — 5 new (all new file)
- `NewSkillModal.test.tsx` — 6 new (4 initial + 2 code-review patches: close-during-pending-create, stale-duplicate-on-edit)
- `DeleteSkillModal.test.tsx` — 3 new (all new file)
- `ContentLookupPanel.test.tsx` — 10 new (9 initial + 1 code-review patch: panel-wide Approve disabling)
- `SkillsPage.test.tsx` — 10 new (7 initial + 3 code-review patches: unlocked/locked/not-found "Use existing skill" cases)

### Regression Verification
- Full backend suite run after implementation (631 passed, 2 skipped, 1 pre-existing failure — exact match to the documented 621-passed baseline + 10 new tests) — untouched by the code review's patches (all 4 were frontend-only)
- Full frontend suite run after implementation (337 passed) and again after the four patches (343 passed), zero failures at either stage
- `tsc --noEmit` explicitly checked before and after every change set — 31 pre-existing errors both before implementation and after the final patch round; one transient 32nd error introduced by an under-typed test mock during the patch round was caught and fixed before final verification
- Live-verified end-to-end via `curl` against rebuilt/redeployed Docker containers: `GET /api/admin/skills` returns the extended shape for real seeded/test skills; a fresh Skill's `approved_content` starts `null`; attaching Content makes it appear in the list response exactly; rejecting it clears it again; EMPLOYEE → 403; unauthenticated → 401; a rebuilt frontend container serves `/skills` (200)
- Interactive real-browser click-through of the full UI flow (New Skill hand-off, search/approve, Watch Modal, Edit/Delete) was not performed — honestly noted as not performed (no Playwright/browser-automation tool available this session) rather than overclaimed, covered instead by the 36 new RTL tests exercising the real component tree with only the underlying API-client functions mocked

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: single-owner module, cross-module calls via Service API only** | `content/service.py::list_skills_with_content` composes `skills_service.list_all_skills` (a thin, already-existing Service API call) rather than importing `Skill`/querying the `skills` table directly | `content/service.py` |
| **AD-8: dependency arrow points Content → Skills, never back** | `SkillWithContentResponse` (which embeds `ContentResponse`) lives in `content/schemas.py`, not `skills/schemas.py`; `skills/router.py` imports it the same way it already imports `ContentLookupResponse` for its other sub-routes — `skills/service.py` itself stays untouched | `content/schemas.py`, `skills/router.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | `list_skills_with_content` calls `require_hr_admin(current_user)` first, before any query — same ordering as every other Epic 6 write/read endpoint | `content/service.py` |
| **UX-DR25: exactly one approved link per Skill, never a list** | Enforced server-side by `list_admin_lookup_content_for_skills`'s bulk query + the service's "keep only the last (most recent) row per skill_id" reduction — the frontend renders whatever single `approved_content` it's given, no client-side "pick the latest of several" logic | `content/repository.py`, `content/service.py` |
| **UX-DR29: approving from any tab closes the panel immediately** | One shared `ContentLookupPanel.handleApproved()` (`onClose()` then `onApproved(name)`), invoked identically by the Search tab's fresh `ResultCard` and by `ManualContentEntryForm`'s new additive `onApproved` hook | `ContentLookupPanel.tsx`, `ManualContentEntryForm.tsx` |
| **UX-DR33 / PRD Open Question 17: locked Skills have no content-sourcing entry point** | `SkillCard` renders only the 🔒 lock text for `ever_assigned=true`, no Edit/Delete/lookup control; the code review additionally closed an *unintended* back door into the same invariant via the "Use existing skill" hand-off, without inventing the *intended* entry point the UX spec itself still leaves undefined | `SkillCard.tsx`, `SkillsPage.tsx` |

---

## Key Technical Achievements

✅ **Found and closed a real, undocumented backend gap before writing any frontend code** — `GET /api/admin/skills` never existed, despite the epics AC's own text assuming it as a given dependency; discovered by a dedicated research agent reading the actual current source, not by trusting planning documents
✅ **Composed rather than rebuilt at every opportunity** — `ApiKeysModal`, `ContentPreviewModal`, `CurrentlyApprovedContent`, and `ManualContentEntryForm` were all reused exactly as Stories 6.5/6.7/6.9 had explicitly built them "ahead of" this story, with only one small, additive, backward-compatible change (`onApproved` on `ManualContentEntryForm`)
✅ **Three parallel research agents front-loaded exactly the risk this story's scale demanded** — UX/visual fidelity, real (not assumed) API contracts, and an inventory of reusable pieces — preventing the two most likely disasters for a story this size: reinventing already-shipped components, or building a frontend against an endpoint that didn't exist
✅ **Two independent adversarial review layers converged on the same real defect from different angles** (access-control framing vs. race-condition framing) — the "Use existing skill" lock-bypass — giving high confidence it was a genuine gap worth fixing, not a single reviewer's false positive
✅ **Code review correctly separated real defects from pre-existing, codebase-wide conventions** — 14 of 18 non-lock-bypass findings were dismissed as matching an already-shipped, identical pattern elsewhere in this codebase (imperative authorization, no client role gate, narrowed `useEffect` deps, generic error messages) rather than treated as blanket "issues," and one claimed finding was directly disproven by re-reading a passing test
✅ **Self-caught and immediately fixed an editing mistake during test authoring** — the exact category of risk ("an imprecise `Edit` match orphans a prior test's final assertion") Story 6.9's own Dev Notes had explicitly flagged as worth watching for, caught by the very first test run rather than shipped
✅ **Zero regressions across every full-suite run, on both stacks, at every stage** — backend held steady at 631 passed through the entire (frontend-only) patch round; frontend went 337 → 343 passed; `tsc --noEmit` returned to its exact 31-error baseline after one transient test-typing slip was caught and fixed
✅ **Honest gap disclosure instead of a false completeness claim** — explicitly recorded that the full interactive UI click-through was verified via 36 new automated component tests, not a live browser session, matching the same honest-disclosure pattern established throughout Epic 6

---

## Deferred Items (Not Story 6-10 Scope)

Logged in `_bmad-output/implementation-artifacts/deferred-work.md` under "Deferred from: code review of 6-10-skills-tab-frontend-card-grid-lookup-api-keys-watch-modal (2026-09-10)":

1. **Non-unique `data-testid`s across a rendered list and across composed components** — `ResultCard`'s test ids repeat across every candidate in a search result list, and collide again with `CurrentlyApprovedContent`'s own test ids when both sections render together. Zero end-user impact; test-tooling reliability only.
2. **`SkillsPage.refetch()` hides the whole grid behind a full error banner if it fails right after a successful mutation** — the admin's action already succeeded server-side, but a transient refetch failure loses the just-updated view until Retry succeeds.
3. **`ContentLookupPanel`'s `getApiKeysStatus()` failure is indistinguishable from "neither source configured"** — a transient fetch error disables both search checkboxes even if both are actually configured; recoverable by reopening the panel or checking the toolbar's own status.
4. **No message when a search completes with both source checkboxes unchecked** — the results area renders empty with no explanation.
5. **Duplicated `duration_hours` extraction expression** across `SkillCard.tsx`/`ContentLookupPanel.tsx` — matches this codebase's pre-existing tolerance for small duplicated per-component helpers.
6. **`GET /api/admin/skills`'s router-level test never exercises the multi-row-per-skill tie-break** — that behavior is unit-tested at the repository/service layers but not through the real HTTP contract the frontend consumes.

---

## Conclusion

Story 6-10 is **✅ DONE** after a research-then-create-then-implement cycle (three parallel research agents grounding the story in real UX/API/component truth) followed by one full adversarial code review pass — and it closes out **Epic 6 (Admin-Assisted Content Sourcing) in its entirety**:

- All acceptance criteria satisfied, including a real backend gap (`GET /api/admin/skills`) this story discovered and built from scratch — confirmed independently by a clean Acceptance Auditor pass against every AC and Scope Note
- Composed rather than rebuilt four already-shipped components from Stories 6.5/6.7/6.9, keeping the actual new surface area small relative to the feature's visible scope
- Two independent review layers converged on the same real access-control gap from different angles, giving high confidence in the fix rather than chasing a single reviewer's guess
- 4 patches applied from this story's own code review, all small and unambiguous; 14 other raised findings correctly dismissed as pre-existing codebase-wide patterns or a factual mix-up, not chased as blanket "issues"
- Zero regressions across every full-suite run, on both the backend and frontend stacks, through both the implementation and patch rounds
- 6 items deferred with clear "how to apply" notes, none blocking
- Live-verified via `curl` against rebuilt Docker containers, including the complete create → attach → list → reject → list cycle on the new endpoint
- One honestly-disclosed verification gap (interactive browser click-through) rather than an overclaimed "done," covered instead by 36 new automated component tests
- Not yet committed to git in this session

**Epic 6 status:** All 10 stories (6-1 through 6-10) are now `done`. Only the optional epic-6 retrospective remains.
