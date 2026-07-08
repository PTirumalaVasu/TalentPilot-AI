# Product Concept

**Step:** 7a — Product Concept
**Completed:** 2026-07-08
**Session:** 1

---

## Opening Question

"We've established vision, positioning, and target users. Now I want to get at the structural idea — not features, but the organizing principle that makes this work differently." Proposed a synthesized concept drawn from the design-thinking session rather than asking cold, since the underlying structural idea was already implicit there but never named explicitly as "the concept."

**User's response:** "Yes, that's exactly the founding idea."

---

## Key Exchanges

No corrections needed — confirmed first try. This step named and formalized a structural principle that existed implicitly across the design-thinking session's Top Concepts (#8-#10, #13-#15) but had not previously been stated as a single unifying idea.

---

## Reflection Checkpoint

**Agent Synthesis (Core Structural Idea):**
"One signal, two payoffs" — video watch-position is captured once and powers two things simultaneously: (1) the trust signal HR's dashboard is built on, and (2) the "continue watching" resume experience for employees. Paired with "labeled trust, not uniform trust" on the dashboard side — every cell explicitly tagged verified / self-reported / needs-attention rather than blended into one indistinguishable grid.

**User Response:** Confirmed first try, no corrections.

---

## Documented Concept

**Core Structural Idea:**
A single data pipe (video watch-position/percentage) does double duty: it is simultaneously the auto-captured trust signal for HR's dashboard and the resume/"continue watching" mechanic for employees. This is not two features sharing a database table — it's one signal deliberately designed to serve two audiences at once, so building the tracking infrastructure and building the delight feature are the same act of work.

**Implementation Principle:**
Ship tracking and resume as a single atomic feature/pipeline/UI card, not two bolted-together ones (design-thinking Top Concept #2, ideas #8-#10). On the dashboard side, apply the same discipline to trust: never present a data point without a freshness/provenance label (verified / self-reported / needs-attention) — a blank or explicitly "Unknown" cell beats a guessed one (Top Concept #1, ideas #13-#15).

**Rationale:**
Two failure modes are avoided by this structural choice:
1. Building tracking and resume as separate efforts would double the work and risk them drifting out of sync (e.g., resume position and dashboard-reported progress disagreeing).
2. A uniform-looking dashboard that doesn't distinguish real signal from stale self-report is *worse* than the spreadsheet it replaces — because it looks more trustworthy than it is (this exact failure mode was flagged as the single worst-case outcome in the PRFAQ's Internal FAQ).

**Concrete Example:**
An employee watches a video, closes the tab at 73% through. The same watch-position write that lets them resume exactly at 73% next time they open the app is the same write that updates their row on HR's dashboard as "verified, 73% complete, updated 2 minutes ago." No separate "mark as complete" action, no separate sync step — one event, two consumers.

**Features That Stem From This Concept:**
- Unified Auto-Capture + Resume mechanic (video polling → conditional-write persistence → dashboard read + resume read from the same row)
- Trust/Freshness Dashboard (freshness-coded cells, "Needs Attention" filter, drill-down reasoning) — the labeling half of the same discipline applied to non-video content, which stays explicitly self-reported rather than being visually blended with verified data
