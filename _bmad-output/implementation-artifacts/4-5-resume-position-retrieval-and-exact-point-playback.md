---
story_key: 4-5-resume-position-retrieval-and-exact-point-playback
epic: 4
story_num: 5
dependencies: 
  - 4-1-skill-progress-data-model-and-watch-position-storage
  - 4-2-watch-position-capture-and-periodic-posting
  - 4-3-tab-close-flush-via-sendbeacon-reliability
  - 4-4-server-side-anti-spoofing-validate-position-advances
status: done
completed_date: 2026-07-11
---

# Story 4-5: Resume Position Retrieval & Exact-Point Playback

**Epic:** 4 (Video Progress Capture & Resume)  
**Status:** ✅ DONE (2026-07-11)  
**Story ID:** 4.5  
**Functional Requirements:** FR-6 (Employee resumes a video at the exact last-watched position)  
**Non-Functional Requirements:** NFR-L4 (Video resume starts within 1 second of clicking Continue Watching)  
**Architecture Decisions:** AD-5, AD-9  

---

## User Story

As an **Employee**,
I want to resume a video from exactly where I left off,
So that I don't have to re-scrub or lose my place, enabling fast re-engagement with interrupted learning.

---

## Acceptance Criteria

### AC1: GET Endpoint for Position Retrieval

**Given** an authenticated Employee session  
**When** calling `GET /api/assignments/{assignment_id}/progress`  
**Then**:
- The endpoint returns the stored watch position (if any) and its event timestamp
- Response format: `{ watch_position: integer (seconds), event_time: ISO-8601 string, verified: boolean }`
- If no position has been recorded yet (first view), return `{ watch_position: 0, event_time: null, verified: false }`
- Endpoint requires authentication (JWT from cookie) and role=EMPLOYEE (AD-6)
- Endpoint hard-scopes the result to the authenticated session's identity (session.user_id must match assignment.employee_id)

**Status Code Responses:**
- `200 OK` — position found, start playback at watch_position
- `404 Not Found` — assignment does not exist (or authenticated user cannot access it)
- `401 Unauthorized` — no valid session
- `403 Forbidden` — user is not the assignment's owner (security boundary)

**Example Response (Successful Resume):**
```json
{
  "watch_position": 872,
  "event_time": "2026-07-06T14:32:00Z",
  "verified": true
}
```

**Example Response (First View):**
```json
{
  "watch_position": 0,
  "event_time": null,
  "verified": false
}
```

---

### AC2: Exact Position Accuracy (Launch-Blocking Quality Gate)

**Given** an Employee watched a video to 14:32 (872 seconds) and closed the tab  
**When** they return 3 days later and fetch the resume position  
**Then**:
- The returned `watch_position: 872` must be the EXACT stored position (not rounded, not approximate)
- The YouTube IFrame is initialized with `startSeconds=872`
- Playback starts at 14:32 ± 1 second tolerance (due to video encoding keyframes)
- **CRITICAL:** On first-ever resume, the position must be exact; a wrong resume point on first encounter is a **launch-blocking defect** (NFR-L4 feedback target)

**Test Scenario (Regression Prevention):**
- Student watches to minute 5:23 (323 seconds) and closes
- 5 minutes later, resumes: position must be 323 seconds (not 300, not 330, not 0)
- Video player initializes with `startSeconds=323`
- Playback visibly starts at ~5:23 mark

---

### AC3: Out-of-Bounds Position Fallback

**Given** the stored `watch_position` is corrupted or beyond video duration  
**When** the backend retrieves it or the frontend prepares to resume  
**Then**:
- Validation: if stored position > video_duration (from content metadata), treat as invalid
- Fallback behavior: return `{ watch_position: 0 }` (start from beginning, fail-safe)
- Log diagnostic: `event="progress_out_of_bounds_fallback" assignment_id=X stored_position=Y video_duration=Z`
- Client sees a "Start from the beginning" state, not a crash or blank player

**Edge Case: Missing Video Duration**  
**Given** an assignment has `content_id = NULL` (no linked content)  
**When** retrieval cannot validate bounds (no duration available)  
**Then** return the stored position as-is (no bounds check possible)
- Log diagnostic: `event="progress_no_video_duration_skip_bounds_check" assignment_id=X`

