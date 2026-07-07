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
- Still-open technical constraint carried into build: self-hosted vs. third-party video embeds — unresolved, and changes what "auto-captured watch %" can technically mean.
