---
title: TalentPilot-AI Product Brief
status: draft
created: 2026-07-08
updated: 2026-07-08
---

# TalentPilot-AI: Replacing Spreadsheets with Trustworthy Skill Readiness

## The Problem

HR teams manage employee skill development through spreadsheets—manually assigning courses, chasing status updates, and eyeballing grids to judge who's ready for what. This process is broken:

- **Data is unreliable.** 88% of HR spreadsheets contain errors (The Hackett Group).
- **HR can't trust their own data.** Only 20% of HR leaders feel confident they have accurate employee skill information (Gartner).
- **Visibility is manual and slow.** Consolidating status updates across dozens or hundreds of employees consumes significant admin time; HR has no live picture of org-wide readiness.
- **Employees shoulder unnecessary burden.** The self-reporting loop—where employees update their own progress status—is an easy-to-deprioritize chore with no personal payoff, leaving HR to chase people instead of managing skills.

The fundamental constraint: **spreadsheets depend entirely on people remembering to update them.** Auto-capture is not possible; HR can't know if silence means completion or neglect.

The impact: **87% of companies cite lack of workforce-skills visibility as their top barrier to growth.**

## The Opportunity

Replace the spreadsheet choreography with a platform where:

1. **HR assigns** must-do skills/courses per employee (sets the roadmap).
2. **The system recommends** relevant learning content (videos, documents, websites) matched to those assignments, removing manual content hunting.
3. **System auto-captures** progress from actual behavior (video watch %), not self-reported status.
4. **HR dashboard** reflects reality in real-time without re-typing or chasing—a single source of truth for readiness decisions.

The result: HR stops maintaining the tracking spreadsheet; employees learn without admin overhead; the dashboard becomes trustworthy enough that HR actually uses it to make readiness calls.

## MVP Scope

### For HR

- **Assignment Flow**: Assign must-do skills/courses to employees. Sets the learning roadmap.
- **Readiness Dashboard**: Per-employee columns (name, skills, progress, dates, status). Built entirely from auto-captured signals—no manual entry required.
- **Dashboard Confidence Features**: Freshness indicators, drill-down reasoning, and "Needs Attention" filter that distinguish auto-captured data (trustworthy) from aging self-reported data vs. missing signals.

### For Employees

- **AI-Assisted Content Discovery**: Given assigned skills, the system recommends relevant videos, documents, and websites. Scoped to search/discovery only—the system does not automatically identify and assign unmet skills (HR retains that responsibility).
- **Video Progress Tracking**: Auto-captured from actual watch %. No manual entry by employee.
- **Continue-Watching / Resume**: Netflix/Spotify-style "resume exactly where you left off" for videos. Eliminates re-watching and shows progress without asking employees to log anything.

### Out of Scope (This Time)

- Automated skill-gap-to-project matching (HR does this manually via dashboard).
- Manager/Team Lead role (only HR and Employee).
- Progress tracking for documents/websites (videos only).
- Post-completion recommendations.
- AI substituting for human judgment in staffing calls.

## Why This Wedge, Why Now

### Competitive Gap

Reviewed competitors fall into three tiers—heavyweight talent-intelligence suites (Eightfold, Gloat), LMS/LXP incumbents (Cornerstone, Degreed, LinkedIn Learning), and newer AI gap-analysis tools (Valamis, Paradiso). **None combine TalentPilot-AI's specific wedge**: HR-assignment-driven roadmap + AI content discovery + fully automatic video-progress capture + consumer-grade resume UX in one narrow, fast-to-deploy product. This is a currently undefended positioning gap, not just a feature checklist difference.

### Market Validation

The pain is large, acute, and documented:

- **79% of HR teams** are adopting skills-based approaches to hiring/training/development but lack the tooling to operationalize it.
- **4–6-month enterprise procurement cycles** favor narrow, fast-to-pilot products over heavyweight suites—a built-in structural advantage.
- **Employees waste ~35% of their time** searching for information (industry research); they resent manual progress logging with no personal payoff.
- Research confirms independent sources corroborate the core pain: spreadsheet errors (88%), HR data-confidence gaps (20% trust), and skills-visibility barriers (87% of companies).

### Market Entry Timing

The LMS/LXP category is consolidating, not settled—incumbents are blurring lines since 2022, with LMS vendors adding LXP discovery and LXP vendors adding compliance features. This window to establish a distinct, defensible position is open *now*, before the boundary fully closes.

## Success Criteria for POC

### Functional Success

