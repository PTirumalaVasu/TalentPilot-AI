# Story HR-Dashboard.13: Inline Content Search + Approval Gate on Skill Creation

**View**: HR Dashboard — Skills tab, replaces the "Add a New Skill" flow built in `HR-Dashboard.10-skills-view.md` and `HR-Dashboard.11-content-discovery-mockup.md`
**Implements**: `_bmad-output/planning-artifacts/epics/epic-automated-content-discovery.md` Stories 2-3 (revised via `/bmad-correct-course`, 2026-09-03), and the corresponding revision to `epic-skill-catalog-management.md` Story 2

---

## ⚠️ This Supersedes the Previous Add-Skill Flow

`HR-Dashboard.11-content-discovery-mockup.md` documented a flow where clicking "+ Add Skill" created the skill immediately, and a simulated search + per-card Approve/Reject panel appeared afterward, asynchronously, in the skills list ("the below cards"). **That flow no longer exists.** Via `/bmad-correct-course`, the user reordered this: search now happens *before* the skill exists, review/approval is inline in the Add-Skill panel itself, and creating the skill requires approving at least one candidate first. `HR-Dashboard.11`'s content is left in place as a historical record (per that file's own note pointing here) rather than deleted, but its described behavior is no longer what the code does.

---

## 📋 What Was Built

**Stateful Add-Skill panel** (`renderAddSkillPanel()`), three states:

1. **`form`** — Name + Description inputs, "Search for Content" button (gated by both API keys being configured, same gate mechanics as before, just moved to this earlier step)
2. **`searching`** — simulated ~900ms delay, labeled SIMULATED
3. **`reviewing`** — all fabricated candidates (2 YouTube + 1 Udemy, same generator as before) shown with Approve/Unapprove/Reject per candidate; "+ Add Skill" stays disabled until at least one is approved, then reads "+ Add Skill (N approved)"; Cancel discards everything and returns to a blank `form` state

**On finalize**: the skill is pushed into `skills` and its first approved candidate is wired into `window.DEMO_DATA.contentMatches[newSkillId]` in the same step — a skill and its content always come into existence together now, never separately.

**Update — visible links (user request)**: each candidate now shows its actual URL beneath the title (a plausible-looking `youtube.com/watch?v=SIMULATED_...` or `udemy.com/course/SIMULATED-...`, generated per candidate, not a placeholder string). The chosen URL is carried through to `contentMatches` on approval too, replacing the earlier generic `#simulated-not-a-real-link` placeholder.

**Update — preview as a popup, not a page navigation (user request)**: clicking a candidate's link no longer shows a toast — it opens `#hr-dashboard-candidate-preview-backdrop`, a modal matching this file's other popup patterns (Provenance Drill-Down, Delete Confirm): title, source/duration, a black placeholder video area (honestly labeled "no real video exists for this fabricated search result" — there's genuinely nothing real to embed, unlike Scenario 02's Content Discovery prototype which embeds real YouTube videos for the real seeded skills), the URL as plain text, and Approve/Reject right in the popup so reviewing and deciding happen in one place. Built with `style.display` from the start (the lesson from the earlier `hidden`+`flex` bug). Approve/Reject in the popup delegate to the same `toggleCandidateApproval()`/`rejectCandidate()` used in the inline list, so there's one source of truth for candidate state, not two.

**Removed**: the per-card discovery UI in `renderSkillsList()` (skill cards are back to plain name+description, matching the original `HR-Dashboard.10` design) and all the functions that drove it (`contentDiscoveryHtml`, `startContentDiscovery`, the old per-skill `approveCandidate`/`rejectCandidate`). `generateSimulatedCandidates` and `sourceBadgeHtml` were kept and reused — the fabricated-data generator itself didn't need to change, only when/where it's invoked and reviewed.

**API-key gate note**: `updateAddSkillGate()` now targets `#hr-dashboard-search-content-button` (only present during the `form` state) instead of the old always-present `#hr-dashboard-add-skill-button`, and is null-safe — it can run while the panel is in `searching`/`reviewing` state (e.g. if someone saves API keys while a different browser tab is mid-review) without erroring on a missing element.

---

## 🚫 Explicitly Out of Scope

- Same simulation caveats as `HR-Dashboard.11`: no real search, no real embeddings/relevance filtering, no real playable URLs.
- Only the **first** approved candidate is wired into `contentMatches` (that object holds one match per skill, matching the existing shape used throughout this prototype) — approving multiple candidates marks all of them "✓ Approved" in the UI and both count toward unlocking "+ Add Skill", but only the first becomes the skill's live content match. The epic's Story 3 notes a real backend would store all approved candidates in `content_catalog`, not just one — flagged there, not solved here.
- No "resume a draft" — Cancel is a hard discard, matching the epic's explicit AC on this point.

---

## ✅ Acceptance Criteria (traced to the epic's revised Stories 2-3)

| # | Criterion | Result |
|---|---|---|
| 1 | Search step gated by API keys, not skill creation itself | ✓ `updateAddSkillGate()` targets the search button |
| 2 | Search runs before the skill exists — nothing pushed to `skills` yet | ✓ `triggerSkillSearch()` only sets draft/candidate state |
| 3 | Candidates shown inline in the Add-Skill panel, not per-card in the list | ✓ `renderAddSkillPanel()`'s `reviewing` branch; `renderSkillsList()` no longer calls any discovery renderer |
| 4 | "+ Add Skill" disabled until ≥1 approved | ✓ `disabled` conditional on `approvedCount === 0` |
| 5 | Finalize creates skill + attaches approved content together | ✓ `finalizeAddSkill()` |
| 6 | Cancel discards everything | ✓ `cancelAddSkillFlow()` resets all three state variables |
| 7 | No duplicate IDs, no `hidden`+`flex` bug, no syntax errors | ✓ full-file scan clean |

### User-Evaluable (Qualitative)

- [ ] Full flow: enter a skill → search → approve one candidate → Add Skill → confirm it appears in the list with content already attached (check via "+ New Assignment" → that skill → Step 3 shows approved content, not "no content found")
- [ ] Confirm "+ Add Skill" genuinely can't be clicked with zero approvals
- [ ] Confirm Cancel from the reviewing state truly discards (name field is blank on return)

---

## 📊 Status

**Status**: ✅ Built, pending user review
**Started / Completed**: 2026-09-03
**Trigger**: `/bmad-correct-course` — bundled Sprint Change Proposal covering the shared-API-key reversion and this flow reordering