---

### AC4: Hard-Scoping to Authenticated Session Identity (AD-6 Compliance)

**Given** an authenticated Employee session for user_id=casey  
**When** that session calls `GET /api/assignments/{assignment_id}/progress`  
**Then** the repository layer HARD-SCOPES the query:
- Fetch the Assignment matching {assignment_id}
- Verify assignment.employee_id == session.user_id
- If mismatch: return 403 Forbidden (not 404, to avoid timing leaks)
- If match: proceed to fetch skill_progress

**CRITICAL: Repository-Layer Enforcement**  
**Given** the hardcoded parameter `?employee_id=morgan` in the request (attempt override)  
**WHEN** the repository layer queries  
**THEN** it still applies the hard-scoped WHERE clause `employee_id = casey` (from JWT), returning only casey's progress
- Response is casey's position (not morgan's, not an error)
- Log: no special log (silent enforcement is correct, no need to leak scoping mechanism)

**Example Query (Pseudocode):**
```python
# Service receives: session.user_id = casey, assignment_id = X
# Repository builds:
assignment = db.query(Assignment).filter(
    Assignment.id == assignment_id,
    Assignment.employee_id == session.user_id  # HARD-SCOPED
).first()
if not assignment:
    raise Forbidden("No access to this assignment")
```

---

### AC5: Client-Side Initialization via startSeconds (TypeScript/YouTube Adapter)

**Given** the client receives `{ watch_position: 872 }`  
**When** the video player is initialized  
**Then**:
- The YouTube IFrame Adapter calls `player.seekTo(watch_position, true)` OR sets `startSeconds: watch_position` in the iframe URL
- Playback begins at the exact second (within ±1 second tolerance for keyframes)
- No manual scrubbing or offset calculations on the client side
- The adapter must handle `startSeconds=0` correctly (first view case, no seeking needed)

**Implementation Detail:**  
The YouTube IFrame API supports both approaches:
1. **URL Parameter:** `https://www.youtube.com/embed/{video_id}?start={startSeconds}`
2. **Seekto Call:** `player.seekTo(seconds, true)` after player ready

Choose URL parameter for simplicity (no race condition with player initialization).

---

### AC6: No Data Loss on Retry (Idempotent Read)

**Given** the client calls `GET /api/assignments/{assignment_id}/progress` multiple times  
**When** the same assignment is queried repeatedly  
**Then**:
- Response is identical (same position, same timestamp)
- No side effects (read-only, no writes)
- Multiple retries due to network errors don't corrupt or advance progress
- Each call is safe to repeat

---

### AC7: Latency Performance (NFR-L4)

**Given** an Employee clicks "Continue Watching"  
**WHEN** the flow is triggered:
1. Client calls `GET /api/assignments/{assignment_id}/progress` (network latency + server processing)
2. Server returns position (database query + serialization)
3. Client initializes player with `startSeconds=position` (client processing)
4. Video begins playback  
**THEN** total latency from click to playback ≤ 1 second (NFR-L4 requirement)

**Performance Optimization Hints:**
- GET endpoint should execute in <100ms (fast query: single row from `skill_progress`, join to fetch duration)
- Client must not debounce or delay initialization
- No polling loops or retries in the happy path (only on error)

**Test Scenario (Performance):**
- Client sends GET at T=0
- Server responds by T=80ms (database + serialization)
- Client initializes player by T=100ms
- Playback starts by T=300-500ms (network + browser rendering)
- Total: well under 1 second ✅

---

### AC8: Null/Empty Position Handling (Edge Case)

**Given** the `skill_progress` row does NOT exist (first view of assignment)  
**WHEN** the GET endpoint is called  
**THEN**:
- Query returns no rows (no skill_progress row exists yet)
- Service interprets this as "no position recorded"
- Response: `{ watch_position: 0, event_time: null, verified: false }`
- Client treats this as "start from beginning"

**Do NOT create a dummy skill_progress row on GET.** Reading must never write.

---

### AC9: TypeScript Types & Frontend Integration

**Given** the frontend `src/types/progress.ts`  
**When** types are defined  
**Then** they match the backend response:

