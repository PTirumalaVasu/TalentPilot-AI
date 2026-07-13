---
epic: [3, 5]
epic_titles: ['Skill Assignment Flow & Content Review', 'Readiness Dashboard - Status, Provenance, Auto-Update & Override']
date: '2026-07-13'
facilitator: Amelia (Developer)
participants: [Amelia (Developer), Alice (Product Owner), Charlie (Senior Dev), Dana (QA Engineer), Elena (Junior Dev), TalentPilot (Project Lead)]
combined_retrospective: true
previous_retrospective: epic-1-retro-2026-07-10.md
---

# Epic 3 & Epic 5 Retrospective: Skill Assignment Flow & Readiness Dashboard

Run as a single combined session covering both epics, since both were completed back-to-back with Epic 4 in between and share several structural patterns worth evaluating together.

## Epic Summary

**Epic 3 — Skill Assignment Flow & Content Review:** 6/6 stories done (3.1–3.6). Data model + HR-scoping (3.1–3.3), the multi-step assignment modal (3.4, 3 review rounds), assignment creation/toast/highlight (3.5), and cancel-flow orphan-safety (3.6, 2 review rounds).

**Epic 5 — Readiness Dashboard:** 7/7 stories done (5.1–5.6 plus 5.5b). Dashboard grid (5.1), provenance drill-down (5.2), needs-attention staleness (5.3), live auto-update polling (5.4), HR override (5.5), override reversal (5.5b), accessibility pass (5.6, 2 review rounds).

**Quality:** every story in both epics went through at least one full 3-layer adversarial code review (Blind Hunter / Edge Case Hunter / Acceptance Auditor); five stories (3.4, 3.6, 5.5b, 5.6 ×2) got user-requested additional review rounds, each of which found genuinely new, previously-missed issues rather than rubber-stamping the prior round.

