# Talent Pool Management — Intent

Replace manual Excel-based skill/learning tracking with a platform where HR assigns must-do skills, employees learn via AI-assisted video discovery, and progress is auto-captured — giving HR a live, dashboard-based view of org skill readiness without chasing spreadsheets.

## Roles

- **HR**: assigns must-do skills/courses to employees, views org-wide dashboard, manually judges project-readiness.
- **Employee**: consumes assigned learning content, resumes where they left off; does zero manual progress logging.

## MVP Scope (Must-have)

**HR Dashboard**
- Per-employee columns: name, skills, sub-skills, start date, estimated end date, actual end date, status.
- HR manually reviews dashboard to judge project-readiness (no automated matching).

**HR Assignment Flow**
- HR assigns must-do skills/courses per employee (sets the roadmap; two-layer model — HR defines what, employee/AI finds how).

**AI Assistant — Content Discovery**
- Given an employee's assigned skills, surfaces relevant videos, documents, and websites.
- Scope limited to content discovery/search only — no proactive skill-gap detection, no gap-matching logic.

**Video Progress Tracking**
- Auto-captured from actual video watch % (no manual entry by employee).
- Applies to videos only — documents/websites are recommended content with no progress tracking.

**Continue-Watching / Resume**
- Netflix/Spotify-style "continue watching" row.
- Resume exactly at last-watched position.
- No auto-recommendations in this row.

## Fast-Follow (Should)

- Proactive resume nudges (e.g., "you paused 3 days ago, 8 min left").
- Transcript-level semantic search: natural-language question jumps to exact video timestamp.

## Won't (this time)

- Automated skill-gap-to-project matcher (HR does this manually via dashboard).
- Blocker column on HR dashboard.
- Manager/Team Lead role (only HR and Employee exist).
- Progress tracking for documents/websites.
- Post-completion content recommendations.
- AI substituting for manager 1:1s or proactive gap-flagging.

## Core Synthesis Insight

MVP reduces to three data flows:
1. HR writes assignments in (must-do skills/courses per employee).
2. Platform auto-reads video-consumption signals (watch %, position) — no manual employee entry.
3. HR reads the dashboard, built entirely from those signals.

No fuzzy AI judgment calls (gap-matching, mentoring) are in scope — this keeps the slice narrow, scalable, and enterprise-buildable.
