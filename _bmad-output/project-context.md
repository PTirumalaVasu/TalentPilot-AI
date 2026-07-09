---
project_name: 'TalentPilot-AI'
user_name: 'TalentPilot'
date: '2026-07-07'
sections_completed: ['mandatory_rules', 'development_workflow_rules']
existing_patterns_found: 0
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## ⚠️ Mandatory Rule: Project Context Maintenance

**Every time any meaningful work happens on this project, this Project Context file must be updated as part of that work.** This includes, but is not limited to:

- Running any BMAD command or workflow
- Invoking agents or sub-agents
- Performing brainstorming, analysis, reviews, or investigations
- Making implementation decisions
- Creating, modifying, or deleting features
- Refactoring code
- Fixing bugs
- Updating architecture or workflows
- Recording assumptions, trade-offs, risks, blockers, and learnings

This file must always reflect the latest state of the project. **No significant activity — human or AI-driven — is considered complete until this Project Context has been updated to reflect it.** If new work doesn't fit an existing section below, add one rather than skipping the update.

---

## Technology Stack & Versions

_Documented after discovery phase_

## Critical Implementation Rules

_Language, framework, testing, and code quality rules: documented after architecture/code exist — none in this repo yet._

### Development Workflow Rules

**Git/Repository:**
- Branch naming: `feature/<kebab-case-slug>` (e.g., `feature/design-thinking`, `feature/talentpilot-brainstorming`)
- Commits: short imperative-sentence messages; changes land on `main` via PR (merge commits carry a `(#N)` suffix) — avoid direct pushes to `main`
- PR review requirements: not yet established
- Deployment: not applicable yet (no deployable code exists)

**BMAD process conventions:**
- Brainstorming sessions live under `_bmad-output/brainstorming/<slug-with-date>/`
- `.memlog.md` is the append-only, timestamped source of record for a session (every idea/decision/technique tagged by author) — treat it as authoritative over conversational memory
- `brainstorm-intent.md` is the condensed, decisions-only artifact generated from the memlog, meant to feed downstream skills (`bmad-prd`, `bmad-product-brief`, etc.)
- Ad hoc session writeups (e.g., `documentation/PROJECTWORKFLOW.md`) document which skills/agents ran and why, on request — not a BMAD skill itself
- Design Thinking sessions (`bmad-cis-design-thinking`, facilitated by Maya) live at `_bmad-output/design-thinking-<date>.md`, saved incrementally after every checkpoint
- Party-mode memlogs live at `_bmad-output/party-mode/memories/<party>/.memlog.md` (`installed/` = the default all-agents room) — persist across sessions, distilled and re-read on entry, never dumped raw
- On Windows, BMAD's python helper scripts (`resolve_customization.py`, `resolve_party.py`, `memlog.py`) need the `python` launcher (not `python3`) and `PYTHONUTF8=1` when output contains emoji, since `uv` is not installed in this environment

## Product & Design Decisions

