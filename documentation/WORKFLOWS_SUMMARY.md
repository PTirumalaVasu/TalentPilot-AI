# TalentPilot-AI Comprehensive Workflow Summary

## Overview
This document consolidates all BMAD and WDS workflows used in the TalentPilot-AI project, organized by phase. Each workflow includes the agent called, skill called, and a one-line purpose statement.

---

## BMAD Workflows (Business Model & Design)

### Phase 1: Brainstorming
| Component | Details |
|-----------|---------|
| **Agent Called** | Carson (bmad-cis-agent-brainstorming-coach) |
| **Skill Called** | bmad-brainstorming |
| **Purpose** | Multi-phase ideation engine using Job to Be Done, SCAMPER, Morphological Analysis, and Cross-Pollination techniques to identify MVP vs. roadmap features for Talent Pool Management. |
| **Output Directory** | `_bmad-output/brainstorming/brainstorm-talent-pool-management-capabilities-2026-07-07/` |

**Files Created:**
1. **`.memlog.md`** — Append-only session memory (24 entries) with ideas, scope decisions, MoSCoW convergence, and final synthesis insights.
2. **`brainstorm-intent.md`** — Condensed summary of confirmed MVP decisions (Must/Should/Won't) and architectural framing for downstream use.

---

### Phase 2: Design Thinking
| Component | Details |
|-----------|---------|
| **Agent Called** | Maya (bmad-cis-agent-design-thinking-coach) |
| **Skill Called** | bmad-cis-design-thinking |
| **Purpose** | Seven-step human-centered design workflow (Empathize→Define→Ideate→Prototype→Test→Next Steps) to translate brainstorm insights into tangible user-centered design artifacts. |
| **Output Directory** | `_bmad-output/` |

**Files Created by bmad-cis-design-thinking:**
1. **`design-thinking-2026-07-07.md`** — Seven-step design artifact with challenge, empathy map, POV statements, 21 ideas, 3 top concepts, prototyping methods, test plan, and next steps saved incrementally at checkpoints.

**Supporting Skill (bmad-party-mode - Invoked at Checkpoints):**
| Component | Details |
|-----------|---------|
| **Skill Called** | bmad-party-mode |
| **Purpose** | Multi-persona stress-test round-table (22 agents across bmm, cis, gds, wds modules) at Step 1 & 2 checkpoints to challenge design challenge and empathy map through diverse perspectives (Analyst Mary, PM John, UX Sally, Architect Winston, Dev Amelia, Test Murat, Innovation Victor, Problem-Solver Quinn, Brainstorming Carson). |
| **Invoked By** | Maya persona (Design Thinking Coach) at Step 1 & 2 checkpoints |
| **Output Directory** | `_bmad-output/party-mode/memories/installed/` |

**Files Created by bmad-party-mode:**
1. **`.memlog.md`** — Append-only party-room memory across two rounds documenting diverse persona feedback (Victor's challenges, John's defenses, Mary's gaps, Sally's risks, Quinn's hypotheses) for future sessions.

---

### Phase 3: Domain Research
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation) |
| **Skill Called** | bmad-domain-research |
| **Purpose** | Conduct time-boxed, pitch-focused industry research via web search covering market sizing, competitive landscape, and technology trends for corporate skill-tracking AI video-learning platforms. |
| **Output Directory** | `_bmad-output/planning-artifacts/research/` |

**Files Created:**
1. **`domain-corporate-skill-tracking-ai-video-learning-platforms-research-2026-07-07.md`** — Pitch-focused research covering industry analysis, market drivers, competitive landscape, technology trends, and strategic recommendations right-sized for 1-week hackathon.

---

### Phase 4: Market Research
| Component | Details |
|-----------|---------|
| **Agent Called** | Mary (bmad-agent-analyst) |
| **Skill Called** | bmad-market-research |
| **Purpose** | Six-step, source-cited market research workflow (customer behavior→pain points→decision journey→competitive landscape→synthesis) validating TalentPilot-AI MVP positioning against corporate LMS/skills-intelligence market. |
| **Output Directory** | `_bmad-output/planning-artifacts/research/` |

**Files Created:**
1. **`market-ai-talent-pool-management-platform-research-2026-07-07.md`** — 11-section comprehensive market research with customer insights, competitive landscape (three tiers: enterprise suites, LMS incumbents, point tools), market sizing ($15–34B CAGR 8.4–22.9%), GTM strategy, and risk mitigation—all source-cited from 18 web searches.

---

### Phase 5: Innovation Strategy
| Component | Details |
|-----------|---------|
| **Agent Called** | Victor (bmad-cis-agent-innovation-strategist) |
| **Skill Called** | bmad-cis-innovation-strategy |
| **Purpose** | Nine-step innovation strategy workflow (context→market→business-model→disruption/innovation-opportunities→strategic-options→execution-roadmap→success-metrics) recommending "Focused Wedge" strategy with 24-month 3-phase roadmap. |
| **Output Directory** | `_bmad-output/` |

**Files Created:**
1. **`innovation-strategy-2026-07-07.md`** — Nine-section strategy document recommending "Focused Wedge" Option A with 24-month 3-phase roadmap (POC→MVP→leadership), including business-model analysis, disruption vectors, 9-10 innovation opportunities, three strategic options comparison, execution phases with exit gates, and 8 risk mitigations with 12 success metrics.

---

### Phase 6: Technical Research (3 Runs)

#### Run 1 - Video Embedding
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation) |
| **Skill Called** | bmad-technical-research |
| **Purpose** | Six-step technical research on third-party video embed (YouTube vs. Vimeo) with custom watch-progress tracking via player API and database persistence—decision: **YouTube chosen**. |
| **Output Directory** | `_bmad-output/planning-artifacts/research/` |

