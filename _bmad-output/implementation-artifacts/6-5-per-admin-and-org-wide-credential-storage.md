---
baseline_commit: f065a93a
---

# Story 6.5: Per-Admin & Org-Wide Credential Storage (FR-16, AD-10)

Status: done

## Story

As an **HR Admin**,
I want to add, view the connection status of, and remove my own YouTube key and the shared Udemy credential,
so that live content lookup (Story 6.6) has something to authenticate with, without ever seeing a previously-saved secret again.

## Scope Notes (read before starting)

1. **A stray early commit already built half of this story's schema — do not redo it, extend it.** Commit `4e99d275` ("Migration done for the Skill tab", 2026-09-08 — the same kind of premature/get-ahead commit the project has already flagged once before for Story 1.7) added `backend/alembic/versions/005_add_admin_api_keys.py` and `AdminApiKey` (in `backend/app/assignments/models.py`) **before this story was ever created**. Verified directly against both files: the table/model already exactly match AD-10's spec (`id`, `admin_id` FK→`employees.id`, `source`, `encrypted_key`, `created_at`/`updated_at`, `UNIQUE(admin_id, source)`). **Do not write a new migration for `admin_api_keys` or touch `AdminApiKey`** — it's correct and done. This story's only new migration is `org_api_credentials` (AC1's second table). No `core/secrets.py`, no config setting, no repository/service/router code exists yet for either table — that's all this story's real scope.
2. **`core/secrets.py` encrypts/decrypts at the repository layer, not the service layer.** The epic AC says `core/secrets.py` is "called only from `content/repository.py`, never from a router" — it does not say service. Follow that literally: `content/service.py`'s new functions pass plaintext straight through to `content/repository.py`, and the repository functions call `encrypt_secret`/`decrypt_secret` internally before/after touching the DB. This mirrors `skills/service.py`'s existing pattern of keeping DB-shape concerns (there: the conditional-UPDATE idempotency; here: encryption) inside the repository, with the service layer only handling auth + orchestration.
3. **AD-10's `org_api_credentials` schema has only one `encrypted_key` column, but the Udemy AC requires storing both `client_id` and `client_secret` encrypted.** This is a real gap in the epic text (compare the schema list in AC1 against AC3's "both fields encrypted" wording) — resolved here, not silently worked around: pack `{"client_id": ..., "client_secret": ...}` as a JSON string and Fernet-encrypt the whole blob into the single `encrypted_key` column. This satisfies "both fields encrypted" (they're both inside the one encrypted blob) without adding a column AD-10 never specified. Document this exact judgment call in code (a docstring on the repository's upsert function and/or the `OrgApiCredential` model), since a future reader diffing this table against AD-10 will otherwise wonder where the second column went.
4. **`admin_id` / `configured_by` are UUID columns; `CurrentUser.user_id` is a `str`.** Every write/read against these tables needs `uuid.UUID(current_user.user_id)` — same conversion `auth/router.py::get_me_route` already does (`backend/app/auth/router.py:36`). Forgetting this raises a type/adapter error at the DB driver level, not a validation error, so get it right in `content/service.py`'s new functions, not deep in a repository call site.
5. **Resolving the Udemy row's "connected by {Admin name}" display name requires reading `employees`, which `content/` may never depend on directly (AD-8: skills/ and content/ never depend back on assignments/).** There is already exactly one precedent for this exact composition problem in this codebase: `auth/router.py::get_me_route` resolves its own display name by importing `app.assignments.service.get_employee_by_id_service` **at the router layer**, not inside `auth/service.py`. Do the same here — `content/service.py::get_api_keys_status` returns a raw status object with `udemy_configured_by_id: UUID | None` (no name), and the new admin-api-keys router composes the final response by calling `get_employee_by_id_service` itself when that id is present. Do not import `assignments` anywhere inside `content/service.py` or `content/repository.py`.
6. **New router file, not an addition to the existing `content/router.py`.** `content/router.py` is mounted at `/api/content` (Story 3.4's `GET /match`); these endpoints live at `/api/admin/api-keys/*` (a different prefix, admin-only). This codebase already has a precedent for one module owning two separately-mounted router files — `progress/router.py` (mounted with a `tags` prefix) and `progress/my_assignments.py` (mounted separately under `/api`, `backend/app/main.py:43-45`). Create `backend/app/content/admin_api_keys_router.py`, mount it in `main.py` as `app.include_router(admin_api_keys_router, prefix="/api/admin/api-keys", tags=["admin-api-keys"])`.
7. **HR_ADMIN gating is a service-layer call, not a router-level `Depends`**, matching every other admin-gated module in this codebase (`skills/service.py`'s `require_hr_admin(current_user)` calls inside `create_skill_service`/`update_skill_service`/`delete_skill_service`). Every one of this story's five new service functions (`set_youtube_key`, `remove_youtube_key`, `set_udemy_credential`, `remove_udemy_credential`, `get_api_keys_status`) calls `require_hr_admin(current_user)` as its first line — the AC's blanket "an EMPLOYEE session calling **any** `/api/admin/api-keys/*` endpoint gets 403" includes the `GET`, so don't skip the gate there just because it's a read.
8. **No explicit `db.commit()` anywhere in this story's new code.** `core/db.py::get_db` commits once, automatically, after the route handler returns (documented convention, already the pattern Story 6.2/6.3's `skills/service.py` follows). `content/service.py`'s older `manual_seed_content`/`ingest_content_for_skill` call `db.commit()` explicitly only because those are also invoked directly from the CLI (`content/cli.py`) outside any `get_db`-managed request — that's not a general pattern to copy, it's specific to those two CLI-reachable functions. This story's functions are only ever reached through a route, so follow the newer `skills/service.py` convention: Core-level `db.execute(...)` statements need no `flush()` either (same reasoning as Story 6.4's code review, which removed a no-op `flush()` after a bare Core `UPDATE`).
9. **Cryptography note:** `cryptography` was not previously a project dependency (verified: absent from `backend/requirements.txt` and from `backend/.venv`). It has already been installed into `backend/.venv` for this story (`cryptography==50.0.1`) — add the exact same pin to `requirements.txt` so a fresh environment matches. `ADMIN_KEY_ENCRYPTION_SECRET` is a new **required** `core/config.py` setting (no default, deliberately separate from `JWT_SECRET` per AD-10) — `Settings()` will fail fast (existing `load_settings()` behavior) if it's missing, so it must be added to both `backend/.env.example` (placeholder + comment) and the real `backend/.env` (a real random value) before the app or tests can run. A Fernet key must be exactly 32 url-safe-base64 bytes; `ADMIN_KEY_ENCRYPTION_SECRET` is an arbitrary-length string like `JWT_SECRET`, not a ready-made Fernet key — derive one deterministically (`base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())`) inside `core/secrets.py`, don't require the operator to hand-generate a real Fernet key.
10. **No UI page exists yet to host this modal.** The full Skills tab (card grid, toolbar, "Manage API Keys" trigger button) is Story 6.10 — not built yet, and out of scope here. Build the API Keys modal itself as a self-contained, reusable component per the UX spec's object IDs (`04.1-skills-content-sourcing.md` §"API Keys Panel (Modal)") so Story 6.10 can drop it in directly, and add a temporary dev-only route to exercise it manually — this codebase already has exactly this precedent (`pages/dev/VideoPlayerDemo.tsx`, built and routed ahead of the page that would eventually host it, Story 1.8). Do not build the Skills grid, Content Lookup, or Watch modal — those are separate, later stories.
11. **Per the UX spec's own Form Validation section** (`04.1-skills-content-sourcing.md` §"Form Validation & Requirements" → "API Keys"): "YouTube key: required non-empty string to save; no further format validation... real validation happens at first search" and "Udemy credential: client ID + client secret, both required non-empty." There is no real format check to build — only a non-blank check, client-side (disable Save on blank input) and server-side (schema validator rejecting blank/whitespace-only, mirroring `skills/schemas.py::_reject_blank`). The UX spec's "Save error — invalid format" state table row describes a *hypothetical* format check this project's own Form Validation section says doesn't exist for this story — do not build a fake format validator or a "[Learn more]" link just to satisfy that row; a real invalid/revoked credential surfaces its error at first search (Story 6.6), not here.

## Acceptance Criteria

**Given** neither table exists yet
**When** I write a new Alembic migration
**Then** it creates both tables from AD-10:
- `admin_api_keys`: `id` (UUID PK), `admin_id` (UUID, FK → `employees.id`), `source` (text), `encrypted_key` (text), `created_at`/`updated_at` (timestamptz) — `UNIQUE(admin_id, source)`
- `org_api_credentials`: `id` (UUID PK), `source` (text), `encrypted_key` (text), `configured_by` (UUID, nullable FK → `employees.id`), `created_at`/`updated_at` (timestamptz) — `UNIQUE(source)`

*(Scope Note 1: `admin_api_keys` already exists, byte-for-byte matching this spec, from a prior stray commit — only `org_api_credentials` is a new migration in this story.)*

**And** the migration is purely additive (two new tables, no existing table touched) — no backfill needed, since no credentials have ever existed before this story

**Given** the two new tables from AD-10 (now created by this story's own migration, above)
**When** I implement `core/secrets.py`
**Then** it provides `encrypt_secret(plaintext: str) -> str` / `decrypt_secret(ciphertext: str) -> str` using **Fernet** symmetric encryption (`cryptography` lib), keyed by a new required setting `ADMIN_KEY_ENCRYPTION_SECRET` (`core/config.py`) — deliberately separate from `JWT_SECRET` (AD-10) — and this module is generic/domain-free, called only from `content/repository.py`, never from a router

**Given** I am authenticated as HR_ADMIN
**When** I call `PUT /api/admin/api-keys/youtube` with `{ key: str }`
**Then** my own `admin_api_keys` row (`admin_id` = my session identity, `source = "YOUTUBE"`) is created or replaced (encrypted via `core/secrets.py`), and `204 No Content` is returned — the key itself is never echoed back

**Given** I am authenticated as HR_ADMIN
**When** I call `PUT /api/admin/api-keys/udemy` with `{ client_id: str, client_secret: str }`
**Then** the single `org_api_credentials` row (`source = "UDEMY"`) is created or replaced (both fields encrypted, `configured_by` = my session identity), regardless of which Admin configured it before me — this is deliberately org-wide, not scoped to my own admin identity (AD-10)

**Given** either credential type
**When** I call `GET /api/admin/api-keys`
**Then** the response is `{ youtube: { configured: bool }, udemy: { configured: bool, configured_by: str | null, configured_at: str | null } }` — **never** the encrypted or decrypted key/secret value, in any field, under any condition

**Given** either credential type
**When** I call `DELETE /api/admin/api-keys/youtube` or `DELETE /api/admin/api-keys/udemy`
**Then** the corresponding row is deleted and `204 No Content` returned; a subsequent `GET` shows `configured: false`

**Given** an EMPLOYEE session
**When** it calls any `/api/admin/api-keys/*` endpoint
**Then** `403 Forbidden` (AD-6)

## Tasks / Subtasks

- [x] Task 1: `core/config.py` + env files — `ADMIN_KEY_ENCRYPTION_SECRET` setting (AC2, Scope Note 9)
  - [x] Add `ADMIN_KEY_ENCRYPTION_SECRET: str` (required, no default) to `Settings`
  - [x] Add a placeholder + comment to `backend/.env.example`; add a real random value to `backend/.env`
  - [x] Add `cryptography==50.0.1` to `backend/requirements.txt` (already installed in `.venv` for this story)
- [x] Task 2: `core/secrets.py` (NEW) — Fernet encrypt/decrypt (AC2, Scope Note 9)
  - [x] `encrypt_secret(plaintext: str) -> str` / `decrypt_secret(ciphertext: str) -> str`, key derived via `base64.urlsafe_b64encode(hashlib.sha256(settings.ADMIN_KEY_ENCRYPTION_SECRET.encode()).digest())`
  - [x] Domain-free — no imports from `content/`, `skills/`, or any router
- [x] Task 3: `assignments/models.py` — add `OrgApiCredential` ORM model (AC1)
  - [x] Mirrors `AdminApiKey`'s existing shape/placement exactly; `configured_by` nullable FK → `employees.id`; `UniqueConstraint("source", name="uq_org_api_credentials_source")`
  - [x] Docstring documents the single-`encrypted_key`-holds-both-fields judgment call (Scope Note 3)
- [x] Task 4: New Alembic migration `008_add_org_api_credentials.py` (AC1)
  - [x] `create_table('org_api_credentials', ...)`, FK to `employees`, unique constraint on `source` — purely additive, matches migration `005`'s style exactly
- [x] Task 5: `content/schemas.py` — request/response schemas (AC3–AC6)
  - [x] `SetYoutubeKeyRequest { key: str }`, `SetUdemyCredentialRequest { client_id: str, client_secret: str }` — both reject blank/whitespace-only via a field validator mirroring `skills/schemas.py::_reject_blank`
  - [x] `YoutubeKeyStatus { configured: bool }`, `UdemyCredentialStatus { configured: bool, configured_by: str | None, configured_at: str | None }`, `ApiKeysStatusResponse { youtube: YoutubeKeyStatus, udemy: UdemyCredentialStatus }`
- [x] Task 6: `content/repository.py` — CRUD + encryption boundary (AC3, AC4, AC5, AC6, Scope Note 2/3)
  - [x] `upsert_admin_api_key(db, *, admin_id, source, plaintext_key)` — encrypts internally, Postgres `INSERT ... ON CONFLICT (admin_id, source) DO UPDATE`
  - [x] `delete_admin_api_key(db, *, admin_id, source)`
  - [x] `get_admin_api_key(db, *, admin_id, source) -> AdminApiKey | None`
  - [x] `upsert_org_api_credential(db, *, source, client_id, client_secret, configured_by)` — encrypts `json.dumps({...})` internally, `INSERT ... ON CONFLICT (source) DO UPDATE`
  - [x] `delete_org_api_credential(db, *, source)`
  - [x] `get_org_api_credential(db, *, source) -> OrgApiCredential | None`
- [x] Task 7: `content/service.py` — orchestration + auth gate (AC3–AC6, Scope Note 4, 5, 7, 8)
  - [x] `set_youtube_key(db, *, current_user, key)`, `remove_youtube_key(db, *, current_user)`
  - [x] `set_udemy_credential(db, *, current_user, client_id, client_secret)`, `remove_udemy_credential(db, *, current_user)`
  - [x] `get_api_keys_status(db, *, current_user) -> ApiKeysStatusRaw` (small internal dataclass: `youtube_configured`, `udemy_configured`, `udemy_configured_by_id: UUID | None`, `udemy_configured_at: datetime | None`) — every function calls `require_hr_admin(current_user)` first
- [x] Task 8: `content/admin_api_keys_router.py` (NEW) — routes + name-resolution composition (AC3–AC6, Scope Note 5, 6)
  - [x] `PUT /youtube`, `DELETE /youtube`, `PUT /udemy`, `DELETE /udemy` (all `204`), `GET ""` (→ `ApiKeysStatusResponse`)
  - [x] `GET`'s handler resolves `udemy_configured_by_id` to a display name via `app.assignments.service.get_employee_by_id_service`, mirroring `auth/router.py::get_me_route`
  - [x] Mount in `backend/app/main.py`: `app.include_router(admin_api_keys_router, prefix="/api/admin/api-keys", tags=["admin-api-keys"])`
- [x] Task 9: Backend tests
  - [x] `tests/test_secrets.py`: encrypt→decrypt round trip returns the original plaintext; two encryptions of the same plaintext produce different ciphertext (Fernet includes a random IV/timestamp); decrypting garbage raises cleanly
  - [x] `tests/test_content_repository.py` (extend): upsert-then-get round trips for both tables; a second upsert for the same `(admin_id, source)` / `source` replaces rather than duplicates (`UNIQUE` respected); delete removes the row; getting a nonexistent row returns `None`
  - [x] `tests/test_content_service.py` (extend): each of the 5 new service functions — happy path, and a 403 (`AppException`) for an EMPLOYEE `current_user`
  - [x] `tests/test_admin_api_keys_router.py` (NEW, private-engine pattern per `test_skills_router.py`/`test_content_router.py` precedent — never the shared `db_session` fixture): full HTTP-level matrix — YouTube save/status/remove round trip; Udemy save/status/remove round trip; Udemy "connected by" shows the saving Admin's real name; a second Admin replacing the Udemy credential updates `configured_by` to the second Admin; every endpoint (including `GET`) returns 403 for an EMPLOYEE session and 401 unauthenticated; the key/secret value never appears anywhere in any response body (grep the raw JSON, not just the typed fields)
- [x] Task 10: Frontend — API client (Scope Note 10)
  - [x] `frontend/src/lib/api/adminApiKeysApi.ts`: `getApiKeysStatus`, `saveYoutubeKey`, `removeYoutubeKey`, `saveUdemyCredential`, `removeUdemyCredential`, matching `assignmentsApi.ts`'s existing style (typed interfaces + thin `apiClient` wrappers)
- [x] Task 11: Frontend — `ApiKeysModal` component (Scope Note 10, 11)
  - [x] `frontend/src/features/admin/ApiKeysModal.tsx`, built on the existing `Dialog` primitive exactly as `DeleteAssignmentModal.tsx`/`ProvenanceDrillDownModal.tsx` do
  - [x] YouTube row: label, status text ("Not connected"/"Connected"), input, Save/Remove — one row
  - [x] Udemy row: label, status text ("Not connected"/"Connected by {name}, {date}"), Client ID input (own full-width row), Client secret input + Save/Remove (second row), helper text "This credential is shared across all HR Admins, not personal to your account."
  - [x] States: loading status on open; per-row saving spinner; save clears the input and refreshes status; remove requires an inline confirm step before the DELETE fires; API failures show an inline error, never a silent no-op
  - [x] Fully keyboard-operable (inherited from `Dialog`: Escape closes, focus trap, focus-return-to-trigger)
- [x] Task 12: Frontend — temporary dev route to exercise the modal (Scope Note 10)
  - [x] `frontend/src/pages/dev/ApiKeysModalDemo.tsx` (mirrors `VideoPlayerDemo.tsx`'s role: a minimal page with an "Open API Keys" button rendering the real modal)
  - [x] Route in `App.tsx`: `/dev/api-keys-modal-demo`, `RequireAuth`-gated, same pattern as the existing `/dev/video-player-demo` route
- [x] Task 13: Frontend tests
  - [x] `frontend/src/tests/ApiKeysModal.test.tsx` (mirrors `AssignmentModal.test.tsx`'s mocking style — `vi.mock('@/lib/api/adminApiKeysApi', ...)`): renders both rows with fetched status; saving a key calls the API and clears the input; remove requires confirm before calling the API; a failed save shows an inline error and does not clear the input

### Review Findings

`bmad-code-review` (2026-09-10, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). Acceptance Auditor reported a fully clean pass (zero AC/Scope-Note violations). 1 decision-needed, 6 patches, 4 deferred, 3 dismissed.

- [x] [Review][Decision] A real, freshly-generated `ADMIN_KEY_ENCRYPTION_SECRET` value was committed into the already-tracked `backend/.env` — the encryption key for the very credentials this story exists to protect now lives in git history alongside the pre-existing committed `JWT_SECRET`/`YOUTUBE_API_KEY`. **Resolved by user (2026-09-10): keep as-is.** Matches the existing repo-wide convention (`JWT_SECRET`/`YOUTUBE_API_KEY` are already committed the identical way) — this is a local-only, internal-pilot tool with no production deployment target, so real-world exposure risk is low. No code change made; not treated as blocking.
- [x] [Review][Patch] `SetYoutubeKeyRequest.key`/`SetUdemyCredentialRequest.client_id`/`client_secret` have no `max_length` — this codebase already learned this exact lesson in Story 6.2's review (`CreateSkillRequest.name` got `max_length=255` for the identical reason: unbounded client input reaching the DB/encryption path unchecked). **Fixed:** added a shared `CREDENTIAL_MAX_LENGTH = 4096` constant applied to all three fields, plus 3 new router tests asserting 422 on an over-limit value. [backend/app/content/schemas.py]
- [x] [Review][Patch] `ApiKeysModal.tsx`'s Save button is never disabled while a Remove is in-flight (`youtubeRemoving`/`udemyRemoving`) — a user can click Remove → Confirm, then before the DELETE resolves, edit and submit Save for the same credential, racing a PUT against a DELETE with the final state determined by request order, not user intent. **Fixed:** both Save buttons and their inputs now also disable on `youtubeRemoving`/`udemyRemoving`. [frontend/src/features/admin/ApiKeysModal.tsx:200-215, 264-287]
- [x] [Review][Patch] `refreshStatus`'s async `setState` calls (in `handleSaveYoutube`/`handleConfirmRemoveYoutube`/`handleSaveUdemy`/`handleConfirmRemoveUdemy`) have no unmount guard — if a future consumer (Story 6.10) conditionally unmounts `ApiKeysModal` rather than toggling `open`, an in-flight request resolving after unmount calls `setState` on an unmounted component. **Fixed:** added an `isMountedRef` (set in a mount-effect's cleanup) checked before every post-await `setState` call. [frontend/src/features/admin/ApiKeysModal.tsx:83-157]
- [x] [Review][Patch] `test_udemy_save_by_second_admin_replaces_configured_by` logs in as Rita twice (the only seeded HR_ADMIN) and asserts `configured_by` stays `"Rita the Recommender"` both times — it would pass even if the code never updated `configured_by` at all. **Fixed:** added `_create_second_hr_admin`/`_delete_second_hr_admin` test helpers creating a real second `Employee` row plus a temporary entry in `auth/repository.py::_MOCK_ACCOUNTS` (discovered mid-fix: login in this codebase is a hardcoded in-memory dict, not DB-backed — a DB `accounts` row alone would never let a new identity log in), so the test now proves the replace-regardless-of-who-configured-it-before behavior through a real second admin's authenticated HTTP session. [backend/tests/test_admin_api_keys_router.py]
- [x] [Review][Patch] No test asserts `extra="forbid"` is actually enforced on `SetYoutubeKeyRequest`/`SetUdemyCredentialRequest` — this codebase has an established precedent for exactly this test (`test_skills_router.py::test_update_skill_rejects_unknown_field`) that wasn't carried forward here. **Fixed:** added `test_youtube_save_rejects_unknown_field`/`test_udemy_save_rejects_unknown_field`. [backend/tests/test_admin_api_keys_router.py]
- [x] [Review][Patch] `OrgApiCredential.configured_by`'s FK has no `ondelete=` behavior, contradicting its own docstring ("attribution only... not an ownership scope," nullable) — deleting the referenced Employee today raises a Postgres FK violation instead of nulling the attribution as the design implies. **Fixed:** added `ondelete="SET NULL"` to the FK in both the model and migration `008`; re-ran `alembic downgrade 007` → `upgrade head` locally and verified via `pg_constraint.confdeltype = 'n'` that the live dev DB's constraint now matches. [backend/app/assignments/models.py, backend/alembic/versions/008_add_org_api_credentials.py]
- [x] [Review][Defer] No key-rotation/versioning story in `core/secrets.py` — real architectural gap, but out of this story's scope and no other secret in this codebase (`JWT_SECRET` included) has rotation either. — deferred, pre-existing pattern, out of scope [backend/app/core/secrets.py]
- [x] [Review][Defer] Key derivation is a bare, unsalted SHA-256 hash rather than a real KDF (HKDF/PBKDF2) — a legitimate hardening opportunity, but low real risk here since the actual generated secret is a 256-bit `secrets.token_urlsafe(32)` value (high-entropy input doesn't need a salted/slow KDF the way a human-chosen password would). — deferred, low real risk given actual secret generation, worth revisiting if this ever needs real hardening [backend/app/core/secrets.py]
- [x] [Review][Defer] `test_admin_api_keys_router.py`'s cleanup helper (`_clear_credentials`) deletes every row for `source == "YOUTUBE"`/`"UDEMY"` across the whole table, not scoped to rows the test itself created — matches this codebase's own previously-documented "shared dev DB, cross-file conflict" risk pattern (Story 6.1's retro notes), but no other test file currently writes committed rows to these two brand-new tables, so there's no active conflict today. — deferred, no active conflict, flag for whoever next touches these tables' tests [backend/tests/test_admin_api_keys_router.py]
- [x] [Review][Defer] `configured_at` in the API response is actually `updated_at`, not a "first connected" timestamp — the UI's "Connected by {name}, {date}" will silently change its date on every re-save, even by the same Admin re-entering the same values. Inherent to AD-10's schema (only one `updated_at` column exists; no separate "first configured" column was ever specified) and the epic's own exact field name — fixing this properly needs a spec-level decision (add a real first-connected column), not a code patch. — deferred, spec-level constraint, not a code defect [backend/app/content/schemas.py, backend/app/assignments/models.py]
- [x] [Review][Dismiss] `admin_api_keys_router.py` declares `Depends(get_current_user)` at both the router level and again per-route — this exactly matches this codebase's own established convention (`skills/router.py` does the identical thing), relying on FastAPI's standard same-request dependency caching. Not a new risk introduced here.
- [x] [Review][Dismiss] `content/schemas.py`'s blank-rejection validators strip and return the trimmed value rather than preserving exact whitespace — this is a faithful, intentional mirror of `skills/schemas.py::_reject_blank`'s established precedent, and trimming a pasted key/secret's leading/trailing whitespace (a common paste artifact) is desirable behavior, not a defect.
- [x] [Review][Dismiss] The temporary `/dev/api-keys-modal-demo` route has no role gating (`RequireAuth` checks authentication only) — this exactly matches the existing `VideoPlayerDemo.tsx` dev-route precedent it was explicitly built to mirror (Scope Note 10); the real security boundary (every underlying API call) already correctly 403s for non-HR_ADMIN sessions.

## Dev Notes

- **This is the first story to use Fernet/`cryptography` in this codebase** — no prior precedent to match beyond AD-10's own text. The key-derivation-from-arbitrary-string approach (SHA-256 → base64) is a standard, safe way to turn any operator-supplied secret into a valid 32-byte Fernet key without requiring them to generate one by hand (consistent with how `JWT_SECRET` is also just an arbitrary string, not a pre-formatted key).
- **Why the repository owns encryption, not the service (Scope Note 2):** the epic AC is explicit that `core/secrets.py` is called "only from `content/repository.py`, never from a router" — read literally, that puts the encrypt/decrypt calls at the repository boundary, right next to the SQL. This is a deliberate architectural choice worth preserving rather than "simplifying" into the service layer during implementation — it keeps `content/service.py` fully storage-format-agnostic (it never sees ciphertext).
- **The single-`encrypted_key`-column-for-two-fields decision (Scope Note 3) is a real interpretation call, not a typo fix** — AD-10's schema table and the Udemy AC's prose are in tension, and this story resolves it in the schema's favor (don't add a column AD-10 doesn't list) by packing both values into one encrypted JSON blob. Flag this decision in the `OrgApiCredential` model's docstring so Story 6.6 (which will need to *decrypt and parse* this blob to actually call Udemy) doesn't have to rediscover the shape by reading raw bytes.
- **`get_api_keys_status`'s cross-module name resolution happens at the router layer (Scope Note 5)** — this is an existing, if slightly unusual, precedent (`auth/router.py` importing `app.assignments.service`), not a new architectural exception invented for this story. Keep `content/service.py` and `content/repository.py` free of any `assignments` import; only `content/admin_api_keys_router.py` may import `get_employee_by_id_service`.
- **Docker is live in this environment** (`talentpilot-api`, `talentpilot-db`, `talentpilot-ui` containers all healthy) — after implementation, rebuild and redeploy the backend image and live-verify via `curl` the same way Stories 6.2/6.4 did (save a YouTube key as Rita, confirm `GET` shows `configured: true`, confirm Casey/EMPLOYEE gets 403, remove it, confirm `GET` reverts to `false`), not just via the test suite.
- **Story 6.6 (not in scope here) is the first real consumer of the decrypted values** — this story only needs `encrypt_secret`/`decrypt_secret` to exist and round-trip correctly (proven by `test_secrets.py`); no endpoint in this story ever calls `decrypt_secret` in a live code path, since `GET /api/admin/api-keys` only reports `configured: bool`, never the value.

### Project Structure Notes

New files:
- `backend/app/core/secrets.py`
- `backend/alembic/versions/008_add_org_api_credentials.py`
- `backend/app/content/admin_api_keys_router.py`
- `backend/tests/test_secrets.py`
- `backend/tests/test_admin_api_keys_router.py`
- `frontend/src/lib/api/adminApiKeysApi.ts`
- `frontend/src/features/admin/ApiKeysModal.tsx`
- `frontend/src/pages/dev/ApiKeysModalDemo.tsx`
- `frontend/src/tests/ApiKeysModal.test.tsx`

Modified files:
- `backend/app/core/config.py` — `ADMIN_KEY_ENCRYPTION_SECRET`
- `backend/.env.example`, `backend/.env`
- `backend/requirements.txt` — `cryptography==50.0.1`
- `backend/app/assignments/models.py` — adds `OrgApiCredential` (alongside the pre-existing `AdminApiKey`)
- `backend/app/content/schemas.py`, `backend/app/content/repository.py`, `backend/app/content/service.py`
- `backend/app/main.py` — mounts the new router
- `backend/tests/test_content_repository.py`, `backend/tests/test_content_service.py`
- `frontend/src/App.tsx` — new dev route

Not touched (out of scope, later stories): `content/youtube_client.py`, any `udemy_client.py` (Story 6.6), `skills/*` (unrelated to this story), the real Skills tab page/grid (Story 6.10).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5] — full AC text (lines 2227–2265)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-10] — table schemas, Fernet/`ADMIN_KEY_ENCRYPTION_SECRET` requirement (lines 90–96)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-8] — module dependency direction (`content/`/`skills/` never depend back on `assignments/`)
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-16] — full FR text/consequences (lines 267–277)
- [Source: _bmad-output/C-UX-Scenarios/04-ritas-content-curation/04.1-skills-content-sourcing/04.1-skills-content-sourcing.md] — API Keys Panel object IDs (lines 224–239), state table (403–411), Form Validation (452–454), Accessibility (458–464)
- [Source: backend/alembic/versions/005_add_admin_api_keys.py], [Source: backend/app/assignments/models.py:80-103] — the pre-existing `admin_api_keys`/`AdminApiKey` this story extends rather than recreates (Scope Note 1)
- [Source: backend/app/skills/service.py] — `require_hr_admin` service-layer gating convention, no-explicit-commit convention
- [Source: backend/app/auth/router.py:36] — `uuid.UUID(current_user.user_id)` conversion and the router-layer cross-module name-resolution precedent this story mirrors
- [Source: backend/app/core/db.py] — `get_db`'s single-commit-per-request convention
- [Source: backend/app/main.py:43-47] — multi-router-per-module precedent (`progress/`) and admin-router mounting convention (`skills/`)
- [Source: backend/tests/test_skills_router.py], [Source: backend/tests/test_content_ad7_regression_guard.py] — router test patterns (private engine, login helper, regression-guard style)
- [Source: frontend/src/components/ui/dialog.tsx], [Source: frontend/src/features/dashboard/DeleteAssignmentModal.tsx] — Dialog primitive and existing modal-authoring pattern
- [Source: frontend/src/pages/dev/VideoPlayerDemo.tsx], [Source: frontend/src/App.tsx] — dev-route-ahead-of-real-page precedent
- [Source: frontend/src/lib/api/assignmentsApi.ts] — API client file style
- [Source: frontend/src/tests/AssignmentModal.test.tsx] — frontend modal test/mocking style

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- TDD: `core/secrets.py` written test-first (`tests/test_secrets.py`, 4 tests) — confirmed RED (`ModuleNotFoundError`) before implementing, GREEN immediately after.
- Repository layer (`tests/test_content_repository.py`, 12 new tests): 16/16 passed on first run after implementation.
- Service layer (`tests/test_content_service.py`, 10 new tests): 15/15 passed on first run.
- Router layer (`tests/test_admin_api_keys_router.py`, 24 new tests): first run hit `sqlalchemy.exc.InterfaceError: another operation is in progress` on 23/24 tests — traced to an autouse async `pytest.fixture` corrupting this file's private module-level engine under `loop_scope="module"`. Fixed by removing the fixture and calling the cleanup helper explicitly at the top of each test (matching `test_skills_router.py`'s established plain-helper convention, which uses no async fixtures at all) — 24/24 passed after the fix.
- Full backend regression (`pytest --deselect tests/test_content_repository.py --deselect tests/test_content_service.py`): first run surfaced 3 *new* failures beyond the 3 already-documented pre-existing ones (`test_cookie_settings_defaults`, `test_youtube_api_key_defaults_to_none_app_boots_without_it` — both call `load_settings(_env_file=None)` without the new required `ADMIN_KEY_ENCRYPTION_SECRET`; `test_all_tables_defined` — pinned table count, needed bumping for the new `org_api_credentials` table). Fixed all 3; re-ran clean: `3 failed, 460 passed, 2 skipped, 31 deselected` — the 3 failures are the same pre-existing, unrelated ones documented since Story 6.4 (`test_find_existing_assignment_returns_empty_when_no_match`, `test_assignment_with_no_qualifying_content_has_null_content`, `test_content_match_returns_null_when_no_content_matches_the_skill`).
- `test_content_repository.py` + `test_content_service.py` run together in isolation (this codebase's documented cross-file DB conflict pattern): 31/31 passed.
- Frontend: `ApiKeysModal.test.tsx` (13 tests) passed in isolation on first run. Full suite (`vitest run`, 274 tests) showed 1-2 flaky failures under full-suite resource contention (`getByPlaceholderText` racing the async status fetch, before the component finished loading) — fixed by switching those assertions to `findByPlaceholderText`/`findByTestId` (awaited, retrying queries) instead of synchronous `getBy*` right after only the static title had rendered. Re-ran full suite twice after the fix: `274 passed` both times, zero flakiness.
- `tsc --noEmit`: 73 pre-existing errors, confirmed identical count via `git stash` against the pre-story baseline (none touch any file this story added/changed). `vite build`: clean, 516 modules.
- Live Docker verification (rebuilt `talentpilot-ai-backend` and `talentpilot-ai-frontend` images — cryptography needed adding to `requirements-prod.txt` too, not just `requirements.txt`, since the Docker build uses the prod requirements file; `ADMIN_KEY_ENCRYPTION_SECRET` added to `docker-compose.yml` with the same `${VAR:-dev-default}` pattern as `JWT_SECRET`): confirmed via `curl` against the running container — Rita saves YouTube key (204) and Udemy credential (204), `GET` shows both `configured: true` with `"configured_by": "Rita the Recommender"` and a real ISO timestamp; Casey (EMPLOYEE) gets 403 on `GET`; Rita removes both (204 each), `GET` reverts to both `configured: false`.
- Live browser verification (Playwright/Chromium, installed ad hoc into `frontend/node_modules` via `npm install --no-save`, uninstalled after use — same disposable pattern as Story 5.7's Debug Log): full lifecycle against the real Docker frontend at `/dev/api-keys-modal-demo` — login as Rita, open modal, both rows show "Not connected", save YouTube key → status flips to "Connected", save Udemy credential → status shows "Connected by Rita the Recommender", remove YouTube key requires and respects the confirm step, status reverts to "Not connected" after confirming, modal closes cleanly. One console message logged during the run (`401 Unauthorized`) — traced to the app's own pre-login session-check request on the `/login` page load (`AuthContext`'s existing behavior, unrelated to this story, occurs before any login attempt).

### Completion Notes List

- Implemented Story 6.5 end-to-end: `core/secrets.py` (Fernet encrypt/decrypt, keyed by a new required `ADMIN_KEY_ENCRYPTION_SECRET` setting, called only from `content/repository.py`); `OrgApiCredential` ORM model + migration `008` (the `admin_api_keys` half already existed from a prior stray commit, verified rather than redone — Scope Note 1); `content/repository.py`/`service.py` CRUD + HR_ADMIN gating for both credential types; a new `content/admin_api_keys_router.py` mounted at `/api/admin/api-keys`, whose `GET` handler resolves the Udemy "connected by" display name via `assignments.service.get_employee_by_id_service` at the router layer (mirroring `auth/router.py::get_me_route`'s existing precedent, since `content/` may never depend on `assignments/` directly per AD-8); the `ApiKeysModal` React component (self-contained, matches the UX spec's object IDs) plus its API client and a temporary dev route to exercise it ahead of the real Skills tab (Story 6.10).
- **Real judgment call, documented in the story and in code:** AD-10's `org_api_credentials` schema defines only one `encrypted_key` column, but the Udemy AC requires "both fields encrypted." Resolved by packing `{client_id, client_secret}` into one JSON string before encrypting it as a single blob, rather than adding a column AD-10 never specified — documented on `OrgApiCredential`'s docstring and `upsert_org_api_credential`'s so Story 6.6 (the real consumer) doesn't have to rediscover the shape.
- **Two real gaps found and fixed that weren't anticipated in the story's Scope Notes:** (1) `requirements-prod.txt` is a separate file from `requirements.txt` and is what the Docker build actually installs from — `cryptography` had to be added there too, found only when the backend image rebuild would otherwise have failed at runtime; (2) `docker-compose.yml` had no `ADMIN_KEY_ENCRYPTION_SECRET` env var, so the containerized backend would have failed `Settings()` validation at startup — added with the same `${VAR:-dev-default}` fallback pattern already used for `JWT_SECRET`.
- **A real, if minor, test-authoring bug found and fixed during router testing:** an autouse async `pytest.fixture` for DB cleanup corrupted `test_admin_api_keys_router.py`'s private module-level engine under `loop_scope="module"` (`another operation is in progress`). Removed the fixture in favor of this codebase's established plain-helper-function convention (already used by every other router test file) — worth remembering as a pattern to avoid in any future router test file using this same module-scoped-engine style.
- No frontend regressions, no new TypeScript errors, clean production build, zero new backend test regressions (same 3 pre-existing failures as every story since 6.4). Live-verified end-to-end via `curl` against the real Docker container and via a real Chromium browser session against the real Docker frontend — not just at the test level.
- **Code review (`bmad-code-review`, 2026-09-10, 3 parallel adversarial layers): 1 decision-needed (resolved by user: keep the committed `ADMIN_KEY_ENCRYPTION_SECRET` value as-is, matching this repo's existing `JWT_SECRET`/`YOUTUBE_API_KEY` convention for a local-only pilot tool), 6 patches applied, 4 deferred, 3 dismissed.** Patches: `max_length=4096` added to all three credential fields (+3 tests); `ApiKeysModal.tsx`'s Save buttons/inputs now also disable while a Remove is in-flight, closing a real Save-vs-Remove request race; an `isMountedRef` guard added around every post-await `setState` in the modal (protects the next real consumer, Story 6.10, against an unmount-during-request warning); the `configured_by`-replacement router test was genuinely broken (tautological — it re-logged in as Rita twice) and is now fixed with a real second HR_ADMIN identity, which required discovering that this codebase's login is a hardcoded in-memory dict (`auth/repository.py::_MOCK_ACCOUNTS`), not DB-backed — a DB `accounts` row alone would never have let the new identity log in; 2 new tests assert `extra="forbid"` is enforced (matching an existing `test_skills_router.py` precedent that wasn't carried forward initially); `OrgApiCredential.configured_by`'s FK gained `ondelete="SET NULL"` (matching its own docstring's stated "attribution only" intent), applied to the live dev DB via `alembic downgrade 007` → `upgrade head` and verified against `pg_constraint`. Deferred (`deferred-work.md`): no key-rotation/versioning story; unsalted-SHA-256 key derivation (low real risk given the actual secret is a 256-bit generated value, not a human password); the router test file's whole-table cleanup helper (no active conflict today, flagged for future stories touching the same tables); `configured_at` actually being `updated_at` semantics (inherent to AD-10's schema and the epic's own field name, not a code defect). Dismissed: the router's double `Depends(get_current_user)` (matches `skills/router.py`'s identical established convention); the blank-rejection validators' whitespace-stripping (matches `skills/schemas.py`'s precedent and is desirable paste-artifact handling); the temp dev route's lack of role gating (matches the existing `VideoPlayerDemo.tsx` dev-route precedent; the real security boundary, the API, already 403s correctly). Full regression re-verified post-patch: backend 465 passed (5 new net) / 2 skipped / same 3 pre-existing failures; frontend 13/13 (`ApiKeysModal.test.tsx`), `tsc --noEmit` unchanged at 73 pre-existing errors. Live-reverified via `curl` against rebuilt Docker containers, including the new max_length/extra-forbid 422s and the FK constraint change. Status → `done`.

### File List

- `backend/app/core/config.py` (modified) — adds required `ADMIN_KEY_ENCRYPTION_SECRET` setting
- `backend/app/core/secrets.py` (new) — Fernet `encrypt_secret`/`decrypt_secret`
- `backend/app/assignments/models.py` (modified) — adds `OrgApiCredential` ORM model; review patch: `configured_by` FK gained `ondelete="SET NULL"`
- `backend/alembic/versions/008_add_org_api_credentials.py` (new); review patch: FK now created with `ondelete="SET NULL"`
- `backend/app/content/schemas.py` (modified) — adds `SetYoutubeKeyRequest`, `SetUdemyCredentialRequest`, `YoutubeKeyStatus`, `UdemyCredentialStatus`, `ApiKeysStatusResponse`; review patch: `CREDENTIAL_MAX_LENGTH = 4096` bound added to all three credential fields
- `backend/app/content/repository.py` (modified) — adds admin/org credential CRUD (upsert/get/delete for both tables)
- `backend/app/content/service.py` (modified) — adds `set_youtube_key`, `remove_youtube_key`, `set_udemy_credential`, `remove_udemy_credential`, `get_api_keys_status` (+ `ApiKeysStatusRaw` dataclass)
- `backend/app/content/admin_api_keys_router.py` (new) — `GET`/`PUT`/`DELETE` routes, mounted at `/api/admin/api-keys`
- `backend/app/main.py` (modified) — mounts the new router
- `backend/requirements.txt`, `backend/requirements-prod.txt` (modified) — add `cryptography==50.0.1`
- `backend/.env.example`, `backend/.env` (modified) — `ADMIN_KEY_ENCRYPTION_SECRET`
- `docker-compose.yml` (modified) — `ADMIN_KEY_ENCRYPTION_SECRET` env var for the `backend` service
- `backend/tests/test_secrets.py` (new) — 4 tests
- `backend/tests/test_content_repository.py` (modified) — 12 new tests
- `backend/tests/test_content_service.py` (modified) — 10 new tests
- `backend/tests/test_admin_api_keys_router.py` (new) — 24 tests; review patches: fixed the tautological second-admin test (real second HR_ADMIN identity via `_create_second_hr_admin`/`_delete_second_hr_admin`), +2 `extra="forbid"` tests, +3 `max_length` tests (29 total)
- `backend/tests/test_config.py` (modified) — 2 existing tests fixed to set the new required env var
- `backend/tests/test_schema_definition.py` (modified) — `test_all_tables_defined` bumped to include `org_api_credentials`
- `frontend/src/lib/api/adminApiKeysApi.ts` (new) — API client
- `frontend/src/features/admin/ApiKeysModal.tsx` (new) — the modal component; review patches: Save buttons/inputs also disable during an in-flight Remove (race fix), `isMountedRef` guard around post-await `setState` calls
- `frontend/src/pages/dev/ApiKeysModalDemo.tsx` (new) — temporary dev route
- `frontend/src/App.tsx` (modified) — adds `/dev/api-keys-modal-demo` route
- `frontend/src/tests/ApiKeysModal.test.tsx` (new) — 13 tests
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — story status tracking

## Change Log

- 2026-09-10: Story 6.5 created (`bmad-create-story`), scoped after discovering a prior stray commit (`4e99d275`) had already built the `admin_api_keys` half of AD-10's schema ahead of any story existing for it — this story's real scope is `org_api_credentials`, `core/secrets.py`, the service/repository/router layer for both credential types, and the API Keys modal UI (Skills tab itself is Story 6.10, not yet built).
- 2026-09-10: Story 6.5 implemented (`bmad-agent-dev`, TDD, same session as creation). Backend: `core/secrets.py` (Fernet, test-first), `OrgApiCredential` model + migration 008, `content/` repository/service/router additions, mounted at `/api/admin/api-keys`. Frontend: `ApiKeysModal.tsx` (self-contained, UX-spec object IDs), API client, temporary dev route (`/dev/api-keys-modal-demo`, Story 6.10 will wire the real trigger). 46 new/extended backend tests + 13 new frontend tests, all passing; fixed 2 pre-existing tests (`test_config.py`) and 1 pre-existing assertion (`test_schema_definition.py::test_all_tables_defined`) that the new required setting/table broke. Zero net-new regressions: backend full suite at the same 3 pre-existing failures documented since Story 6.4; frontend full suite (274 tests) clean after fixing 2 test-timing races surfaced only under full-suite load; `tsc --noEmit` at the same 73 pre-existing errors (confirmed via `git stash` against the pre-story baseline); `vite build` clean. Found and fixed 2 real deployment gaps beyond the story's own Scope Notes: `cryptography` also needed adding to `requirements-prod.txt` (the file Docker actually builds from) and `ADMIN_KEY_ENCRYPTION_SECRET` needed adding to `docker-compose.yml`. Live-verified end-to-end twice: via `curl` against the rebuilt Docker containers (save/status/403-for-employee/remove, full round trip) and via a real Chromium browser session (Playwright, installed/removed ad hoc) against the live frontend at `/dev/api-keys-modal-demo` — save, status update, remove-with-confirm, and modal close all confirmed working in a real browser, not just in tests. Status → `review`.
- 2026-09-10: `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor; Acceptance Auditor reported a fully clean pass, zero AC/Scope-Note violations). 1 decision-needed resolved by user (keep the committed `ADMIN_KEY_ENCRYPTION_SECRET` value as-is — matches this repo's existing `JWT_SECRET`/`YOUTUBE_API_KEY` convention for a local-only pilot tool with no production target), 6 patches applied, 4 deferred (`deferred-work.md`), 3 dismissed. Patches: `max_length=4096` bound added to all three credential fields; `ApiKeysModal.tsx`'s Save buttons/inputs now disable while a Remove is in-flight, closing a real request race; an `isMountedRef` guard added around every post-await `setState`; the second-admin router test was genuinely tautological (re-logged in as Rita twice) and is now fixed with a real second HR_ADMIN identity — required discovering this codebase's login is a hardcoded in-memory dict (`_MOCK_ACCOUNTS`), not DB-backed; 2 new `extra="forbid"` enforcement tests; `OrgApiCredential.configured_by`'s FK gained `ondelete="SET NULL"`, re-applied to the live dev DB and verified via `pg_constraint`. Full regression re-verified: backend 465 passed / 2 skipped / same 3 pre-existing failures; frontend 13/13, `tsc --noEmit` unchanged at 73 pre-existing errors. Live-reverified via `curl` against rebuilt Docker containers. Status → `done`.