- **Talent Pool Management design-thinking session** (`_bmad-output/design-thinking-2026-07-07.md`) covered the full Empathize→Define→Ideate→Prototype→Test→Next-Steps arc for the Excel-replacement platform (see `_bmad-output/brainstorming/brainstorm-talent-pool-management-capabilities-2026-07-07/brainstorm-intent.md` for the underlying MVP scope).
- **Deliberate decision: no pre-build validation sprint / HR admin interviews.** TalentPilot chose to proceed straight to build/refine on the two selected concepts (Trust/Freshness Dashboard; Unified Auto-Capture + Resume) using empathy work already gathered from internal knowledge, rather than gating on real-user interviews first. Validation is deferred to real post-launch usage telemetry (staleness %, needs-attention filter adoption, time-to-readiness-judgment) instead of upfront research — so treat the root-cause hypothesis ("self-reporting, not the spreadsheet, is the real pain") and the "tolerable vs. resigned" question as still-open assumptions, not settled facts, when building on top of this work.
- ~~Still-open technical constraint: self-hosted vs. third-party video embeds~~ — **Resolved 2026-07-07**: third-party embed, provider = **YouTube** (see decision note below).
- **Domain research completed** (`_bmad-output/planning-artifacts/research/domain-corporate-skill-tracking-ai-video-learning-platforms-research-2026-07-07.md`), deliberately trimmed/time-boxed for the 1-week hackathon pitch (regulatory and supply-chain analysis explicitly deferred as non-decision-relevant). Key takeaways: corporate LMS/skill-tech market is large and growing fast (~22% CAGR, ~$18.5B corporate segment in 2026) with high AI-in-HR receptiveness (87% of CHROs); the "chasing spreadsheets" pain is industry-validated, not anecdotal (95% of L&D orgs can't reliably tie learning data to business decisions); the core tech bet (auto-captured video watch %) is proven, off-the-shelf-category tech (video engagement analytics), not a novel research risk; named competitors (iMocha, Gloat, Continu, D2L) solve adjacent problems (assessments, internal mobility, broad LMS analytics) but none targets replacing HR's manual-assignment-and-chasing workflow specifically — that gap is the pitch's positioning wedge.
- **Technical research completed on the video-embed/watch-tracking approach** (`_bmad-output/planning-artifacts/research/technical-third-party-video-embeds-youtubevimeo-with-custom-watch-progress-tracking-research-2026-07-07.md`) — resolves the previously-open "self-hosted vs. third-party video embeds" question down to: **third-party embed (YouTube or Vimeo), provider TBD pending a brand/privacy vs. cost decision** (not a technical blocker). Key implementation decisions to carry forward into architecture/build: use an **Adapter pattern** to normalize YouTube's polling-based `getCurrentTime()` vs. Vimeo's event-driven `timeupdate` into one common interface; persist progress via **conditional writes** (only if incoming timestamp is newer), not naive upsert, to avoid stale writes regressing progress; flush the last known position via `sendBeacon`/`visibilitychange` on tab close. Note: **YouTube's branding cannot be removed** (ToS-violating to hide) — if the dashboard needs to feel fully native/branded, that pushes the provider choice to Vimeo (paid tier for privacy/branding features).
- **Provider decision made: YouTube IFrame API** (2026-07-07). Rationale: no branding-native requirement for the MVP, and free-only budget — so Vimeo's paid-tier advantages (custom branding, stronger privacy) buy nothing here while its cost has no offsetting benefit. Implication for build: use the **polling-based** `getCurrentTime()`/`onStateChange` capture approach (not Vimeo's event-driven `timeupdate`) inside the Adapter layer.
- **Technical research completed on tutorial-to-skill matching** (`_bmad-output/planning-artifacts/research/technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md`) — scope is explicit: recommend tutorials matching skills HR already assigned to an employee; automatic skill-gap inference is explicitly out of scope. Key findings/decisions to carry forward: (1) this is a **retrieval-only** problem, no LLM/generation step needed (not full RAG); (2) **vector search may not even be necessary** — try a plain metadata/tag filter first if HR's skill taxonomy and tutorial tags share vocabulary, add embeddings only if that proves insufficient; (3) if needed, use **`pgvector` inside the existing Postgres DB** (not Pinecone/Weaviate) with `text-embedding-3-small`, queried via **filter-then-rank** (metadata pre-filter on skill tag, then vector similarity ranks within that set); (4) **YouTube's `search.list` quota is ~100 calls/day** (June 2026 policy change) — content discovery must be a scheduled batch job, never a live per-request search; (5) **real, non-technical risk**: external/web-sourced content (YouTube) has no quality assurance and documented "AI slop" contamination — ingestion needs a human-approval checkpoint before content reaches employees, not full automation.
- **Decision made (2026-07-08): exact skill-to-content matching is NOT required.** TalentPilot confirmed loose/approximate matches between a video's content and the employee's HR-assigned skill are acceptable for now. This resolves the research's open "do you even need vector search?" question in favor of **yes — use semantic/vector matching** (`pgvector` + `text-embedding-3-small`), not a plain exact-tag filter, since vector search is specifically what surfaces relevant-but-differently-worded content (e.g., skill "Data Visualization" matching a video tagged "Charting in Excel").
- **PRFAQ stress-test completed** (`_bmad-output/planning-artifacts/prfaq-TalentPilot-AI.md` + distillate, 2026-07-08) — Working Backwards press release, Customer FAQ, and Internal FAQ, run against the product brief and all prior research. Verdict: forged, with two structural cracks flagged for the PRD/architecture pass to inherit as real requirements, not narrative color. Key decisions locked during this process:
  - **Concept confirmed as an internal tool/pilot** (not commercial) — no unit-economics or external-customer framing applies to downstream planning docs.
  - **Root-cause framing locked**: the villain is manual self-reporting/status-chasing, not the spreadsheet format — Excel is where the process happens, not the cause. Positioning language should center "automatic tracking reduces manual reporting," not "replacing spreadsheets."
  - **Privacy policy: auto-captured progress data is coaching-only, never used in performance evaluations** — this must hold in the actual data access/reporting architecture, not just in documentation. Surfaced as a launch-blocking question during the Customer FAQ and resolved by explicit decision.
  - **No data migration at launch** — the dashboard starts clean on 13 July 2026; historical spreadsheet data does not import.
  - **Dashboard trust model is explicitly mixed, not universal**: video progress is auto-verified; everything else (docs/websites) remains self-reported and must be visibly labeled as such rather than blended indistinguishably with verified data. This labeling distinction — not "the whole dashboard is trustworthy" — is the real differentiator, and the Internal FAQ flagged the labeling UI's clarity as a genuine pre-launch risk requiring a usability check, not just a design pass.
  - **Open execution gaps, explicitly accepted as "aspirational for now":** no named owner exists yet for post-pilot maintenance, and no team/timeline commitment exists behind the 5-week build plan — both must be finalized **before the Pilot & Validation phase begins**, not before the 13 July 2026 build start. Treat as still-unresolved if any downstream work assumes a maintainer or team is already in place.
  - **Legal/compliance review of employee video-watch tracking has NOT happened and was explicitly declined as unnecessary for current scope** (internal pilot, coaching-only data use, no external customers) — a consciously accepted risk, not an oversight. Revisit if scope expands (more departments, external customers, or the coaching-only data policy changes).
  - Full detail (rejected framings, adversarial FAQ answers, competitive/build-vs-buy evidence) lives in the PRFAQ and its distillate — read those directly for anything not summarized here rather than re-deriving from this bullet alone.