```typescript
interface SkillProgressResponse {
  watch_position: number;         // seconds (integer)
  event_time: string | null;      // ISO-8601 UTC or null if first view
  verified: boolean;              // true if passed anti-spoofing, false if not recorded yet
}
```

**Client State Hook (Example Pattern):**
```typescript
const [resumePosition, setResumePosition] = useState<number>(0);
const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  apiClient
    .get(`/assignments/${assignmentId}/progress`)
    .then(r => {
      setResumePosition(r.data.watch_position || 0);
      // Use resumePosition in player initialization
    })
    .catch(err => {
      console.error('Failed to fetch resume position', err);
      setResumePosition(0); // fallback to start
    })
    .finally(() => setIsLoading(false));
}, [assignmentId]);
```

---

### AC10: Access Control & Coaching-Only Boundary (AD-2)

**Given** an HR_ADMIN session  
**WHEN** calling `GET /api/assignments/{assignment_id}/progress` for an assignment they manage  
**THEN** the endpoint returns 403 Forbidden (Employees only can resume their own videos)
- HR Admins view drill-down provenance via Story 5-2's separate endpoint
- This resume endpoint is Employee-only (role check at router/dependency layer)

**Given** a valid EMPLOYEE session but for a different assignment  
**WHEN** calling GET with `assignment_id=someone_else_s_assignment`  
**THEN** returns 403 Forbidden (session.user_id != assignment.employee_id)

---

### AC11: Backward Compatibility (Stories 4-1, 4-2, 4-3, 4-4)

**Given** all prior stories have shipped  
**WHEN** this story retrieves positions  
**THEN**:
- Response format matches existing `SkillProgressResponse` (AC9)
- No breaking changes to `skill_progress` table schema
- Works seamlessly with verified flag from Story 4-4 (client logs diagnostic if verified=false)
- sendBeacon writes from Story 4-3 are read correctly here
- No regressions in Stories 4-1 through 4-4 test suites

---

### AC12: Comprehensive Testing

**Given** all acceptance criteria  
**WHEN** test coverage is complete  
**THEN** implement:

#### **Unit Tests (Repository Layer)**
- `test_get_position_for_assignment_first_view` — no skill_progress row, returns 0
- `test_get_position_for_assignment_resume` — skill_progress exists, returns stored position
- `test_get_position_hard_scoped_to_employee` — query includes employee_id filter
- `test_get_position_missing_assignment` — assignment doesn't exist, returns empty

#### **Unit Tests (Service Layer)**
- `test_retrieve_position_converts_null_to_zero` — null event_time on first view
- `test_retrieve_position_handles_verified_flag` — passes through verified from repo
- `test_retrieve_position_validation_out_of_bounds` — position > duration, returns 0 (fallback)

#### **Integration Tests (API Endpoint)**
- `test_get_progress_endpoint_returns_200_with_position` — happy path, authenticated employee
- `test_get_progress_endpoint_returns_403_wrong_employee` — hard-scoped, different employee
- `test_get_progress_endpoint_returns_401_no_auth` — unauthenticated, rejected
- `test_get_progress_endpoint_hr_admin_forbidden` — role check, HR cannot call
- `test_get_progress_idempotent_repeated_calls` — multiple calls return same result

#### **End-to-End Tests (Full Resume Flow)**
- `test_resume_flow_watch_record_retrieve_initialize` — write a position via POST (Story 4-2), retrieve via GET (this story), verify exact match
- `test_resume_flow_performance_under_1_second` — measure end-to-end latency
- `test_resume_flow_no_position_starts_at_zero` — first view, starts from beginning

#### **Edge Case Tests**
- `test_resume_position_null_event_time_on_first_view` — correctly handled
- `test_resume_position_out_of_bounds_fallback` — invalid stored value triggers fallback
- `test_resume_position_missing_video_duration_no_validation` — assignment.content_id=NULL, returns as-is
- `test_resume_position_concurrent_write_and_read` — simultaneous POST (Story 4-2) and GET race (no corruption)

#### **Test Organization**
- Unit tests: `backend/app/progress/tests/test_position_retrieval.py`
- Integration tests: `backend/app/progress/tests/test_progress_endpoint.py`
- E2E tests: `backend/tests/test_resume_flow_integration.py` (or within existing test file)

