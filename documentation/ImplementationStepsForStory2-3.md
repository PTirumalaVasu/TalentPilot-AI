# Story 2.3: Batch Content Ingestion Job (YouTube Search)

## What was built

A scheduled batch job that populates `content_catalog` with YouTube videos, without ever calling YouTube's API live from a request (AD-7's batch-only rule). Delivered as:

- **`content/youtube_client.py`** — thin `requests`-based wrapper around YouTube Data API v3's `search.list` (find videos) and `videos.list` (fetch durations). Raises `QuotaExceededError` specifically on a 403 `quotaExceeded` response, since `search.list` draws from a separate, much smaller (~100/day) quota bucket than `videos.list`.
- **`content/service.py`** — `ingest_content_for_skill` (search → dedupe → embed → store, per Skill), `run_ingestion_job` (loops all Skills, stops the whole run on quota exhaustion, isolates non-quota per-Skill failures), `manual_seed_content` (insert Content with zero YouTube calls), `_build_embedding_text` (truncates title+description to 1000 chars before embedding — closes a deferred item from Story 2.2).
- **`content/cli.py`** — `python -m app.content.cli {ingest,seed}`. A CLI, not an HTTP admin endpoint, so it adds no new authenticated route surface.
- **`content/repository.py::list_all_skills`** — a documented, narrow exception to the "one module owns one table" rule (AD-1), since no module owns `skills` yet.
- **`core/config.py::YOUTUBE_API_KEY`** — optional; the app boots fine without it, only the CLI needs it.

Automatic recurring scheduling (cron/APScheduler) was deliberately **not** built — this story delivers the job logic and a manual trigger; wiring a real recurring trigger is out of scope for this local-only, no-deployment project.

## Issues found in code review, and root causes

Three independent adversarial review passes (Blind Hunter, Edge Case Hunter, Acceptance Auditor) ran against the diff. The most serious issues, with root causes:

### 1. A single Skill's DB failure could silently fail the entire batch run
**Root cause:** `run_ingestion_job` loops over every Skill using one shared database session. When a Skill's ingestion failed partway through (e.g. an embedding error after one video was already inserted), the code logged the error and moved to the next Skill — but never called `db.rollback()`. In SQLAlchemy/Postgres, a session left in a failed-transaction state rejects every further query until it's rolled back. So skill 2's failure would silently break skills 3, 4, 5 too, each logged as an unrelated "ingestion failed" error with no indication they were all the same root cause.
**Fix:** Added `db.rollback()` to both failure branches (quota-exceeded and generic exception) in `run_ingestion_job`.

### 2. The rollback fix itself introduced a crash (caught during patch verification, not by the review)
**Root cause:** SQLAlchemy's `rollback()` expires every ORM object bound to that session — not just the one that failed. The loop was iterating over live `Skill` objects, so after a rollback, the *next* Skill's `.name`/`.id` attributes were expired. Reading an expired attribute outside of an active async context (`await`) crashes with `MissingGreenlet` because SQLAlchemy tries to silently re-fetch it from the database and there's no running event-loop context to do that in.
**Fix:** Changed `ingest_content_for_skill` to take plain `skill_id`/`skill_name` values instead of a live ORM object, and extracted all Skills' `(id, name)` pairs into plain Python values *before* the loop starts — so nothing in the loop ever touches a potentially-expired attribute.

### 3. Quota-exceeded skills were double-counted in the summary
**Root cause:** When quota ran out partway through, the code added all remaining Skill names to `skipped_due_to_quota` in one go — but then let the loop keep running, where a separate check at the top of each iteration added the *same* names again.
**Fix:** Added `break` immediately after recording the skipped Skills, so the loop actually stops instead of just skipping work while still iterating.

### 4. A malformed YouTube API response could crash instead of failing cleanly
**Root cause:** The code called `response.json()` before checking whether the HTTP status was successful. If YouTube (or a proxy in front of it) returned a non-2xx response with a non-JSON body (e.g. an HTML error page), parsing it as JSON would raise an unhandled crash instead of the intended "here's what went wrong" exception.
**Fix:** Check `status_code` first; only parse JSON if a request actually needs the body, with a safe fallback if parsing still fails.

### 5. A missing video ID from YouTube could corrupt downstream data
**Root cause:** The code assumed every search result always has a valid video ID and used it directly to build URLs and to batch-fetch durations. A malformed or unexpected API response could yield `None`, producing a broken stored URL (`.../watch?v=None`) and crashing the batched duration lookup.
**Fix:** Skip any result item that doesn't have a real video ID instead of trusting it blindly.

### 6. A manually-seeded row could look like a real YouTube video but hide from de-duplication
**Root cause:** The manual-seed schema allowed marking a hand-entered row as `source="YOUTUBE"`, but manual seeding never stores a `video_id`. The de-duplication logic only checks rows that have `video_id` in their metadata — so this row would be invisible to it, and a later real ingestion run could insert a genuine duplicate of that same video without knowing.
**Fix (user decision):** Pinned the manual-seed schema's `source` field to always be `"MANUAL"` — removed the option to claim it's a YouTube video through that path.

### 7. Smaller hardening fixes
- `run_ingestion_job` now checks the API key itself before doing anything, instead of relying only on the CLI's check (so any future caller gets the same fast, clear failure).
- Replaced a duplicated literal `3` with the shared `MAX_RESULTS_PER_SKILL` constant, so the two can't silently drift apart.
- Hardened the automated test that guards against this job ever being called from a live HTTP route — it now also catches an aliased-import bypass, not just the literal function name.

## Verification

All fixes were re-verified with the full backend test suite: 143/143 passing in the main run, plus the content-module tests (18/18) and two pre-existing, already-known test-isolation quirks (16/16 and 7/7) confirmed unrelated to this story. Zero regressions.

## Deferred (not fixed — logged for later, low severity)

- No database-level protection against two ingestion runs racing to insert the same video simultaneously.
- Truncation of long descriptions is logged at debug level, so an operator likely won't notice it happening in practice.
- No retry for a one-off network blip talking to YouTube.
- Manually-seeded content isn't checked against a real Skill existing first.
- Passing a typo'd Skill ID to the CLI silently processes zero Skills with no warning.
- The "retry tomorrow" date is computed from UTC, not YouTube's actual Pacific-Time quota reset — can be off by a day right at the boundary.
