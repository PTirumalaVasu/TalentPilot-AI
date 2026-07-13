---
title: 'Fix stale content_metadata field name hiding video thumbnail/duration in the Assign a New Skill dialog'
type: 'bugfix'
created: '2026-07-12'
status: 'done'
review_loop_iteration: 0
context: []
route: 'one-shot'
---

## Intent

**Problem:** Step 3 of the HR "Assign a New Skill" dialog never showed the matched video's thumbnail or duration, even when the backend found a real content match. `AssignmentModal.tsx` read `content?.content_metadata`, but the backend (`ContentResponse.metadata`, fixed by Story 2.5 to serialize as `"metadata"`) actually returns the key `"metadata"` — confirmed live via `curl`. `content_metadata` was a leftover from Story 3.4, built in parallel before Story 2.5's fix landed and never reconciled after merge. Adversarial review then found a second, related bug in the same block: the duration text also never rendered, since it checked `typeof duration === 'number'` against a value that's always an ISO-8601 string (`"PT28M33S"`).

**Approach:** Rename the field to `metadata` in the TS interface and its one read site; fix the duration parsing to use the already-correct, already-used-elsewhere `parseIso8601DurationSeconds`/`formatDurationMinutes` utilities (matching `AssignmentCard.tsx`'s established pattern) instead of the broken ad hoc numeric check. Fixed the test fixture that was mocking the same wrong shapes the (buggy) component read, which is why neither bug was ever caught by the existing test suite.

## Suggested Review Order

**Field name fix (the reported bug)**

- The stale interface field, now matching the real backend wire key.
  [`assignmentsApi.ts:39`](../../frontend/src/lib/api/assignmentsApi.ts#L39)

- The one read site that was always `undefined` in production.
  [`AssignmentModal.tsx:266`](../../frontend/src/features/assignments/AssignmentModal.tsx#L266)

**Duration parsing fix (found by review, same root symptom)**

- `ContentMetadata.duration`'s real type (ISO-8601 string, not a number).
  [`AssignmentModal.tsx:23`](../../frontend/src/features/assignments/AssignmentModal.tsx#L23)

- Now reuses the already-correct utility instead of a broken ad hoc parse.
  [`AssignmentModal.tsx:267`](../../frontend/src/features/assignments/AssignmentModal.tsx#L267)

**Test fixtures (were mocking the same wrong shapes the bugs relied on)**

- Updated to the real wire key and a real ISO-8601 duration string.
  [`AssignmentModal.test.tsx:39`](../../frontend/src/tests/AssignmentModal.test.tsx#L39)

**Peripherals**

- Stale doc-comment reference corrected.
  [`duration.ts:3`](../../frontend/src/lib/utils/duration.ts#L3)

**Deferred (pre-existing, not caused by this change)**

- Thumbnail-URL reconstruction inconsistency, duplicate `ContentMatch`/`ContentItem` interfaces, missing contract test, and `tsc` error count drift (25 → 45) — logged with full detail.
  [`deferred-work.md`](../../_bmad-output/implementation-artifacts/deferred-work.md#deferred-from-fix-of-content_metadatametadata-field-mismatch-2026-07-12)
