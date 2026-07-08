# Agent Experience: Dream Up - TalentPilot-AI Trigger Map

**Created:** 2026-07-08
**Mode:** Dream (autonomous)
**Phase:** 2 (Trigger Mapping)
**Project:** TalentPilot-AI

---

## Layer 1: WDS Form Learned

**Methodology loaded:**
- `_bmad/wds/data/agent-guides/saga/trigger-mapping.md` (WDS Trigger Mapping methodology — no equivalent of `docs/method/phase-wds-2-trigger-mapping-guide.md`, `docs/models/impact-effect-mapping.md`, or `docs/method/dream-up-rubric-phase-2.md` exists in this project; those paths are generic skill defaults, not populated here)
- `_bmad/wds/data/agent-guides/saga/dream-up-approach.md` (5-layer generation process, mode presentation formats, completeness gate)
- `.claude/skills/wds-2-trigger-mapping/templates/*.template.md` (trigger-map, persona-document, feature-impact)
- `.claude/skills/wds-2-trigger-mapping/data/*.md` (business-goals-template, key-insights-structure, mermaid-formatting-guide, quality-checklist)

**Structure internalized:**
- 4 layers: Business Goals → Product/Solution Hub → Target Groups → Usage Goals (Positive/Negative Drivers)
- 3×3 Business Goals format (3 visionary goals, 3 SMART objectives each)
- 2-4 target groups max, prioritized, psychological (not demographic) personas
- 3-5 positive + 3-5 negative driving forces per persona, WHAT+WHY+WHEN pattern
- Feature Impact scoring: Frequency × Intensity × Fit (1-5 each, max 15)

