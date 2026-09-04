# Story HR-Dashboard.11: Simulated Content Discovery Mockup

**View**: HR Dashboard — Skills view, extends the Add Skill flow
**Implements**: `_bmad-output/planning-artifacts/epics/epic-automated-content-discovery.md` — visual mockup only, not the real feature

---

## ⚠️ SUPERSEDED by `HR-Dashboard.13-inline-content-approval.md`

Via `/bmad-correct-course` (2026-09-03), the flow this story describes — skill created immediately, discovery/approval shown afterward per-card in the skills list — was replaced with search-before-creation + inline approval-gated skill creation. Kept here as a historical record; the code no longer works this way. See `HR-Dashboard.13` for the current behavior.

---

## ⚠️ Important: This Is a Mockup, Not a Real Feature

A static HTML prototype **cannot** search YouTube/Udemy or sign into external services — API keys can't live in client-side JavaScript, and browsers can't call those search APIs directly (CORS). The user explicitly asked for both an Epic (real backend design) and a mockup (visual demo) — this story is the mockup half. Every "search result" here is fabricated by `generateSimulatedCandidates()`, not fetched from anywhere.

**Visibly labeled in the UI itself**: an amber banner above the Add Skill form, an amber "🔍 SIMULATED: searching..." label during the fake search, and "⚠️ SIMULATED results" on the fake candidate list — so nobody mistakes this for a working integration.

---

## 📋 What Was Built

1. **Add a skill** → `addNewSkill()` now also calls `startContentDiscovery(skillId)`
2. **Simulated search** (900ms delay) → skill card shows a loading indicator, clearly labeled SIMULATED
3. **Simulated results**: 3 fabricated candidates per skill (2 "YouTube", 1 "Udemy" — reflecting the epic's real scoping note that Udemy has zero real backend integration today), each with a source badge, title, and duration
4. **Review**: Approve / Reject per candidate, inline on the skill's card
5. **Approve** writes the candidate into `window.DEMO_DATA.contentMatches[skillId]` — the same object the Assign wizard's Step 3 reads — so approving a simulated result makes that skill show "content found" in the real Assign flow too (closing the demo loop, still fabricated data — `url` is a literal `#simulated-not-a-real-link` placeholder, not a real thumbnail-generating video ID)
6. **Reject** discards the candidate

---

## 🚫 Explicitly Out of Scope (this is the whole point of the mockup vs. real epic split)

- No real API calls, no credentials, no YouTube/Udemy accounts of any kind
- No embedding generation or relevance filtering (the epic's Story 1, AC2) — every candidate is shown, none are algorithmically screened
- Approved "content" has no real, playable URL — the Assign wizard's Step 3 will show it as approved content but the "View on YouTube" link (if clicked) goes nowhere real
- Pre-existing seeded skills (the 5 real ones) never show discovery UI — only skills added through this session's Add Skill form do, since `discoveryStatus` starts undefined for seeded skills

---

## ✅ Acceptance Criteria (structural, self-verified)

| # | Criterion | Result |
|---|---|---|
| 1 | Adding a skill triggers the simulated search automatically | ✓ `addNewSkill()` calls `startContentDiscovery()` |
| 2 | Loading state clearly labeled SIMULATED | ✓ amber text, explicit wording |
| 3 | Candidates clearly labeled SIMULATED, span both fake sources | ✓ 2 YouTube + 1 Udemy per skill |
| 4 | Approve feeds into the same `contentMatches` object the Assign wizard reads | ✓ `approveCandidate()` |
| 5 | Reject removes the candidate without side effects | ✓ `rejectCandidate()` |
| 6 | No `hidden`+`flex` bug, no duplicate IDs, no syntax errors | ✓ full-file scan clean |

### User-Evaluable (Qualitative)

- [ ] Add a new skill, watch the simulated search → review → approve/reject flow
- [ ] Approve one candidate, then open "+ New Assignment" for that skill — confirm Step 3 now shows the approved (fabricated) content instead of "No approved content found"
- [ ] The SIMULATED labeling reads clearly, not easy to mistake for a real feature

---

## 📊 Status

**Status**: ✅ Built, pending user review
**Started / Completed**: 2026-09-03

## 🔄 Update

Following `HR-Dashboard.12-api-keys-view.md`, "+ Add Skill" (and therefore this whole simulated discovery flow) is now gated behind configuring both API keys on the new API Keys screen — matches the epic's Story 1, added after this story was first built. To test this flow: configure both keys first, then add a skill.

## 🔄 Update: removed the top-level "Simulated feature" banner

User asked to remove the standalone amber banner above the Add Skill form ("Simulated feature: adding a skill triggers a mocked YouTube/Udemy search..."). Removed — it was redundant with the per-candidate SIMULATED labels still shown during the discovery flow itself (the "🔍 SIMULATED: searching..." and "⚠️ SIMULATED results" labels on each skill card are unchanged), so the honesty-labeling requirement is still met, just without the extra static banner at the top of the whole tab.
