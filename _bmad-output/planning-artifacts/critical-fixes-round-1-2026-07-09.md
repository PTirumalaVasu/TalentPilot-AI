---
date: '2026-07-09'
round: '1'
status: 'COMPLETED'
criticalIssuesFixed: 3
nextRoundTier: 'TIER-2-HIGH-PRIORITY'
---

# Critical Fixes Round 1 — TIER 1 Launch Blockers

**Date:** 2026-07-09  
**Scope:** 3 critical launch-blocking issues fixed in `epics.md`  
**Time Required:** ~2 hours implementation  
**Status:** ✅ **COMPLETED** (Acceptance Criteria Updated)

---

## Fixed Issues

### **Issue #2: FR-9 Drill-Down Entry Point Regression** ✅

**Story:** E5.S2 (Provenance Drill-Down Modal)  
**Problem:** Row-level drill-down button was deleted from prototype; only accessible via debug URL param  
**Impact:** HR Admins cannot defend readiness calls; trust mechanism broken  

**Fix Applied:**
- ✅ Added explicit AC: **CRITICAL FIX: Row-Level Entry Point** section
- ✅ Required "[View Details]" button visible on every row
- ✅ Stated button must NOT be a debug URL parameter
- ✅ Added AC stating "always visible and functional on every row"
- ✅ Added "Needs Attention" rendering spec (icon + text, not color-only per WCAG 2.1 AA)
- ✅ Documented all 4 Provenance states with plain-language copy

**New Acceptance Criteria Highlights:**
```
- "[View Details]" button in Actions column on every row
- Opens Provenance Drill-Down modal immediately
- Entry point ALWAYS visible and functional (not debug URL)
- Needs Attention shows: "⚠️ Needs Attention" (icon + text)
- Freshness stated in plain language: "Not updated in 14 days"
```

**Test Cases Added:**
- ✅ Row-level button visibility on grid load
- ✅ Modal opens on button click
- ✅ All 4 Provenance states render correctly
- ✅ No color-only signals (WCAG 2.1 AA)

---

### **Issue #4: FR-14 Identity Hard-Scoping Missing** ✅

**Story:** E1.S3 (Role & Identity Scoping on Every Request)  
**Problem:** Story validated role but didn't spec hard-scoping to prevent Employee cross-access  
**Impact:** Privacy violation; Employee could theoretically see another Employee's data

**Fix Applied:**
- ✅ Added new section: **CRITICAL: Employee Hard-Scoping at Repository Layer (FR-14 Enforcement)**
- ✅ Specified hard-scoping happens at **repository layer**, not service layer
- ✅ Added 4 explicit AC scenarios for cross-employee access attempts
- ✅ Documented `?employee_id=morgan` override rejection (silent, no error)
- ✅ Added SQL injection defense scenario
- ✅ Documented "defense in depth" (scoping at every layer)

**New Acceptance Criteria Highlights:**
```
**Hard-Scoping at Repository Layer:**
- Employee sessions ALWAYS filtered by their own user_id
- Query parameter overrides (e.g., ?employee_id=OTHER) ignored
- Cross-employee access returns only user's own data (silent filtering)
- SQL injection attempts still filtered by WHERE clause

**Test Cases:**
- ✅ Employee casey requests ?employee_id=morgan → returns casey's data only
- ✅ UNION-based SQL injection attempt → still returns casey's data only
- ✅ GET /api/assignments/{other_employee_id} → returns 403 Forbidden
- ✅ Assignment belonging to another employee → 403 not found
```

**Defense in Depth:**
- FastAPI dependency validates role/user_id
- Request context passes identity through stack
- Service layer receives scoped identity
- Repository layer applies WHERE clause (hard-scoped)
- If service tries to override, WHERE still applies

---

### **Issue #5: FR-7 Event-Time Ordering — Atomic Write Underspecified** ✅

**Story:** E4.S5 (Event-Time Ordering: Conditional Write)  
**Problem:** Story described logic but didn't spec atomic SQL; race condition possible under concurrent load  
**Impact:** Watch-progress could regress; core feature broken

**Fix Applied:**
- ✅ Added new section: **Atomic SQL Implementation (CRITICAL)**
- ✅ Specified exact SQL pattern with WHERE clause on event_time
- ✅ Documented that this is a **single round-trip**, not separate SELECT + UPDATE
- ✅ Added 3 detailed scenarios: out-of-order, rewind, concurrent writes
- ✅ Documented race condition prevention
- ✅ Added logging/observability requirements
- ✅ Added 5 explicit test cases (no story done until all pass)

**New Acceptance Criteria Highlights:**
```sql
UPDATE skill_progress 
SET watch_position = %s,
    event_time = %s,
    updated_at = NOW(),
    verified = %s
WHERE assignment_id = %s 
  AND (event_time IS NULL OR event_time < %s)
RETURNING watch_position, event_time, verified;
```

