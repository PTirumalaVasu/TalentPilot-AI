# Sprint Change Proposal — 2026-09-03

**Workflow**: `/bmad-correct-course`
**Prepared for**: Vasu
**Mode**: Incremental
**Status**: ✅ Approved by Vasu (2026-09-03) — implementation already complete at time of approval

---

## Addendum (during review): visible candidate links

Refinement requested during proposal review, before final approval: each reviewed candidate in the Add-Skill flow now shows its actual (fabricated but plausible) URL, not just title/source/duration. Rendered as a real `<a>` for visual clarity, but non-navigating (`preventDefault` + a "simulated, not real" toast on click) since the URLs are invented, not live. The chosen candidate's URL now carries through into `contentMatches` on approval, replacing the earlier generic placeholder string. `epic-automated-content-discovery.md` Story 3 AC1 and `HR-Dashboard.13-inline-content-approval.md` updated accordingly; re-verified (no duplicate IDs, no `hidden`+`flex` bug, clean syntax).

---

## Section 1: Issue Summary

Two bundled scope changes to `epic-automated-content-discovery.md`, discovered/decided in the same session that first created it, both affecting the "Skills tab" feature area shared with `epic-skill-catalog-management.md`:

1. **API key storage design over-engineered.** Story 1 originally specified a per-`employee_id` `admin_api_keys` table (added the same day, at explicit request). On reflection, this added complexity — per-admin ownership, per-admin gating, per-admin quota — the product doesn't actually need. Reverted to a single shared/organization-level key per provider.
2. **Content approval sequencing was backwards.** The original design let HR create a skill immediately and review/approve auto-found content afterward, optionally, per-skill in the skills list. The corrected requirement: search runs *before* the skill is saved, all candidates (YouTube + Udemy) are reviewed inline as part of creating the skill, and the skill can only be created once at least one candidate is approved — never a skill with zero vetted content.

No formal PRD exists for this project (confirmed via document discovery — see below); the two Epics under `_bmad-output/planning-artifacts/epics/` serve as the requirements baseline, per the user's explicit choice at the start of this workflow.

---

## Section 2: Impact Analysis

### Epic Impact

- **`epic-automated-content-discovery.md`**: Story 1 rewritten (shared `integration_api_keys` table replaces per-admin `admin_api_keys`). Stories 2 and 3 rewritten for the new sequencing (search-before-create; approve-at-least-one gates creation). Story 4 (Udemy) unaffected in substance, gained a note clarifying the mockup fabricates Udemy candidates regardless of Story 4's real-backend status. Change Log section added at the top of the file recording both revisions with rationale.
- **`epic-skill-catalog-management.md`**: Story 2 ("Add a New Skill") rewritten — its AC "skill appears immediately" was made false by the sequencing change. Story 3 ("Skill Creation Requires Configured API Keys") reworded from personal ("my keys") to organizational ("the organization's keys") ownership language to match Story 1's revision; mechanics (banner, gate) unchanged.

### Story Impact (prototype implementation)

- `HR-Dashboard.11-content-discovery-mockup.md` — superseded, marked as a historical record pointing to its replacement, not deleted.
- `HR-Dashboard.12-api-keys-view.md` — unaffected in UI structure; its underlying real-world design reference is now the shared-key model, not per-admin (documentation-only change, no prototype code change was needed here since the prototype never had per-admin scoping in code).
- `HR-Dashboard.13-inline-content-approval.md` — new story documenting the rebuilt Add-Skill flow.

### Artifact Conflicts

- **PRD**: none exists — n/a.
- **Architecture doc**: none exists — n/a.
- **UI/UX spec**: no formal `*ux*.md` exists; the `design-system.md` and `specs/` page specifications from the Reverse Engineering activity are unaffected (this feature is new scope beyond reverse-engineered production, not a modification to any captured page).
- **Other artifacts**: none — this is a self-contained static HTML prototype with no deployment/CI/IaC/monitoring artifacts in scope.

### Technical Impact

Prototype code (`hr-dashboard.html`) rebuilt: the "Add a New Skill" panel is now a three-state stateful widget (`form` → `searching` → `reviewing`) instead of a single static form. Per-card content-discovery UI and its supporting functions (`contentDiscoveryHtml`, `startContentDiscovery`, old per-skill `approveCandidate`/`rejectCandidate`) removed entirely. New functions: `renderAddSkillPanel`, `triggerSkillSearch`, `toggleCandidateApproval`, `rejectCandidate` (new signature), `cancelAddSkillFlow`, `finalizeAddSkill`. `updateAddSkillGate()` retargeted to the new search button, made null-safe since the panel may be in a different state when it runs. Full verification (duplicate IDs, the `hidden`+`flex` CSS bug pattern found earlier this session, syntax check) re-run clean after the rebuild.

