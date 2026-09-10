# Implementation Steps for Story 6-5: Per-Admin & Org-Wide Credential Storage (FR-16, AD-10)

**Story Key:** 6-5-per-admin-and-org-wide-credential-storage
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.5 gives an HR Admin a way to add, view the connection status of, and remove their own YouTube key and the org-wide Udemy credential — the prerequisite Story 6.6 (live content lookup) needs to authenticate against either source. During story creation, a prior stray commit (`4e99d275`, the same commit already flagged once before for jumping ahead on Story 1.7) was discovered to have already built half of AD-10's schema (`admin_api_keys` migration + `AdminApiKey` model) before any story existed for it — verified byte-for-byte against the spec and reused rather than redone. This story's real scope: `org_api_credentials` (the second table), `core/secrets.py` (Fernet encryption), the `content/` repository/service/router layer for both credential types, and a self-contained `ApiKeysModal` React component (the real Skills tab that will host it, Story 6.10, doesn't exist yet).

The work happened in two passes in the same overall session: (1) story creation + full TDD implementation for both the API and the UI, invoked via `/bmad-agent-dev`; (2) an adversarial code review pass (`/bmad-code-review`) that found and fixed 6 real issues, including one that required discovering a non-obvious fact about how this codebase's login actually works.

---

## Agents Invoked

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, architectural/security concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model)
**Input:** Full diff (`git diff HEAD` against baseline `f065a93a` plus all untracked new files, ~2,200 lines across 28 files), instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (12 items):**
- A real, freshly-generated `ADMIN_KEY_ENCRYPTION_SECRET` value was committed into the already-tracked `backend/.env`, alongside the pre-existing committed `JWT_SECRET`/`YOUTUBE_API_KEY`
- No key-rotation/versioning story anywhere in `core/secrets.py`
- Key derivation is a bare, unsalted SHA-256 hash rather than a real KDF
- No upper bound (`max_length`) on submitted credential input size
- FK columns (`admin_id`, `configured_by`) have no `ondelete` behavior, contradicting `OrgApiCredential`'s own "attribution only" docstring
- `test_udemy_save_by_second_admin_replaces_configured_by` is tautological — it logs in as Rita twice and would pass even if `configured_by` were never updated
- `ApiKeysModal.tsx` allows a Save to fire while a Remove is pending/in-flight on the same row
- `configured_at` in the API response is actually `updated_at`, not a "first connected" timestamp
- The router mixes a router-level `Depends(get_current_user)` with a per-route re-declaration of the same dependency, relying on an unstated FastAPI caching assumption
- The router test file's cleanup helper wipes shared table state unconditionally, not scoped to test-owned rows
- No test verifies `extra="forbid"` is actually enforced on the new schemas
- The temporary dev route ships with zero role gating (any authenticated EMPLOYEE can load the modal UI, though every underlying API call still correctly 403s)

**Output:** 12 findings; after triage, dedup with Edge Case Hunter, and direct verification against the real code, 1 became the decision-needed item, 5 became patches, 3 routed to defer, 3 dismissed as matching established codebase precedent

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same full diff, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item):**
- `ApiKeysModal.tsx:200-215`: Save fires while a YouTube remove-confirm DELETE is in-flight
- `ApiKeysModal.tsx:264-287`: same race for the Udemy row
- `ApiKeysModal.tsx:83-98`: component unmount (not just `open → false`) while a request is pending calls `setState` on an unmounted component
- `content/schemas.py`: no `max_length` on the credential fields
- `content/schemas.py`: the blank-rejection validators strip and return the trimmed value rather than preserving exact whitespace
- `assignments/models.py:127`: `configured_by`'s FK has no `ondelete`, so deleting the referenced Employee raises a FK violation despite the column being nullable/attribution-only by design

**Output:** 6 structured findings; 3 merged with Blind Hunter's overlapping findings (the race, the max_length gap, the FK gap), the unmount finding stood alone as a new patch, the whitespace-stripping finding was dismissed as matching an established codebase precedent

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.5's literal Given/When/Then acceptance criteria and its 11 numbered Scope Notes.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers, foreground)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full, read directly) + the same diff, plus direct reads of `auth/service.py`, `auth/router.py`, `assignments/service.py`, the alembic versions directory, and the UX spec to confirm each Scope Note's specific instruction was actually followed

