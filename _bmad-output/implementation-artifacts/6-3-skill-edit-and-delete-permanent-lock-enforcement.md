---
baseline_commit: 3849efad
---

# Story 6.3: Skill Edit & Delete — Permanent Lock Enforcement (FR-21/22)

Status: done

## Story

As an **HR Admin**,
I want to rename, re-describe, or delete a Skill — but only while it has never been assigned to an Employee,
so that I can fix a mistake cleanly, while every Skill an Employee has ever been assigned keeps a stable identity for audit purposes.

## Scope Notes (read before starting)

1. **Builds on Story 6.1/6.2's existing `skills/` module** — no new module directories. `skills/router.py`/`service.py`/`schemas.py` already have Story 6.2's `POST` (create) code; this story adds `PATCH`/`DELETE /api/admin/skills/{id}` to the same files, plus a shared `UpdateSkillRequest` schema.
2. **`ever_assigned` already exists and is already correctly maintained** — the column (migration 004), its one-way semantics (AD-11 point 2), and the backfill for pre-existing assigned Skills all landed in Story 6.1. Story 6.4 (still backlog) is what *sets* the flag on Assignment creation going forward; this story only *reads* it as the lock check. Do not touch `mark_ever_assigned` — it doesn't exist yet and is out of scope here.
3. **Real architecture gap this story must resolve: cascading a Skill delete into `content_catalog` without violating AD-1/AD-8.** AC4 requires that deleting an unassigned Skill also deletes its attached `content_catalog` rows, atomically. But `content_catalog` is owned by `content/` (AD-1), and `skills/` must never depend on `content/` (AD-8: "dependencies point Content → Skills, never back") — so `skills/service.py` cannot call into `content/` to delete those rows, and `skills/repository.py` querying `content_catalog` directly would reopen the exact kind of cross-module table access Story 6.1 just finished retiring (in the opposite direction). **Resolution: a DB-level FK cascade**, not a cross-module call. New migration 007 alters `content_catalog.skill_id`'s existing FK (`content_catalog_skill_id_fkey`, currently plain `REFERENCES skills(id)`, RESTRICT by default) to `ON DELETE CASCADE`. `skills/repository.py::delete_skill()` then issues a single `DELETE FROM skills WHERE id = ...` (Core-level `delete()`, not `session.delete(<ORM obj>)` — the latter would make SQLAlchemy's unit-of-work try to load and null out the `content_items` relationship, which fails since `content_catalog.skill_id` is `NOT NULL`); Postgres itself cascades the `content_catalog` deletes as part of that one statement, atomically, with zero application code touching `content_catalog`. Safe by construction: a Skill only reaches this path while `ever_assigned = false`, which (AD-11) means it has never had an `Assignment` row either, so `assignments.skill_id`'s own FK (left untouched, still RESTRICT) is never at risk here.
4. **Lock check is a plain column read, not a live join** — `skill.ever_assigned` (AD-11 point 2). No query against `assignments` from `skills/` — that would violate AD-8/AD-1 and also be unnecessary, since the flag is the authoritative, already-correct signal.
5. **Not-found vs. locked are distinct outcomes.** AC2's "never a 404" language for a *locked* Skill implies a genuinely nonexistent `skill_id` **is** a 404 (distinct from "exists but disallowed"). Use `AppException(404, "SKILL_NOT_FOUND", ...)` for missing rows, `AppException(403, "SKILL_LOCKED", "Skill has been assigned to an Employee and can no longer be edited or deleted")` (AC2's exact wording) for locked ones. Check existence before the lock check.
6. **PATCH is a true partial update.** Both `name`/`description` are optional; read `UpdateSkillRequest.model_dump(exclude_unset=True)` to distinguish "field omitted" (leave unchanged) from "field explicitly sent" (apply, including `description: null` to clear it) — do not default missing fields to `None` and overwrite.
7. **Duplicate check excludes the Skill's own current name** (AC1) — resubmitting "Python Basics" onto the Skill already named "Python Basics" is not a conflict with itself. Implement via `get_skill_by_name_ci` (already exists, Story 6.2) then compare `existing.id != skill.id`, not a new query.
8. **Embedding recompute is conditional on an actual value change**, not merely on the field being present in the request body (epics AC1: "if `name` or `description` changed"). Compare the resolved new value against the current column value before deciding to call `embed_text(_build_embedding_text(...))` — mirrors Story 6.1 AC3/Story 6.2's existing inline-composition convention exactly, still no wrapper function.
9. **Same `IntegrityError`→409 race-conversion pattern as `create_skill_service`** (Story 6.2 review patch) applies to rename too — migration 006's `lower(name)` unique index is table-wide, so two concurrent renames onto the same new name can race the same way two concurrent creates can. Mirror the existing `try/except IntegrityError: rollback, re-query, re-raise as _conflict()` shape.
10. **Gate pattern: service-layer `require_hr_admin(current_user)`**, matching `create_skill_service` exactly — not a router-level `Depends`.