- **Dashboard becomes the source of truth.** HR uses it as their primary reference for skill readiness (not the old spreadsheet) within 60 days of go-live.
- **Video tracking works end-to-end.** Watch % is auto-captured and surfaces on the dashboard with zero manual employee entry.
- **Resume reduces friction.** Employees can resume a video exactly where they left off.

### Business Success

- **Self-reported status staleness drops to near-zero.** The % of assignment rows with self-reported status stale beyond 7 days drops from 100% (current baseline in spreadsheet) to near-zero once auto-capture replaces manual updates for video content.
- **Trust indicators guide readiness calls.** HR actively uses freshness indicators and drill-down reasoning to confidently judge project-readiness without opening the old spreadsheet.

### Adoption Success

- **No shadow spreadsheet.** HR stops maintaining a parallel Excel file after dashboard go-live.
- **Employee engagement.** Video completion rate and resume-feature usage indicate employees are consuming assigned content without manual logging friction.

## Implementation Plan

### Phase 1: Foundation (Weeks 1–2)

- Finalize technical architecture (video hosting, AI content-discovery service integration, database schema).
- Build HR assignment flow (simple UI for assigning skills/courses per employee).
- Stand up video embed with auto-capture (polling watch % from video player; persist to database).

### Phase 2: Dashboard & Content Discovery (Weeks 3–4)

- Create low-fidelity mockups for HR dashboard (freshness indicators, drill-down, "Needs Attention" filter) and align with stakeholders.
- Build HR dashboard with freshness-coded status cells.
- Implement AI-assisted content discovery (skill → relevant video/doc/website).
- Implement "Continue Watching" resume feature.
- Begin data instrumentation for success metrics (track stale status %, dashboard usage, video completion, resume adoption).

### Phase 3: Pilot & Validation (Week 5+)

- Deploy to internal pilot (or first customer cohort).
- Collect quantitative metrics (stale status %, dashboard adoption, video completion, resume feature usage).
- Collect qualitative feedback (HR confidence in data, employee friction reduction).
- Iterate on dashboard UX and content-discovery relevance based on real usage.

## Key Assumptions & Risks

### Critical Assumptions

- `[ASSUMPTION]` **Root-cause hypothesis**: Self-reporting compliance is the real pain, not the spreadsheet format. Auto-capturing video-watch signals removes the exact behavior HR can't rely on today. Validated post-launch via usage metrics (staleness %, dashboard adoption).
- `[ASSUMPTION]` **HR-assignment-first model.** Employees don't need to search for "what should I learn"—HR tells them. If real pilots reveal employees want exploratory learning, scope may expand.
- `[ASSUMPTION]` **Dashboard confidence features drive trust.** Freshness indicators and drill-down reasoning are the mechanism that closes HR's trust gap. If pilots show HR ignores these indicators and reverts to spreadsheets, the UX needs rethinking.

### Scope Constraints

- `[ASSUMPTION]` **Video-only progress tracking for MVP.** Documents/websites are recommended content; only video watch % is auto-captured. If stakeholders need trustworthy signals from other content types, this may need to shift.
- `[ASSUMPTION]` **Two-week real-data POC timeline.** The plan assumes a narrow scope prototypable quickly with demo data or a small customer dataset. Significant data migration or external integrations may extend this.

### Open Questions

- Should the POC include manager/team-lead role visibility, or is HR-only sufficient for sign-off? (Currently assumed HR-only per scope; can add post-MVP if demand surfaces.)

## Next Steps & Timeline

**This POC will validate whether auto-capture and dashboard transparency can solve the trust and visibility gaps that spreadsheets structurally cannot.**

- **Week 1–2 (Foundation):** Finalize tech stack; stand up assignment flow and video embed with auto-capture.
- **Week 3–4 (Dashboard & Discovery):** Build dashboard with confidence features and AI-assisted content discovery.
- **Week 5+ (Pilot & Validation):** Deploy to pilot cohort; track stale-status %, dashboard adoption, video completion, and resume usage.
- **Success gate:** HR uses the dashboard as their primary reference (not the old spreadsheet) within 60 days, and staleness of self-reported data approaches zero for video content.

**Decision required:** Stakeholder approval to proceed with build-out, resource allocation, and confirmation of pilot customer (size, industry, maturity).

---

**Document Owner:** TalentPilot  
**Brief Status:** Draft (ready for stakeholder review)  
**Next Step:** Present to stakeholders; incorporate feedback and finalize implementation roadmap with resource assignments.