**Blockers encountered:** the conftest.py `Base.metadata.drop_all()` cross-file pool-corruption bug (flagged since Story 1.7, still open); the `progress/router.py` double-prefix bug discovered in Story 5.2 (Story 4's watch-tracking endpoints unreachable at their documented URL in the running app — high severity, still open); Docker/Postgres availability gaps.

**Production incidents:** 0 — no production target (local pilot).

## Lesson 1 — WDS Prototype vs. Production Stack: Numbering Collision

The prototype's own internal numbering (`_bmad-output/E-Development/03-Ritas-Assignment-and-Track-Prototype/stories/03.1` through `03.6`) tracks the **assignment modal's own UI steps** (03.1 = Step 1 employee picker, 03.2 = Step 2 skill selection, 03.3 = Step 3 content review, 03.5 = toast/highlight, 03.6 = interaction polish). Epic 3's own story numbers (3-1 through 3-6) track an entirely different decomposition — 3.1–3.3 are backend data-model/seed stories with **no UI at all**, and the modal itself doesn't appear until 3.4. So "Story 3.1" and "prototype 03.1" refer to unrelated work by coincidence of numbering only.

**Verdict: guardrails held, no real confusion or rework resulted.**

- Story 3.1's own story file makes zero references to the prototype at all — correctly, since it's a data-model story with no UI surface. The story-creation step didn't go looking for a UI reference where none was needed.
- Story 3.4 (the actual modal) correctly cites `stories/03.1-03.4.md` "for step-by-step interaction narrative" and explicitly frames the prototype as "interaction/copy/object-ID reference only, not code to port" — never as an authority on scope or acceptance criteria (epics.md kept that role throughout).
- Story 3.6's own creation notes explicitly flag that "WDS prototype's own stories/03.6-interactions-and-polish.md is unrelated (covers [+ New Assignment] wiring + two-modal Escape handling, both already done)" — i.e., the numbering collision was noticed and explicitly called out as a non-match rather than assumed to align.
- Story 3.5 is the one case where the numbers *do* roughly line up in subject (both are about the toast/highlight), but nothing in that story's file treats that alignment as load-bearing — it still cites epics.md as authoritative for exact copy, and independently found the referenced UX doc (03.2) stale on a different point (conflated Status+Provenance grid format).

The pattern that made this safe: every story file's Dev Notes / References section treats the prototype as "interaction reference only, not code to port," with epics.md explicitly winning any conflict — a discipline established as early as Story 3.4 ("epics.md wins" precedent) and reused verbatim through 3.5, 3.6, and into Epic 5. The prototype's *numbering* never had authority to begin with, so its collision with the epic's numbering had nothing to bite into.

**No action item needed here** — this is a case where an existing discipline (cite-but-don't-defer-to-the-prototype) already absorbed a risk the team didn't even have to notice in the moment. Worth stating explicitly so it doesn't get "fixed" by someone trying to make the numbering match, which would be solving a problem that isn't actually causing harm.

## Lesson 2 — Decision-Needed Findings: Documented Well, or Only in Chat?

Two specific HALTs were named for this retro: Story 3.4's duplicate-pair interstitial-vs-banner choice, and Story 3.5's toast-gated-on-refetch-success choice.

**Verdict: both are documented directly in the story files' own Review Findings sections, with the "before" state, the "after" decision, and the reasoning — not just a status-line summary in sprint-status.yaml.**

- Story 3.4 (`3-4-hr-assignment-flow-...md`, Review Findings, first bullet): records that `handleContinueFromStep2` originally skipped the AC5-specified `[View]`/`[Assign Again]` interstitial in favor of a passive warning banner, states the resolved decision inline ("resolved decision: build the literal interstitial"), and specifies exactly what was built instead (a distinct interstitial state with `[Assign Again]` proceeding to Step 3 and `[View]` closing the modal, per the story's own AC5 scoping note about drill-down navigation being Epic 5's territory).
- Story 3.5 (`3-5-assignment-creation-...md`, Review Findings, first bullet): records the same pattern — states the bug (toast/highlight gated on `refetch()` resolving `true`, silently suppressing the toast on a refresh failure even though the Assignment was genuinely created), states the resolved decision inline ("resolved decision: fire the toast unconditionally on POST success"), and describes the actual behavioral split that resulted (toast fires on POST success unconditionally; highlight stays gated on refetch success, since there's no row to highlight if the list didn't load; the refresh-error banner now renders *alongside* the toast, not instead of it).

Someone unfamiliar with this session could open either story file cold and reconstruct both the problem and the reasoning without needing chat history. sprint-status.yaml's own log lines (3-4's and 3-5's code-review entries) additionally carry a one-line summary of each decision, which is sufficient as an index but isn't the primary record — the story files are.

**No action item needed** — the "decision resolved" annotation convention (used consistently across both 3.4 and 3.5, and again later in 5.2, 5.3, 5.5, 5.6) is already doing the job this lesson was checking for. Worth naming as a pattern to keep enforcing rather than something to fix.

## Lesson 3 — Story 5.3's Confirmed Dangling Gap: Still Dangling

Story 5.3 (`5-3-needs-attention-flagging-...`) built `ProgressService.derive_self_reported_provenance()` — correct, unit-tested, but confirmed via full-repo grep at story-creation time to have **no live self-report submission mechanism anywhere in the codebase** to call it from. The story's own review surfaced this as a decision-needed finding, and the user explicitly decided (2026-07-11) to keep it as forward-looking scaffolding per AR-3's single-derivation-authority principle, "may stay uncalled indefinitely until (if ever) a self-report entry mechanism is built."

**Verdict: confirmed still dangling. No later story in Epic 5 (or since) built a self-report submission mechanism.**

- Cross-checked every subsequent Epic 5 story (5.4 auto-update/polling, 5.5 HR override, 5.5b override reversal, 5.6 accessibility) — none of them touch a self-report entry point. 5.4 through 5.6 build on video-progress polling, HR-driven override, and presentation-layer work respectively; none reference `derive_self_reported_provenance` as newly-called.
- `ARCHITECTURE-SPINE.md:248` (cited directly in the deferred-work.md entry) lists "self-reported non-video status entry" under Deferred/Out of Scope — this isn't an oversight the team forgot to close, it's a deliberate MVP non-goal that the team chose to keep the derivation code around for anyway.
- deferred-work.md's own entry for this (`5-3-...` review section) already states the correct next step: "Revisit if/when a future story either builds that entry mechanism or formally decides not to (in which case this code could be removed as truly dead)."

**Action item:** carry this forward explicitly into backlog/Epic 6+ planning rather than letting it sit invisibly — either (a) a future epic builds the self-report entry mechanism and wires this function in for real, or (b) a deliberate decision is made to delete `ProvenanceLabel.SELF_REPORTED`/`derive_self_reported_provenance` as confirmed-dead scaffolding. Don't let it linger a third epic without one of those two outcomes — dead-but-tested code that nobody re-examines is exactly the kind of thing that erodes trust in "if it's in the codebase, it's live."

## Lesson 4 — Story 5.6: No Prototype Equivalent, and That's Fine

Story 5.6 (accessibility & real-time announcements) is explicitly marked in its own story file: *"No WDS prototype equivalent exists for this story (verified: no accessibility/aria story exists anywhere under `_bmad-output/E-Development/`) — do not search for one."* Every other story in Epic 3 and Epic 5 has at least a loosely-corresponding prototype file to reference (even if, per Lesson 1, only as an interaction-copy reference, not an authority). 5.6 is the one exception across both epics.

**Verdict: worth naming as a category, not a gap.** Cross-cutting accessibility passes are typically added after a feature's core interaction model already exists — WDS prototypes model happy-path visual/interaction flows, not the a11y layer laid on top afterward. There's no reason to expect a "browse to a matching prototype file" habit to apply here, and the story correctly didn't waste effort looking for one.

**Action item:** add a note to the create-story workflow's own guidance (or the project-context.md conventions) that accessibility/cross-cutting-verification stories are expected to have *no* prototype equivalent by category, so future story creation doesn't burn time searching for one or treat its absence as a red flag. This is a small process note, not a fix to anything broken.

## Cross-Reference: Open deferred-work.md Items from These Two Epics

Reviewed every deferred-work.md section logged during Epic 3 and Epic 5 code reviews. Grouped by disposition:

**Should be explicitly carried into backlog/next epics (not closed, still real):**

| Item | Logged at | Why still open |
|---|---|---|
| `progress/router.py` double-prefix bug — Story 4's watch-progress POST/GET are unreachable at their documented URL in the running app | Story 5.2 review | High severity, confirmed live via `app.openapi()`; still nobody's assigned story. Should be a Epic-6-or-sooner ticket, not left as a footnote. |
| conftest.py `Base.metadata.drop_all()` cross-file pool corruption / no isolated test DB | First flagged Story 1.7, re-confirmed in nearly every Epic 3/5 story review | Epic 4 retro already logged an action item for this ("before Epic 5 kickoff") — it's now been open across two full epics unaddressed. This is the most-repeated open item in the entire ledger. |
| Dashboard/drill-down transaction/snapshot race (concurrent override + read) | Story 5.1 review, re-confirmed Story 5.2 | Story 5.4's own creation notes explicitly say it does **not** close this item despite superficially looking related (5.4 is client-polling only, never touches `dashboard/service.py`). Still unowned. |
| `test_dashboard.py` / `test_dashboard_router.py` — both broken/stale against the real endpoints since Story 5.1/5.2 | Story 5.2 review | Story 5-1's dedicated dashboard-endpoint test file has had **zero passing coverage since it was built** — a real testing gap masked by Story 5.2's own live-smoke-testing substituting for it. |
| `_DEMO_EMPLOYEE_IDS` import gap in `app.core.seeds` (breaks 2 test files' collection) | Story 5.2 / 5.3 reviews | Confirmed independently in two files now; small fix, still nobody's picked it up. |
| Epic 4 retro's 3 remaining open action items (verified flag semantics doc, DB transaction pattern doc, snapshot-consistency verification) | Epic 4 retro, still `open` in sprint-status action_items | These predate Epic 5 and were meant to inform it; Epic 5 shipped without them ever being formally closed. |

**Correctly left open / low-severity, fine to keep deferred as-is:** the long tail of "unreachable given current call path" items (FK-validation gaps, pagination-at-current-scale items, `formatRole`/`formatStatus` silent-fallback precedents, ARIA-timing nuances untestable in jsdom, Toast message-queueing) — these were each explicitly re-verified as low-risk/not-currently-reachable at the time they were logged, and nothing in Epic 3 or 5's subsequent work has changed that. No action needed; they're doing their job as documented, low-priority ledger entries.

**Action item:** the double-prefix bug and the conftest.py pool-corruption item are both now old enough (2+ epics) and severe enough (one breaks a live feature's real URL, the other has caused diagnosis time loss repeatedly) that they should stop being "whoever touches this file next" items and become explicitly-scheduled work — either their own small story or bundled into whichever Epic 6 story first touches progress/routing or the test suite.

## What Went Well

- **Review rounds kept finding real things, not diminishing returns.** Story 3.4 got 3 rounds; round 2 caught a critical wire-key mismatch that round 1's own headline fix silently never worked against in production (only ever passed against a mocked test with the wrong key). Story 5.6 round 2 caught a real NFR-A2 regression *introduced by round 1's own fix* (0-day staleness suppression left a color-only state at the boundary). This project's practice of user-requested re-reviews earns its keep every time it's used.
- **Discovered gaps were flagged loudly, not silently absorbed** — the Story 5.3 self-report gap, the Story 5.2 double-prefix bug, and the Story 3.5 cross-epic dashboard-placeholder gap were all explicitly called out in the story that found them rather than quietly worked around.
- **The "epics.md wins" precedent held consistently** across both epics whenever a UX doc or prototype disagreed with epics.md's literal text (Story 3.4's approval-badge framing, Story 3.5's refresh-error copy, Story 5.6 round 2's toast checkmark/first-name wording) — a single, well-understood tie-breaker rule prevented repeated re-litigation of the same class of conflict.

## What Slowed Us Down

- **The conftest.py pool-corruption bug has now cost diagnosis time in nearly every story across three epics** without ever being fixed — it's the single most-repeated line item in deferred-work.md. Every story works around it individually (private engines, `git stash` comparisons to prove "not my regression") rather than the root cause being closed once.
- **Dashboard endpoint test coverage silently rotted** — `test_dashboard.py`/`test_dashboard_router.py` both went stale against the real endpoint shape without anyone noticing until Story 5.2's review went looking, and live-smoke-testing had to substitute for automated coverage in the meantime.

## Action Items

| # | Action | Owner | Category | Success Criteria |
|---|---|---|---|---|
| 1 | Schedule a dedicated fix for the conftest.py `drop_all()` / no-isolated-test-DB gap — stop treating it as a per-story workaround | Charlie (senior dev) | Technical debt | A test-DB isolation mechanism (separate schema, transaction-rollback-per-test, or session-scoped fixture) lands as its own change, and no story after it needs a private-engine workaround |
| 2 | Fix the `progress/router.py` double-prefix bug (Story 4's watch-progress endpoints unreachable at documented URL) | Charlie (senior dev) | Bug (high severity) | `GET/POST /api/assignments/{id}/progress` resolve at their documented path in a live `app.openapi()` check, and `test_progress_retrieval_endpoint.py`/`test_position_retrieval.py` can at least collect |
| 3 | Rewrite or delete `test_dashboard.py`/`test_dashboard_router.py` against the real current `/api/dashboard` endpoint shape | Dana (QA) | Test coverage | Both files either pass against real endpoints or are removed; dashboard endpoint has real automated coverage, not just live-smoke substitution |
| 4 | Decide the fate of Story 5.3's `derive_self_reported_provenance()` — build a real caller, or formally mark it dead and remove it | Alice (Product Owner) + Amelia (dev) | Decision | Either a future story wires a self-report entry mechanism to this function, or a story explicitly deletes it with rationale — not left uncalled a third epic running |
| 5 | Add a note to create-story guidance: cross-cutting/accessibility stories are expected to have no WDS prototype equivalent — don't search for one, don't treat absence as a gap | Amelia (dev-story workflow) | Process | Documented in project-context.md or the create-story workflow's own conventions section |

## Epic 6 Preparation

No Epic 6 definition exists yet in the planning artifacts at time of this retro — the epics.md structure implies Epic 5 was the last currently-planned epic. **No blocking preparation for a next epic**, but items 1–4 above should be triaged into whatever backlog exists before further feature epics compound on top of the still-open conftest.py and double-prefix bugs.

## Readiness Assessment

| Area | Status |
|---|---|
| Testing & Quality | ✅ Every story reviewed at least once, several multiple rounds; ⚠️ two dashboard test files (`test_dashboard.py`, `test_dashboard_router.py`) have been stale/broken since Story 5.1/5.2 |
| Deployment | N/A — local-only pilot, no production target |
| Stakeholder Acceptance | ✅ Sole stakeholder (TalentPilot) directly involved throughout |
| Technical Health | ⚠️ Two known, real, open bugs of consequence (progress/router double-prefix; conftest.py pool corruption) carried across multiple epics without being fixed |
| Unresolved Blockers | None blocking a hypothetical next epic, but items 1–2 above should not be allowed to reach a third epic still open |

**Epic 3 and Epic 5 are genuinely done** at the story level — sprint-status.yaml's `epic-3: in-progress` and `epic-5: in-progress` should both be updated to `done` now that this retrospective is complete, per the standard "in-progress → done: manually when all stories reach done" transition rule. This retro found no gaps in story completeness, only carried-forward technical debt that was already correctly logged as deferred rather than silently dropped.

## Closing Notes

Both epics show the same pattern the Epic 1 retro predicted would be worth watching: review processes here consistently earn their keep (re-review rounds keep finding real, previously-missed issues rather than confirming prior work), and decision-needed findings get resolved with a recorded rationale rather than punted wordlessly. The one genuine, un-closed thread carried out of this retro is that two specific technical-debt items (conftest.py isolation, the double-prefix routing bug) have now survived three epics of "whoever touches this file next" without anyone actually being that person — that pattern itself, not the bugs individually, is the thing worth fixing going into whatever comes next.
