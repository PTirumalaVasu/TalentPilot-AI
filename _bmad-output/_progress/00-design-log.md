# Design Log: TalentPilot-AI

> Project progress and key decisions across design phases

**Project:** TalentPilot-AI  
**Owner:** TalentPilot  
**Started:** 2026-07-08

---

## Progress

### 2026-07-08 — Phase 3: UX Scenarios Complete

**Agent:** Saga (Scenario Outline) with Claude Code  
**Scenarios:** 3 scenarios covering 6 of 7 core pages  
**Quality:** ✅ Excellent (all scenarios 7/7 / 7/7 / 7/7 / 4/4)

**Artifacts Created:**
- `C-UX-Scenarios/00-ux-scenarios.md` — Master scenario index with coverage matrix and POC hypothesis alignment
- `C-UX-Scenarios/01-ritas-trust-call/01-ritas-trust-call.md` — Scenario 01 outline (Rita's readiness decision workflow)
- `C-UX-Scenarios/01-ritas-trust-call/01.1-assignment-dashboard/01.1-assignment-dashboard.md` — Step 01.1 page spec (provenance labels, dashboard grid)
- `C-UX-Scenarios/01-ritas-trust-call/01.2-provenance-drill-down/01.2-provenance-drill-down.md` — Step 01.2 page spec (raw data view, modal/panel)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02-caseys-resume-and-watch.md` — Scenario 02 outline (frictionless resume + auto-capture)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02.1-content-discovery/02.1-content-discovery.md` — Step 02.1 page spec (single human-approved recommendation)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02.2-resume-continue-watching/02.2-resume-continue-watching.md` — Step 02.2 page spec (resume at exact position, real-time tracking)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03-ritas-assignment-and-track.md` — Scenario 03 outline (frictionless assignment + auto-update)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03.1-skill-assignment-flow/03.1-skill-assignment-flow.md` — Step 03.1 page spec (multi-step form with auto-linked content)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03.2-assignment-confirmation-and-auto-update/03.2-assignment-confirmation-and-auto-update.md` — Step 03.2 page spec (new row appears on dashboard)

**Summary:** Three scenarios were outlined covering the full POC hypothesis: (1) Rita's Trust Call tests whether provenance labeling (Verified / Self-reported / Needs Attention) actually changes Rita's behavior and eliminates cross-referencing; (2) Casey's Resume & Watch tests whether frictionless resume + passive auto-capture generates honest signal without surveillance anxiety; (3) Rita's Assignment & Track tests whether frictionless assignment flow with auto-linked content and auto-updating dashboard eliminates Rita's chasing burden. Key design decision: removed the "Needs Attention" filter as a separate page since drill-down directly from dashboard rows is simpler and addresses the same need. All scenarios are grounded in Trigger Map personas, driving forces, and business goals. Page coverage: 6 of 7 core pages assigned; Employee Profile View explicitly deferred (not needed for POC scope).

**Next:** Phase 4 — UX Design (detailed page specs, wireframes, component definitions, interaction design)

---

## Key Decisions

| Date | Decision | Phase | Contributors |
|------|----------|-------|---------------|
| 2026-07-08 | Removed Needs Attention Filter as separate page; integrated into Assignment Dashboard via direct drill-down on stale rows | Phase 3: Scenarios | Claude Code + TalentPilot |
| 2026-07-08 | Deferred Employee Profile View (not required for POC scope); all persona-specific data flows demonstrated through 6-page scenario outlines | Phase 3: Scenarios | Claude Code + TalentPilot |
| 2026-07-08 | Confirmed "Needs Attention" as implicit label state on Assignment Dashboard rows rather than a separate filter UI | Phase 3: Scenarios | Claude Code + TalentPilot |

---

## Quality Scores

### Phase 3: UX Scenarios

| Scenario | Completeness | Quality | Mistakes Avoided | Best Practices | Overall |
|----------|--------------|---------|------------------|----------------|---------|
| 01: Rita's Trust Call | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |
| 02: Casey's Resume & Watch | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |
| 03: Rita's Assignment & Track | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |

**Overall Quality Rating:** Excellent — All scenarios exceed minimum thresholds. All 7 mistakes avoided in all scenarios. No gaps identified.

---

## Phase Completion Checklist

### Phase 1: Product Brief ✅
- [x] Strategic summary defined
- [x] Vision statement locked
- [x] Target users identified
- [x] Success criteria established

### Phase 2: Trigger Mapping ✅
- [x] Business goals mapped (Primary/Secondary/Tertiary)
- [x] Personas detailed (Rita, Casey)
- [x] Driving forces documented (wants + fears)
- [x] Trigger map created with visual flow

### Phase 3: UX Scenarios ✅
- [x] Scenario plan approved (3 scenarios, 6 pages)
- [x] All scenarios outlined (8-question format, Q1-Q8 answered)
- [x] All scenario steps detailed (6 page specs created)
- [x] Overview index created (00-ux-scenarios.md)
- [x] Quality review passed (all scenarios Excellent)
- [x] Design log updated

### Phase 4: UX Design ✅ (Scenario Specifications Complete)
- [x] Page context defined (01.1 - Skills Dashboard) — page purpose, entry point, mental state, goals captured
- [x] Page 01.1 (Skills Dashboard) specification complete — layout, components, interactions, states, spacing, typography
- [x] Page 01.2 (Assignment Details modal) specification complete — simplified modal with employee and skill info
- [x] Page 02.1 (Content Discovery) specification complete — employee-facing assignment card with AI-recommended content
- [x] Page 02.2 (Continue Watching) specification complete — resume interface with progress tracking
- [x] Page 03.1 (Skill Assignment Flow) specification complete — multi-step form for Rita to assign skills
- [x] Page 03.2 (Assignment Confirmation & Auto-Update) specification complete — dashboard confirmation with real-time updates
- [ ] Wireframes and visual design (all 6 pages)
- [ ] Component definitions and design system extraction
- [ ] Real-time update architecture documentation
- [ ] Accessibility verification and WCAG AA audit

---

_Design log for TalentPilot-AI project, maintained throughout WDS phases_