**Files Created:**
1. **`technical-third-party-video-embeds-youtubevimeo-with-custom-watch-progress-tracking-research-2026-07-07.md`** — Video-embed technical research comparing YouTube IFrame API vs. Vimeo SDK, Adapter pattern architecture, conditional-write data persistence, and implementation risks; concluded with YouTube as chosen provider.

#### Run 2 - RAG/Vector Database
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation) |
| **Skill Called** | bmad-technical-research |
| **Purpose** | Six-step technical research on RAG/vector-database tutorial matching against assigned skills—decision: **pgvector + text-embedding-3-small confirmed** as embedding/retrieval backend. |
| **Output Directory** | `_bmad-output/planning-artifacts/research/` |

**Files Created:**
1. **`technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md`** — RAG/vector research confirming retrieval-only (no LLM), pgvector backend, batch-then-query pipeline, filter-then-rank pattern, YouTube quota constraints (100 calls/day), embedding cost ($0.02/1M tokens), and content-quality risk with human-approval checkpoint.

#### Run 3 - Overall Stack & Architecture
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation) |
| **Skill Called** | bmad-technical-research |
| **Purpose** | Comprehensive full-stack technical research covering architecture, frontend (React), backend (Python+FastAPI), database (PostgreSQL+pgvector), API design, auth, and testing patterns. |
| **Output Directory** | `_bmad-output/planning-artifacts/research/` |

**Files Created:**
1. **`technical-overall-stack-architecture-for-talentpilot-ai-research-2026-07-08.md`** — Full-stack architecture recommending Python/FastAPI + React/Vite + PostgreSQL/pgvector, RESTful API with JWT-cookie auth, two-tier design, feature-domain layering, shadcn/ui+Tailwind UI, testing frameworks (pytest/Vitest/RTL), with hosting/deployment deferred.

---

### Phase 7: Product Brief
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation); Parallel subagents spawned during finalization: Editorial Structure Review Agent, Editorial Prose Review Agent |
| **Skill Called** | bmad-product-brief |
| **Purpose** | Create a concise, structured product brief (1–2 pages) that aligns the team on solution concept, MVP scope, competitive positioning, and implementation feasibility for stakeholder decision gate. |
| **Output Directory** | `_bmad-output/planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/` |

**Files Created:**
1. **`brief.md`** — ~1,400-word product brief aligning stakeholders on solution (HR assigns → system recommends → auto-captures → dashboard tracks), MVP scope, competitive wedge, success criteria, 5-week implementation plan, and flagged assumptions.

2. **`.memlog.md`** — Append-only session record tracking stakeholder alignment decisions, POC scope, success gates, and editorial refinements applied.

---

### Phase 8: PRFAQ (Press Release & FAQ)
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Direct invocation); Parallel subagent spawned: Web Researcher (for build-vs-buy landscape research) |
| **Skill Called** | bmad-prfaq |
| **Purpose** | Amazon's Working Backwards methodology—write the press release for the finished product, then stress-test through Customer FAQ and Internal FAQ, ending in a three-category verdict (forged in steel / needs more heat / cracks in foundation) and distillate for downstream PRD work. |
| **Output Directory** | `_bmad-output/planning-artifacts/` |