## Acceptance Criteria

**Given** a Skill with `ever_assigned = false`
**When** I call `PATCH /api/admin/skills/{id}` with `{ name?: str, description?: str }`
**Then**:
- If `name` changes, the same case-insensitive duplicate check as Story 6.2 applies, **excluding the Skill's own current name** — on conflict, `409 Conflict`, no redirect payload
- On success, the name/description update in place, the embedding is recomputed if `name` or `description` changed, and `200 OK` returns the updated `SkillResponse`

**Given** a Skill with `ever_assigned = true`
**When** I call `PATCH /api/admin/skills/{id}` or `DELETE /api/admin/skills/{id}`
**Then** both return `403 Forbidden` with a clear error message (e.g., `"Skill has been assigned to an Employee and can no longer be edited or deleted"`) — never a silent no-op, never a 404

**Given** a Skill with `ever_assigned = false` and zero approved Content attached
**When** I call `DELETE /api/admin/skills/{id}`
**Then** the Skill row is **hard deleted** (no soft-delete/audit columns) and returns `204 No Content`

**Given** a Skill with `ever_assigned = false` **and** one or more admin-approved `content_catalog` rows attached
**When** I call `DELETE /api/admin/skills/{id}`
**Then** those `content_catalog` rows are deleted in the same transaction (cascade) before the Skill row itself is deleted; both succeed or both roll back together

**Given** any of the above
**When** an EMPLOYEE session calls either endpoint
**Then** `403 Forbidden` (AD-6)

## Tasks / Subtasks

- [x] Task 1: `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py` (AC4)
  - [x] `content_catalog_skill_id_fkey` dropped and recreated with `ondelete='CASCADE'`
  - [x] Applied live: rebuilt backend image, `docker compose up -d backend` (no volume mount for `backend/`, same as every prior migration), verified `\d content_catalog` shows `ON DELETE CASCADE` and `alembic_version = 007`
- [x] Task 2: `skills/schemas.py` — `UpdateSkillRequest` (AC1)
  - [x] `name: str | None`, `description: str | None`, both optional, `extra="forbid"`; shared blank-name validator with `CreateSkillRequest` via a `_reject_blank` helper
- [x] Task 3: `skills/repository.py` (AC1, AC3, AC4)
  - [x] `get_skill_by_id(db, skill_id) -> Skill | None`
  - [x] `update_skill(db, skill, updates: dict) -> Skill` — sets attributes, flushes, refreshes
  - [x] `delete_skill(db, skill_id) -> None` — Core-level `delete(Skill).where(Skill.id == skill_id)`, relies on migration 007's DB cascade for `content_catalog`
- [x] Task 4: `skills/service.py` (AC1, AC2, AC3, AC4)
  - [x] `_not_found()`, `_locked()` error helpers alongside the existing `_conflict()`
  - [x] `update_skill_service`: `require_hr_admin` → load-or-404 → lock-check-or-403 → partial-field resolution (`exclude_unset=True`) → self-excluding duplicate check → conditional embedding recompute → `IntegrityError`→409 race handling
  - [x] `delete_skill_service`: `require_hr_admin` → load-or-404 → lock-check-or-403 → `repository.delete_skill`