**Adaptation decision:** The template/rubric language ("champions," "convert users," "community flywheel") is tuned for a consumer/community product. TalentPilot-AI is an internal, single-organization pilot tool with two in-house roles (HR Admin, Employee) — no external community or commercial flywheel exists. Adapted language: "trust flywheel" (HR's growing trust → validated evidence pipeline → case for post-pilot investment) replaces "champion flywheel," and "creating awesome users" is reframed as "making the honest data model work for the people who live with it daily." Structure and rigor preserved; metaphor adapted to fit an internal B2B context.

**Quality standards target:** 7+/9 completeness, 5+/7 quality criteria, 4/4 mistakes avoided, 2+/4 best practices (minimum); 9/9, 7/7, 4/4, 4/4 (excellent).

---

## Layer 2: Project Context (Cumulative)

### Initial: Product Brief (`_bmad-output/A-Product-Brief/project-brief.md`)

**Business:** TalentPilot-AI — solo-built internal pilot for SAILS Software's HR function. Zero budget, hard launch 13 July 2026, no external stakeholder gate, no commercial ambition.

**Challenge:** HR's shared spreadsheet depends on self-reported status nobody trusts; the villain is the self-reporting chore, not the spreadsheet format itself.

**Goal:** Prove cheaply that automated (video-watch) evidence outperforms self-reporting for skill-readiness signal, before SAILS commits further.

**User archetypes (from brief, to deepen into personas):**
1. **HR Admin (Primary)** — opens shared sheet daily to assign + judge readiness; resigned, not tolerant, about the current process; doesn't trust the status column; anxious making staffing calls on suspect data.
2. **Employee (Secondary)** — self-reports into the same sheet today, zero personal payoff, easy to deprioritize; wants Netflix/Spotify-style resume.

**Constraints:** Desktop-first responsive web; YouTube IFrame API + Postgres/pgvector; no native app; zero budget; solo team (TalentPilot owns bug fixes/content approval/metrics).

**Strategic direction:** Primary metric — self-reported staleness <5% within 60 days (~11 Sept 2026). Secondary — HR uses TalentPilot-AI as primary source of truth with minimal spreadsheet reliance, measured via usage analytics + stakeholder feedback.

### Added: Design Thinking Session (2026-07-07)

- Confirms HR's core recurring action is *entry* (assigning), with *readiness judgment* as a separate, occasional, high-stakes act — two distinct interaction modes in one tool.
- Confirms Employee's self-reporting is a single point of failure with zero personal payoff; "mild guilt or avoidance," not malicious noncompliance.
- Surfaces the "Trust/Freshness Dashboard" concept (per-cell freshness indicator, Needs Attention filter, drill-down reasoning) and "Unified Auto-Capture + Resume" concept (one signal, two payoffs) — both carried directly into driving-force design below.
- Flags an unresolved risk: sub-skills/status fields that aren't video-shaped still depend on self-report even post-launch — an uneven trust story is itself a UX risk, informs a negative driver for Rita.

### Added: Domain Research (2026-07-07)

- Corporate LMS market growing ~22% CAGR; 87% of CHROs expect more AI-in-HR adoption in 2026 — validates timing but is background market context, not persona-specific; not force-fit into personas.
- 95% of L&D orgs can't reliably tie learning data to business decisions — external validation that Rita's distrust of the status column is an industry-wide pattern, not an idiosyncratic complaint. Used to strengthen driving-force intensity scoring (this is a common, not edge-case, fear).
- Video watch-time tracking is a mature, named analytics category — de-risks Casey's "progress speaks for itself" driver as buildable, not speculative.

---

## Layer 3: Domain Research Notes (applied, not re-run)

No live WebSearch tool was available in this environment. Rather than fabricate new domain research, Layer 3 draws on the domain research report already completed for this project (above) plus the confirmed empathy-map findings from the design thinking session — both are legitimate research inputs per the dream-up-approach guide, and re-running the same research would add no new signal.

---

## Generation & Self-Review Log

### Business Goals — Iteration 1

**Applied:** 3×3 structure from Layer 1; Business Context + Success Criteria + Constraints sections from Product Brief (Layer 2).

**Self-review:**
- Vision: character-for-character sourced from brief's Business Context primary goal statement — ✅ traceable, not paraphrased loosely.
- 3 goals hierarchically ordered: (1) Prove the evidence-pipeline hypothesis [primary/engine], (2) Earn HR's trust as primary source of truth [prerequisite], (3) Eliminate the self-report chore [prerequisite, enables #2].
- Each objective sourced directly from brief's locked Success Criteria / Constraints / Design Thinking success metrics — no invented numbers.
- Check: "Metrics ≠ Goals" — goals stated as outcomes (prove hypothesis, earn trust, eliminate chore), objectives carry the measurable targets. ✅
- Quality: 9/9 complete, 7/7 quality, 4/4 mistakes avoided, 3/4 best practices (no visual diagram at this sub-step; that's Layer 4 hub work). Threshold met, no refinement needed.

### Target Groups / Personas — Iteration 1

**Applied:** 2-persona structure (matches brief's explicit Primary/Secondary + design thinking's "two roles in scope, no third role"). Did not fabricate a third/tertiary persona — the source material is explicit that only two roles exist; inventing a tertiary persona would violate "no solutions/personas without grounding."

**Rita the Referee (HR Admin, Primary)** — psychological profile drawn from design thinking's confirmed Does/Says/Thinks/Feels (resigned-not-tolerant, chases people not data errors, judges readiness as separate occasional act from daily assignment entry).

**Casey the Continuer (Employee, Secondary)** — psychological profile drawn from design thinking's Employee empathy map (mild guilt/avoidance, no personal payoff, wants Netflix-style resume) plus brief's explicit "Netflix/Spotify pattern" language.

**Self-review:** 9/9 complete, 7/7 quality (psychological not demographic — evidence: "resigned, not tolerant" and "no personal payoff" are stated motivations, not traits), 4/4 mistakes avoided (no solutions on the persona cards themselves — the Product Promise/Answer sections in the full persona docs describe how the product responds to psychology, which the template explicitly requires, not features baked into the persona definition), 4/4 best practices (alliterative names, equal driver weight, explicit usage context, mermaid diagram planned for hub). Threshold met.

### Driving Forces — Iteration 1

**Applied:** WHAT+WHY+WHEN pattern; 3 positive + 3 negative per persona, scored via Frequency × Intensity × Fit.

**Self-review:** Checked each force against the "too vague" test (Actionability / Psychology / Context) from the trigger-mapping guide — no force reads as "want convenience" or "feel confident" without qualification. All scored using domain-research-supported intensity (e.g., Rita's data-distrust fear scored high-intensity based on the "95% of L&D orgs can't trust their data" external validation, not just internal assumption). 4/4 mistakes avoided, 7/7 quality criteria met. Threshold met.

### Prioritization — Iteration 1

**Applied:** Feature Impact scoring method from trigger-mapping.md. Top scores: Rita's "trust the dashboard immediately" (15/15, HIGH), Casey's "progress speaks for itself" (14/15, HIGH) — both map directly to the brief's "one signal, two payoffs" structural idea, confirming internal consistency rather than the workshop inventing a new priority.

**Self-review:** Prioritization is defensible and traceable to the brief's own stated differentiator (auto-capture is the core mechanic serving both personas at once) rather than an arbitrary ranking. 4/4 mistakes avoided (clear priority exists). Threshold met.

---

## Final Output

**Artifacts:** `_bmad-output/B-Trigger-Map/00-trigger-map.md`, `01-Business-Goals.md`, `02-Rita-the-Referee.md`, `03-Casey-the-Continuer.md`, `05-Key-Insights.md`, `06-Feature-Impact.md`

**Final Quality Assessment:** 9/10 — all four documents meet or exceed minimum thresholds; adapted "champion/flywheel" language to internal-tool context deliberately and documented above, which is the only meaningful deviation from template defaults.

**User Approved:** Pending (Dream mode — presented for review after generation).