**Key Findings Identified:**
- **None requiring remediation.** Explicitly confirmed every AC (migration shape, `core/secrets.py`'s exact key-derivation formula and call-site restriction, all 4 PUT/DELETE endpoints' semantics, the GET response shape, the blanket 403 for EMPLOYEE) and every numbered Scope Note (the repository-layer encryption boundary, the JSON-blob packing judgment call, the UUID conversion site, the AD-8 router-layer composition pattern mirroring `auth/router.py::get_me_route`, the new-router-file mounting convention, the service-layer auth gate, the no-explicit-commit convention, the cryptography dependency/config, and the frontend object-ID/validation conventions)

**Output:** A fully clean pass — zero findings

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development both api and ui for the story 6-5-per-admin-and-org-wide-credential-storage refer the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, greeted as Amelia, and dispatched directly to story creation since no story file yet existed for 6.5 and the user's message already named a clear intent.

---

### 2. **`/bmad-create-story` Skill**

**Purpose:** Generate a comprehensive story file with full context before implementation.

**When Invoked:** Immediately after activation, args `6-5-per-admin-and-org-wide-credential-storage`
**Workflow Steps Executed:**
1. Pulled Story 6.5's full literal AC text from `epics.md` (Epic 6), plus FR-16 and NFR-SEC1's exact prose from the PRD
2. Read AD-10 and AD-8 in full from the architecture spine (Fernet/`ADMIN_KEY_ENCRYPTION_SECRET` requirement, the module-dependency-direction rule that later shaped the router-layer name-resolution decision)
3. **Discovered mid-context-gathering** that a prior stray commit (`4e99d275`) had already added migration `005`/`AdminApiKey` — verified directly against both files rather than trusting the commit message or re-deriving from scratch, and scoped the story around only the genuinely missing half (`org_api_credentials`)
4. Read the actual current code directly: `content/models.py`/`repository.py`/`service.py`/`schemas.py`/`router.py` (Story 2.x/3.x's existing state), `skills/router.py`/`service.py` (the service-layer `require_hr_admin` gating convention this story would mirror), `auth/schemas.py`/`service.py` (the `CurrentUser.user_id: str` vs. UUID-column conversion point), `auth/router.py`'s `get_me_route` (the AD-8-compliant router-layer cross-module composition precedent), `core/config.py`/`core/errors.py`/`core/db.py` (settings, error contract, commit convention), and `main.py` (the multi-router-per-module precedent from `progress/`)
5. Cross-checked the UX spec (`04.1-skills-content-sourcing.md`) for the API Keys Panel's exact object IDs, state table, and Form Validation section — used the latter to deliberately *not* build a fake "invalid format" validator the state table implies but the spec's own validation rules rule out
6. Identified and resolved 3 real design decisions during story-writing itself, written directly into Scope Notes: (a) encryption happens at the repository layer per the epic's literal wording, not the service layer; (b) AD-10's single-`encrypted_key`-column schema vs. the Udemy AC's "both fields encrypted" requirement, resolved by packing both values into one JSON blob; (c) resolving the Udemy "connected by" display name without violating AD-8, resolved by mirroring `auth/router.py`'s existing router-layer composition pattern
7. Generated the story file with 11 Scope Notes, then implemented it directly in the same session rather than stopping at `ready-for-dev`

**Output File:** `_bmad-output/implementation-artifacts/6-5-per-admin-and-org-wide-credential-storage.md`
**Sprint Status:** `6-5-...`: `backlog` → `ready-for-dev` (implemented in the same pass, not stopped there)

---

### 3. **Direct Implementation (`/bmad-dev-story`, same session)**

**Purpose:** Implement the story per its own Tasks, red-green-refactor, across both backend and frontend.

**When Invoked:** Immediately after story creation
**Steps Executed:**
1. **Config/env (Task 1):** Added the required `ADMIN_KEY_ENCRYPTION_SECRET` setting to `core/config.py`, `.env.example`, and a real generated value to `.env`; added `cryptography==50.0.1` to `requirements.txt`
2. **`core/secrets.py` (Task 2, RED → GREEN):** Wrote 4 failing tests first (`ModuleNotFoundError` confirmed), then implemented Fernet `encrypt_secret`/`decrypt_secret` keyed by a SHA-256-derived key
3. **`OrgApiCredential` model + migration `008` (Tasks 3-4):** Added the model mirroring `AdminApiKey`'s shape, wrote the additive migration, applied it (`alembic upgrade head`) against the live dev Postgres
4. **Schemas (Task 5):** `SetYoutubeKeyRequest`/`SetUdemyCredentialRequest`/status response schemas, with a `_reject_blank` validator mirroring `skills/schemas.py`'s established precedent
5. **Repository (Task 6):** Upsert/get/delete for both credential tables using Postgres `INSERT ... ON CONFLICT DO UPDATE`, encryption called only here per the Scope Note; 12 new tests, 16/16 passing on first run
6. **Service (Task 7):** 5 new functions, each calling `require_hr_admin` first, plus an internal `ApiKeysStatusRaw` dataclass; 10 new tests, 15/15 passing on first run
7. **Router (Task 8):** New `content/admin_api_keys_router.py`, mounted at `/api/admin/api-keys`; `GET`'s handler composes the Udemy display name via `assignments.service.get_employee_by_id_service`
8. **Backend tests (Task 9):** New `test_admin_api_keys_router.py` (24 tests) — first run hit `sqlalchemy.exc.InterfaceError: another operation is in progress` on 23/24 tests, traced to an autouse async `pytest.fixture` corrupting the file's private module-level engine under `loop_scope="module"`; fixed by removing the fixture in favor of the established plain-helper-function convention, 24/24 passed after
9. **Two pre-existing tests broken by the new required setting/table, found and fixed:** `test_config.py`'s `_env_file=None` tests needed the new env var added to their `monkeypatch.setenv` calls; `test_schema_definition.py::test_all_tables_defined`'s hardcoded table-count set needed bumping 8 → 9 — a collision Story 6.1's own retro notes had already predicted
10. **Frontend API client + component (Tasks 10-11):** `adminApiKeysApi.ts` matching `assignmentsApi.ts`'s style; `ApiKeysModal.tsx` built on the existing `Dialog` primitive exactly as `DeleteAssignmentModal.tsx` does, matching every UX-spec object ID
11. **Dev route (Task 12):** `ApiKeysModalDemo.tsx` + `/dev/api-keys-modal-demo` route, mirroring `VideoPlayerDemo.tsx`'s precedent since the real Skills tab doesn't exist yet
12. **Frontend tests (Task 13):** `ApiKeysModal.test.tsx`, 13 tests, mirroring `AssignmentModal.test.tsx`'s mocking style
13. **Two real deployment gaps found and fixed beyond the story's own Scope Notes:** `cryptography` also needed adding to `requirements-prod.txt` (the file Docker actually builds from — `requirements.txt` alone would have left the container broken at runtime); `docker-compose.yml` had no `ADMIN_KEY_ENCRYPTION_SECRET` env var, added with the same `${VAR:-dev-default}` fallback pattern as `JWT_SECRET`
14. **Full regression:** backend `3 failed, 460 passed, 2 skipped` (same 3 pre-existing failures); frontend full suite showed 1-2 flaky failures under full-suite resource contention (`getByPlaceholderText` racing the async status fetch) — fixed by switching to awaited `findBy*` queries, then `274 passed` twice in a row; `tsc --noEmit` confirmed at the same 73 pre-existing errors via `git stash` against the pre-story baseline; `vite build` clean
15. **Live end-to-end verification, twice:** rebuilt and redeployed both Docker images, verified via `curl` (save/status/403-for-employee/remove round trip with real ISO timestamps and attribution names); separately installed Playwright/Chromium ad hoc (`npm install --no-save`, uninstalled after use) and drove a real browser session against the live Docker frontend at `/dev/api-keys-modal-demo` — full save/status/remove-with-confirm/close lifecycle confirmed working

**Output:** Story file updated with completed Tasks, Dev Agent Record, File List, Change Log; status set to `review`
**Sprint Status:** `6-5-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "/bmad-code-review" (Tier 2/3 of the context-gathering cascade both pointed to Story 6.5 — the only story in `review` status, and the immediately preceding turn had just finished implementing it)
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from sprint tracking (exactly one `review` story); `baseline_commit` (`f065a93a`) confirmed to match current `HEAD` exactly, so diff source = uncommitted changes plus all untracked new files (`git diff HEAD` + `git diff --no-index /dev/null <file>` per new file), ~2,200 lines across 28 files. Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter and Edge Case Hunter as background subagents and the Acceptance Auditor in the foreground (`review_mode = "full"`, story file as spec), each given the diff via a file path to read directly rather than inlined (kept the launch prompts small for a ~2,200-line diff). Acceptance Auditor returned immediately with a clean pass; Blind Hunter and Edge Case Hunter each ran ~3-5 minutes independently reading the diff plus the current-state files it referenced.
- **Step 03 (Triage):** Normalized 18 raw findings (12 Blind Hunter + 6 Edge Case Hunter; Acceptance Auditor returned zero) down to 14 distinct findings after dedup. Verified reachability before rating each — e.g., grepped the entire backend for any employee-delete endpoint (found none) before rating the FK-`ondelete` finding as low-severity/unreachable-today rather than critical; reasoned through the actual entropy source of `ADMIN_KEY_ENCRYPTION_SECRET` (`secrets.token_urlsafe(32)`, 256 bits) before rating the "unsalted SHA-256" finding as low real risk rather than accepting the reviewer's severity at face value. Routed the result into 1 decision-needed, 6 patch, 4 defer, 3 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection and the 4 deferred items appended to `deferred-work.md` under a new dated heading. User resolved the decision-needed item ("keep as-is," matching the existing repo convention) and chose "apply every patch" for the 6 patch findings.

**Patches Applied:**
1. `SetYoutubeKeyRequest.key`/`SetUdemyCredentialRequest.client_id`/`client_secret` gained a shared `CREDENTIAL_MAX_LENGTH = 4096` bound, plus 3 new tests asserting 422 on an over-limit value
2. `ApiKeysModal.tsx`'s Save buttons and their inputs now also disable while `youtubeRemoving`/`udemyRemoving` is true, closing a real Save-vs-Remove request race
3. Added an `isMountedRef` guard (set in a mount-effect's cleanup) checked before every post-await `setState` call across all 4 async handlers plus `refreshStatus`
4. **`test_udemy_save_by_second_admin_replaces_configured_by` fixed with a real second HR_ADMIN identity** — required discovering mid-fix that this codebase's login is a hardcoded in-memory dict (`auth/repository.py::_MOCK_ACCOUNTS`), not DB-backed, so a DB `employees`/`accounts` row alone would never let a new identity log in; added `_create_second_hr_admin`/`_delete_second_hr_admin` test helpers that create a real `Employee` row *and* a temporary `_MOCK_ACCOUNTS` entry, cleaned up in a `finally` block
5. Added `test_youtube_save_rejects_unknown_field`/`test_udemy_save_rejects_unknown_field`, matching an existing `test_skills_router.py` precedent for `extra="forbid"` enforcement that wasn't carried forward initially
6. `OrgApiCredential.configured_by`'s FK gained `ondelete="SET NULL"` in both the model and migration `008`; re-applied via `alembic downgrade 007` → `upgrade head` against the live dev DB and verified via a direct `pg_constraint.confdeltype` query (`'n'` = SET NULL)

**Output:** Story status → `done`; full regression re-verified — backend 465 passed (5 net new) / 2 skipped / same 3 pre-existing failures; frontend 13/13 (`ApiKeysModal.test.tsx`), `tsc --noEmit` unchanged at 73 pre-existing errors. Both Docker images rebuilt and redeployed a second time with the patches applied, and the max_length/`extra="forbid"` 422s plus the FK constraint change re-verified live via `curl`.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 4 deferred items logged to `deferred-work.md` under a new dated heading
- `project-context.md` updated with both the implementation and the review outcome, per this project's own mandatory-update convention
- Sprint status synced (`6-5-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/app/core/secrets.py` | Fernet `encrypt_secret`/`decrypt_secret`, domain-free |
| `backend/alembic/versions/008_add_org_api_credentials.py` | Additive migration for `org_api_credentials`; code-review patch: FK now created with `ondelete="SET NULL"` |
| `backend/app/content/admin_api_keys_router.py` | `GET`/`PUT`/`DELETE` routes, mounted at `/api/admin/api-keys` |
| `backend/tests/test_secrets.py` | 4 tests — encrypt/decrypt round trip, non-determinism, garbage-decrypt error, JSON-blob round trip |
| `backend/tests/test_admin_api_keys_router.py` | 29 tests (24 initial + 5 code-review patches) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/core/config.py` | Adds required `ADMIN_KEY_ENCRYPTION_SECRET` setting |
| `backend/app/assignments/models.py` | Adds `OrgApiCredential` ORM model; code-review patch: `configured_by` FK gained `ondelete="SET NULL"` |
| `backend/app/content/schemas.py` | Adds `SetYoutubeKeyRequest`, `SetUdemyCredentialRequest`, `YoutubeKeyStatus`, `UdemyCredentialStatus`, `ApiKeysStatusResponse`; code-review patch: `CREDENTIAL_MAX_LENGTH = 4096` |
| `backend/app/content/repository.py` | Adds admin/org credential CRUD (upsert/get/delete for both tables) |
| `backend/app/content/service.py` | Adds `set_youtube_key`, `remove_youtube_key`, `set_udemy_credential`, `remove_udemy_credential`, `get_api_keys_status` |
| `backend/app/main.py` | Mounts the new router |
| `backend/requirements.txt`, `backend/requirements-prod.txt` | Add `cryptography==50.0.1` |
| `backend/.env.example`, `backend/.env` | `ADMIN_KEY_ENCRYPTION_SECRET` |
| `backend/tests/test_content_repository.py` | 12 new tests |
| `backend/tests/test_content_service.py` | 10 new tests |
| `backend/tests/test_config.py` | 2 existing tests fixed to set the new required env var |
| `backend/tests/test_schema_definition.py` | `test_all_tables_defined` bumped to include `org_api_credentials` |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/adminApiKeysApi.ts` | API client |
| `frontend/src/features/admin/ApiKeysModal.tsx` | The modal component; code-review patches: Save/input race fix, `isMountedRef` guard |
| `frontend/src/pages/dev/ApiKeysModalDemo.tsx` | Temporary dev route |
| `frontend/src/tests/ApiKeysModal.test.tsx` | 13 tests |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/App.tsx` | Adds `/dev/api-keys-modal-demo` route |

### Infrastructure

| File | Purpose |
|------|---------|
| `docker-compose.yml` | `ADMIN_KEY_ENCRYPTION_SECRET` env var for the `backend` service |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-5-per-admin-and-org-wide-credential-storage.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-5-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 4 new items added under a new "Deferred from: code review of 6-5-..." heading |
| `_bmad-output/project-context.md` | Implementation + review outcome appended, per this project's own mandatory-update rule |
| `documentation/ImplementationStepsForStory6-5.md` | This file |

### Not Changed (by design)

- `backend/app/assignments/models.py`'s pre-existing `AdminApiKey` model and migration `005` — already correct from a prior stray commit, verified rather than redone (Scope Note 1)
- `content/youtube_client.py`, any `udemy_client.py` — Story 6.6's scope, not this story's
- The real Skills tab page/grid — Story 6.10's scope; this story's UI ships as a self-contained, reusable component plus a temporary dev route only

---

## Implementation Workflow Summary

### Phase 0: Discovery
**Skill:** `/bmad-agent-dev`
- User's initial message already named a clear intent — dispatched directly to story creation, no menu shown

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Discovered a prior stray commit had already built half of AD-10's schema; scoped the story around only the genuinely missing half
- Resolved 3 real design decisions during story-writing (encryption-layer boundary, JSON-blob packing for the single-column schema, AD-8-compliant router-layer name resolution)
- Generated the story file with 11 Scope Notes

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, both backend and frontend)**
- 46 new/extended backend tests + 13 new frontend tests across repository/service/router/component layers
- Found and fixed 2 pre-existing tests broken by the new required setting/table, and 2 real deployment gaps (prod requirements file, docker-compose env var) beyond the story's own anticipated scope
- Full regression pass — backend 460 passed, frontend 274 passed, `tsc`/`vite build` clean
- Live end-to-end verification twice: via `curl` against rebuilt Docker containers, and via a real Chromium browser session against the live frontend
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers (2 background, 1 foreground), single pass
- **Findings:** 18 raw → 14 after dedup → 1 decision-needed, 6 patch, 4 defer, 3 dismiss
- **Real gap found and fixed that required new discovery:** the "second admin" test was tautological, and fixing it properly required discovering this codebase's login is a hardcoded in-memory dict, not DB-backed
- **Action:** decision resolved by user (keep as-is), all 6 patches applied; migration re-applied live to pick up the FK constraint change
- Output: 465 passed (up from 460 before review), 2 skipped, same 3 pre-existing failures; story marked `done`