- [x] Task 5: `skills/router.py` (AC1–AC5)
  - [x] `PATCH /{skill_id}` → `update_skill_service`, `response_model=SkillResponse`
  - [x] `DELETE /{skill_id}` → `delete_skill_service`, `status_code=204`
- [x] Task 6: Tests
  - [x] `tests/test_skills_service.py` extended: rename success (embedding recomputed), rename with unchanged name/description (embedding untouched), self-name-resubmit is not a conflict, cross-skill duplicate name → 409 excluding self, locked Skill → 403 on both update/delete, nonexistent Skill → 404 on both, delete cascades attached `content_catalog` rows, delete with zero attached content, EMPLOYEE → 403 on both
  - [x] `tests/test_skills_router.py` extended: same matrix at the HTTP layer (200/403/404/409/204), unauthenticated → 401, partial-update (description-only, name-only) leaves the other field untouched
  - [x] Full regression pass

### Review Findings

`bmad-code-review` (2026-09-09, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed (resolved: defer to Story 6.4), 6 patches, 2 deferred, 2 dismissed.

- [x] [Review][Decision] `ever_assigned` is never set by the only live Assignment-creation path — Story 6.3's permanent lock is currently a no-op for real assignments. `assignments/service.py::create_assignment_service` (live at `POST /api/assignments`, `assignments/router.py:77`) creates the Assignment and returns; nothing calls `skills.service.mark_ever_assigned` anywhere in the codebase (`mark_ever_assigned` doesn't exist — it's Story 6.4's scope, still `backlog`). Net effect: an HR Admin can assign a Skill via the existing live endpoint, and this story's `PATCH`/`DELETE /api/admin/skills/{id}` will still treat that Skill as unlocked and let it be renamed or hard-deleted — silently defeating AC2 for every Skill assigned since migration 004's backfill, until Story 6.4 lands. **Decision (user, 2026-09-09): ship 6.3 as-is, do Story 6.4 next.** Reason: matches epics.md's own planned sequencing (Story 6.4's own text: "so that Story 6.3's permanent lock actually engages the first time a Skill is assigned") — Story 6.4 is already next in the backlog and closes this fully, including flag-setting idempotency edge cases that are explicitly its own scope, not this story's. — deferred, closes with Story 6.4 [backend/app/assignments/service.py:83-110, backend/app/skills/service.py]

- [x] [Review][Patch] `delete_skill_service` has no `IntegrityError` handling around `repository.delete_skill`, unlike `update_skill_service`'s existing rename-race handling. If a Skill somehow reaches the delete path while a real Assignment/Content still references it (currently reachable per the decision above, since `ever_assigned` isn't reliably set yet), the DB's `RESTRICT` FK on `assignments.skill_id`/`assignments.content_id` raises an unhandled `IntegrityError` → raw 500 instead of a clean 4xx. Fixed: wrapped in `try/except IntegrityError`, rolls back, converts to the same `_locked()` 403. New test simulates the exact stale-flag scenario directly (a committed Assignment referencing a Skill whose `ever_assigned` still reads `false`). [backend/app/skills/service.py, backend/tests/test_skills_service.py]

- [x] [Review][Patch] `UpdateSkillRequest.name` silently accepted an explicit `null` in the PATCH body. The blank-name validator only checked the non-`None` arm, so `{"name": null}` sailed through untouched; that `None` then defeated the case-insensitive duplicate check (SQL `lower(NULL)` never matches anything), flowed into `repository.update_skill`, and violated `skills.name`'s `NOT NULL` constraint at flush — raising a raw `IntegrityError` that the race-handler's fallback re-query (also querying with `name=None`) couldn't resolve, bare-re-raising as an unhandled 500. Fixed: the validator now explicitly rejects `None` for `name` with a clean 422 (`description` remains null-clearable, per Scope Note 6). New tests cover both the schema-level rejection and the router-level 422. [backend/app/skills/schemas.py, backend/tests/test_skills_service.py, backend/tests/test_skills_router.py]

