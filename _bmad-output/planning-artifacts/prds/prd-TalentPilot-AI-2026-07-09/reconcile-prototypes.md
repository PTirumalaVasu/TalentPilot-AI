# Reconciliation: prd.md / addendum.md vs. prototype & delivery source inputs

**Date:** 2026-07-09
**Method:** Read prd.md and addendum.md in full, then diffed against 8 source files (3 PROTOTYPE-ROADMAP.md, DD-001-handoff-log.md, DD-001-poc-hypothesis-flows.yaml, TS-001-poc-hypothesis-flows.yaml, 00-design-log.md, validation-report.md). Deliberate exclusions already documented in the PRD (manager role, content-approval gate, non-video progress tracking, Employee Profile View, "Needs Attention" as standalone page) are excluded from this report per instructions.

---

## Gap 1 — Four of five concrete performance targets are missing from Cross-Cutting NFRs

**Source:** DD-001-handoff-log.md §4, DD-001-poc-hypothesis-flows.yaml `technical_requirements.performance`, TS-001 `performance` (PERF-001..005).

The source specifies five latency targets:
- Dashboard loads in < 2 seconds (PERF-001)
- Content Discovery page + video player load in < 3 seconds (PERF-002)
- Assignment creation reflected on dashboard within 1 second of submission (PERF-003)
- Resume playback begins within 1 second of click, no seek lag (PERF-004)
- Dashboard row updates within 30 seconds of a watch-position change (PERF-005)

PRD's Cross-Cutting NFRs → Latency bullet captures only the last one (the 30s/FR-11 figure). The other four (dashboard load <2s, content+player load <3s, assignment→dashboard <1s, resume-start <1s) do not appear anywhere in prd.md or addendum.md, as a Cross-Cutting NFR or as a Consequence under FR-1, FR-4, FR-6, or FR-8. Note FR-1's own consequence ("Assignment flow ... completes in under 2 minutes") describes total flow time, not the tighter <1s dashboard-reflection target from PERF-003 — these are different claims and only the softer one made it in.

## Gap 2 — Accessibility NFR scope is narrower than source: keyboard nav and screen-reader live-update announcement are absent

**Source:** TS-001 accessibility A11Y-002 ("Full keyboard navigation across all 6 pages" — Tab/Shift-Tab/Enter/Escape only, dropdowns via arrow keys, modals close via Escape) and A11Y-003 ("Screen reader announces dynamic updates" — assignment confirmation toast and real-time dashboard row update must be perceivable to screen-reader users, not just sighted users). Also DD-001-poc-hypothesis-flows.yaml `non_functional`: "All interactive elements keyboard-navigable (grid, dropdowns, modals, video player controls)."

PRD's Cross-Cutting NFRs → Accessibility bullet states only "WCAG 2.1 AA. Provenance Labels are never color-only (FR-8)." Full keyboard operability and screen-reader announcement of dynamic content (the toast, the auto-updating dashboard row from FR-11) are real, source-specified, testable accessibility requirements with no representation as an FR consequence or NFR anywhere in prd.md/addendum.md.

## Gap 3 — Toast confirmation + visually-highlighted new row on assignment creation is an unstated UI mechanism

**Source:** 03-Ritas-Assignment-and-Track-Prototype/PROTOTYPE-ROADMAP.md ("03.2's own spec says ... plus: Toast/Confirmation, New Row Highlight"); 00-design-log.md ("new row appears with toast + highlight"); TS-001 HP-003 ("New row appears immediately, visually highlighted") and ES-006 ("Toast shows: 'Skill assigned, but the dashboard couldn't refresh. [Refresh]'").

FR-1's consequences describe the new Assignment appearing "immediately" and the refresh-failure UI, but never mention that (a) a success case also produces a toast/confirmation, or (b) the new row is visually highlighted to draw Rita's attention. The addendum's copy list captures the refresh-error toast copy but not the happy-path confirmation toast. This is a concrete, source-specified UI state with no FR consequence, and it compounds Gap 2 (the toast needs to be screen-reader announced per A11Y-003).

## Gap 4 — FR-5/FR-6 (video capture/resume) have no stated failure-mode consequences, unlike sibling FRs

**Source:** TS-001 ES-003 ("This video couldn't be loaded. [Try again] · [View alternatives]"), ES-004 ("Couldn't resume this video. [Try again] · [Start over]"), EC-002 ("Nothing in progress right now. [View your assignments]" — empty Continue Watching state).

FR-1 and FR-2 (assignment flow) get explicit testable failure-state consequences (refresh error distinct from save error; assign-without-content path). FR-5 (auto-capture) and FR-6 (resume) do not get an equivalent treatment: nothing in the PRD states what happens when video playback fails to load, when a saved resume position fails to load, or that a fallback "start over" path must always exist so Casey is never blocked. The addendum's "Concrete UI copy" list includes the assignment-flow error copy but omits all three of these video-side copy items. Given the PRD elsewhere treats a wrong resume point as "launch-blocking" (FR-6), the asymmetry — no equivalent bar for what happens on an outright load/resume failure — reads like an oversight rather than a deliberate scope cut.

## Gap 5 — Cancel-mid-flow data-integrity guarantee is unstated

**Source:** TS-001 EC-005 ("Interrupted assignment flow — cancel mid-step" — Rita cancels after selecting employee+skill but before confirming; expected: no assignment record created, dashboard unchanged; success criteria: "No partial/orphaned assignment records exist after a mid-flow cancel").

PRD's Cross-Cutting NFRs → Data integrity bullet covers watch-progress non-regression (FR-7) and assignment-not-lost-on-refresh-failure (FR-1), but says nothing about the guarantee that an abandoned/cancelled assignment flow leaves no partial record. This is a real, testable data-integrity consequence of FR-1 that isn't captured.

---

## Minor / lower-confidence note (not counted above)

- **sendBeacon as the tab-close flush mechanism** is named explicitly in DD-001-handoff-log.md §4, DD-001-poc-hypothesis-flows.yaml (`integrations`), and TS-001 HP-002/ES step ("flushed via sendBeacon on tab close"). Addendum's Technical Stack → Video provider paragraph describes the YouTube IFrame API polling approach (`getCurrentTime()` / `onStateChange`) but never names `sendBeacon` as the mechanism satisfying FR-5's "flushed reliably on tab close" consequence. Since the addendum is explicitly the implementation-how document, this is arguably its gap to close, not the PRD's — flagged as minor/optional.

---

## Confirmed as already reconciled (no gap)

- The prototype's "✓ Approved"/"human-approved content" language (roadmap 02, design-log, TS-001 HP-002) is explicitly called out in the PRD's Assumptions Index (§4.1) as not to be read as a spec — correctly caught.
- YouTube-vs-self-hosted video-embed ambiguity (still "open" per DD-001 complexity section) is resolved in addendum's Technical Stack (YouTube IFrame API, Adapter pattern for future Vimeo swap) — superseding decision, not a gap.
- Data models (`assignments`, `skill_progress` conditional-write, `content_catalog`+embeddings) match 1:1 between DD-001 yaml and addendum.md.
- Deferred UX-spec structural gaps (Page Metadata section, Prev/Next nav links, Object Registry) from validation-report.md are explicitly labeled there as "cosmetic/structural rather than functional" — correctly out of PRD scope.
- Privacy/coaching-only enforcement-at-data-layer requirement is fully reflected in PRD's Constraints and Guardrails section.
