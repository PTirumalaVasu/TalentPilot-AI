---
title: TalentPilot-AI — Watch Progress Tracking Architecture
status: final
updated: 2026-07-14
---

# TalentPilot-AI — Watch Progress Tracking (Employee capture & HR Admin dashboard)

How an Employee's video-watch behavior becomes a validated `skill_progress` write, and how that same data reaches the HR Admin's Readiness Dashboard as a trustworthy Status/Provenance badge.

## 1. Employee workflow — capture, validated write, resume

The player never talks to the backend directly. A capture service batches position samples and posts them; the backend independently validates every write before trusting it.

- **Capture:** `WatchProgressCaptureService` listens to the player adapter's `timeupdate` event, queues samples locally, and posts the latest sample every ~10s or once 3 samples have queued — not on every tick.
- **Anti-spoofing (`antiflow.py`):** every write runs four checks before being trusted — session identity must match the assignment's employee, position must be within `[0, duration]`, the advance rate must be realistic (≤10x realtime; rewinds always pass), and the client's event-time must be within ±5 minutes of the server clock. A failed check doesn't reject the request — it persists the write with `verified=false` for forensics (silent-rejection pattern).
- **Conditional write:** the row is only overwritten if the incoming `event_time` is newer than what's stored — ordering by time, not position, so a legitimate rewind (lower position, newer timestamp) is still accepted.
- **Resume:** on next visit, the resume endpoint is Employee-only and hard-scoped to the caller's own session identity; it returns the exact stored position (0 on first view, or as a fail-safe if the stored value is out of bounds).
- **Tab close:** `beforeunload` flushes the last known position via `navigator.sendBeacon()` — fire-and-forget, no response wait.

```mermaid
sequenceDiagram
    actor Casey as Employee
    participant Player as YouTube Player (adapter)
    participant Cap as WatchProgressCaptureService (SPA)
    participant API as progress/ router
    participant Anti as antiflow.py (anti-spoofing)
    participant SVC as progress/ service
    participant DB as skill_progress

    Casey->>Player: Opens assigned video
    Player->>API: GET /api/assignments/{id}/progress (resume)
    API->>SVC: get_resume_position()
    SVC->>DB: fetch skill_progress (hard-scoped to Casey's session identity)
    alt no row yet
        SVC-->>Player: position 0
    else stored position out of bounds
        SVC-->>Player: position 0 (fail-safe)
    else
        SVC-->>Player: exact stored watch_position
    end
    Player-->>Casey: Resumes at exact last position

    loop every 'timeupdate' while playing
        Player->>Cap: position(), duration()
        Cap->>Cap: queue sample locally (posts every ~10s or at 3 samples)
    end

    Cap->>API: POST /api/assignments/{id}/progress {watch_position, event_time, video_url}
    API->>Anti: run_all_validations()
    Anti->>Anti: 1) session identity == assignment.employee_id
    Anti->>Anti: 2) 0 <= position <= duration
    Anti->>Anti: 3) advance rate <= 10x realtime (rewinds always allowed)
    Anti->>Anti: 4) event_time within +/-5 min of server clock
    Anti-->>API: verified = true/false (never rejects the request)
    API->>SVC: record_watch_progress()
    SVC->>DB: write IFF event_time newer than stored (conditional write)
    DB-->>Cap: verified flag in response

    Note over Casey,Cap: Tab close / hidden -> beforeunload fires<br/>sendBeacon() flushes last position, fire-and-forget, no response wait
```

## 2. HR Admin workflow — dashboard polling, derivation, drill-down, override

The dashboard never reads raw watch data. Every row's Status and Provenance are computed by one shared derivation function, called identically by the grid, the drill-down modal, and the override mutation — so the three surfaces can never disagree about the same assignment.

- **Derivation authority:** `get_provenance_detail()` composes Status (from watch % vs. video duration) and Provenance (Verified / Self-reported / Needs Attention past 7 days / HR Override) in one place. Status and Provenance are orthogonal — a stale row is `In Progress` + `Needs Attention`, never a Status of "Needs Attention".
- **Live updates:** the dashboard silently polls every 12 seconds while the tab is visible (paused when hidden), diffs rows by status/provenance/percentage only, and announces changed rows via an `aria-live` region rather than reloading the whole grid.
- **Drill-down:** reached from any row, calls the exact same derivation function as the grid — showing the raw signal (watch %, timestamp) behind the badge.
- **HR Override:** a separate, coexisting record — never a field overwrite on `skill_progress`. Setting one deactivates any prior active override first (at most one active override per assignment), and an active override wins the effective Status while the underlying (pre-override) signal stays visible in the drill-down rather than being erased.

```mermaid
sequenceDiagram
    actor Rita as HR Admin
    participant UI as Dashboard (SPA)
    participant API as dashboard / assignments router
    participant SVC as progress/ service<br/>(single derivation authority)
    participant DB as skill_progress + assignment_overrides

    Rita->>UI: Opens Readiness Dashboard
    UI->>API: GET /api/dashboard
    loop each assignment row
        API->>SVC: get_provenance_detail(assignment, progress, override, duration)
        SVC->>SVC: derive_dashboard_status_and_percent() -> Status
        SVC->>SVC: derive_self_reported_provenance() -> stale >7d = Needs Attention
        alt active HR Override exists
            SVC->>SVC: Override wins Status, Provenance = "HR Override"<br/>underlying signal still attached, never erased
        end
    end
    SVC-->>UI: rows: {status, provenance, percentage}

    loop every 12s while tab visible
        UI->>API: GET /api/dashboard (silent background poll)
        API-->>UI: latest rows
        UI->>UI: diff rows (status/provenance/% only) -> highlight + aria-live announce changes
    end
    Note over UI: polling pauses when tab is hidden (visibilitychange)

    Rita->>UI: Click a row -> Drill-down
    UI->>API: GET /assignments/{id}/progress/drill-down
    API->>SVC: get_provenance_detail() (same function as dashboard)
    SVC-->>UI: Provenance + raw signal (watch %, timestamp) + underlying signal if overridden

    Rita->>UI: Set/reverse HR Override (+ optional reason)
    UI->>API: POST /assignments/{id}/override {action: set|unset}
    API->>SVC: set_override()
    SVC->>DB: lock row -> deactivate any prior active override -> create/deactivate override record
    SVC->>SVC: re-derive via get_provenance_detail() (same authority, no drift)
    SVC-->>UI: updated drill-down response
```

## 3. Why the two workflows never collide

- **Separate write paths, one per role.** Only `record_watch_progress()` writes `skill_progress`, and it explicitly rejects an HR_ADMIN session trying to report progress (`antiflow.py`, `validate_session_identity`). Only `set_override()` writes `assignment_overrides`. Neither role can write into the other's table.
- **One read authority.** The dashboard grid, the drill-down modal, and the override response all resolve through `get_provenance_detail()` / `derive_dashboard_status_and_percent()` in `progress/service.py` — never re-derived independently, so the same assignment can't show a different answer on two different screens.