- [x] [Review][Patch] The rename-conflict `409` reused `_conflict()` unmodified, attaching the same `existing_skill` redirect payload as create's 409 — directly contradicting AC1's explicit "no redirect payload" requirement for rename. Fixed: new `_rename_conflict()` helper (no `extra` payload) used at both rename conflict sites (pre-check and the post-`IntegrityError` race path). Updated the two existing tests that had locked in the wrong behavior to assert the payload is now absent. [backend/app/skills/service.py, backend/tests/test_skills_service.py, backend/tests/test_skills_router.py]

- [x] [Review][Patch] `update_skill_service` wrote a field into the `updates` dict whenever it was merely present in the request body, not only when its value actually changed — so a PATCH resubmitting the Skill's current, unchanged name/description still performed a real `UPDATE` + `flush` + `refresh` instead of a true no-op. Fixed: gated on `name_changed`/`description_changed` instead of `"name" in fields`/`"description" in fields`. [backend/app/skills/service.py]

- [x] [Review][Patch] Missing test coverage on the PATCH path for behavior already covered on POST/create using the identical shared validators: blank-name → 422, name over 255 chars → 422, `extra="forbid"` rejects an unrecognized field → 422. Also missing: a direct test that `{"description": null}` actually clears the description. Fixed: added all of the above at the router layer, plus schema/service-level tests for the null-name fix above. [backend/tests/test_skills_router.py, backend/tests/test_skills_service.py]

- [x] [Review][Patch] Migration `007`'s `downgrade()` silently reverted the FK to `RESTRICT` with no comment noting that any `content_catalog` rows already cascade-deleted while the migration was live are permanently gone. Fixed: added a comment noting the schema-only/data-loss asymmetry. [backend/alembic/versions/007_content_catalog_skill_cascade_delete.py]

- [x] [Review][Defer] No row-level locking/TOCTOU guard between the existence-check `SELECT` and the later `UPDATE`/`DELETE` in `update_skill_service`/`delete_skill_service`. A genuinely concurrent request pair on the same `skill_id` (e.g. two admins double-clicking, or a retry racing an in-flight delete) can raise an unhandled `ObjectDeletedError` on `update_skill`'s post-flush `refresh()`, or (for a delete racing another delete) silently affect 0 rows while still returning `204`. Very low likelihood for this internal, admin-only, low-concurrency tool — no other endpoint in this codebase implements row-level locking either, and a same-class concurrency gap was already deferred, not fixed, for Story 6.6's Udemy rate-limit handling. — deferred, pre-existing class of gap, low likelihood [backend/app/skills/service.py, backend/app/skills/repository.py]

**Dismissed** (noise, false positive, or already handled elsewhere): no dedicated `test_skills_repository.py` entries for the new `get_skill_by_id`/`update_skill`/`delete_skill` functions — matches Story 6.2's own established precedent exactly (its new `create_skill`/`get_skill_by_name_ci` repository functions also got no dedicated repository-test entries, covered only indirectly via service/router tests; `test_skills_repository.py` only covers the pre-existing `list_all_skills`/`get_skill_embedding` from Story 6.1); the sprint-status/project-context narrative reading as pre-emptively finalized despite self-flagging "not yet reviewed" (a documentation-tone observation about this session's own log-writing, not a code defect in this diff).

## Dev Notes

- **`ever_assigned` lock is enforced entirely within `skills/`** — no cross-module read of `assignments`. This is the point of AD-11 point 2 ("a local boolean, not a live join").
- **Embedding dimension 384**, same model as everywhere else — no new config.
- **This story does not touch Story 6.4's `mark_ever_assigned`** (still backlog) — `ever_assigned` is only *read* here.
- **`content_catalog`'s cascade is DB-level only** — no ORM `cascade=` on `Skill.content_items`/`ContentCatalog.skill` relationships was added or needed, since the delete path uses a Core `delete()` statement that never loads that relationship.

### Project Structure Notes