**Expected Test Count:** 15–20 tests, all passing, 0 regressions

---

## Developer Context — What You Must Know

### Critical Files Being Modified

#### `backend/app/progress/service.py`
**Current State:** Service layer with `record_watch_progress()` for writes (Stories 4-1, 4-2, 4-4).

**What This Story Adds:**
- New method: `async def get_resume_position(session, assignment_id) -> SkillProgressResponse`
- Logic:
  1. Fetch Assignment where `id==assignment_id AND employee_id==session.user_id` (hard-scoping)
  2. If not found: return 403
  3. Fetch related `skill_progress` row (if it exists)
  4. If no skill_progress row: return `{ watch_position: 0, event_time: null, verified: false }`
  5. If skill_progress exists:
     - Check if `watch_position > video_duration` (from assignment.content.metadata)
     - If out-of-bounds: return 0 (fallback), log diagnostic
     - Otherwise: return `{ watch_position, event_time, verified }`

**What Must NOT Change:**
- Existing `record_watch_progress()` method (Stories 4-1, 4-2, 4-4 depend on it)
- `SkillProgressResponse` schema (already defined in Story 4-1)
- Any write paths

---

#### `backend/app/progress/router.py`
**Current State:** Router with POST endpoint for watch-progress writes.

**What This Story Adds:**
- New GET endpoint: `GET /api/assignments/{assignment_id}/progress`
- Dependencies: JWT authentication (FastAPI dependency for CurrentUser), assignment_id path param
- Route handler:
  1. Extract CurrentUser from dependency
  2. Call `service.get_resume_position(current_user, assignment_id)`
  3. Return SkillProgressResponse with 200 OK

**Example Route:**
```python
@router.get("/assignments/{assignment_id}/progress")
async def get_watch_progress(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(require_role("EMPLOYEE")),
    service: ProgressService = Depends(),
):
    result = await service.get_resume_position(current_user, assignment_id)
    return result
```

---

#### `backend/app/progress/repository.py`
**Current State:** Repository with `record_watch_progress()` write method.

**What This Story Adds:**
- New method: `async def get_progress_by_assignment(assignment_id, employee_id) -> SkillProgress | None`
- Query: `SELECT * FROM skill_progress WHERE assignment_id = ? AND EXISTS (SELECT 1 FROM assignments WHERE id=? AND employee_id=?)`
- This ensures hard-scoping at the repository layer (double-check)

**Relationship Fetching:**
- Join to `assignments` table to verify employee_id (hard-scoping)
- Join to `assignments.content` to fetch video_duration (for bounds validation)
- Fetch `assignments.skill` if needed (optional, for logging context)

---

#### `frontend/src/api/progressApi.ts`
**Current State:** API client for progress endpoints (writes from Story 4-2).