**Files Created:**
1. **`prfaq-TalentPilot-AI.md`** — Working Backwards artifact: press release, customer FAQ (9 questions on trust/quality/discontinuation), internal FAQ (9 on maintenance/adoption/root-cause), three-category verdict (Forged in Steel / Needs More Heat / Cracks in Foundation), and coaching notes.

2. **`prfaq-TalentPilot-AI-distillate.md`** — Token-efficient summary of press release claims, FAQs, verdict, and carry-forward decisions for downstream PRD work.

---

## WDS Workflows (Whiteport Design Studio)

### Phase 0: Alignment Signoff (Partial)
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Saga identity) |
| **Skill Called** | wds-0-alignment-signoff |
| **Purpose** | Establish whether stakeholder alignment is needed (preliminary step); exited early by design after determining alignment wasn't required before proceeding to Phase 1. |
| **Output Directory** | None (exited early) |
| **Key Finding** | Confirmed alignment was not the blocker; proceeded directly to Phase 1. |

**Files Created:** None (exited after step-01b determine-if-needed decision).

---

### Phase 1: WDS Product Brief
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Saga identity: "Saga the Analyst") |
| **Skill Called** | wds-1-project-brief |
| **Purpose** | Establish the strategic foundation for downstream WDS design work (Phase 2-5) through collaborative discovery—capturing formal vision statement, positioning, target-user behavioral profiles, structural product concept, and platform/tone-of-voice direction. |
| **Distinct From** | BMAD's `bmad-product-brief` (business/stakeholder sign-off) vs. WDS brief (design-pipeline strategic foundation). |
| **Output Directory** | `_bmad-output/A-Product-Brief/` |
| **Key Decision** | Deferred resolution of brief-consolidation question (keep separate / consolidate BMAD+WDS briefs / decide later)—user chose to continue; marked as outstanding item in brief's "Next Steps" section. |

**Files Created:**
1. **`project-brief.md`** — Strategic foundation with vision statement, positioning, target-user profiles (Rita/Casey), product concept (dashboard-first auto-capture system), and tone-of-voice direction (coaching-only privacy, trust-focused).

2. **`dialog/00-context.md`** — Project metadata capturing stakes, collaboration style, and documentation approach.

3. **`dialog/decisions.md`** — Decision log with brief-level choice, stakeholder alignment, success criteria, and carry-forward assumptions.

---