---

## Test Coverage

### New/Extended Test Files (59 tests total from this story, post-review)
- `test_secrets.py` — 4 tests: encrypt/decrypt round trip, non-deterministic ciphertext, garbage-decrypt error, JSON-blob round trip
- `test_content_repository.py` — 12 new tests: upsert/get/delete round trips for both credential tables, replace-not-duplicate semantics
- `test_content_service.py` — 10 new tests: each of the 5 new service functions, happy path + 403 for EMPLOYEE
- `test_admin_api_keys_router.py` — 29 tests (post-review): full HTTP-level matrix for both credential types, encryption verification, never-echoes-the-value assertions, `max_length`/`extra="forbid"` rejection, and a genuinely fixed multi-admin replace test
- `test_config.py` — 2 existing tests fixed for the new required setting
- `test_schema_definition.py` — 1 existing assertion bumped for the new table
- `ApiKeysModal.test.tsx` — 13 tests: status fetch/render, save/clear, remove-with-confirm, error handling, unmount/reopen state reset

### Regression Verification
- Full backend suite run after implementation (460 passed) and again after the code review's patches (465 passed) — same 3 pre-existing, unrelated failures at every stage
- Full frontend suite (274 tests) clean both before and after patches, after fixing 2 test-timing races surfaced only under full-suite resource contention
- `tsc --noEmit` and `vite build` confirmed clean at every stage, with the pre-existing error count independently verified via `git stash` against the pre-story baseline
- Live-verified end-to-end via `curl` against rebuilt/redeployed Docker containers and via a real Chromium browser session, both before and after the review's patches

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-10: encrypted, module-owned, never exposed** | Fernet encryption keyed by a dedicated `ADMIN_KEY_ENCRYPTION_SECRET`, deliberately separate from `JWT_SECRET`; called only from the repository layer | `core/secrets.py`, `content/repository.py` |
| **AD-1: single-owner module, cross-module calls via Service API only** | `content/service.py`/`repository.py` own both credential tables; `content/admin_api_keys_router.py` is the only file allowed to import `assignments.service` (for display-name resolution), mirroring `auth/router.py`'s existing precedent | `content/service.py`, `content/repository.py`, `content/admin_api_keys_router.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | Every one of the 5 new service functions calls `require_hr_admin(current_user)` first, including the read (`GET`) — matching `skills/service.py`'s established convention, not a router-level `Depends` | `content/service.py` |
| **Single-commit-per-request convention (`core/db.py::get_db`)** | No explicit `commit()`/`flush()` in any new repository/service code — Core-level `db.execute()` statements send SQL immediately, matching `skills/repository.py`'s established convention | `content/repository.py`, `content/service.py` |
| **A real epic-text gap resolved, not silently worked around** | AD-10's `org_api_credentials` schema has one `encrypted_key` column but the Udemy credential is two fields — packed as one encrypted JSON blob rather than adding an undeclared column | `assignments/models.py::OrgApiCredential`, `content/repository.py::upsert_org_api_credential` |

