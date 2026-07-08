# Handoff Log: DD-001

**Date:** 2026-07-08
**Participants:**
- WDS UX Expert: Freya (design agent)
- Receiving: `wds-5-agentic-development` ([P] Prototyping) — no separate BMad Architect persona in play on this project; TalentPilot drives both sides

---

## 1. Introduction

Design Delivery **DD-001: POC Hypothesis Flows — Trust, Resume/Watch, Assignment** is complete and ready for the build phase. It covers 3 scenarios / 6 pages, no design system components (design_system_mode: none), and a complete test scenario (TS-001).

## 2. User Value

**Problem:** Rita can't trust self-reported skill progress without cross-referencing; Casey gets no credit unless they manually log progress and loses their place in videos; assignment is disconnected from tracking.

**Solution:** Provenance-labeled dashboard + frictionless auto-captured resumable watch progress + a 3-step assignment flow that closes the loop in real time.

**Success Criteria:**
- Dashboard staleness < 5% within 60 days of launch
- Assignment completed in < 2 minutes
- Exact-position resume, no seeking
- Dashboard row auto-updates within 30s of a watch-position change

## 3. Scenario Walkthrough

| Scenario | Entry → Exit | Spec |
|---|---|---|
| 01: Rita's Trust Call | Dashboard → drill-down → close | `C-UX-Scenarios/01-ritas-trust-call/` |
| 02: Casey's Resume & Watch | Notification → content discovery → play → tab close → return → resume | `C-UX-Scenarios/02-caseys-resume-and-watch/` |
| 03: Rita's Assignment & Track | [+ New Assignment] → 3-step form → dashboard confirmation → real-time update | `C-UX-Scenarios/03-ritas-assignment-and-track/` |

## 4. Technical Requirements

- **Frontend:** React + TypeScript + Vite (SPA, no SSR/Next.js — internal, authenticated, no SEO need)
- **Backend:** Python 3.12+ / FastAPI, domain-module structure
- **Database:** PostgreSQL + pgvector, async SQLAlchemy 2.0 + asyncpg
- **Integration:** YouTube IFrame API, polling `getCurrentTime()`, `sendBeacon` on unload
- **Data models:** `assignments`, `skill_progress` (conditional writes), `content_catalog` + embeddings
- **Performance:** dashboard < 2s, content+player < 3s, assignment→dashboard < 1s, resume start < 1s, real-time row update < 30s
- **Privacy constraint:** coaching-only data must be enforced at the data-access layer — not just UI copy. This is a launch blocker per the PRFAQ decision, not optional polish.
- **No data migration:** dashboard starts clean 2026-07-13.

## 5. Design System Components

N/A — `design_system_mode: none`. No shared component library for this pilot.

## 6. Acceptance Criteria

Full functional/non-functional/edge-case list is in `DD-001-poc-hypothesis-flows.yaml`. Highlights:
- Provenance labels always color + text (never color-only)
- All 6 pages implement Loading/Empty/Error states, not just happy path (see the Phase 4 validation retrofit — this was a gap found and fixed on 2026-07-08)
- No manual "save"/"sync" UI anywhere in the watch-tracking flow

## 7. Testing Approach

`TS-001-poc-hypothesis-flows.yaml`: 3 happy-path, 6 error-state, 5 edge-case, 3 accessibility, 2 usability, 5 performance tests. Freya (or whoever runs Phase 5 [T] Acceptance Testing) validates against this after implementation.

## 8. Complexity Estimate

- **Size:** L
- **Risk:** Medium — concentrated in (1) the real-time dashboard-update pipeline, the most novel piece and central to the POC hypothesis, and (2) enforcing the coaching-only data boundary at the backend layer.
- **Dependencies:** self-hosted vs. third-party video embed decision still open (affects what "auto-captured watch %" can technically mean).
- **Assumptions:** legal/compliance review of video-watch tracking was consciously declined for this internal-pilot scope; no named post-pilot owner/timeline yet (both accepted, revisit before Pilot & Validation phase).

## 9. Special Considerations

- The coaching-only privacy boundary (auto-captured data never usable in performance evaluations) is a **launch blocker**, surfaced during PRFAQ stress-testing as a surveillance-optics risk — it must be a real data-access/reporting boundary in the implementation, not just stated in copy.
- Root-cause framing: this is positioned as reducing manual self-reporting/status-chasing, not "replacing the spreadsheet" — keep that framing in any user-facing copy touched during build.
- Deferred spec-structure gaps (Page Metadata standardization, Prev/Next nav links across pages) were consciously left unfixed — see `_progress/validation-report.md` — they don't affect what gets built.

## 10. Confirmation & Next Steps

- DD-001 (Design Delivery) ✅
- TS-001 (Test Scenario) ✅
- All 6 page specs in `C-UX-Scenarios/` ✅
- No design system components (N/A)
- Next: proceed to `wds-5-agentic-development` [P] Prototyping to build section-by-section against these specs
- Freya (or a future session) runs TS-001 for validation once a scenario's pages are built

---

## Status

**Handoff:** Complete ✅
**Delivery Status:** in_development
**Next Touch Point:** Acceptance testing against TS-001 once prototyping produces a testable flow