**What This Story Adds:**
- New method: `getResumePosition(assignmentId: UUID): Promise<SkillProgressResponse>`
- Calls: `GET /api/assignments/{assignmentId}/progress`
- Error handling:
  - 404: assignment not found → treat as first view (return position 0)
  - 403: access denied → redirect to dashboard (shouldn't happen in normal flow)
  - 401: not authenticated → redirect to login
  - 500: server error → log and fall back to position 0

---

#### `frontend/src/features/video-player/hooks/useResumePosition.ts`
**Current State:** Hook for initializing video player (story 4.0 foundation).

**What This Story Adds:**
- Hook calls `progressApi.getResumePosition(assignmentId)` on component mount
- Sets `resumePosition` state
- Passes to YouTube IFrame: `startSeconds={resumePosition}`
- Handles loading/error states

**Example Implementation:**
```typescript
export function useResumePosition(assignmentId: string) {
  const [position, setPosition] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPosition = async () => {
      try {
        const data = await progressApi.getResumePosition(assignmentId);
        setPosition(data.watch_position ?? 0);
      } catch (err) {
        console.error('Failed to fetch resume position:', err);
        setError('Could not load resume position. Starting from beginning.');
        setPosition(0);
      } finally {
        setLoading(false);
      }
    };

    fetchPosition();
  }, [assignmentId]);

  return { position, loading, error };
}
```

---

### Key Architecture Decisions (AD-5, AD-6, AD-9)

**AD-5: Watch-progress write path**
- This story is the READ side of AD-5 (write side is Stories 4-1/4-2/4-4)
- Reading must never write or advance progress
- Idempotent reads only

**AD-6: Server-side session/role/identity gate**
- Hard-scoping at repository layer ensures session identity is enforced
- HR_ADMIN role denied at router (dependency check)
- 403 on identity mismatch (not 404, to avoid timing leaks)

**AD-9: Video capture behind a player Adapter**
- This story uses adapter's `startSeconds` initialization
- Adapter handles YouTube's seekTo API details
- Future Vimeo adapter will use same pattern

---

### Previous Story Patterns (Stories 4-1 through 4-4 Intelligence)

**Story 4-1 (Watch-Position Storage):**
- `skill_progress` table keyed by `assignment_id` (not user_id/skill_id pair)
- Stores `watch_position` (integer, seconds), `event_time` (ISO-8601), `verified` (boolean)
- ✅ This story reads from the same table structure

**Story 4-2 (Client Capture):**
- Posts to `/api/assignments/{assignment_id}/progress` every 10–15 seconds
- Sends `{ watch_position, event_time, video_url }`
- ✅ This story retrieves what Story 4-2 wrote

**Story 4-3 (sendBeacon Flush):**
- Sends final position on tab close via sendBeacon
- Same POST endpoint, same payload
- ✅ This story sees the last flushed position from sendBeacon

**Story 4-4 (Anti-Spoofing):**
- Validates incoming positions and sets `verified: true/false`
- ✅ This story returns the `verified` flag to client (informational only for resume)

---

### Testing & Implementation Order

**Phase 1: Repository Method (Data Access)**
1. Write unit test: `test_get_progress_by_assignment_with_hard_scoping`
2. Implement `get_progress_by_assignment()` in repository
3. Run test, verify passing

**Phase 2: Service Layer (Business Logic)**
1. Write unit tests for `get_resume_position()` (happy path, no position, out-of-bounds)
2. Implement service method
3. Run tests

**Phase 3: Router & Endpoint (HTTP API)**
1. Write integration tests for GET endpoint (200, 403, 401)
2. Implement router GET method
3. Run tests

**Phase 4: Frontend Integration**
1. Write API client method: `progressApi.getResumePosition()`
2. Implement hook: `useResumePosition()`
3. Integrate into video player component

**Phase 5: End-to-End & Performance**
1. Write E2E test: watch → record → retrieve → verify exact match
2. Measure latency (target <1 second)
3. Performance tune if needed

---

### Common Developer Mistakes to Avoid

1. **Do NOT write to skill_progress on read.** GET must be read-only, idempotent. No side effects.

2. **Do NOT skip the hard-scoping check.** Even though the JWT is already validated, verify `assignment.employee_id == session.user_id` at the repository layer (defense in depth per AD-6).

3. **Do NOT return HR-accessible data.** This endpoint is EMPLOYEE-only. If an HR_ADMIN somehow calls it, reject with 403 (enforced at router dependency layer).

4. **Do NOT assume video_duration always exists.** Assignment can have `content_id = NULL`. Handle gracefully: skip out-of-bounds check, return position as-is, log diagnostic.

5. **Do NOT use position=0 as "no position recorded."** The difference matters: start-from-beginning (user watched nothing) vs. out-of-bounds-fallback (corrupted data). Both return 0, but log differently for forensics.

6. **Do NOT cache positions in the client across sessions.** Always fetch fresh from backend (positions can change if Story 4-2 writes new data).

7. **Do NOT delay player initialization while fetching position.** Use a loading state, show skeleton, but don't block video player mount. Use fallback position=0 if fetch fails.

8. **Do NOT hardcode the 1-second latency tolerance.** NFR-L4 is a target, not a guardrail. Measure real deployments; adjust if needed.

---

### Architecture Compliance Checklist

- ✅ **AD-1 (Single-owner modules):** Read method in `progress/` service (owns `skill_progress`)
- ✅ **AD-2 (Coaching-only read boundary):** GET endpoint is EMPLOYEE-only, HR uses Story 5-2 drill-down instead
- ✅ **AD-5 (Watch-progress write path):** READ side only, doesn't interfere with write ordering (AC5 from Story 4-1)
- ✅ **AD-6 (Session/role/identity gate):** Hard-scoped at repository, role-checked at router, 403 on mismatch
- ✅ **AD-9 (Video adapter):** Uses content metadata (video_duration), not YouTube API

---

### Files & Modules Summary

| File | Role | Change Type |
|------|------|------------|
| `backend/app/progress/service.py` | `get_resume_position()` business logic | **UPDATE** |
| `backend/app/progress/repository.py` | `get_progress_by_assignment()` query | **UPDATE** |
| `backend/app/progress/router.py` | GET `/api/assignments/{id}/progress` endpoint | **UPDATE** |
| `backend/app/progress/schemas.py` | `SkillProgressResponse` (already exists from Story 4-1) | No change |
| `backend/app/progress/models.py` | ORM models (unchanged) | No change |
| `frontend/src/api/progressApi.ts` | `getResumePosition()` client | **UPDATE** |
| `frontend/src/features/video-player/hooks/useResumePosition.ts` | Resume position hook | **NEW** |
| `backend/app/progress/tests/test_position_retrieval.py` | Position retrieval unit tests | **NEW** |
| `backend/app/progress/tests/test_progress_endpoint.py` | Endpoint integration tests | **NEW** |

---

## Success Criteria

**Definition of Done:**
- [ ] AC1–AC12 all implemented and passing
- [ ] All position retrieval tests passing (15–20 tests)
- [ ] Story 4-1 through 4-4 regression tests still passing
- [ ] Performance measured: GET endpoint + client initialization < 1 second (NFR-L4)
- [ ] Hard-scoping verified: calling endpoint as wrong employee returns 403, not 404 or 200
- [ ] Out-of-bounds fallback tested: position > duration returns 0, logs diagnostic
- [ ] Null/empty position on first view tested: returns 0, event_time=null, verified=false
- [ ] Code review identifies 0 security issues (hard-scoping, role checks)
- [ ] End-to-end manual test: watch 5:23 → close → resume → starts at ~5:23 (±1 second)

---

## Open Questions / Deferred Decisions

1. **Out-of-bounds tolerance:** Should the fallback be position=0 or the stored position (unchecked)? Current spec: return 0 (fail-safe). Confirm with team.

2. **Event-time staleness:** Should the endpoint check if the stored event_time is very old (e.g., >30 days) and suggest starting over? Current spec: return as-is, no staleness check on read.

3. **Video duration source:** Assume `content_catalog.metadata['duration']` is populated by Story 2-3. If not, bounds validation skipped. Confirm Story 2-3 populates this field.

4. **Performance optimization:** Should the repository use database-side caching (e.g., Redis) for frequently-accessed positions? Current spec: direct database query (<100ms acceptable for MVP).

---

## Tasks & Subtasks

- [ ] **Task 1: Repository method** (`backend/app/progress/repository.py`)
  - [ ] Implement `get_progress_by_assignment(assignment_id, employee_id)`
  - [ ] Test hard-scoping (employee_id filter applied)
  - [ ] Handle missing skill_progress row (return None)

- [ ] **Task 2: Service method** (`backend/app/progress/service.py`)
  - [ ] Implement `get_resume_position(session, assignment_id)`
  - [ ] Validate hard-scoping (reject if session.user_id != assignment.employee_id)
  - [ ] Handle out-of-bounds: return 0 with diagnostic log
  - [ ] Handle first view (no skill_progress row): return 0

- [ ] **Task 3: Router endpoint** (`backend/app/progress/router.py`)
  - [ ] Create GET `/api/assignments/{assignment_id}/progress`
  - [ ] Add role dependency (EMPLOYEE only)
  - [ ] Wire service method
  - [ ] Return SkillProgressResponse (200 OK)

- [ ] **Task 4: API client** (`frontend/src/api/progressApi.ts`)
  - [ ] Implement `getResumePosition(assignmentId)`
  - [ ] Error handling (404 → treat as first view, 403 → redirect, etc.)

- [ ] **Task 5: Frontend hook** (`frontend/src/features/video-player/hooks/useResumePosition.ts`)
  - [ ] Fetch position on component mount
  - [ ] Manage loading/error state
  - [ ] Return position for player initialization

- [ ] **Task 6: Repository tests** (`backend/app/progress/tests/test_position_retrieval.py`)
  - [ ] Test happy path (position found)
  - [ ] Test first view (no skill_progress row)
  - [ ] Test hard-scoping (employee_id filter)

- [ ] **Task 7: Service tests** (`backend/app/progress/tests/test_position_retrieval.py`)
  - [ ] Test out-of-bounds fallback
  - [ ] Test null event_time on first view
  - [ ] Test verified flag pass-through

- [ ] **Task 8: Integration tests** (`backend/app/progress/tests/test_progress_endpoint.py`)
  - [ ] Test 200 OK response
  - [ ] Test 403 Forbidden (wrong employee)
  - [ ] Test 401 Unauthorized (no auth)
  - [ ] Test HR_ADMIN rejection (role check)
  - [ ] Test idempotency (repeated calls same result)

- [ ] **Task 9: E2E tests** (`backend/tests/test_resume_flow_integration.py`)
  - [ ] Test full flow: watch → record (Story 4-2) → retrieve → verify exact match
  - [ ] Measure latency (target <1 second)
  - [ ] Test concurrent write and read race

---

## Implementation Notes

### Position Retrieval Flow

```
Client: Click "Continue Watching"
  ↓
Client: Fetch GET /api/assignments/{id}/progress
  ↓
Router: Dependency check (CurrentUser, EMPLOYEE role)
  ↓
Service: Validate hard-scoping (session.user_id == assignment.employee_id)
  ↓
Service: Call repository.get_progress_by_assignment(id, user_id)
  ↓
Repository: Query skill_progress where assignment_id = ? (with hard-scope WHERE on employee_id)
  ↓
Service: Check bounds (position ≤ video_duration)
  ↓
Service: If out-of-bounds: return 0 (fallback), log diagnostic
  ↓
Service: Return { watch_position, event_time, verified }
  ↓
Client: Receive response
  ↓
Client: Initialize YouTube IFrame with startSeconds={watch_position}
  ↓
Video playback starts at exact position ✅
```

### Hard-Scoping Pattern (AD-6)

```python
# Repository layer (double-check enforcement):
assignment = db.query(Assignment).filter(
    Assignment.id == assignment_id,
    Assignment.employee_id == employee_id  # <-- HARD-SCOPED
).first()

if not assignment:
    raise Forbidden("No access to this assignment")

skill_progress = db.query(SkillProgress).filter(
    SkillProgress.assignment_id == assignment.id
).first()

# Result: even if someone forges a request with wrong employee_id,
# the WHERE clause ensures only the authenticated user's assignment is returned.
```

---

## Dev Agent Record

### Pre-Implementation Checklist
- ✅ Reviewed Stories 4-1, 4-2, 4-3, 4-4 to understand dependencies
- ✅ Confirmed SkillProgress schema (watch_position, event_time, verified)
- ✅ Confirmed hard-scoping pattern from Story 1-3 (AD-6 compliance)
- ✅ Reviewed NFR-L4 requirement (< 1 second latency)
- ✅ Confirmed YouTube IFrame startSeconds initialization method

### Architecture Integration
- Position retrieval is the READ side of AD-5 (Story 4-1/4-2/4-4 handle writes)
- Hard-scoping enforced at repository layer per AD-6 pattern
- EMPLOYEE-only endpoint per AD-2 coaching-only boundary
- Fallback to 0 on out-of-bounds per fail-safe principle

---

## Story Completion Status

**Status:** ready-for-dev

This story file is comprehensive and provides the dev agent with:
- ✅ Clear acceptance criteria (AC1–AC12)
- ✅ Exact position accuracy requirement (launch-blocking quality gate)
- ✅ Hard-scoping enforcement (AD-6 compliance)
- ✅ Performance requirement (NFR-L4, < 1 second)
- ✅ Testing strategy (15–20 tests covering all scenarios)
- ✅ File-by-file implementation guidance
- ✅ Common mistakes to avoid
- ✅ Integration with Stories 4-1 through 4-4

Ready for dev-story workflow.
