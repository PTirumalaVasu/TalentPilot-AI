# Adversarial Divergence Review — TalentPilot-AI Architecture Spine

**Reviewer:** Adversarial Divergence Hunter Agent  
**Date:** 2026-07-09  
**Target:** ARCHITECTURE-SPINE.md  
**Scope:** Modules one level down (auth, assignments, content_discovery, watch_progress, dashboard)

---

## Verdict: HOLES_FOUND

**Critical Finding:** Multiple modules can legally compute Status/Provenance differently under current ADs, leading to dashboard showing different badge states than watch_progress and assignments modules expect. SSE trigger mechanism is unspecified, allowing races between write completion and dashboard refresh. JWT validation rules are underspecified for edge cases.

---

## Adversarial Attack Scenarios

### 1. Status & Provenance Computation Divergence (CRITICAL)

**Attack:** `watch_progress` and `dashboard` modules each implement AD-16 independently, computing Status/Provenance from same database rows but with different interpretations.

**Construction:**

**watch_progress implementation (literal AD-16 compliance):**
```python
# AD-16: "0% → Not Started, 1-99% → In Progress, 100% → Completed"
if percent == 0:
    status = "not_started"
elif percent == 100:
    status = "completed"
else:
    status = "in_progress"

# Provenance: checks in order listed in AD-16
if row.hr_override:
    provenance = "HR Override"
elif row.provenance == 'verified' and (now - row.updated_at).days <= 7:
    provenance = "Verified"
elif row.provenance == 'self_reported' and (now - row.updated_at).days > 7:
    provenance = "Needs Attention"
else:
    provenance = "Self-reported"
```

**dashboard implementation (equally literal AD-16 compliance, different edge cases):**
```python
# AD-16: "position_seconds / duration_seconds" → what if duration_seconds is 0 or NULL?
if duration_seconds == 0:
    percent = 0  # Defensive: prevent division-by-zero
else:
    percent = position_seconds / duration_seconds

# AD-16: "100% → Completed" but what threshold? 99.5%? 99.9%? Exact 100.0?
if percent >= 0.995:  # 99.5% rounds to 100% in UI
    status = "completed"
elif percent == 0:
    status = "not_started"
else:
    status = "in_progress"

# Provenance: AD-16 says "updated_at within 7 days" — does 7.0 days count? 7.5?
if row.hr_override:
    provenance = "HR Override"
elif row.provenance == 'verified' and (now - row.updated_at).total_seconds() < 7 * 86400:
    provenance = "Verified"
elif row.provenance == 'self_reported' and (now - row.updated_at).total_seconds() >= 7 * 86400:
    provenance = "Needs Attention"
else:
    provenance = "Self-reported"
```

**Divergence:**
1. **Completion threshold:** `watch_progress` treats 99.5% (last 30 seconds of a 100-minute video) as "In Progress", dashboard shows "Completed" badge. HR Admin sees completion, employee sees "keep watching" prompt.
2. **Seven-day boundary:** Video marked Verified at exactly 7.0 days ago. Dashboard uses `< 7 * 86400` seconds (shows Verified), watch_progress uses `<= 7` days check (shows Needs Attention). Same row, different badges in different contexts.
3. **NULL duration_seconds:** `content_catalog.metadata` is JSONB (optional). If `duration_seconds` missing, `watch_progress` crashes on division, dashboard treats as 0% but logs error silently.

**Why AD-16 permits this:**
- AD-16 specifies formula and ranges but NOT rounding rules, NULL handling, or boundary inclusivity (< vs ≤ at 7 days).
- AD-16 says "computed server-side" but doesn't mandate single function or shared library—each module can implement independently.
- AD-3 says dashboard "reads from all but writes to none" but doesn't prohibit independent computation logic.

**Impact:** Dashboard and watch-progress UIs show conflicting Status badges for same assignment. HR Admin marks employee complete based on dashboard, employee still sees 99% resume prompt. Trust labels (Verified vs Needs Attention) flicker depending on exact second of 7-day boundary check.

---

### 2. SSE Trigger Race — Stale Dashboard After write_progress Mutation

**Attack:** `watch_progress` writes to `skill_progress`, then "triggers" SSE push to dashboard. AD-6 says "Server pushes assignment row deltas as watch_progress writes arrive" but doesn't specify synchronization mechanism. Two legal implementations diverge:

**watch_progress module (write-then-notify):**
```python
async def update_progress(assignment_id, position, event_timestamp):
    # Conditional write (AD-4)
    await db.execute(
        "UPDATE skill_progress SET position_seconds = ?, event_timestamp = ? ..."
    )
    await db.commit()
    
    # AD-6: "Trigger SSE push to dashboard"
    await sse_manager.notify_assignment_updated(assignment_id)
```

**dashboard module (poll-on-demand):**
```python
# Interprets "as watch_progress writes arrive" as: dashboard queries on SSE request
async def stream_updates(session_id):
    while True:
        # Wait for notification
        await sse_manager.wait_for_event(session_id)
        
        # Re-query assignments + progress to compute Status/Provenance
        rows = await db.execute("SELECT ... JOIN skill_progress ...")
        yield format_sse_event(rows)
```

**Divergence:**
- `watch_progress` commits at T=0, sends SSE event at T=1ms.
- Dashboard receives event at T=2ms, queries database at T=3ms.
- BUT: Postgres async replication lag means dashboard's read-replica sees stale pre-update state at T=3ms.
- Dashboard pushes old Status ("In Progress 85%") to client at T=4ms.
- Another client queries directly at T=5ms via `/api/assignments`, sees new Status ("In Progress 90%").
- **Result:** Dashboard SSE stream shows 85%, static assignment API shows 90%, same assignment_id.

**Why AD-6 permits this:**
- AD-6 says "Server pushes assignment row deltas as watch_progress writes arrive" but doesn't specify:
  - Read-after-write consistency guarantee
  - Whether SSE event includes full row data (pre-computed) or just assignment_id (requires re-query)
  - Whether notification is synchronous (blocking write until dashboard acknowledges) or fire-and-forget
- AD-1 says "Read paths optimized separately from write paths" which could mean read-replica with replication lag
- AD-15 "single-server deployment" implies no replication, but doesn't prohibit it—could be PostgreSQL streaming replication on same VM

**Impact:** Dashboard shows stale progress for 100ms-5s after legitimate watch_progress write. During high write volume (multiple employees watching videos), dashboard "lags behind" real state. 30-second latency target (FR-11) met in aggregate but individual writes show momentary staleness.

---

### 3. JWT Claims Interpretation — employee_id NULL Handling

**Attack:** `auth` and `assignments` modules interpret AD-9 JWT payload differently for HR Admin sessions.

**auth module (issues tokens):**
```python
# AD-9: "Token payload: {role: 'hr_admin' | 'employee', employee_id: string | null, exp: timestamp}"
# HR Admin has no employee_id → set to null
token_payload = {
    "role": "hr_admin",
    "employee_id": None,  # Python None
    "exp": now + timedelta(hours=8)
}
jwt_token = jwt.encode(token_payload, secret_key)
```

**assignments module (validates assignment ownership):**
```python
# AD-12: "Employee-scoped routes enforce employee_id match from token claims"
# AD-5: "Employee sessions can only read own progress"
async def get_my_assignments(request):
    claims = validate_jwt(request.cookies["session"])
    employee_id = claims["employee_id"]
    
    # Query scoped to employee_id
    rows = await db.execute(
        "SELECT * FROM assignments WHERE employee_id = ?",
        employee_id
    )
    return rows
```

**Divergence:**
- HR Admin logs in, receives JWT with `employee_id: None` (Python `None` serializes to JSON `null`)
- HR Admin navigates to `/api/assignments` (intended to see all assignments per UJ-1)
- `assignments` module extracts `employee_id = None`, passes to SQL query
- SQL: `WHERE employee_id = NULL` returns zero rows (SQL NULL comparison semantics)
- **Result:** HR Admin sees empty assignment list despite database containing hundreds of assignments

**Alternative divergence (JSON null vs missing key):**
- `auth` module sets `"employee_id": null` (JSON null literal)
- `assignments` module checks `if claims.get("employee_id")` (Python falsy check)
- Both `None` and missing key are falsy → HR Admin treated as unauthorized, gets 403 Forbidden

**Why AD-9 permits this:**
- AD-9 specifies payload structure `{role, employee_id, exp}` but doesn't mandate:
  - Whether `employee_id: null` means "no employee identity" vs "query all employees"
  - Whether HR Admin sessions should omit `employee_id` key entirely or set to null
  - Whether route-level validation should check role first (bypass employee_id check for hr_admin) or check employee_id universally