---

## Section 3: Recommended Approach

**Selected: Direct Adjustment (Option 1).** Both changes were addressed by modifying the existing two epics' content in place and rebuilding the affected portion of the prototype — no rollback of other completed work was needed, and no PRD/MVP scope question arises (no PRD exists; both epics are additive scope beyond reverse-engineered production, not commitments with external deadlines).

**Rationale:**
- **Effort**: Medium — one substantial prototype rebuild (the Add-Skill panel), two epic-file rewrites, no other artifacts touched.
- **Risk**: Low — static prototype, single feature area, thoroughly re-verified (structural scans + syntax check) after the rebuild, consistent with every other change made this session.
- **Timeline**: No externally-committed timeline exists for this prototyping effort; no impact.
- **Sustainability**: The new design (shared key, approval-gated creation) is simpler than what it replaces on both counts — less state to reason about, not more — so this change reduces future maintenance burden rather than adding to it.

Option 2 (Rollback) was not viable/needed — nothing needed reverting beyond the specific Story 1 design and the Add-Skill flow's sequencing, both handled as direct edits. Option 3 (MVP Review) doesn't apply — there is no PRD-defined MVP to review.

---

## Section 4: Detailed Change Proposals

### Epics (`_bmad-output/planning-artifacts/epics/`)

**`epic-automated-content-discovery.md`**
- Added a "Change Log" section documenting both revisions with rationale, at the top of the file.
- Story 1: retitled "Configure a Shared API Key Per Integration..."; `admin_api_keys` (per-employee) table replaced with `integration_api_keys` (one row per provider, `UNIQUE(provider)`, `updated_by` for audit); AC rewritten for organization-wide gating instead of per-admin.
- Story 2: retitled "Search for Content When Adding a New Skill (Before the Skill Is Saved)"; AC rewritten so search precedes skill creation and a search failure now blocks creation (previously it didn't).
- Story 3: retitled "Approve At Least One Candidate Before the Skill Is Created"; AC rewritten around the new gate; old AC about the empty-content state marked no-longer-applicable through this path.
- Story 4: unchanged in substance; added a note distinguishing the mockup's fabricated Udemy candidates from this story's still-unresolved real-backend status.
- Out of Scope/Notes: quota note updated (shared quota, not per-admin); prototype-limitation note updated (per-admin login-switching limitation is now moot).

**`epic-skill-catalog-management.md`**
- Story 2 ("Add a New Skill"): AC rewritten to require search + approval before "+ Add Skill" is clickable, referencing the other epic's Stories 2-3 rather than duplicating them.
- Story 3 ("Skill Creation Requires Configured API Keys"): ownership language changed from personal ("my keys") to organizational; mechanics unchanged.
- `implementationStory` frontmatter updated on both files to point at current vs. superseded story files.

### Prototype (`design-artifacts/E-Development/01-Assign-New-Skill-Prototype/`)

- `hr-dashboard.html`: Add-Skill panel rebuilt as a 3-state widget; old per-card discovery UI and functions removed; new functions added (see Technical Impact above); `updateAddSkillGate()` retargeted and made null-safe.
- `stories/HR-Dashboard.11-content-discovery-mockup.md`: marked superseded, left in place as history.
- `stories/HR-Dashboard.13-inline-content-approval.md`: new, documents the current behavior with full traceability to the revised epic ACs.
- `PROTOTYPE-ROADMAP.md`: status table updated (Content Discovery Mockup → superseded; new row for Inline Content Search + Approval Gate).

---

## Section 5: Implementation Handoff

**Scope classification: Minor.** Both changes were fully implemented directly within this session — no backlog reorganization, no PM/Architect escalation needed. This section records the classification per the workflow's own structure, not a pending handoff.

- **Documentation**: Complete — both epics rewritten, implementation story files updated/added, roadmap updated.
- **Prototype code**: Complete — rebuilt, verified (structural scans + syntax check), consistent with this session's established quality bar.
- **Remaining work**: User review of the rebuilt flow in-browser (functional testing of the actual click-through experience) — the one thing not yet done as of this proposal.
- **Success criteria**: User confirms the rebuilt Add-Skill flow behaves as specified (search-before-create, approval gate, shared-key messaging) when exercised in the browser.