- **PRD finalized** (`_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md` + `addendum.md`, 2026-07-09) — consolidates the full prior pipeline (Product Brief, Trigger Map, UX Scenarios, prototypes, research, PRFAQ) into 12 FRs across 4 features. Decisions made during PRD authoring that supersede or extend earlier artifacts:
  - **Content-approval/QA gate is explicitly NOT in MVP**, reversing an earlier PRFAQ commitment to a human-approval checkpoint — the prototype's "✓ Approved" badge was a placeholder, not a spec. Revisit if pilot feedback surfaces real content-quality problems.
  - **HR manual-override capability added to MVP as FR-12** (a new "HR Override" provenance-label state, distinct from Verified/Self-reported/Needs Attention) — promotes what feature-scoring had called the "Assessed Live" v2 candidate into v1, per PRFAQ reconciliation. No existing UX scenario or prototype covers this interaction — downstream UX work needs to design it.
  - **No dedicated "Needs Attention" filter control** — despite early feature-scoring naming it a target behavior, the PRD keeps the per-row drill-down (FR-9) + visual flagging (FR-10) model instead. Confirmed deliberately, not an oversight.
  - **FR-7's conditional-write rule is ordered by event timestamp, not by position value** — a correctness fix caught during review; the originally-drafted "never overwrite a further-along position" framing would have incorrectly blocked legitimate mid-session rewinds.
  - **Needs-Attention staleness threshold locked at 7 days** (sourced from the original design-thinking success-metric proposal, not invented during PRD authoring).
  - **Real open gaps surfaced during review, not yet resolved:** authentication/employee-roster provisioning has no FR anywhere; deployment/hosting target remains undecided despite the hard 2026-07-13 launch date; no fallback defined for Content that becomes unavailable after assignment; provenance-label comprehension has never been usability-tested (PRFAQ-flagged risk). All logged as PRD Open Questions — treat as still-open when starting architecture/UX work, not as resolved just because the PRD exists.
- **PRD updated 2026-07-09 (same day) to reconcile with WDS prototyping that had moved ahead of it.** Two confirmed product pivots, both already live in the prototype code with no prior decision record until this update: (1) the Readiness Dashboard's primary at-a-glance signal is now a **Status badge** (Not Started/In Progress/Completed, computed from Watch Progress %) — the Provenance Label (Verified/Self-reported/Needs Attention/HR Override) moved to drill-down only. **Flagged as an unresolved coherence risk** (PRD Open Question 11): a Status badge alone doesn't distinguish Verified from Self-reported data, which risks reintroducing the exact trust-ambiguity problem this product exists to solve — resolve before this goes further. (2) Content Discovery (FR-4) pivoted from a single AI-recommended video per skill to a list of all the Employee's assigned Skills/Content with Total/In Progress/To Start stats.
  - **The prototype's data layer has latent, unbuilt support for one Employee viewing another Employee's assignments** (`getEmployees`/`setSelectedEmployee`, built for cross-scenario demo reuse) — now a hard Non-Goal in the PRD (Open Question 12). Watch that nobody wires this up by accident.
  - **Two prototype regressions were found and are NOT PRD scope changes** — they're bugs to fix in the real build: the dashboard's drill-down is currently unreachable from the grid (the row-level entry button was deleted in an unrelated cleanup commit), and Content Discovery lost its previously-approved loading/error states. See `addendum.md`'s "Known prototype regressions" section.
  - **Process note:** the original PRD-authoring pass missed an entire layer of WDS phase-5 artifacts (`stories/*.md`, `work/*.yaml`, `Logical-View-Map.md` under each `E-Development/*/` folder) because the initial directory scan didn't go deep enough. If reading `_bmad-output/E-Development/` again for any reason, go at least 4 levels deep, not 3.