Files this story modifies (all pre-existing from Story 6.1/6.2):
- `backend/app/skills/schemas.py` — adds `UpdateSkillRequest`, extracts shared `_reject_blank` helper
- `backend/app/skills/repository.py` — adds `get_skill_by_id`, `update_skill`, `delete_skill`
- `backend/app/skills/service.py` — adds `update_skill_service`, `delete_skill_service`, `_not_found`, `_locked`
- `backend/app/skills/router.py` — adds `PATCH`/`DELETE /{skill_id}` routes

New migration:
- `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py`

Extended test files:
- `backend/tests/test_skills_service.py`
- `backend/tests/test_skills_router.py`

No changes to `backend/app/skills/models.py` (schema/flag already correct from Story 6.1) or `backend/app/main.py` (router already mounted, Story 6.2).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3] — full AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-11] — sole-ownership + one-way-lock rule (points 2, 4)
- [Source: _bmad-output/implementation-artifacts/6-2-skill-creation-endpoint.md] — `require_hr_admin` gate pattern, `AppException`/409 shape, `IntegrityError`→409 race-conversion pattern this story mirrors for rename
- [Source: backend/app/skills/service.py, repository.py, schemas.py, router.py] — Story 6.1/6.2 existing code this story extends in place
- [Source: backend/app/assignments/models.py] — `content_catalog.skill_id`/`assignments.skill_id` FK definitions (both plain RESTRICT before this story)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

Pre-review: `test_skills_service.py` + `test_skills_router.py` in isolation: 43 passed (26 new). Full suite: 413 passed / 2 skipped / same 3 pre-existing failures.

Post-review (after all 6 patches applied): `test_skills_service.py` + `test_skills_router.py` in isolation: 52 passed (9 more, from the review's new regression tests). Full regression suite (deselecting `test_content_repository.py`/`test_content_service.py`, this codebase's own established exclusion — they wipe the shared dev DB via `drop_all()`):
```
3 failed, 422 passed, 2 skipped, 11 deselected
FAILED tests/test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match
FAILED tests/test_content_discovery.py::test_assignment_with_no_qualifying_content_has_null_content
FAILED tests/test_content_router.py::test_content_match_returns_null_when_no_content_matches_the_skill
```
Identical to Story 6.1/6.2's documented pre-existing 3 failures (unrelated to this story — real dev-DB FK-referenced row state, confirmed by name match against Story 6.2's own debug log). Zero regressions. Migration 007 applied live: rebuilt `talentpilot-ai-backend` image, `docker compose up -d backend`, verified `\d content_catalog` shows `content_catalog_skill_id_fkey ... ON DELETE CASCADE` and `alembic_version = 007`.

### Completion Notes List

