# Reconciliation: prd.md + addendum.md vs. Trigger Map + UX Scenarios

Sources checked:
- `_bmad-output/B-Trigger-Map/00-trigger-map.md`
- `_bmad-output/B-Trigger-Map/01-Business-Goals.md`
- `_bmad-output/B-Trigger-Map/02-Rita-the-Referee.md`
- `_bmad-output/B-Trigger-Map/03-Casey-the-Continuer.md`
- `_bmad-output/B-Trigger-Map/05-Key-Insights.md`
- `_bmad-output/B-Trigger-Map/06-Feature-Impact.md`
- `_bmad-output/C-UX-Scenarios/00-ux-scenarios.md`
- `_bmad-output/C-UX-Scenarios/01-ritas-trust-call/01-ritas-trust-call.md`
- `_bmad-output/C-UX-Scenarios/02-caseys-resume-and-watch/02-caseys-resume-and-watch.md`
- `_bmad-output/C-UX-Scenarios/03-ritas-assignment-and-track/03-ritas-assignment-and-track.md`

Scope note: items already deliberately excluded per the PRD's own stated decisions — manager role, content-approval gate ("human-approved" content appears repeatedly in the UX scenario docs; PRD §4.1 explicitly rules this out as a confirmed decision), non-video progress tracking, and "Needs Attention" as a **standalone page** — are NOT flagged below. Those are intentional per PRD §2.2/§4.1/§4.4/§5/§6.2.

