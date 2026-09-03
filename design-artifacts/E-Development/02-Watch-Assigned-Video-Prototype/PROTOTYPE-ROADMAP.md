# Scenario 02: Watch Assigned Video - Prototype Roadmap

**Scenario**: Watch Assigned Video (Employee)
**Pages**: Employee Content Discovery (grid + inline video view)
**Device Compatibility**: Fully Responsive (same as Scenario 01)
**Design Fidelity**: Design System Components (same tokens as Scenario 01)
**Last Updated**: 2026-09-03

---

## Scenario Overview

**User Journey**: An employee (Casey) lands on Content Discovery, sees their assigned skills grouped by status (In Progress / To Start / Completed), clicks a card, and watches the matched YouTube video inline on the same page — matching `_bmad-output/planning-artifacts/scenarios/scenario-watch-assigned-video.md` and `page-content-discovery.md` from the Reverse Engineering activity.

Setup choices reused from Scenario 01 without re-asking (no signal to change them): Fully Responsive, Design System Components, real seed-derived data.

**Pages in this Scenario**:
1. `content-discovery.html` — single page, two render modes: Mode A (assignment grid) and Mode B (inline video, swaps the body in place — no route change, matching real `ContentDiscovery.tsx`)

---

## Demo Data

**Source: real backend seed data**, same convention as Scenario 01. `currentUser` = Casey the Continuer (EMPLOYEE, not Rita — this is the employee-facing view). `myAssignments[]` = 3 synthesized rows spanning all 3 status groups (In Progress / To Start / Completed), reusing Casey's actual Scenario 01 assignment IDs where the pairing is the same (Data Visualization, SQL & Databases), plus one new To Start row (Communication Skills) purely so that group has content to render.

---

## Known Open Question (carried from Reverse Engineering)

Real production has **two ways** to reach a video: this page's inline Mode B, and a separate `/assignments/:id/watch` route (`AssignmentWatch.tsx`) that does the same thing. Flagged in `scenario-watch-assigned-video.md` as possibly redundant. Building the inline mode first (the primary, always-reachable path); the standalone route is lower priority unless requested.

---

## Prototype Status

| Page | Status | Notes |
|------|--------|-------|
| Content Discovery (Mode A: grid) | ✅ Complete & Approved | "looks good for me" |
| Content Discovery (Mode B: inline video) | ✅ Complete & Approved | Real YouTube iframe embed, not the full custom capture-service integration from `VideoPlayer.tsx` (out of scope for a static prototype — no backend to post progress to) |

---

## Change Log

### 2026-09-03
- Prototype environment created (folder structure, demo data, this roadmap), reusing Scenario 01's `shared/init.js` as-is
