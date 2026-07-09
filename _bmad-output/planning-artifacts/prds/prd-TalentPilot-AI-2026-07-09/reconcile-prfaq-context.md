---
title: "Reconciliation: PRD vs. PRFAQ / Distillate / Project Context"
type: completeness-check
subject: "_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md (+ addendum.md)"
created: "2026-07-09"
---

# Reconciliation Findings

Scope: completeness check only, not a rewrite recommendation. Sources reconciled against the finished `prd.md` + `addendum.md`:
- `_bmad-output/planning-artifacts/prfaq-TalentPilot-AI.md`
- `_bmad-output/planning-artifacts/prfaq-TalentPilot-AI-distillate.md`
- `_bmad-output/project-context.md`

Deliberate exclusions the PRD already bakes in and flags explicitly (e.g., no content-approval gate with an `[ASSUMPTION]` tag, no "Needs Attention" filter page, no manager role, no HRIS integration) are **not** re-flagged below — those are traceable, intentional decisions, not gaps.

---

## Gap 1 — HR's manual-override authority on readiness (MVP capability, not v2) is missing from the PRD entirely

**Source:** PRFAQ Customer FAQ ("I already know this skill — do I have to sit through the video anyway?"): *"you watch anyway, or tell HR directly and they manually override the record, since HR retains manual readiness judgment regardless of what the automated signal shows."* Distillate promotes this to **"Confirmed Product Decisions (binding for PRD/architecture)"**: *"HR retains full manual override authority on readiness judgment regardless of automated signal (e.g., employee who already knows a skill can be manually marked ready by HR without watching the video)."* It is also the PRFAQ's answer to the "no test-out path" question — override is the stated MVP mitigation, not a future one.

**What's in the PRD instead:** A search for "override" in `prd.md`/`addendum.md` returns exactly two hits, both describing an **"Assessed Live" manual-override audit flag** — explicitly a **v2 candidate** for the non-video trust gap (§6.2, Open Question 4), not an MVP feature. There is no FR, Glossary entry, or dashboard behavior in §4.4 (FR-8–FR-11) that lets HR mark a video-tracked Assignment "ready" without a watch signal, and no Non-Goal that explicitly retires this capability for MVP either.

**Why it matters:** The PRFAQ presented this as the live, MVP-scope answer to a real customer objection (already-competent employees forced to sit through video). The PRD silently drops it without either implementing it as an FR or logging it as a Non-Goal/Open Question explaining the reversal. As written, an implementer following the PRD alone would not know HR needs any override path at all in v1.

---

## Gap 2 — The PRFAQ's "labeling UI clarity" pre-launch usability risk has no corresponding requirement or open item

**Source:** This is one of the PRFAQ's two headline "structural cracks," and the distillate's Verdict lists it as one of exactly three things "the PRD must carry forward as first-class requirements": *"A tested (not assumed) freshness/labeling UI."* Internal FAQ: *"The freshness/labeling UI needs a real usability check before pilot, not just build-and-ship."* Worst-case scenario named explicitly: HR misreads a stale self-reported cell as verified and makes a bad staffing call *because the labeling wasn't unmistakable in practice* — called out as worse than the status quo.