- Implemented `PATCH`/`DELETE /api/admin/skills/{id}` end-to-end (FR-21/22): `UpdateSkillRequest` schema, `get_skill_by_id`/`update_skill`/`delete_skill` repository functions, `update_skill_service`/`delete_skill_service` (HR_ADMIN gate, not-found vs. locked distinction, self-excluding duplicate check, conditional embedding recompute, `IntegrityError` race handling on rename), router routes.
- Resolved the story's one real design decision (cascading Skill delete into `content_catalog` without a forbidden `skills/` → `content/` dependency) via a DB-level `ON DELETE CASCADE` migration (007) rather than a cross-module service call — keeps AD-1/AD-8 intact, and makes the delete atomic by construction (one SQL statement).
- Code review (`bmad-code-review`, 3 parallel adversarial layers) found and fixed 6 real gaps: `delete_skill_service` had no `IntegrityError` handling (unlike `update_skill_service`'s existing rename-race handling) — now converts to a clean 403; `UpdateSkillRequest.name` silently accepted an explicit `null`, causing an eventual unhandled 500 via a `NOT NULL` violation — now rejected with 422; the rename-conflict 409 incorrectly carried the same `existing_skill` redirect payload as create's 409, contradicting AC1's explicit "no redirect payload" requirement — split into a dedicated `_rename_conflict()` with no `extra`; `update_skill_service` performed a real write even on a true no-op PATCH — now gated on actual value change; added missing PATCH-path test coverage (blank-name, max-length, `extra=forbid`, null-description-clears) mirroring create's existing coverage; added a data-loss-asymmetry comment to migration 007's `downgrade()`.
- One decision-needed item resolved by the user: `ever_assigned` is not yet set by the live `POST /api/assignments` flow (Story 6.4, still backlog, is what wires this) — accepted as a known, intentionally-sequenced gap per epics.md's own design, not fixed here; logged to `deferred-work.md`, closes automatically once Story 6.4 ships.
- One item deferred (pre-existing class of gap, low likelihood): no row-level locking/TOCTOU guard on concurrent update/delete of the same Skill — logged to `deferred-work.md`.

### File List

- `backend/app/skills/schemas.py` (modified) — `UpdateSkillRequest`, shared `_reject_blank` helper; review patch: reject explicit `null` for `name`
- `backend/app/skills/repository.py` (modified) — `get_skill_by_id`, `update_skill`, `delete_skill`
- `backend/app/skills/service.py` (modified) — `update_skill_service`, `delete_skill_service`, `_not_found`, `_locked`; review patches: `_rename_conflict()` helper (no redirect payload), `IntegrityError` handling on delete, `updates` dict gated on actual value change
- `backend/app/skills/router.py` (modified) — `PATCH`/`DELETE /{skill_id}` routes
- `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py` (new) — `content_catalog.skill_id` FK gains `ON DELETE CASCADE`; review patch: data-loss-asymmetry comment on `downgrade()`
- `backend/tests/test_skills_service.py` (modified) — review patches: fixed rename-conflict payload assertion, added null-name/null-description-clears/stale-flag-delete tests
- `backend/tests/test_skills_router.py` (modified) — review patches: fixed rename-conflict payload assertion, added null-name/blank-name/max-length/extra-forbid/null-description-clears tests

## Change Log

- 2026-09-09: Story 6.3 created and implemented in the same session (`bmad-create-story` + `bmad-agent-dev`, direct implementation). `PATCH`/`DELETE /api/admin/skills/{id}` (FR-21/22) added: HR_ADMIN-only, `ever_assigned` one-way lock enforced as a local column read (403 `SKILL_LOCKED` if set, 404 `SKILL_NOT_FOUND` if the Skill doesn't exist), case-insensitive rename-duplicate check excluding the Skill's own row (409), embedding recomputed only on an actual name/description value change, hard delete with `content_catalog` cascade resolved via a new DB-level `ON DELETE CASCADE` migration (007) to avoid a `skills/` → `content/` cross-module dependency AD-8 forbids. Status → `review`.
- 2026-09-09: `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed resolved (user: ship 6.3 as-is on the `ever_assigned`-not-yet-set gap, do Story 6.4 next as already planned — the gap is epics.md's own intentional sequencing, not a 6.3 defect, but is live/exploitable until 6.4 lands), 6 patches applied, 2 deferred (`deferred-work.md`), 2 dismissed. Patches: `delete_skill_service` now catches `IntegrityError` and converts to a clean 403 instead of a raw 500; `UpdateSkillRequest.name` now rejects an explicit `null` with 422 instead of eventually crashing on a `NOT NULL` violation; rename's 409 no longer carries create's `existing_skill` redirect payload (new `_rename_conflict()` helper), matching AC1's explicit "no redirect payload" requirement; `update_skill_service` no longer performs a write on a true no-op PATCH (gated on actual value change, not field presence); added missing PATCH-path test coverage (blank-name, max-length, `extra=forbid`, null-description-clears, plus a new test simulating the stale-`ever_assigned`-flag delete scenario end-to-end); added a data-loss-asymmetry comment to migration 007's `downgrade()`. Deferred: the `ever_assigned`-not-yet-set gap itself (closes with Story 6.4); no row-level locking/TOCTOU guard on concurrent update/delete of the same Skill (pre-existing class of gap, low likelihood). Dismissed: no dedicated repository-layer tests for the new functions (matches Story 6.2's own precedent); documentation-tone observation about sprint-status/project-context narrative (out of scope for a code diff review). Full regression re-verified: 422 passed (35 new total from this story) / 2 skipped / same 3 pre-existing failures. Status → `done`.