- AD-12 says "Employee-scoped routes enforce employee_id match" but doesn't define HR Admin behavior—are they exempt from scoping, or do they have a special sentinel value?

**Impact:** HR Admin cannot access assignment list (core UJ-1 scenario). Auth succeeds, but every protected endpoint returns empty results or 403. Symptom looks like "database is empty" or "permissions broken", not "JWT claims ambiguous".

---

### 4. watch_progress Anti-Spoofing vs assignments Status Mutation

**Attack:** `watch_progress` and `assignments` modules both mutate assignment state, but AD-3 says only assignments owns assignments table. They diverge on update authority.

**Scenario:**
1. HR Admin creates assignment (employee_id=Alice, skill_id=JavaScript, status="not_started")
2. Alice watches video, sends progress update (position=500s / duration=1000s = 50%)
3. `watch_progress` module receives update, passes AD-10 anti-spoofing checks, writes to `skill_progress`
4. **Question:** Should `watch_progress` also update `assignments.status` to "in_progress"?

**watch_progress interpretation (literal AD-3 compliance):**
```python
# AD-3: "assignments owns assignments table"
# AD-3: "No module may mutate another module's tables"
# → watch_progress only writes to skill_progress, never touches assignments
async def update_progress(assignment_id, position):
    await db.execute(
        "UPDATE skill_progress SET position_seconds = ? WHERE assignment_id = ?",
        position, assignment_id
    )
    # Do NOT update assignments.status — not our table
```

**assignments module interpretation (equally literal AD-3 compliance):**
```python
# AD-3: "assignments owns assignments table"
# AD-16: "Status computed from position_seconds / duration_seconds"
# → assignments computes Status on-demand from skill_progress, but skill_progress is owned by watch_progress
# → Can assignments read skill_progress to compute derived Status? Or does AD-3 forbid cross-module reads?

# OPTION A: Assignments queries skill_progress directly (reads OK, writes forbidden)
async def get_assignment_with_status(assignment_id):
    assignment = await db.execute("SELECT * FROM assignments WHERE id = ?", assignment_id)
    progress = await db.execute("SELECT * FROM skill_progress WHERE assignment_id = ?", assignment_id)
    status = compute_status(progress.position_seconds, progress.duration_seconds)
    return {**assignment, "computed_status": status}

# OPTION B: Assignments never touches skill_progress, maintains status field independently
async def mark_assignment_in_progress(assignment_id):
    # Called by watch_progress via service interface (AD-2 "service interfaces")
    await db.execute(
        "UPDATE assignments SET status = 'in_progress', updated_at = NOW() WHERE id = ?",
        assignment_id
    )
```

**Divergence:**
- **Option A (cross-module read):** Dashboard queries `assignments` module for Status, gets "not_started" (from assignments.status column), then queries `watch_progress` module for progress, gets 50% position. Conflicting state: assignment says "not_started", progress says "50% complete".
- **Option B (service interface callback):** `watch_progress` must call `assignments.mark_in_progress(assignment_id)` after every write. But AD-2 says "service interfaces", AD-3 says "no direct table access"—doesn't specify callback protocol. If watch_progress forgets to call callback, assignments table remains "not_started" forever despite video being watched.

**Why AD-3 + AD-16 permit this:**
- AD-3 defines table ownership but not read permissions—can modules read other modules' tables, or only via service interfaces?
- AD-16 says Status is "computed from position_seconds / duration_seconds" (in skill_progress) but doesn't say which module performs computation or stores result
- AD-11 defines `assignments.status` column as `NOT NULL DEFAULT 'not_started'`—is this a cache of computed Status (derived from skill_progress) or independent state (owned by assignments, synchronized via callbacks)?

**Impact:** Dashboard shows Assignment status="not_started" while progress=50%. HR Admin sees employee hasn't started, employee sees resume-from-halfway prompt. Assignment list and video player disagree on fundamental state.

---

### 5. content_discovery skill_tags vs assignments skill_id Mismatch

**Attack:** `content_discovery` and `assignments` modules use different skill identifiers, allowing valid assignment to have no discoverable content.