### Phase 2: WDS Trigger Mapping
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Saga identity: "Saga the Analyst") |
| **Skill Called** | wds-2-trigger-mapping |
| **Purpose** | Connect business goals to user psychology through Trigger Mapping (WDS's Impact/Effect Mapping adaptation)—producing a four-layer strategic map (Business Goals → Product/Solution → Target Groups → Usage Goals) with explicit positive/negative driving forces, prioritized via Feature Impact scoring. |
| **Output Directory** | `_bmad-output/B-Trigger-Map/` |
| **Key Adaptation** | "Trust flywheel" reframing (internal tool context) instead of default "champion/community flywheel" commercial metaphor. |

**Files Created:**
1. **`00-trigger-map.md`** — Four-layer Trigger Map (Business Goals → Product/Solution → Target Groups → Usage Goals) with positive/negative driving forces, personas (Rita, Casey), and Feature Impact scoring prioritizing dashboard and auto-capture.

2. **`persona-rita-hr-manager.md`** — Profile of Rita with goals, pain points, mental model, decision-making, and objection handlers.

3. **`persona-casey-employee.md`** — Profile of Casey with learning goals, pain points, behavior patterns, and objection handlers.

4. **`feature-impact-matrix.md`** — Feature prioritization table scoring impact for dashboard, auto-capture, resume, and supporting features.

---

### Phase 3: WDS UX Scenarios
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Saga identity: "UX Scenario Facilitator") |
| **Skill Called** | wds-3-scenarios |
| **Purpose** | Define three target user scenarios (Scenario 01: Rita's Trust Call / Scenario 02: Casey's Resume & Watch / Scenario 03: Rita's Assignment & Track) with detailed page flows, wireframes, and user journeys to operationalize trigger mapping insights. |
| **Output Directory** | `_bmad-output/B-Trigger-Map/scenarios/` |

**Files Created:**

**Scenario 01: Rita's Trust Call**
1. **`Scenario-01/00-scenario.md`** — Overview: Rita verifies employee progress and auto-capture evidence via Skills Dashboard + Provenance Drill-Down modal.
2. **`Scenario-01/wireframes.md`** — Wireframes with Object IDs, component structure, and state variations (Loaded/Loading/Empty/Error).
3. **`Scenario-01/acceptance-criteria.md`** — User journey: view assignments → spot incomplete → drill down → see play history → confirm trustworthiness → mark complete.

**Scenario 02: Casey's Resume & Watch**
1. **`Scenario-02/00-scenario.md`** — Overview: Casey resumes interrupted video via Content Discovery page and Continue Watching with saved timestamp.
2. **`Scenario-02/wireframes.md`** — Wireframes for assignment card (title, play buttons, approval badge) and progress bar (resume timestamp, playhead).
3. **`Scenario-02/acceptance-criteria.md`** — User journey: find assignment → click Play → resume at exact timestamp.

**Scenario 03: Rita's Assignment & Track**
1. **`Scenario-03/00-scenario.md`** — Overview: Rita assigns skill to Casey via 3-step modal, confirms, and watches toast/highlight on dashboard.
2. **`Scenario-03/wireframes.md`** — Wireframes: Dashboard + [+ New Assignment] button → 3-step modal → toast confirmation with new row highlight.
3. **`Scenario-03/acceptance-criteria.md`** — User journey: click New Assignment → select employee/skill/content → confirm → new row appears with toast and auto-capture starts.

---

### Phase 4: WDS UX Design
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Freya identity: "Freya the UX Designer") |
| **Skill Called** | wds-4-ux-design |
| **Purpose** | Specify design for all 3 scenarios through step-by-step page-specification workflow—defining components, interactions, Object IDs, states, and acceptance criteria; includes Validation Retrofit (close readiness gaps) and Design Delivery handoff (package into dev-ready requirements contract). |
| **Modes Invoked** | `[S] Suggest Design` → `[V] Validate Specs` (retrofit) → `[H] Design Delivery` |
| **Output Directory** | `_bmad-output/C-UX-Scenarios/`, `_bmad-output/_progress/` |

**Files Created:**

**Phase 4a: Suggest Design (Specification)**
1. **`C-UX-Scenarios/01.1-skills-dashboard.md`** — Spec for Skills Dashboard: components (Header, Filter, Grid, Provenance Modal), Object IDs, state matrix (grid/modal states), interactions, <2s load acceptance criteria.

2. **`C-UX-Scenarios/02.1-content-discovery.md`** — Spec for Content Discovery: assignment card components, Object IDs, Loaded/Loading/Error states, Play button primary action, <2s load.

3. **`C-UX-Scenarios/02.2-continue-watching.md`** — Spec for Continue Watching: progress card, resume button, playhead indicator, Object IDs, timestamp accuracy to nearest second.

4. **`C-UX-Scenarios/03.1-assignment-flow-modal.md`** — Spec for 3-Step Assignment Modal: employee/skill/content selectors, Object IDs, form validation, auto-recommended content, "assign without content" fallback.

**Phase 4b: Validate Specs (Retrofit)**
1. **`_progress/validation-report.md`** — Retrofit findings: identified and added 4 missing Object IDs for modal body content (Provenance Summary, Raw Signal Data, explanatory text, Actions); confirmed all specs ready for build.

**Phase 4c: Design Delivery Handoff**
1. **`DD-001.md`** — Design Delivery: user value (Rita proves progress, Casey reports automatically), design artifacts (4 page specs, 40+ Object IDs), React/FastAPI/PostgreSQL tech stack, 60-day source-of-truth acceptance, Medium complexity estimate, status in_development.

2. **`TS-001.md`** — Test Scenario: happy paths (Rita drills down, Casey resumes, Rita assigns), test data (4 assignments, 2 employees), verification of persistence/modals/auto-capture.

---

