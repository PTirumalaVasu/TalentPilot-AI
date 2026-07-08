---
title: "PRFAQ Distillate: TalentPilot-AI"
type: llm-distillate
source: "prfaq-TalentPilot-AI.md"
created: "2026-07-08"
purpose: "Token-efficient context for downstream PRD creation"
---

## Concept Type & Framing

- TalentPilot-AI is an **internal tool/pilot**, not a commercial product — no unit economics, no customer-acquisition, no external pricing. Framing calibrated to stakeholder value, adoption path, build-vs-buy justification.
- Core positioning: the villain is **manual self-reporting/status-chasing**, not the spreadsheet format. Excel is where the process happens, not the cause of the pain. This reframe is confirmed and should anchor PRD problem statements — do not regress to "replace the spreadsheet" framing.
- Differentiator is **narrow and specific**: "mixed trust, clearly labeled" — video progress is auto-verified, everything else remains self-reported but visibly labeled as such. The claim is NOT "the dashboard is fully trustworthy." Carry this precise framing into PRD non-goals/scope language to avoid overselling.

## Rejected Framings (do not resurrect without reason)

- "Nobody has to report progress anymore" / "no more chasing status updates" (unscoped) — false; non-video content still requires manual self-report. Any claim about eliminating self-reporting must be scoped to video only.
- Dual-audience-equal headline/positioning — rejected in favor of HR-led framing with employee benefit as supporting, since this is an internal HR-sponsored tool.
- "Dashboard HR can fully trust" — rejected as overclaim; replaced with the mixed/labeled framing above.

## Confirmed Product Decisions (binding for PRD/architecture)

- **Launch date: 13 July 2026.**
- **No data migration at launch** — dashboard starts empty; historical spreadsheet data is not imported.
- **Privacy policy: auto-captured progress data is coaching-only, never used in performance evaluations.** This must be enforced in actual data access/reporting architecture, not just stated in docs.
- Dashboard freshness/label states: **verified** (auto-captured video), **self-reported** (employee-entered, non-video), **needs attention** (stale/inconsistent/unclear) — with drill-down explaining why a status is what it is (ties to existing Trust/Freshness Dashboard design-thinking concept).
- HR retains full manual override authority on readiness judgment regardless of automated signal (e.g., employee who already knows a skill can be manually marked ready by HR without watching the video).

## Requirements Signals Surfaced During Coaching

- **Freshness/labeling UI must be visually unambiguous** — identified as the single point of failure for the entire trust story. If "self-reported" vs. "verified" isn't unmistakable at a glance, HR could misread stale data as verified and make a bad readiness call — a worse outcome than the current spreadsheet, since it happens through a system that appears more trustworthy. Recommend a dedicated usability check before pilot, not just visual design.
- **Content-curation human-approval gate** is a required MVP feature (AI-matched YouTube content needs review before reaching employees, per existing technical research on "AI slop" risk) and an **ongoing operational cost**, not a one-time build item — needs a named operational owner, not just a technical checkpoint.
- Recommended technical de-risking move: a **week-one spike** of the video polling → persist → dashboard pipeline before committing the rest of the build timeline, since integration (not invention) is the real technical risk.
- No test-out/skip-competency path for employees exists in MVP scope — confirmed acceptable, mitigated by HR's manual override.

## Open Questions / Unknowns (carry into PRD as tracked risks, not silently dropped)

1. **Root-cause hypothesis unvalidated.** "Self-reporting, not spreadsheet format, is the real pain" was never tested via HR interviews (deliberate 2026-07-07 decision) — will be validated post-launch via telemetry instead. **Action needed:** define specific telemetry thresholds (staleness % drop, dashboard adoption rate) that count as confirming/refuting this hypothesis, decided in advance, not read favorably after the fact.
2. **No named owner for post-pilot maintenance** (content-approval operations, bug fixes, watching success metrics). User-confirmed deadline: must be resolved **before the Pilot & Validation phase begins**, not before the 13 July build start.
3. **No committed team size/roles/timeline** behind the brief's 5-week phased plan — currently aspirational. Same deadline as above.
4. **Legal/compliance review of employee video-watch tracking has NOT happened.** User explicitly decided this is unnecessary for current scope (internal pilot, coaching-only, no external customers) — a consciously accepted risk. **Action needed:** document an explicit trigger condition for when this becomes mandatory again (e.g., scope expands beyond this pilot, or data use policy changes) so the waiver doesn't silently persist past its valid context.
5. **Post-pilot success path undecided** — expand to other departments vs. ship fast-follows (proactive resume nudges, transcript-level semantic search) vs. other. Should be named before the pilot phase ends.
6. **Comprehension-vs-exposure gap**: watch-% proves engagement, not learning — explicitly accepted as an MVP trade-off (stronger signal than a self-report checkbox, but not proof of competency). Risk: if leadership starts treating dashboard "verified" status as proof of actual skill acquisition rather than engagement, that's a foundation crack surfacing later. PRD should preserve this distinction in any status/label language.

## Competitive / Build-vs-Buy Intelligence

- Reviewed vendors (Cornerstone, Degreed, LinkedIn Learning, Eightfold, Gloat, Continu, Valamis, Paradiso) — none do granular auto-polled video watch-% as a core trust signal; Degreed's "skill signals" remain self-assessment/peer-endorsed (still self-reported).
- Heavyweight platform implementation commonly costs 20–50% of first-year license again, plus meaningful admin overhead — disproportionate for testing one narrow hypothesis, supports the lean-build decision.
- Industry direction (2026 analysis, Bersin) is shifting from completion/self-reported tracking toward behavioral/auto-inferred signals — TalentPilot's bet is directionally aligned with the category, not against it. "Completion is a vanity metric" is a widely shared practitioner complaint, supporting the problem statement.
- No vendor confirmed to use this exact mechanism (auto-polled watch-%) as its primary trust signal — real differentiation, but also means no external validation yet that it actually reduces status-chasing at the scale claimed.

## Scope Boundaries (reaffirmed, unchanged from prior brief/MVP scope)

- Two roles only: HR (assigns, judges readiness manually) and Employee (consumes, resumes).
- Video-only auto-capture; documents/websites remain content-discovery-only with employee self-reported progress.
- No automated skill-gap-to-project matching; HR does this manually.
- No manager/team-lead role.
- No post-completion content recommendations.
- YouTube IFrame API confirmed as video provider (polling-based capture, not event-driven).

## The Verdict (from PRFAQ Stage 5)

**Overall: Forged, with two structural cracks requiring active tending — ready for PRD, but the PRD must carry these forward as first-class requirements:**
1. A tested (not assumed) freshness/labeling UI.
2. A named, accountable owner with a real team/timeline commitment, gated before the pilot phase.
3. An explicit, documented revisit-trigger for the legal/compliance waiver.

Forged-in-steel elements (root-cause reframe, mixed-trust-labeled positioning, privacy boundary, build-vs-buy reasoning, technical feasibility) do not need further validation before PRD — they held up under adversarial questioning and can be treated as settled.