**content_discovery interpretation (AD-8 compliance):**
```python
# AD-8: "skill-tag metadata pre-filter, then cosine similarity ranking"
# AD-11: content_catalog has "skill_tags TEXT[]"
# → Stores freeform tags like ["javascript", "frontend", "react"]
async def discover_content_for_skill(skill_name: str):
    # Filter by skill_tags array contains search term
    results = await db.execute(
        "SELECT * FROM content_catalog WHERE ? = ANY(skill_tags) ORDER BY ...",
        skill_name.lower()
    )
    return results
```

**assignments interpretation (AD-11 compliance):**
```python
# AD-11: assignments has "skill_id UUID REFERENCES skills(id)"
# skills table has "name TEXT NOT NULL"
# → Stores normalized skill reference, not freeform tags
async def create_assignment(employee_id, skill_id):
    await db.execute(
        "INSERT INTO assignments (employee_id, skill_id, status) VALUES (?, ?, 'not_started')",
        employee_id, skill_id
    )
```

**Divergence:**
- HR Admin creates assignment for skill_id=UUID-123 (skills.name="JavaScript")
- Alice receives assignment, clicks "Find Content"
- `content_discovery` queries `content_catalog` WHERE 'javascript' IN skill_tags
- BUT: Content ingestion job (AD-17) tagged videos with "JS", "ECMAScript", "scripting"—none match "JavaScript" exact string
- **Result:** Alice sees "No content found for JavaScript" despite content_catalog containing 50 JavaScript videos with different tag spellings

**Why AD-8 + AD-11 permit this:**
- AD-8 defines `skill_tags TEXT[]` as freeform array, doesn't mandate controlled vocabulary or FK to skills table
- AD-11 defines `skills` table as authoritative catalog but doesn't require content_catalog to reference it
- AD-17 (content ingestion) doesn't specify tag normalization rules or skill_id linkage
- No AD enforces referential integrity between content_catalog.skill_tags and skills.name

**Impact:** Assignments exist for skills with zero discoverable content. UJ-2 scenario (employee finds content for assigned skill) breaks—search returns empty results, employee manually browses YouTube outside system.

---

### 6. SSE Connection Lifecycle — Stale Connection Not Detected

**Attack:** `dashboard` module interprets AD-6 "Connection drop shows explicit refresh prompt" differently from client expectations.

**dashboard SSE implementation (literal AD-6 compliance):**
```python
# AD-6: "Client establishes /api/dashboard/stream connection on mount"
# AD-6: "Server pushes assignment row deltas"
async def stream_dashboard_updates(request):
    async def event_generator():
        while True:
            # Wait for progress update
            event = await sse_queue.get()
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Client SSE implementation (literal AD-6 compliance):**
```javascript
// AD-6: "Connection drop shows explicit refresh prompt"
const eventSource = new EventSource('/api/dashboard/stream');

eventSource.onerror = (error) => {
    // Connection dropped
    showRefreshPrompt();
};

eventSource.onmessage = (event) => {
    updateDashboardRow(JSON.parse(event.data));
};
```

**Divergence:**
- Dashboard opens SSE connection at T=0
- Server sends events at T=10s, T=20s, T=30s (all received successfully)
- Network blip at T=35s — connection stalls but doesn't close (TCP half-open)
- Server sends event at T=40s, never reaches client (TCP buffer full, no ACK)
- Client `onerror` never fires (connection not officially closed)
- Client shows stale T=30s data, user assumes dashboard is live
- Server continues sending events to dead connection, logs no error (write succeeds to kernel buffer)

**Why AD-6 permits this:**
- AD-6 says "Connection drop shows explicit refresh prompt" but doesn't define drop detection mechanism:
  - Client-side heartbeat/keepalive?
  - Server-side ping/pong?
  - Timeout if no events received in N seconds?
- AD-6 specifies 30-second latency target but doesn't mandate staleness detection beyond "connection drop"
- EventSource API `onerror` only fires on explicit close/failure, not on stalled connection

**Impact:** Dashboard shows stale data for minutes/hours, user trusts outdated Status badges. HR Admin sees assignment as "In Progress 20%" while employee actually completed (100%) 10 minutes ago. Silent staleness worse than explicit error.

---

## Recommended Architecture Decision Additions/Clarifications

### AD-16 Amendment: Unified Status/Provenance Computation

**Add to AD-16:**
> Status/Provenance MUST be computed by a single shared function in `dashboard` module, callable by all modules requiring these values. Implementation rules:
> - Completion threshold: `position_seconds / duration_seconds >= 0.995` (99.5%)
> - Seven-day boundary: `(now_utc - updated_at_utc).total_seconds() < 604800` (7 days = 604800 seconds, exclusive)
> - NULL duration_seconds: treat as 0% (Not Started), log warning
> - Rounding: Status computed from exact decimal percentage, no premature rounding
> 
> Other modules MAY cache computed values but MUST refresh via shared function on every user-visible query.

### AD-6 Amendment: SSE Synchronization & Staleness Detection

**Add to AD-6:**
> SSE push MUST include read-after-write consistency guarantee: `watch_progress` write commits, then SSE event contains full post-write row state (not re-queried). Dashboard module receives event payload with pre-computed Status/Provenance, no additional query required.
>
> Staleness detection: Client sends comment-ping every 15 seconds (`': ping\n\n`), server echoes. If client receives no data (event or ping) for 45 seconds, show refresh prompt. Server drops connection if client hasn't ACKed (TCP level) in 60 seconds.