**Scenario Tests:**

1. **Out-of-Order Arrival (Two Tabs):**
   - Tab 1 sends 50% at 14:10:00 → Stored: 50%
   - Tab 2 sends 40% at 14:08:00 (delayed) → Rejected (stale)
   - Result: 50% remains ✅

2. **Legitimate Rewind:**
   - User rewinds to 20% at 14:11:00 (newer timestamp)
   - WHERE succeeds (14:10:00 < 14:11:00)
   - Result: 20% persisted ✅

3. **Concurrent Rapid Writes:**
   - A: 60% @ 14:10:00, B: 50% @ 14:09:00, C: 65% @ 14:10:30
   - Only C succeeds (newest event_time)
   - Result: 65% wins ✅

**Test Requirements (Definition of Done):**
- ✅ Out-of-order writes rejected
- ✅ Rewind within session accepted
- ✅ Concurrent writes: newest wins
- ✅ No race condition (atomic WHERE only)
- ✅ Silent stale-write success (201 Created, not 409)

---

## Summary

| Issue # | Story | Problem | Fix Type | Lines Changed | Test Cases |
|---------|-------|---------|----------|---|---|
| #2 | E5.S2 | Drill-down regression | Spec restore + rendering | +60 | 4 |
| #4 | E1.S3 | Missing hard-scoping | Add explicit ACs | +50 | 4 |
| #5 | E4.S5 | Atomic write unclear | Specify SQL pattern | +80 | 5 |

**Total Lines Added:** ~190  
**Total Test Cases:** 13 (all required before "done")  
**Risk Reduction:** Critical launch blockers → resolved before implementation starts

---

## What Changed in epics.md

**File Location:** `_bmad-output/planning-artifacts/epics.md`  
**Frontmatter Updated:**
- `stepsCompleted`: Added `'critical-issue-resolution-round-1'`
- `blockersResolved`: Added 3 new entries (drill-down-regression-fixed, identity-hard-scoping-added, atomic-write-specified)
- `readinessStatus`: Changed to `'TIER-1-CRITICAL-ISSUES-FIXED'`
- `lastUpdated`: `'2026-07-09-round-2'`
- `criticalFixesApplied`: Added summary of changes

---

## Next Steps

### **TIER 2: High-Priority Issues (4 issues, ~4 hours)**
These should be addressed this week before development sprint begins:

1. **Issue #1: FR-4 List Model Mismatch** — Clarify with UX: is Content Discovery a grouped-Skills list or single Assignment card?
2. **Issue #3: FR-2 "Approved" Badge Contradiction** — Decision: remove all "✓ Approved" badges OR create approval workflow (out of scope)
3. **Issue #7: FR-9 "Needs Attention" Rendering** — Already partially fixed in E5.S2; add explicit Needs Attention icon/copy spec
4. **Issue #8: FR-12 Override Reversal** — Create E5.S5b story with reversal flow + confirmation modal + state reversion

### **TIER 3: Documentation Issues (5 issues)**
These can be handled in dev runbook; not blocking launch:

- Issue #6: NFR-L5 polling interval hardcoded
- Issue #9: OQ9 auth provisioning path (decision note)
- Issue #10: Migration tool lock (Alembic or generic?)
- Issue #11: Resume seek tolerance reworded
- Issue #12: Status badge accessibility icons added
- Issue #13: Embedding model retry logic added

---

## Verification Checklist

Before Phase 4 implementation starts:

- [ ] **E5.S2 drill-down button restored** in prototype (regression fix verified)
- [ ] **E1.S3 hard-scoping test cases pass** (casey cannot see morgan's data)
- [ ] **E4.S5 atomic SQL implemented** (race condition test passes)
- [ ] **All 13 test cases in these 3 stories marked "Ready to Test"** in dev acceptance
- [ ] **TIER 2 issues addressed** (4 stories updated or decisions made)
- [ ] **TIER 3 issues documented** in dev runbook

---

## Handoff to Development

**Ready to Hand Off:**
- ✅ E5.S2 (Provenance Drill-Down) — All ACs clear, drill-down button required, Needs Attention rendering spec'd
- ✅ E1.S3 (Identity Hard-Scoping) — Repository-layer enforcement req'd, cross-employee rejection spec'd
- ✅ E4.S5 (Atomic Write) — SQL pattern locked, race condition tests documented

**Not Yet Ready (Requires TIER 2 Fixes):**
- ⏳ E2.S4 (Content Discovery) — Awaiting UX clarification on list vs. card
- ⏳ E5.S1 (Status Badge) — Awaiting accessibility icon specs
- ⏳ E5.S5b (Override Reversal) — Story not yet written

---

**Document Updated:** 2026-07-09  
**Next Review:** After TIER 2 fixes complete (target: within 48 hours)
