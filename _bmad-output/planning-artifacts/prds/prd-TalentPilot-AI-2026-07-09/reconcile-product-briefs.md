# Reconciliation: prd.md + addendum.md vs. source briefs

Sources checked:
- `_bmad-output/A-Product-Brief/project-brief.md` (2026-07-08, "Complete" brief — the more authoritative/current one)
- `_bmad-output/planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/brief.md` (older draft brief)

Scope note: items already deliberately excluded per the PRD's own stated decisions (manager role, content-approval gate, non-video progress tracking, standalone "Needs Attention" filter page) are NOT flagged below — those are intentional per PRD §2.2/§4.4/§5/§6.2 and addendum's "Rejected Product Alternatives."

## Gaps found

### 1. Tone of Voice section — entirely dropped (project-brief.md, largest single gap)
`project-brief.md` has a full ~45-line "Tone of Voice" section: four named tone attributes (Clear & unambiguous, Calm & matter-of-fact, Honest about uncertainty, Quietly encouraging — employee-facing only), a table of ✅/❌ copy examples (e.g. "Verified · 92% watched, 2 hours ago" vs "✓ Complete"; "Needs a second look" vs "Warning"; "Pick up where you left off — 8 min remaining" vs "Continue"), and explicit Do/Don't guidelines (never color-only, never "In Progress"/"Pending," reserve warmth for employee-facing surfaces only).
Neither `prd.md` nor `addendum.md` contains anything under this heading. The PRD's FR-8 captures the *mechanical* rule ("never color-only," "plain language" freshness) but the voice/register guidance (calm-and-matter-of-fact vs. quietly-encouraging split by audience, and the specific rejected phrasings) is gone. Addendum's "Prototype Implementation Notes" lists four UI copy strings from the prototype, but frames them as "a first-pass source for real copy, not a locked spec" — it does not carry forward the Tone of Voice rationale/attributes at all. This is qualitative texture the PRD's FR format flattened out.

### 2. "Evidence pipeline" strategic framing and the three post-pilot outcomes — dropped
`project-brief.md`'s "Our Unfair Advantage" section states the durable asset is "the evidence pipeline, not first-mover speed," and lays out three explicit post-pilot outcomes if the pilot succeeds (keep evolving standalone / integrate the evidence pipeline into a future LMS / adopt a commercial platform outright) — explicitly framed as resolving the PRFAQ's previously open "post-pilot success path" question.
PRD's Open Question 3 ("No named post-pilot owner...") and "Why Now" section don't carry this forward — the PRD treats post-pilot direction as unresolved, when the source brief actually resolved it into three named options. This is a decision/nuance dropped, not merely deferred.

### 3. `sendBeacon` — named technical mechanism dropped from addendum
`project-brief.md`'s Platform & Device Strategy section names `sendBeacon` explicitly as the mechanism for unload-safe flush ("Native Features: ... `sendBeacon` for unload-safety"; "Video resume/continue-watching works via standard YouTube IFrame API + `sendBeacon` on tab close"). `addendum.md`'s Technical Stack section and `prd.md` FR-5 both describe the *behavior* ("last known position is flushed reliably... not dependent on the next poll interval") but never name the API. Since addendum is explicitly the "implementation-how" document, this is exactly the kind of concrete fact it should retain and doesn't.

### 4. Rejected-alternative rationale (competitive) — partially dropped
`project-brief.md`'s "Competitive Landscape" section gives three explicit alternatives considered and rejected: (1) do nothing/keep the spreadsheet, (2) enforce the spreadsheet harder (rejected — "no amount of policy enforcement fixes an incentive-free chore"), (3) buy an existing LMS/talent-intelligence platform (rejected — "no reviewed vendor does granular auto-polled watch-% as its core trust signal," and "heavyweight implementation commonly costs 20–50% of license again — disproportionate for testing one narrow hypothesis on a 5-week internal pilot").
`addendum.md`'s "Market Landscape Detail" and `prd.md`'s "Why Now" retain the *positioning gap* framing and market stats, but the specific "20–50% of license again" implementation-cost figure and the explicit "enforce harder" rejected-alternative reasoning appear nowhere in the PRD or addendum.

### 5. Employee-side engagement metrics — dropped from Success Metrics
The older `brief.md`'s "Adoption Success" criteria include "Video completion rate and resume-feature usage indicate employees are consuming assigned content without manual logging friction" as a named success signal. `prd.md`'s Success Metrics (SM-1–SM-4, SM-C1–SM-C2) are entirely HR-dashboard/staleness-focused; there is no metric tracking employee-side engagement (completion rate, resume-feature adoption) even though FR-6/UJ-2 make resume a first-class feature. This is a measurable signal from the source material that didn't make it into the PRD's metrics section.

### 6. Minor/supporting drops (lower severity, noted for completeness)
- **79% stat** ("79% of HR teams are adopting skills-based approaches... but lack the tooling") from `brief.md`'s Market Validation section is absent from addendum's "Market Landscape Detail," which otherwise carries forward the 88%/20%/87%/35%/70–80% stats faithfully.
- **Explicit browser support list** — `project-brief.md` states "All modern evergreen browsers (Chrome, Firefox, Edge, Safari) — no legacy browser support required." PRD's Cross-Cutting NFRs only say "responsive web, desktop-first," without naming supported browsers.
- **"1-week hackathon pitch" framing** and "no stakeholder alignment/signoff required (the Alignment & Signoff workflow was explicitly skipped by user choice)" — present in `project-brief.md`'s Strategic Summary/Additional Context as process/governance texture, absent from the PRD (which is a reasonable omission for a capability spec, but worth confirming it's intentional rather than lost).

## Non-gaps (verified present, just relocated)
- "Resigned, not tolerant" characterization — carried into PRD §2.1 with its unconfirmed-inference caveat intact.
- pgvector/embedding/stack decisions, YouTube ToS branding constraint, filter-then-rank matching — all present in addendum.
- Coaching-only / no-performance-eval boundary — present in PRD Constraints and Guardrails.
- 5% staleness / 60-day / 2026-09-11 metric — present in PRD SM-1, matches project-brief.md's locked thresholds.
- Zero-budget, no-migration, 2026-07-13 launch date — present in PRD Constraints.
