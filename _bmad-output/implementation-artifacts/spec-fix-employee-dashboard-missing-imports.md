---
title: 'Fix missing imports crashing the Employee dashboard/Content Discovery endpoint'
type: 'bugfix'
created: '2026-07-12'
status: 'done'
review_loop_iteration: 0
context: []
route: 'one-shot'
---

## Intent

**Problem:** `GET /api/assignments/employee-assignments` (the Employee dashboard / Content Discovery data source) 500'd for every EMPLOYEE-role user with `NameError: name 'match_content_for_skill' is not defined`, because `backend/app/assignments/service.py` was missing that import (and a second, `AppException`) — leftover damage from the Story 2.6 merge's conflict resolution, which also left two duplicate/overlapping import blocks in the same file.

**Approach:** Consolidate the duplicate import blocks into one and add the two missing imports (`match_content_for_skill` from `app.content.service`, `AppException` from `app.core.errors`). No logic change. Verified live by re-testing the endpoint as Casey (real seeded employee) and via `pytest`.

## Suggested Review Order

**Missing imports (the actual fix)**

- Consolidated import block: removed the duplicate `app.assignments.repository`/`app.assignments.schemas`/`CurrentUser` imports, added the two missing names.
  [`service.py:9`](../../backend/app/assignments/service.py#L9)

- This is the call site that was crashing — `match_content_for_skill` now resolves.
  [`service.py:200`](../../backend/app/assignments/service.py#L200)

- This is the (previously dormant, now reachable) call site relying on `AppException` — the EMPLOYEE 403-rejection path.
  [`service.py:190`](../../backend/app/assignments/service.py#L190)

**Related, already-approved change riding in the same working tree**

- `SIMILARITY_THRESHOLD` recalibrated 0.7 → 0.4 (separate fix earlier this session, explicit user decision, unrelated to the import bug but affects the same endpoint's output).
  [`repository.py:13`](../../backend/app/content/repository.py#L13)

**Deferred (pre-existing, not caused by this change)**

- Two backend tests now fail because the shared test/dev DB conflates real interactive-session data with fixture assumptions — logged with full detail.
  [`deferred-work.md`](../../_bmad-output/implementation-artifacts/deferred-work.md#deferred-from-fix-of-assignmentsservicepy-missing-imports-2026-07-12)
