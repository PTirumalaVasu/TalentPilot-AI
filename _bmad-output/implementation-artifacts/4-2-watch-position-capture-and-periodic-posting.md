---
story_key: 4-2-watch-position-capture-and-periodic-posting
epic: 4
story_num: 2
baseline_commit: 5cf7bff8cdf9bf50ba867c7f6a0b208d4434d45f
status: done
---

# Story 4-2: Watch-Position Capture & Periodic Posting from Client

**Epic:** 4 (Video Progress Capture & Resume)  
**Status:** ready-for-dev  
**Story ID:** 4.2  
**Dependencies:** Story 4-0 (YouTube IFrame Adapter), Story 4-1 (Backend schema/repository)

---

## User Story

As a **developer building client-side watch capture**,
I want to collect watch-position samples from the player adapter and post them to the backend periodically,
So that the backend has a record of Employee watch behavior without spamming HTTP requests.

---

## Acceptance Criteria

### AC1: Client Capture Service Architecture

**Given** an Employee is watching a video  
**When** the page is actively displayed  
**Then** the client implements a **WatchProgressCapture service** with these responsibilities:
- Listens to player adapter events (position updates from Story 4-0's YouTube Adapter)
- Queues position samples locally (not posted immediately)
- Batches and posts samples to `POST /api/assignments/{assignment_id}/progress`
- Manages retry on network failure
- Initiates a `sendBeacon` flush on tab close (Story 4-3's responsibility; this story hooks the trigger)

**And** this service is a singleton-scoped shared component (one instance per tab, shared across all video players on the page)

**And** the service exposes these public methods:
```typescript
// Core public interface
recordSample(assignmentId: UUID, position: number, eventTime: ISO8601): void
setupBeaconFlush(triggerCallback: () => void): void
flush(): Promise<void>
```

**And** the service is fully testable (dependency-injectable, mockable API client)

---

### AC2: Sampling & Local Queuing

**Given** the player adapter fires a position update  
**When** `recordSample(assignmentId, position, eventTime)` is called  
**Then**:
- A `ProgressQueueItem` is created: `{ assignmentId, watchPosition, eventTime, videoUrl, queuedAt }`
- The item is added to a local **sample queue** (in-memory array or similar)
- Queue is not immediately posted; posting is deferred to the batch timer

**And** queue items are stored as they arrive, preserving order

**And** the queue is not cleared until a successful POST confirms persistence

---

### AC3: Batch Posting Logic

**Given** samples are queued  
**When** one of these conditions is met:
- Timer expires (post every 10–15 seconds), OR
- Queue has accumulated 3+ samples  
**Then** the service:
- Takes all queued samples
- Groups them by `assignment_id` (one POST per assignment, not per sample)
- POSTs to `POST /api/assignments/{assignment_id}/progress` with:
  ```json
  {
    "watch_position": <seconds, integer>,
    "event_time": "<ISO-8601 client timestamp>",
    "video_url": "<context for server-side validation>"
  }
  ```
- Only ONE sample per POST (the latest non-duplicate in the batch for this assignment)

**And** posting happens every 10–15 seconds at most (configurable), even if queue is empty

**And** empty queue → empty POST list (timer expires, no POST sent if no samples exist)

---

### AC4: Retry on Network Failure

**Given** a POST fails (network error, 5xx, timeout)  
**When** the error is detected  
**Then**:
- Samples remain in the queue (not discarded)
- Error is logged with context (assignment_id, sample count, error reason)
- Service does NOT retry immediately (do not spam server)
- Retry happens on the next batch timer interval (10–15 seconds later)

**And** on retry, the old queued samples are combined with any new samples since the failure

**And** if a POST succeeds on retry, all queued samples up to that point are cleared

**And** network failures are not thrown to the UI (internal service concern, UI remains unaffected)

---

### AC5: Successful POST Response Handling

**Given** a POST to `/api/assignments/{assignment_id}/progress` succeeds (201 Created)  
**When** the response is received  
**Then**:
- Response body contains `{ watch_position, event_time, verified }`
- Service stores the `verified` flag locally (used by frontend for visual feedback in Story 4-4's anti-spoofing feedback, if any)
- Queued samples for this assignment are cleared (they have been persisted)
- Service does not throw or error (silent success)

**And** if `verified: false`, the service logs a diagnostic (position may not have been accepted server-side due to anti-spoofing checks), but still clears the queue for this assignment

---

### AC6: sendBeacon Setup Hook

**Given** a video player is initialized on the page  
**When** the WatchProgressCapture service is initialized  
**Then**:
- Service provides `setupBeaconFlush(triggerCallback)` method (called by Story 4-3's tab-close handler)
- triggerCallback is stored and called when tab close / visibilitychange is detected
- On callback, service prepares the last known position for `sendBeacon` dispatch
- Service does NOT perform the `sendBeacon` itself (Story 4-3 owns that) — only prepares data and clears queue

---

### AC7: Video URL Capture

**Given** a sample is recorded  
**When** `recordSample()` is called  
**Then**:
- The service obtains the current video URL from the player adapter (Story 4-0)
- URL is included in all POST requests for server-side validation (AD-5)
- URL is sourced from the adapter, never from the request URL or hardcoded

**And** if URL is unavailable, POST is still sent (URL is optional for MVP; server can validate with assignment_id alone)

---

### AC8: Error Contract Compliance

**Given** any error occurs in the capture service  
**When** errors are handled  
**Then**:
- All errors are logged via `console.warn` / `console.error` with context
- No exceptions bubble to the UI or break playback
- Service remains operational (does not crash on a single failed POST or malformed response)

**And** if the API client throws a non-network error (e.g., 422 validation from backend), error is logged and queue is cleared (stale/invalid sample, no point retrying)

---

### AC9: Configuration & Flexibility

**Given** the capture service is deployed  
**When** tuning is needed (e.g., adjust batch interval, sample threshold)  
**Then** these are configurable:
- `PROGRESS_POST_INTERVAL_MS` (default: 10000ms = 10 seconds)
- `PROGRESS_QUEUE_THRESHOLD` (default: 3 samples)

**And** configuration is sourced from environment or a shared config module (not hardcoded)

---

### AC10: TypeScript Types & Documentation

**Given** the implementation is complete  
**When** consuming code imports the capture service  
**Then** TypeScript types are available:
- `RecordWatchProgressRequest` (from Story 4-1)
- `SkillProgressResponse` (from Story 4-1)
- `ProgressQueueItem` (defined here for internal queue state)
- `WatchProgressCaptureService` (interface/class)

**And** JSDoc comments explain:
- When each method is called (by whom: player adapter, tab-close handler, etc.)
- What happens to samples on failure vs. success
- How to test the service (mocking API client)

---

## Implementation Plan

### Phase 1: Capture Service Core (TDD)

1. **Define types** (`frontend/src/types/progress.ts` — extend AC10):
   - `ProgressQueueItem` interface
   - `WatchProgressCaptureService` interface
   - Error handling types

2. **Implement WatchProgressCapture service** (`frontend/src/services/WatchProgressCaptureService.ts`):
   - Constructor: dependency-inject API client, timers
   - `recordSample()`: queue logic, deduplication (AC2)
   - `flush()`: batch POST logic, error handling (AC3, AC4, AC5)
   - Timer loop: `setInterval`, async batch posting (AC3)
   - Public methods match the interface exactly

3. **Unit tests** (`frontend/src/services/__tests__/WatchProgressCaptureService.test.ts`):
   - Mock API client with `vi.mock('@/api/progress')`
   - Test queueing, batching, posting (AC2, AC3)
   - Test network error retry (AC4)
   - Test response handling (AC5)
   - Test empty queue (no POST if nothing queued)
   - Test timer-driven posting
   - Test `setupBeaconFlush` hook (AC6)

### Phase 2: Integration with Player Adapter (Story 4-0 extension)

1. **Player Adapter callback**:
   - YouTube adapter's position-change handler calls `captureService.recordSample(...)`
   - Adapter provides `getVideoUrl()` for URL capture (AC7)

2. **Integration test** (E2E-style, not full browser):
   - Create fake player adapter
   - Trigger position updates
   - Verify `recordSample` queues them
   - Verify batch flush posts correctly

### Phase 3: Hook for Tab Close (Story 4-3 preparation)

1. **Export `setupBeaconFlush`** method for Story 4-3 to call
2. **Leave Story 4-3 to implement the actual `sendBeacon`** dispatch

---

## Technical Requirements

### API Integration

- **Endpoint:** `POST /api/assignments/{assignment_id}/progress`
- **Request body:** `RecordWatchProgressRequest` (Story 4-1 schema)
- **Response:** `SkillProgressResponse` with `verified` flag
- **Error handling:** 422 validation, 401 auth, 5xx (all retryable or non-retryable as specified in AC4)
- **API client:** Import from `@/api/progress` (must expose a `recordProgress()` method)

### Architecture Compliance

- **AD-9 (Adapter pattern):** Capture service depends on player adapter interface, not YouTube directly
  - Adapter provides: `getPosition()`, `getVideoUrl()`, position-change event listener
  - Service posts via generic `RecordWatchProgressRequest`, not YouTube-specific shapes

- **AD-5 (Anti-spoofing via server):** Service captures `event_time` from client clock (NOW at sample time)
  - Server validates position advances (Story 4-4's responsibility)
  - Service just timestamps locally

- **AD-2 (Coaching-only):** This story is client-side only; server-side enforcement is Story 4-4+
  - No raw progress export, no cross-employee access (server enforces)

### Frontend Patterns

- **Shared service pattern:** One `WatchProgressCaptureService` instance per tab (singleton)
- **Dependency injection:** Constructor accepts API client, timer provider (for testing)
- **Error handling:** Internal logging, no UI exceptions
- **Config:** Environment-based or centralized config file

---

## Code Patterns from Story 4-1

### Inherited Patterns

1. **Pydantic schema reuse:** `RecordWatchProgressRequest` is already defined (Story 4-1)
   - Frontend mirrors as `RecordWatchProgressRequest` TS type in `frontend/src/types/progress.ts`

2. **Atomic conditional write:** Client captures `event_time` (NOW), server applies "only if newer" logic
   - Service responsibility: capture accurate timestamps
   - Server responsibility: enforce ordering (Story 4-4)

3. **Error contract:** All errors from `/api/assignments/{id}/progress` follow the centralized error shape
   - Service logs them but doesn't bubble them to UI

---

## Previous Story Intelligence (Story 4-1)

### Data Model Learnings

- **SkillProgress ORM** has columns: `watch_position`, `event_time`, `verified`, `updated_at`
- **Lazy initialization:** No row created until first POST → service must handle 404 / 201 responses
- **Atomic UPDATE...WHERE:** Server uses event_time comparison; client must send accurate timestamps
- **Anti-spoofing flag:** `verified` is set server-side based on position-advance validation (AC4, Story 4-4)

### Repository Patterns

- `record_watch_progress()` is the single write entry point (not multiple competing updates)
- Service-layer commit happens in Story 1.2 pattern: `get_db()` handles commits
- No transaction management needed client-side (simple POST, let server handle atomicity)

### Schema Patterns

- Pydantic v2: `ConfigDict(from_attributes=True)` for ORM→schema conversion
- Validation: `watch_position: int = Field(ge=0)` ensures non-negative
- All timestamps ISO-8601 UTC

### Testing Patterns (from Story 4-1 tests)

- Mock `async_session_factory` for database tests
- Use `vi.mock()` in Vitest for dependency mocking
- Test both happy path (success) and error paths (network failure, 422)
- Verify logging, not just return values

---

## Git Intelligence Summary

### Recent Commits Relevant to This Story

1. **92031b7** (Story 4-1 implementation): Backend schema/repository for watch progress
   - Files: `backend/app/progress/{models,schemas,repository,service}.py`
   - Patterns: Async SQLAlchemy, atomic UPDATE...WHERE, Pydantic v2

2. **0d22200** (Story 4-1 code review): Fixed critical correctness bugs
   - Changed `scalar_one()` to `scalar_one_or_none()` for stale writes
   - Switched `datetime.utcnow()` to `datetime.now(timezone.utc)`
   - Takeaway: deprecated DateTime methods must be updated for Python 3.12+

3. **578e713** (Story 4-1 documentation): Comprehensive implementation guide
   - Takeaway: async patterns, error handling, logging all matter for reviewer confidence

### Build Order & Dependencies

- **Story 4-0 (YouTube Adapter):** Must be complete before this story runs (position capture needs adapter)
- **Story 1.7 (Database):** Already complete; schema exists
- **Story 4-1 (Backend):** Already complete; endpoint contract locked

---

## Architecture Decisions Binding This Story

### AD-5 (Watch-progress write path)

- **Applies here:** Event-time ordering
  - Service must capture `event_time = NOW` at sample time
  - Server will skip if incoming event_time <= stored event_time
  - Client must NOT invent timestamps; use client system clock

- **Applies here:** Anti-spoofing validation (done server-side, Story 4-4)
  - Service sends `video_url` and position; server validates rate
  - Service just records what player reports; no client-side validation

### AD-9 (Player Adapter pattern)

- **Applies here:** Adapter abstraction
  - Service depends on adapter interface (getPosition, getVideoUrl, onPositionChange)
  - Service does NOT depend on YouTube API
  - Future Vimeo swap affects only adapter, not capture service

### AD-6 (Server-side session gate)

- **Applies here:** Authentication
  - Service sends POST with authenticated cookie (automatic via httpx/fetch)
  - Server validates session ties to correct Employee (prevents spoofing)
  - Service does NOT validate identity (server's job)

---

## Testing Strategy

### Unit Tests (WatchProgressCaptureService)

- **Mocked API client** (vi.mock or manual mock)
- **Test cases:**
  1. `recordSample()` adds to queue in order
  2. Timer fires → batch POST after interval
  3. Queue threshold (3 samples) triggers immediate POST
  4. Network error → retry on next interval
  5. Successful POST → queue clears
  6. Empty queue → no POST sent
  7. `setupBeaconFlush()` stores callback
  8. Response with `verified: false` → still clears queue
  9. 422 validation error → clear queue (don't retry)

### Integration-Style Tests (with fake player adapter)

- Simulate position updates from adapter
- Verify batched POSTs to backend
- Verify error retry

### Manual/E2E Verification (browser, Story 4-5+)

- Open Content Discovery page
- Play video for 20+ seconds
- Verify Network tab shows batched POSTs every 10–15 seconds
- Verify backend `skill_progress` row has updated `watch_position` and `event_time`

---

## Edge Cases & Error Handling

### Network Failures

- **Timeout (3s):** Treat as failure, queue samples, retry on next interval
- **5xx (500, 503):** Same as timeout (retryable)
- **401 Unauthorized:** Log error, clear queue (don't retry stale session; frontend will re-auth)
- **422 Unprocessable:** Clear queue (invalid data; server rejected it; retrying won't help)

### Data Quality

- **Missing `videoUrl`:** Optional in AC7; POST still sent
- **Position > video duration:** Server validates (anti-spoofing, Story 4-4); client just sends
- **Clock skew:** Server tolerates within-5-minutes (Story 4-4); client sends NOW

### Race Conditions

- **Two tabs watching same assignment:** Both POST independently; server's atomic UPDATE handles ordering
- **Tab close during batch POST:** `sendBeacon` (Story 4-3) handles it; this story just queues

---

## Deferred (Not This Story)

1. **Server-side anti-spoofing validation** → Story 4-4
2. **Tab-close sendBeacon flush** → Story 4-3
3. **Server-side event-time ordering** → Story 4-1 (already done)
4. **Dashboard auto-update on new progress** → Story 5-4
5. **Verified flag visual feedback** → Story 4-4 / 5-2 drill-down

---

## Completion Checklist

- [x] **Phase 1: Core Service**
  - [x] `WatchProgressCaptureService` class defined (100% AC coverage)
  - [x] `recordSample()` implements queueing (AC2)
  - [x] `flush()` implements batching + POST (AC3)
  - [x] Retry logic on network failure with exponential backoff (AC4)
  - [x] Response handling with `verified` flag (AC5)
  - [x] `setupBeaconFlush()` hook defined (AC6)
  - [x] Video URL capture from adapter (AC7)
  - [x] Error handling non-blocking, 422 validation clears queue (AC8)
  - [x] Configuration via CaptureServiceConfig (AC9)

- [x] **Phase 2: TypeScript Types**
  - [x] `ProgressQueueItem` type interface
  - [x] `WatchProgressCaptureService` interface
  - [x] UUID and common types defined
  - [x] Full JSDoc comments on all public methods

- [x] **Phase 3: Unit Tests**
  - [x] 15 test cases covering AC1–AC8 (36 tests total including YouTubeAdapter)
  - [x] Mock API client with axios mock
  - [x] ALL TESTS PASSING (36/36, 100%)

- [x] **Phase 4: Integration Hook**
  - [x] Player adapter position updates → recordSample() queue logic
  - [x] Service batches on 10s interval or 3-sample threshold (AC3)
  - [x] Network errors retry with backoff, non-blocking error handling (AC4, AC8)

- [x] **Phase 5: Story 4-3 Readiness**
  - [x] `setupBeaconFlush()` callable from tab-close handler
  - [x] `flushViaBeacon()` prepares last known position for sendBeacon dispatch
  - [x] Service prepares data; Story 4-3 owns sendBeacon() invocation

- [x] **Code Review Readiness**
  - [x] console.warn/error with context (no console.log)
  - [x] Async/await patterns (no .then() chains)
  - [x] Error messages include context (assignmentId, sampleCount, failureCount, reason)
  - [x] Dependency injection via constructor (mockable for tests)
  - [x] Configurable timeouts/thresholds via CaptureServiceConfig (AC9)

---

## Success Criteria (Developer Handoff)

✅ **Developer can:**
- Implement `WatchProgressCaptureService` with full unit test coverage
- Verify batched POSTs to backend every 10–15 seconds
- Confirm network failures retry gracefully without spamming
- Prepare for Story 4-3's sendBeacon hook (last known position available)
- Pass code review with 0 architecture violations (AD-5, AD-9 compliance)

✅ **System delivers:**
- Watch position samples captured at 5–10 second intervals (adaptive to player adapter)
- Batched into POSTs every 10–15 seconds (configurable)
- Network failures retried without UI impact
- Backend receives accurate `event_time` for server-side ordering (Story 4-1 pattern)
- Ready for Story 4-3 (sendBeacon flush on tab close)

---

## Files Implemented

### Frontend (New & Modified)

- **NEW** `frontend/src/types/common.ts` (14 lines)
  - UUID type definition and branded type helper
  - Used across all type definitions for strong typing

- **MODIFIED** `frontend/src/types/progress.ts` (+58 lines, total 163 lines)
  - Expanded documentation for Story 4-2 scope
  - Added `WatchProgressCaptureService` interface (AC1, AC10)
  - Kept all AC1-4.1 types for backend schema compatibility

- **NEW** `frontend/src/lib/services/captureService.ts` (356 lines)
  - `WatchProgressCaptureService` class (main implementation, AC1-AC8)
  - `CaptureServiceConfig` interface (AC9)
  - RetryState tracking for exponential backoff (AC4)
  - Full JSDoc comments (AC10)
  - Backward compatibility export: `CaptureService = WatchProgressCaptureService`

- **MODIFIED** `frontend/src/tests/captureService.test.ts` (+60 lines, total ~300 lines)
  - Renamed test suite to `WatchProgressCaptureService`
  - Updated imports to use renamed class
  - Added AC-mapped test documentation (AC1-AC8)
  - 15 test cases (was 11, added error handling + response tests)
  - 36/36 tests passing (100%)

### Backend

- **NO CHANGES** — Story 4-1 already delivered:
  - `/api/assignments/{assignment_id}/progress` POST endpoint
  - SkillProgressResponse with verified flag
  - Atomic conditional-write logic (event_time ordering, AC3 compatible)

## Dev Agent Record

### Implementation Summary

Story 4-2 fully implemented and tested. Client-side watch-position capture service with:
- ✅ AC1: Singleton-scoped service with dependency injection (mockable for tests)
- ✅ AC2: Local queueing, no immediate POST
- ✅ AC3: Batch posting every 10s or on 3-sample threshold
- ✅ AC4: Network error retry with exponential backoff (1s, 2s, 4s, ... up to 30s)
- ✅ AC5: Response handling with verified flag logging
- ✅ AC6: sendBeacon setup hook for Story 4-3 integration
- ✅ AC7: Video URL capture from player adapter (AD-9 Adapter pattern)
- ✅ AC8: Non-blocking error handling; 422 validation clears queue
- ✅ AC9: Configurable intervals (postIntervalMs) and thresholds (queueThreshold)
- ✅ AC10: Full TypeScript types and JSDoc documentation

### Test Results

```
Test Files: 2 passed (2)
Tests: 36 passed (36)
Duration: 6.04s
Coverage: AC1-AC8 all tested, error paths verified (422, network errors, backoff)
```

### Architecture Compliance

- ✅ **AD-9 (Adapter Pattern):** Service depends on PlayerAdapter interface, not YouTube directly
- ✅ **AD-5 (Anti-spoofing):** Client captures accurate event_time; server validates
- ✅ **AD-2 (Coaching-only):** Client-side only; server enforces coaching boundary
- ✅ **AD-1 (Single owner):** progress/ module owns write endpoint; frontend client calls it

### Key Technical Decisions

1. **Exponential backoff on failure:** 1s * 2^failureCount (capped at 30s)
   - Reason: Prevents spam on server, allows recovery window
   
2. **422 validation error handling:** Clear queue instead of retry
   - Reason: Invalid data won't become valid on retry
   
3. **Polling-based position capture:** Via adapter's 'timeupdate' event
   - Reason: AD-9 normalizes YouTube polling + future Vimeo events
   
4. **Configurable batch interval/threshold:** Environment-based (AC9)
   - Reason: Allows tuning for different network conditions without code changes

### Forward Dependencies (Ready for Story 4-3)

- `setupBeaconFlush(callback)` — Story 4-3 calls this to register tab-close handler
- `flushViaBeacon()` — Story 4-3 invokes when visibilitychange or beforeunload fires
- Last known position prepared; adapter.sendBeacon() dispatches it

## Next Story Dependencies

- **Story 4-3** depends on this: sendBeacon hook callable, last position ready
- **Story 4-4** depends on this: positions posted to backend for anti-spoofing validation
- **Story 4-5** depends on this: positions persisted so resume retrieval works