Note: a prior reconciliation pass (`reconcile-product-briefs.md`, this same folder) already covers the Product Brief sources and independently found the `sendBeacon` gap (#1 below) from `project-brief.md`. This pass confirms the same gap from a second, independent source set (Trigger Map + UX Scenarios), which strengthens rather than duplicates it.

## Gaps found

### 1. `sendBeacon` and dashboard real-time update mechanism — named technical mechanisms missing from addendum

`05-Key-Insights.md` ("Employee Content & Resume Experience Must") explicitly names the mechanism: "Capture watch-position continuously, including on abrupt tab close (`sendBeacon`), so no session's progress is ever silently lost." `03-Casey-the-Continuer.md`'s answer to Casey's fear #1 repeats it: "Watch-position is captured continuously (with `sendBeacon` on tab close ensuring the position is saved even on an abrupt exit)."

`addendum.md`'s Technical Stack section (the designated home for implementation-how detail) and `prd.md` FR-5 both describe only the *behavior* ("last known position is flushed reliably... not dependent on the next poll interval landing first") without ever naming the API. Since addendum is explicitly scoped to carry forward exactly this kind of concrete implementation fact, this is a retained-but-unnamed gap.

Related and adjacent: `00-ux-scenarios.md`'s "Next Phase" section anticipates resolving "Real-time update architecture (WebSocket, polling, sendBeacon)" in UX Design, but neither `addendum.md` nor `prd.md` states how the dashboard's FR-11 "within 30 seconds" refresh requirement is actually achieved (poll interval vs. WebSocket push). The video-capture side of real-time mechanics is at least behaviorally specified; the dashboard-refresh side has no implementation approach named anywhere.

### 2. "Needs Attention" filter (as a UI control, not a page) is a co-equal Must-Have MVP feature and a named success-metric behavior — PRD has no filter/sort FR at all

This is distinct from the already-intentional "no standalone Needs Attention page" cut — the source material frames the *filter control* (which could live inline on the dashboard, not necessarily a separate page) as one of the six committed MVP features, not an omittable extra:

- `06-Feature-Impact.md` scores "'Needs Attention' Filter + Drill-Down Reasoning" (5 pts) as its own independent line item, explicitly justified: "Why the Provenance-Labeled Dashboard and Needs-Attention Filter are separate line items, not one feature: ... they're independently buildable and testable." It sits in the same Must-Have MVP tier as the Provenance-Labeled Dashboard itself.
- `01-Business-Goals.md` Objective 3 ("Make trust legible, not just present") states its literal success target as: "HR filters to 'Needs Attention' rather than scanning every row out of habit."
- `02-Rita-the-Referee.md` lists, as one of five named "Rita's Trust Becomes Real When She..." success metrics: "Uses the 'Needs Attention' filter as her default readiness-judgment workflow." Her "AFTER" daily-reality narrative states: "Uses the 'Needs Attention' filter as her actual daily workflow, not an occasional afterthought... Spends her attention on genuinely ambiguous cases, not on re-verifying things that were already true."
- `05-Key-Insights.md` lists "Build 'Needs Attention' as a First-Class View, Not an Afterthought" as one of five Primary Development Focus items, and "Surface a 'Needs Attention' filter as a primary, prominent action — not a secondary menu item" as a Dashboard Screen requirement.

`prd.md` FR-10's Out of Scope bullet collapses "filter" and "page" into a single excluded concept ("A separate 'Needs Attention' filter page... deliberately not a standalone view"), and FR-9's consequence goes further, requiring the *opposite* interaction pattern from what the source material treats as the actual success condition: "Drill-down is reachable from every row in one click/tap, not just flagged ones... not just the ones the system already flagged" — i.e., full-grid scanning remains the model, which is precisely the habit Rita's persona doc and Business Goals Objective 3 describe TalentPilot-AI as meant to replace. No FR anywhere in §4.4 provides a filter, sort, or "show only Needs Attention" affordance. Worth a PM decision: either add an FR for an inline dashboard filter/toggle (distinct from a standalone page), or explicitly document the deliberate scope cut and its tension with SM-2/Business-Goals Objective 3.

### 3. Business Goals Objective 3's specific success indicator not carried into PRD's Success Metrics

Following from #2: `01-Business-Goals.md` Objective 3's measurable target — "Presence and usage of provenance labels and the 'Needs Attention' filter in real HR sessions... HR filters to 'Needs Attention' rather than scanning every row out of habit" — is a specific, named behavioral indicator for the "trust legible, not just present" goal. PRD's SM-2 ("HR Admin uses the dashboard as their primary reference for readiness decisions... not the prior spreadsheet") is a coarser proxy that doesn't capture this specific "stops scanning every row, uses filtered attention instead" behavior. If the filter control itself is intentionally cut (per #2), this metric's absence from §7 is consistent and expected; if the filter survives as a PM decision, this metric gap should be closed alongside it.

## Non-gaps (verified present, just compressed or relocated)

- "Resigned, not tolerant" persona characterization — carried into PRD §2.1 with its unconfirmed-inference caveat and Open Question 6 intact.
- Provenance labeling (never color-only, plain-language freshness, drill-down defensibility) — fully present via FR-8/FR-9 and Cross-Cutting NFRs.
- "One signal, two payoffs" / tracking-and-resume-as-one-mechanic framing — explicitly carried into PRD §4.3 description and Feature-Impact's own bundling rationale.
- Casey's three fears (losing place, feeling surveilled, no credit for completed work) — addressed respectively by FR-6/FR-7, the coaching-only guardrail + non-evaluative copy framing (implied, though tone detail itself lives in UX docs by design), and the Needs Attention concept (though see #2 above for the filter-control nuance).
- Semantic/approximate matching over exact-tag filtering — present in PRD FR-3 and Assumptions Index.
- Feature-Impact's Consider-tier (Proxy-Signal Tracking, "Assessed Live" audit flag) and Defer-tier ("Your Week in Learning") — present in PRD §6.2 and Open Question 4.
- Content-approval / "human-approved" language throughout UX scenarios — correctly identified and overridden by PRD as an intentional MVP scope decision (§4.1 assumption, confirmed this session).
- 5-week-pilot / 15–20 employee rows / 90-second staffing call / 2-minute assignment flow — all specific numbers from the scenario docs carried through into UJ-1/UJ-3 and FR consequences.