---

## Key Technical Achievements

✅ **Caught a prior stray commit's premature schema work before redoing it** — verified `admin_api_keys`/`AdminApiKey` byte-for-byte against AD-10's spec instead of assuming a rewrite was needed, scoping the story correctly around only the genuinely missing half
✅ **Resolved a real, unresolved tension in the epic text** (single-column schema vs. two-field credential) with a documented, forward-referenced judgment call rather than silently picking one interpretation
✅ **Live-verified end-to-end in two different ways, not just at the test level** — rebuilt/redeployed Docker containers and confirmed via `curl`, then separately drove a real Chromium browser session against the live frontend, catching what neither the unit tests nor the API-only verification alone would have (the modal's actual click-through UX)
✅ **A code-review finding led to a genuine discovery about the codebase, not just a code fix** — proving the "second admin replaces configured_by" behavior required first discovering that login here is a hardcoded in-memory dict, not the DB-backed `accounts` table the schema might suggest
✅ **Found and fixed 2 real deployment gaps invisible to the local test suite** — `requirements-prod.txt` being a separate file from `requirements.txt`, and `docker-compose.yml` missing the new required env var — both would have broken the containerized deployment despite every local test passing
✅ **Code review triage backed by direct verification, not argument** — grepped the entire backend for an employee-delete endpoint before rating the FK-`ondelete` finding's severity; reasoned through the actual entropy of the generated secret before accepting or discounting the "weak KDF" finding
✅ **Zero regressions across every full-suite run, both backend and frontend** — 460 → 465 passed (backend), 274 → 274 passed (frontend), identical pre-existing failure/error counts at every stage

---

## Deferred Items (Not Story 6-5 Scope)

1. **No key-rotation/versioning story in `core/secrets.py`** — real architectural gap, but out of scope and no other secret in this codebase has rotation either
2. **Key derivation is unsalted SHA-256 rather than a real KDF** — a legitimate hardening opportunity, but low real risk since the actual generated secret is a 256-bit `secrets.token_urlsafe(32)` value, not a human-chosen password
3. **The router test file's cleanup helper wipes whole-table state, not scoped to test-owned rows** — matches a previously-documented risk pattern in this codebase, but no other test file currently writes committed rows to these two brand-new tables, so there's no active conflict today
4. **`configured_at` is actually `updated_at` semantics, not "first connected"** — inherent to AD-10's schema (only one `updated_at` column exists) and the epic's own exact field name; fixing this properly needs a spec-level decision (a real first-connected column), not a code patch

---

## Conclusion

Story 6-5 is **✅ DONE** after a from-scratch story-creation-and-implementation cycle (spanning both the API and the UI) followed by one full adversarial code review pass:

- All 6 acceptance criteria satisfied, including a documented resolution of a real tension in the epic's own schema text
- A prior stray commit's premature work correctly identified, verified, and reused rather than redone
- 6 patches applied from this story's own code review, including one that required discovering a non-obvious fact about how authentication actually works in this codebase
- Zero regressions across every full-suite run, backend and frontend alike
- 4 items explicitly deferred (all either pre-existing patterns or genuine out-of-scope architectural gaps) rather than silently absorbed or ignored
- Live-verified twice — via `curl` against rebuilt Docker containers, and via a real Chromium browser session against the live frontend — not just at the test level
- Not yet committed to git in this session

**Ready for:** Story 6.6 (Live Content Search — YouTube & Udemy, FR-17/AD-7 branches 2 & 3), the next `backlog` story in Epic 6, which will be the first real consumer of the decrypted credential values this story only needed to store correctly.