### Phase 5: WDS Agentic Development (Prototyping)
| Component | Details |
|-----------|---------|
| **Agent Called** | None (Built-in Implementation Partner identity) |
| **Skill Called** | wds-5-agentic-development |
| **Purpose** | Build self-contained, static HTML/Tailwind/vanilla-JS interactive prototypes from approved Phase 4 specs—explicitly throwaway UX-validation artifacts (no real backend, sessionStorage-only demo data) to validate UX before committing to real DD-001 build. |
| **Mode** | `[P] Prototyping` (selected over `[D] Development` to validate UX first) |
| **Scenarios Built** | 01 (Rita's Trust Call), 02 (Casey's Resume & Watch), 03 (Rita's Assignment & Track) |
| **Output** | `E-Development/01-Ritas-Trust-Call-Prototype/`, `02-Caseys-Resume-and-Watch-Prototype/`, `03-Ritas-Assignment-and-Track-Prototype/` |
| **Key Finding** | Fixed `fetch()`-under-`file://` bug discovered in Scenario 01; solution applied proactively to Scenarios 02/03 via `<script>`-tag global pattern instead of network fetch. |

---

## Cross-Workflow Memory & Context

### Persistent Memory File
**`_bmad-output/project-context.md`** — Shared cross-phase memory used by all BMAD (`bmm`, `cis`) phases for carrying forward decisions, research findings, and technical stack choices. **Not used by WDS phases** (which maintain separate `_bmad/wds/config.yaml` and phase-specific design logs instead).

#### Key Decisions Carried Forward:
- Video provider: **YouTube** (not Vimeo)
- Vector database: **pgvector + text-embedding-3-small** (not full RAG)
- Tech stack: **Python/FastAPI + React + PostgreSQL**
- Privacy constraint: **Coaching-only** (never in performance evaluations)
- No pre-build validation sprint (validate post-launch with telemetry)

### WDS Design Log
**`_bmad-output/_progress/00-design-log.md`** — Phase-by-phase narrative log for WDS workflow continuity; documents decisions, substitutions (reference-doc unavailability, methodology adaptations), and completion status per page/scenario.

---

## Summary Table: All Workflows by Sequence

| # | Module | Phase | Agent | Skill | Output Type | Status |
|---|--------|-------|-------|-------|-------------|--------|
| 1 | BMAD | Brainstorming | Carson | bmad-brainstorming | Intent doc + memlog | ✓ Complete |
| 2 | BMAD | Design Thinking | Maya | bmad-cis-design-thinking | 7-step design doc | ✓ Complete |
| 2a | BMAD | Design Thinking (Support) | Maya | bmad-party-mode | Round-table stress-test | ✓ Complete |
| 3 | BMAD | Domain Research | — | bmad-domain-research | Trimmed research doc | ✓ Complete |
| 4 | BMAD | Market Research | Mary | bmad-market-research | Comprehensive market report | ✓ Complete |
| 5 | BMAD | Innovation Strategy | Victor | bmad-cis-innovation-strategy | 9-step strategy + roadmap | ✓ Complete |
| 6.1 | BMAD | Technical Research (Video) | — | bmad-technical-research | Video embed research | ✓ Complete |
| 6.2 | BMAD | Technical Research (RAG) | — | bmad-technical-research | Vector DB research | ✓ Complete |
| 6.3 | BMAD | Technical Research (Stack) | — | bmad-technical-research | Full-stack architecture | ✓ Complete |
| 7 | BMAD | Product Brief | — | bmad-product-brief | 1–2 page brief + memlog | ✓ Complete |
| 8 | BMAD | PRFAQ | — | bmad-prfaq | Press release + FAQs + verdict | ✓ Complete |
| 0 | WDS | Alignment Signoff | — | wds-0-alignment-signoff | (Partial/Exited) | ✓ Exited Early |
| 1 | WDS | WDS Product Brief | Saga | wds-1-project-brief | Strategic brief + dialog | ✓ Complete |
| 2 | WDS | Trigger Mapping | Saga | wds-2-trigger-mapping | 4-layer trigger map + personas | ✓ Complete |
| 3 | WDS | UX Scenarios | Saga | wds-3-scenarios | 3 scenario flows + wireframes | ✓ Complete |
| 4 | WDS | UX Design | Freya | wds-4-ux-design | Specs + Design Delivery | ✓ Complete |
| 5 | WDS | Agentic Development | Implementation Partner | wds-5-agentic-development | 3 HTML prototypes | ✓ Complete |

---

## Detailed File Manifests by Workflow

### WDS Phase 5: Agentic Development (Prototyping)

| Component | Details |
|-----------|---------|
| **Skill Called** | wds-5-agentic-development |
| **Mode** | `[P] Prototyping` (selected over `[D] Development` to validate UX first) |
| **Output Directory** | `_bmad-output/E-Development/` |
| **Key Finding** | Fixed `fetch()`-under-`file://` bug in Scenario 01; solution applied proactively to Scenarios 02/03 |

**Scenario 01: Rita's Trust Call**

Files in `01-Ritas-Trust-Call-Prototype/`:
1. **`PROTOTYPE-ROADMAP.md`** — Build plan correcting from 2-file to 1-file (dashboard + modal overlay as single view).
2. **`data/demo-data.js`** — Mock backend (4 assignments, 3 employees, video progress) using script-tag global (not fetch()).
3. **`shared/prototype-api.js`** — Mock API (loadDashboard, getProvenance, getCurrentTime), debounced state.
4. **`shared/init.js`**, **`shared/utils.js`** — Auto-init, date formatting utilities.
5. **`components/dev-mode.js`**, **`components/dev-mode.css`** — Shift+Click Object ID inspector.
6. **`work/Logical-View-Map.md`** — Confirms single logical view (overlay pattern).
7. **`work/Skills-Dashboard-Work.yaml`** — 6-section build status log.
8. **`stories/01.1.1-*.md`** through **`01.1.6-*.md`** — 6 story files with fetch-bug root-cause in Section 4.
9. **`01.1-Skills-Dashboard.html`** — Dashboard grid + Provenance modal, 17 Object IDs, 8 states.

**Scenario 02: Casey's Resume & Watch**

Files in `02-Caseys-Resume-and-Watch-Prototype/`:
1. **`PROTOTYPE-ROADMAP.md`** — Confirms two separate logical views (02.1, 02.2); fetch fix applied proactively.
2. **`data/demo-data.js`** — Casey's 2 assignments, content catalog; script-tag global from start.
3. **`shared/`**, **`components/`**, **`work/`** — Same pattern as Scenario 01.
4. **`stories/02.1.1-*.md`** through **`02.2.4-*.md`** — 8 story files (4 per view).
5. **`02.1-Content-Discovery.html`** — Assignment card, Play button, 12 Object IDs.
6. **`02.2-Continue-Watching.html`** — Progress card, resume timestamp 14:32, 12 Object IDs, cross-page nav links.

**Scenario 03: Rita's Assignment & Track**

Files in `03-Ritas-Assignment-and-Track-Prototype/`:
1. **`PROTOTYPE-ROADMAP.md`** — Structural decision: duplicated Scenario 01 dashboard per convention; trade-off documented.
2. **`data/demo-data.js`** — 4 starting assignments, skills/content catalog.
3. **`shared/prototype-api.js`** (extended) — `getContentForSkill()`, `createAssignment()` methods.
4. **`shared/`**, **`components/`**, **`work/`** — Same pattern as prior scenarios.
5. **`stories/03.1-*.md`** through **`03.6-*.md`** — 6 story files (modal + toast/highlight).
6. **`03-Skills-Dashboard.html`** — Extended from 01.1 with 3-step Assignment modal (23 IDs), toast, highlight, dual-modal handling.

**Shared Across All Scenarios**

1. **`_progress/00-design-log.md`** — Built status per page, narrative per scenario (logical-view decisions, fetch-bug fix, duplication trade-offs).

---

## Key Insights

### Workflow Patterns
1. **BMAD modules** (bmm, cis) use persona-agents (Carson, Maya, Mary, Victor) with persistent `project-context.md` memory.
2. **WDS module** uses built-in facilitator identities (Saga, Freya, Implementation Partner) with separate `_bmad/wds/config.yaml` and phase-specific design logs.
3. **Subagents** are spawned for specific tasks (editorial review, web research, artifact analysis) but not for core workflow steps.
4. **All workflows read prior artifacts directly** rather than re-asking discovery questions (e.g., PRFAQ read product brief; WDS Trigger Mapping read WDS Product Brief).

### Decision Gates & Outstanding Items
1. **Brief consolidation**: Keep BMAD and WDS briefs separate vs. consolidate—deferred, marked as "Next Steps" item.
2. **Post-pilot owner**: Must be locked before Pilot & Validation phase begins; aspirational timeline noted.
3. **Stack documentation**: Python/FastAPI/React/PostgreSQL stack documented but not yet written to `project-context.md` (noted as "Outstanding follow-up").

---

## How to Use This Document

- **For future sessions**: Read this file + the relevant section's output artifacts to understand what was decided and why.
- **For extending workflows**: Check the phase-specific "Outstanding follow-up" or "Next Steps" items before re-running a skill.
- **For memory consistency**: Verify `project-context.md` (BMAD phases) or `_progress/00-design-log.md` (WDS phases) before making downstream decisions that depend on prior findings.