**What's in the PRD instead:** FR-8 sets static design constraints (never color-only, WCAG 2.1 AA, plain-language freshness text) — a good but purely visual/accessibility answer. Nothing in Open Questions, Constraints and Guardrails, Success Metrics, or Cross-Cutting NFRs commits to a **pre-launch usability check/validation step** on the labeling UI specifically. `addendum.md`'s "2 usability" test count refers to the already-completed prototype test plan (observing SM-C1 spreadsheet-reversion and Casey's resume behavior) — not a forward-looking commitment to validate label comprehension before the 7/13 launch.

**Why it matters:** Per the task's explicit check — this PRFAQ item is not reflected anywhere as a requirement or open item. It was named by the PRFAQ's own Verdict as launch-critical, alongside the owner gap (which *did* make it into PRD Open Question 3) and the legal waiver (which *did* make it into Open Question 2). Of the three carried-forward Verdict items, two landed in the PRD and this one did not.

---

## Gap 3 — Content-approval gate reversal is not reconciled against the PRFAQ's explicit customer-facing commitment

**Source:** PRFAQ Customer FAQ states as settled fact: *"A human-approval checkpoint exists before content reaches employees. Content curation is a manual admin step in MVP, not fully automated — a real, ongoing operational cost."* Distillate's "Requirements Signals Surfaced" section: *"Content-curation human-approval gate is a required MVP feature ... and an ongoing operational cost, not a one-time build item — needs a named operational owner, not just a technical checkpoint."* project-context.md's technical-research bullet: ingestion "needs a human-approval checkpoint before content reaches employees, not full automation."

**What's in the PRD instead:** PRD §4.1 flips this: `[ASSUMPTION: no content-approval step in MVP — confirmed this session; content reaches the Employee automatically once matched, without a human QA checkpoint]`, reinforced in §5 Non-Goals and Constraints ("No human-approval gate exists for AI-surfaced content in v1... Accepted risk"). The PRD's own Assumptions Index (§9) only reconciles this against the **prototype's** "✓ Approved" badge ("should not be read as a spec") — it does not acknowledge or explain the reversal from the PRFAQ's explicit customer-facing answer and the distillate's "required MVP feature" framing.

**Why it matters:** This isn't necessarily a wrong call — dropping an unresourced manual gate is defensible — but as written it's an undocumented reversal of a locked-sounding decision rather than an explained one. Unlike Gaps 1–2, this *is* addressed somewhere in the PRD (Constraints, Non-Goals), so it's borderline "deliberate exclusion already baked in" — flagged here because the reconciliation trail only covers the prototype contradiction, not the source-document contradiction, which seems like the more consequential one to explain.

---

## Gap 4 — Post-pilot success path (what "success" unlocks) is dropped, not carried into Open Questions

**Source:** Distillate Open Questions #5: *"Post-pilot success path undecided — expand to other departments vs. ship fast-follows... Should be named before the pilot phase ends."* PRFAQ Internal FAQ: *"Worth naming before the pilot phase ends, not scrambling to answer it afterward."*

**What's in the PRD instead:** PRD's Open Questions (6 items) cover retention period, legal review, named owner, non-video trust gap, HRIS integration, and the root-cause hypothesis — but not this one. It's a minor/deferred item in the source (explicitly "not a launch blocker"), so this is a lower-severity omission than Gaps 1–2, but it was explicitly flagged as something to track rather than let go silent.

---

## Items checked and found adequately reconciled (no gap)

- **Coaching-only privacy boundary** — PRD Constraints explicitly ties it to PRFAQ stress-testing and requires structural (not just UI-copy) enforcement. Matches project-context.md and PRFAQ language closely.
- **No data migration / clean launch 7/13/2026** — reconciled in Constraints and §4/FAQ.
- **Legal/compliance waiver + revisit trigger** — PRD Open Question 2 states the revisit condition (scope expansion, external customers, policy change), matching the distillate's "Action needed" ask.
- **No named post-pilot owner / no committed team-timeline** — PRD Open Question 3, matches PRFAQ's "before Phase 3" deadline framing.
- **Root-cause hypothesis unvalidated** — PRD Open Question 6 + §2.1 assumption tag + reliance on SM-1/SM-2 telemetry; reasonably matches the PRFAQ's "validate via telemetry, not upfront interviews" framing, though the PRD does not restate the distillate's specific ask to pre-commit exact thresholds distinguishing "resigned" vs. "tolerant" — a soft, lower-severity partial gap worth noting but not listed above as a standalone item since SM-1/SM-2 already function as the threshold.
- **Semantic (not exact-tag) content matching** — FR-3 + Assumptions Index, matches project-context.md's 2026-07-08 decision.
- **YouTube provider, polling, Adapter pattern, conditional writes, sendBeacon flush** — all in addendum.md Technical Stack section, matches project-context.md's locked technical decisions.
- **Content ingestion quota → scheduled batch job** — FR-3/FR-4 feature NFR + Constraints, matches project-context.md's "~100 calls/day" finding.
- **Two-role scope (no manager/team-lead)** — §2.2 + Non-Goals + addendum's Rejected Product Alternatives, matches PRFAQ/distillate scope boundaries.
- **Mixed-trust/clearly-labeled positioning, not "fully trustworthy dashboard"** — carried through Vision (§1) and FR-8, matches the PRFAQ's core differentiator language closely.
- **Employee surveillance-sentiment risk** — captured as counter-metric SM-C2, matches the PRFAQ coaching-notes risk about auto-polling reading as monitoring.
- **Week-one technical de-risking spike recommendation** — not present in the PRD, but this is a build-process/engineering recommendation rather than a product requirement; reasonable to treat as out of scope for a PRD and more appropriate for architecture/sprint planning. Noted for completeness, not counted as a gap.

---

## Summary Table

| # | Gap | Source | Severity |
|---|-----|--------|----------|
| 1 | HR manual-override of readiness (MVP, not v2) missing entirely | PRFAQ Customer FAQ + Distillate "Confirmed Product Decisions" | High |
| 2 | Labeling-UI pre-launch usability check not required anywhere | PRFAQ Verdict (1 of 3 carry-forward items) + Internal FAQ | High |
| 3 | Content-approval gate reversal not reconciled against PRFAQ's explicit commitment | PRFAQ Customer FAQ + Distillate "required MVP feature" | Medium |
| 4 | Post-pilot success path not carried into PRD Open Questions | Distillate Open Question #5 | Low |
