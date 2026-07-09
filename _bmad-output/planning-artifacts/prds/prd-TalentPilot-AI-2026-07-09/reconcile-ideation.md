# Reconciliation: PRD/Addendum vs. Ideation Source Inputs

**Scope:** Completeness check only — no rewrite. Compares `prd.md` + `addendum.md` against:
- `brainstorm-intent.md` (2026-07-07)
- `design-thinking-2026-07-07.md`
- `innovation-strategy-2026-07-07.md`

Excluded per instructions (already documented, intentional cuts): manager role, content-approval gate, non-video progress tracking, skill-gap auto-matcher, blocker column.

---

## Gap 1 — Fast-Follow features from brainstorm-intent.md are entirely absent from prd.md/addendum.md

**Source:** `brainstorm-intent.md`, "Fast-Follow (Should)" section (lines 32–35):
> - Proactive resume nudges (e.g., "you paused 3 days ago, 8 min left").
> - Transcript-level semantic search: natural-language question jumps to exact video timestamp.

These are not throwaway ideas — `innovation-strategy-2026-07-07.md` treats them as committed near-term roadmap items ("Fast-Follow Feature #1: Proactive Resume Nudges" targeted Month 7–8/Q4 2026, "Fast-Follow Feature #2: Semantic Search" targeted Month 11–12/Q1 2027, §Execution Roadmap), and `design-thinking-2026-07-07.md` independently generated the same ideas (#10/#11 recap-adjacent, and the HMW2 unified-mechanic concept references reusing the watch-position log for future purposes).

**Check performed:** grepped `prd.md` and `addendum.md` for "nudge", "semantic search", "transcript", "fast-follow" — zero matches in either file.

**Why it matters:** The PRD's §6.2 "Out of Scope for MVP" carefully documents other deferred items as v2/v3 candidates with rationale (e.g., "Your Week in Learning" recap/streaks — "no confirmed pain point... deferred to Phase 3/4 if ever"; Proxy-Signal Tracking called out as a v2 candidate for the non-video trust gap). Proactive resume nudges and transcript-level semantic search received the same "Should"-priority treatment in the source brainstorm and a firmer roadmap slot in the strategy doc, yet don't appear anywhere in the PRD's Out of Scope list, Open Questions, or the addendum's Rejected Product Alternatives — they're just missing, not deferred-with-reasoning like their siblings.

**Recommendation:** Add both to §6.2 as explicitly-named v2/fast-follow candidates (mirroring the treatment already given to Proxy-Signal Tracking and the recap/streaks items), or add an Open Question noting they were scoped out of this PRD despite Should-priority status in the source ideation.

---

## Gap 2 — Original dashboard column scope (start date / estimated end date / actual end date) not carried into the PRD's dashboard spec, and not documented as a cut

**Source:** `brainstorm-intent.md`, "HR Dashboard" MVP scope (line 13):
> Per-employee columns: name, skills, sub-skills, start date, estimated end date, actual end date, status.

**PRD's current dashboard spec:** §4.4 / FR-8 defines the Readiness Dashboard row as "Skill, progress, and a Provenance Label" (Verified / Self-reported / Needs Attention), plus a freshness statement ("Not updated in 14 days"). The Glossary's "Assignment" and "Readiness Dashboard" entries likewise don't mention start date, estimated end date, or actual end date fields. The addendum's data model note (`assignments`, `skill_progress`, `content_catalog`) also doesn't name these fields.

**Why it matters:** This isn't necessarily wrong — the provenance-label design is a legitimate, more sophisticated redesign of the original plain-columns concept, and it's plausible date columns were superseded by the Provenance Label + freshness-timestamp approach. But that supersession is never stated. Unlike other scope changes (e.g., "Needs Attention" explicitly redesigned from a filter-view idea into a row-level drill-down state, §FR-10 Out of Scope, with reasoning given), the date-column fields simply vanish with no note that they were considered, folded into something else, or dropped.

**Recommendation:** Either confirm in §3 Glossary / FR-8 that start/estimated-end/actual-end dates are superseded by the Provenance Label + freshness-timestamp model (one sentence), or add them as explicit fields if they were meant to persist.

---

## Gap 3 — "Merge Dashboard + Assignment Flow into one view" (SCAMPER Combine) — a considered alternative with no record in Rejected Product Alternatives

**Source:** `design-thinking-2026-07-07.md`, Ideate phase, provocation #19 (line 124):
> Merge the HR Dashboard and HR Assignment Flow into one continuously-updating view instead of two separate flows.

This sits alongside provocation #18 ("Combine assignment + content-discovery into one screen") — which *was* adopted (UJ-3's three-step modal shows content review inline during assignment, realized as FR-2). #19 is a distinct, further-reaching combine idea (merging the dashboard itself with the assignment flow) that was evidently not adopted — the PRD keeps them as two separate features (§4.1 Skill Assignment Flow vs. §4.4 Provenance-Labeled Readiness Dashboard) — but unlike #18, there's no trace of #19 having been considered and rejected anywhere in `addendum.md`'s "Rejected Product Alternatives" section.

**Why it matters:** The addendum's Rejected Product Alternatives section exists precisely to capture this kind of considered-but-not-selected idea (it already lists the "Reversed flow" idea, which came from the same Ideate list). This one specific alternative from the same brainstorm round was dropped silently.

**Recommendation:** Add one line to addendum's Rejected Product Alternatives, e.g.: "Merged Dashboard+Assignment single view — considered (design-thinking Ideate #19), kept as two separate flows/features instead; no reasoning captured beyond the existing UJ-1/UJ-3 split."

---

## Gap 4 (minor) — No §7 success metric validates AI-Assisted Content Discovery (FR-3/FR-4) quality or engagement

**Source:** `innovation-strategy-2026-07-07.md`, "Leading Indicators" (line 830):
> **Employee Video Consumption Rate** — Target: >40% of assigned content completed (video watch >80%)... Engagement proxy; proof that content discovery is working and employees find it valuable.

**PRD's §7 Success Metrics:** SM-1 through SM-4 and the two counter-metrics all validate FR-1, FR-5, FR-8, FR-9, FR-11 — trust/provenance and assignment-flow speed. None validates FR-3/FR-4 (AI-Assisted Content Discovery) — i.e., whether the semantic-matched content is actually relevant/watched, as opposed to just present. This is one of the PRD's four MVP features (§6.1) with no corresponding success criterion.

**Why it matters:** Weaker than Gaps 1–3 — the innovation-strategy metric is framed as a business/GTM leading indicator for a hypothetical commercial product, not obviously portable to the internal-pilot PRD as-is. But the underlying gap (no metric on content-match quality) is real and traces directly to source material.

**Recommendation:** Low priority — consider adding a lightweight secondary metric (e.g., % of assigned video content watched past some threshold) if content-match quality becomes a pilot concern; otherwise note the omission is deliberate.

---

## Checked and found adequately reflected (not gaps)

- **GDPR/CCPA / employee-consent risk** (innovation-strategy Risk 8, "Data Privacy & Compliance Issues") — covered by PRD Open Questions 1 (data retention, including the 90-day default explicitly traced) and 2 (legal/compliance review consciously declined). Addendum's "Innovation Strategy Notes" section also explicitly traces Open Question 1 back to this risk.
- **Checkpoint quizzes, proxy-signal tracking, "assessed live" manual flag** (design-thinking Ideate #1–7) — all reflected in PRD §6.2 and Open Question 4, or addendum's Rejected Product Alternatives.
- **"Your Week in Learning" recap / streaks / badges** (design-thinking #10–12, brainstorm won't-list) — in addendum's Rejected Product Alternatives and PRD §6.2.
- **Reversed flow** (design-thinking #16) — in addendum's Rejected Product Alternatives.
- **Root-cause hypothesis ("resigned vs. tolerant")** and the decision to skip pre-build HR interviews (design-thinking Empathize/Next Steps) — reflected in PRD §2.1 `[ASSUMPTION]`, §9 Assumptions Index, and Open Question 6.
- **Self-hosted vs. third-party video-hosting constraint** (design-thinking "still-open infrastructure constraint") — resolved in addendum (YouTube IFrame API + Adapter pattern for future Vimeo swap).
- **HRIS integration** (innovation-strategy Market Opportunities/Weakness #4) — flagged as an unresolved scope gap in PRD Open Question 5.
- **"Needs Attention" as a first-class filter view** (design-thinking #14) — explicitly redesigned and documented as an Out of Scope decision in FR-10, with reasoning.

---

## Not flagged (business-model / GTM material, correctly out of scope)

`innovation-strategy-2026-07-07.md` is roughly 80% commercialization strategy (pricing models, sales motion, HRIS partnership sequencing, analyst relations, competitive-pricing risk, runway risk, etc.) written for a hypothetical future commercial product. The PRD's Non-Goals §5 explicitly states "Not a commercial product... no unit economics, no external customer, no pricing model," which correctly and deliberately excludes this material. Not treated as gaps.
