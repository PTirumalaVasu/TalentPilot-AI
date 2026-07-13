---
title: 'Seed real ingested content for every environment; fix stale threshold-boundary tests'
type: 'bugfix'
created: '2026-07-13'
status: 'done'
review_loop_iteration: 0
context: []
route: 'one-shot'
---

## Intent

**Problem:** Video matching worked on one machine (where `python -m app.content.cli ingest` had been run manually against the local Postgres volume) but not on any other machine, because `content_catalog` is never populated by migrations or `core/seeds.py` -- it's a deliberate CLI-only, manual, YouTube-quota-conscious step (Story 2.3/AD-7) that was never captured anywhere reproducible. No README exists in this repo to document it either.

**Approach:** Add `seed_content()` to `core/seeds.py`, seeding the 15 real videos already ingested and verified on one machine (embeddings computed fresh at seed time via `embed_text()`, matching `seed_skills()`'s existing pattern -- not stored as literal vectors). Idempotent, skipped entirely if a machine already ran real ingestion. Verified genuinely on a fresh, disposable database (new Postgres DB on the same container, migrations applied, seeds run, matching confirmed) -- not just reasoned about. While re-running the content-matching test suite, found and fixed 2 tests left stale by an earlier session's `SIMILARITY_THRESHOLD` recalibration (0.7 -> 0.4): their boundary values were relative to the old threshold and silently started asserting the wrong thing.

## Suggested Review Order

**The actual fix (cross-machine content gap)**

- New real-content seed data + idempotent seed function.
  [`seeds.py:215`](../../backend/app/core/seeds.py#L215)

- Wired into the existing seed sequence.
  [`seeds.py:301`](../../backend/app/core/seeds.py#L301)

**Stale test fix (found while re-verifying, same threshold this fix's data depends on)**

- Boundary values recalibrated to the current `0.4` threshold, with a comment explaining why they moved.
  [`test_content_matching.py:137-169`](../../backend/tests/test_content_matching.py#L137)

**Deferred (pre-existing, not caused by this change)**

- `test_assignment_with_no_qualifying_content_has_null_content` remains red (already logged in an earlier deferred-work entry -- shared test/dev-DB conflation, not re-logged here).
- The broad full-suite failure set (66 failures across unrelated modules like `test_override_endpoint.py`, `test_protected_router_gate.py`) is the project's already-documented cross-file `asyncpg` connection-pool corruption -- confirmed via isolation re-runs, not caused by this change.