### AD-9 Amendment: JWT Claims for HR Admin

**Add to AD-9:**
> HR Admin sessions omit `employee_id` key entirely (not `null` value). Route validation logic:
> 1. Extract `role` from claims
> 2. If `role == "hr_admin"`, bypass employee_id scoping (access all resources)
> 3. If `role == "employee"`, enforce `employee_id` match against resource ownership
>
> JSON schema: `{role: "hr_admin", exp: timestamp}` (no employee_id key) vs `{role: "employee", employee_id: "uuid", exp: timestamp}`

### AD-3 Amendment: Cross-Module Read Permissions

**Add to AD-3:**
> Modules MAY read any table via service interface (not direct SQL). Table owner provides read methods enforcing access control:
> - `watch_progress` exposes `get_progress(assignment_id) → {position, duration, event_timestamp, provenance}`
> - `assignments` exposes `get_assignment(assignment_id) → {employee_id, skill_id, status, hr_override}`
>
> Computed Status (AD-16) reads skill_progress via service interface, not direct table access. Assignments.status column removed—Status is always computed on-demand from skill_progress, never stored redundantly.

### AD-8 Amendment: Skill Tag Normalization

**Add to AD-8:**
> `content_catalog.skill_tags` MUST reference `skills.name` with exact case-insensitive match. Batch ingestion (AD-17) normalizes tags to lowercase, maps to skills table:
> - "JavaScript", "javascript", "JS" → canonical "javascript" (matches skills.name)
> - Unrecognized tags logged as warnings, not stored
>
> Content discovery query: JOIN skills table, filter WHERE skill_id = assignment.skill_id, then rank by embedding similarity within matched content.

### NEW AD-19: SSE Event Payload Schema

**Binds:** SSE message structure, client parsing  
**Prevents:** Ambiguous event interpretation, missed fields  
**Rule:**
> Every SSE event pushed to `/api/dashboard/stream` MUST conform to schema:
> ```json
> {
>   "event_type": "assignment_updated" | "assignment_created" | "heartbeat",
>   "timestamp": "2026-07-09T14:32:01Z",
>   "payload": {
>     "assignment_id": "uuid",
>     "employee_id": "uuid",
>     "employee_name": "string",
>     "skill_name": "string",
>     "status": "not_started" | "in_progress" | "completed",
>     "provenance": "Verified" | "Self-reported" | "Needs Attention" | "HR Override",
>     "position_seconds": number,
>     "duration_seconds": number,
>     "updated_at": "timestamp"
>   }
> }
> ```
> Heartbeat events have null payload. Clients ignore unknown event_type values (forward compatibility).

---

## Summary

**Holes found:** 6 critical divergence scenarios

**Most severe:**
1. **Status/Provenance computation divergence** — Different rounding/boundary logic produces conflicting badges across modules
2. **SSE staleness race** — Dashboard lags behind watch_progress writes due to unspecified read-after-write consistency
3. **JWT employee_id NULL handling** — HR Admin sessions break due to ambiguous null vs missing key semantics

**Root cause:** ADs specify WHAT (tables, modules, data flow) but under-specify HOW (computation details, synchronization, edge cases). Every "compute server-side" or "via service interface" leaves implementation-divergence room.

**Mitigation:** Add 5 amendments + 1 new AD to close holes. Require shared libraries for Status/Provenance computation, explicit SSE payload schema, JWT role-based bypass logic, service interface read permissions, skill tag normalization.
