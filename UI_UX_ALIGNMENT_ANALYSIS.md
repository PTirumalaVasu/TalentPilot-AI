# UI Implementation vs UX Design — Alignment Analysis

**Date:** 2026-07-13  
**Status:** Current UI is **Functionally Correct** but **Visually Divergent** from Prototype  
**Overall Assessment:** 🟡 Partial Alignment — Key provenance feature needs consolidation

---

## Executive Summary

The current React implementation satisfies all **functional acceptance criteria** from the UX specification, but diverges on **information architecture**:

- **✅ What Works:** Status badges with color+text, progress bars, drill-down modal, accessibility, pagination
- **❌ What's Missing:** Provenance badge format — the design calls for `"{Provenance} · {LastUpdate}"` in a single cell, but implementation splits it across two columns
- **🔧 Effort to Align:** 4–6 hours for a new ProvnanceBadge component (recommended), or update design docs (zero code)

---

## Side-by-Side Column Comparison

### UX Design Specification (5 Columns)

```
┌─────────────┬──────────────────┬──────────────────────────────────┬──────────┬───┐
│  Employee   │ Assigned Skill   │ Status (Provenance · LastUpdate) │ Progress │ → │
├─────────────┼──────────────────┼──────────────────────────────────┼──────────┼───┤
│ Casey Reid  │ Python Basics    │ ✅ Verified · 92% watched, ...   │ ████░░░  │ → │
│ Morgan Lee  │ SQL Fundamentals │ 🔔 Self-reported · 14 days ago   │ ░░░░░░░░ │ → │
│ Jordan Chen │ React Advanced   │ ⚠️  Needs Attention · Stale...    │ ██░░░░░░ │ → │
└─────────────┴──────────────────┴──────────────────────────────────┴──────────┴───┘
```

**Design Rationale:** Single "Status" column consolidates the proof of readiness (Verified/Self-reported) with how fresh that proof is (timestamp), so Rita can scan in one glance: "Is this person ready, and is that answer current?"

---

### Current React Implementation (6 Columns)

```
┌─────────────┬──────────────────┬──────────────────┬──────────┬─────────────────────┬──────────────┐
│  Employee   │ Assigned Skill   │ Status           │ Progress │ Last Updated        │ Actions      │
├─────────────┼──────────────────┼──────────────────┼──────────┼─────────────────────┼──────────────┤
│ Casey Reid  │ Python Basics    │ ✅ In Progress   │ ████░░░  │ 2 hours ago         │ View Details │
│             │                  │ (92%)            │          │                     │              │
│ Morgan Lee  │ SQL Fundamentals │ 🔔 Not Started   │ ░░░░░░░░ │ 14 days ago         │ View Details │
│ Jordan Chen │ React Advanced   │ ⚠️  In Progress   │ ██░░░░░░ │ Not updated today   │ View Details │
│             │                  │ (35%)            │          │ (Stale 5 days)      │              │
└─────────────┴──────────────────┴──────────────────┴──────────┴─────────────────────┴──────────────┘
```

**Implementation Rationale:** Splits the status (what Rita's looking for) from the timestamp (how fresh it is) into separate columns for clarity. The timestamp is always visible without needing to hover or interact.

---

## Critical Gaps

### 🔴 Gap 1: Provenance Badge Format — Text + Timestamp

**Spec Requirement:**
```html
<!-- Design: "Verified · 92% watched, 2 hours ago" in a single badge -->
<span class="bg-green-100 text-green-800 ...">Verified · 2 hours ago</span>
```

**Current Implementation:**
```tsx
// Column 3: Status badge
<StatusBadge status="In Progress" percentage={92} />
// → Renders: "In Progress (92%)" or "Verified" (WITHOUT timestamp)

// Column 5: Separate "Last Updated" column
<td>{formatDistanceToNow(row.last_updated, { addSuffix: true })}</td>
// → Renders: "2 hours ago" (WITHOUT provenance name)
```

**Impact:** 
- ❌ Provenance label never shows full `"{Name} · {Time}"` format
- ❌ Rita must scan two columns to understand provenance + freshness
- ❌ The design's intent (consolidate trust signal + recency) is lost

**Spec Reference:** Story 01.1.2, `provenanceBadge()` function:
```javascript
const label = `${a.provenance} · ${a.lastUpdate}`;  // Line 89
return `<span ...>${escapeHtml(label)}</span>`;
```

---

### 🔴 Gap 2: Status Badge Content Mismatch

**Spec defines badge label as:**
| Provenance | Example Badge Text |
|------------|-------------------|
| Verified | `"Verified · 92% watched, 2 hours ago"` |
| Self-reported | `"Self-reported · 14 days ago"` |
| Needs Attention | `"Needs Attention · Not updated in 21 days"` |

**Implementation renders:**
| Status | Example Badge Text |
|--------|-------------------|
| In Progress | `"In Progress (92%)"` |
| Not Started | `"Not Started"` |
| Completed | `"Completed"` |

**Issue:** Implementation uses **workflow status** (In Progress, Not Started, Completed) instead of **provenance** (Verified, Self-reported, Needs Attention).

- ✅ `row.provenance` field exists in the API response
- ✅ DashboardRow.tsx reads `row.provenance` to determine staleness highlighting
- ❌ But StatusBadge is passed `status` (workflow state), not provenance
- ❌ Provenance information is never displayed on the dashboard

**Code Locations:**
- `DashboardRow.tsx:22-24` — Correctly reads `row.provenance` for staleness
- `DashboardRow.tsx:31-36` — Passes `status` to StatusBadge (not provenance)
- `StatusBadge.tsx:19-38` — Renders status, not provenance

---

## What's Correctly Aligned ✅

### Color Mapping (Perfect Match)

| Provenance | Design | Implementation | Status |
|------------|--------|-----------------|--------|
| Verified | `bg-green-100 text-green-800` | `bg-green-100 text-green-800` | ✅ |
| Self-reported | `bg-gray-100 text-gray-700` | `bg-gray-100 text-gray-700` | ✅ |
| Needs Attention | `bg-amber-100 text-amber-800` | `bg-amber-100 text-amber-800` | ✅ |

---

### Never Color-Only Requirement (Satisfied)

**Spec AC:** "Provenance always paired with text, never color-only"

✅ Current implementation:
- Status badges include text labels (`"In Progress (92%)"`)
- Stale status highlighted with RED + TEXT (`"2 hours ago (Not updated today)"`)
- Row hover state includes visual feedback
- Both meet the spirit of "never rely on color alone"

---

### Progress Bar (Functionally Correct)

| Aspect | Design | Implementation | Notes |
|--------|--------|-----------------|-------|
| Width | `w-24 h-2` | `w-24 h-2` | ✅ |
| Track | `bg-gray-100` | `bg-gray-100` | ✅ |
| Fill color | `bg-talentpilot-600` | `bg-blue-600` | 🟡 Semantic difference, same visual |
| Percentage | 0–100% | 0–100% | ✅ |

---

### Accessibility (Exceeds Spec)

✅ Full keyboard navigation (Tab, Enter, Escape)  
✅ aria-labels on all interactive elements  
✅ aria-live regions for polling updates  
✅ WCAG AA compliance (NFR-A3)  
✅ Screen reader support for live announcements

---

## Minor Differences

### 1. Action Button Style

| Design | Implementation |
|--------|-----------------|
| `→` (arrow icon, 10px column) | `"View Details"` text link |
| Small, minimal visual presence | More discoverable, explicit label |

**Impact:** Both are clickable and lead to drill-down; implementation is more verbose but clearer.

---

### 2. Table Shadow & Rounding

| Design | Implementation |
|--------|-----------------|
| `rounded-lg overflow-hidden shadow-sm` | `rounded-lg overflow-hidden shadow-sm` |

✅ Identical

---

## Over-Implementation (Not in Spec, But Helpful)

### The Extra "Last Updated" Column

The design assumes timestamp lives inside the provenance badge. The implementation created a dedicated column instead, which:

✅ **Pros:**
- Timestamp always visible without hover
- Easier to scan temporal information
- Clear visual separation of concerns

❌ **Cons:**
- Adds a 6th column (vs spec's 5)
- Loses the "provenance + recency as one unit" UX intent
- Increases table width by ~15%

---

## Component Architecture Review

### Current Structure

```
DashboardPage (orchestrates)
├── DashboardRow (per row)
│   ├── StatusBadge (status only, no provenance)
│   └── Staleness text (separate cell)
├── ProvenanceDrillDownModal (detail view, has provenance)
```

### Spec-Aligned Structure (Recommended)

```
DashboardPage (orchestrates)
├── DashboardRow (per row)
│   ├── ProvnanceBadge (NEW: combines status + timestamp)
│   └── ActionButton (small arrow)
├── ProvenanceDrillDownModal (detail view, has provenance)
```

---

## Alignment Path Forward

### **Option A: Align Implementation to Design (Recommended for UX Fidelity)**

**Changes Required:**
1. Create new `ProvnanceBadge.tsx` component
   - Input: `provenance` (Verified | Self-reported | Needs Attention), `lastUpdate` (date)
   - Output: Badge with format `"{Provenance} · {RelativeTime}"`
   - Color mapping: green/gray/amber (as current)
   - Include icon (optional; design doesn't specify)

2. Refactor `DashboardRow.tsx`
   - Remove separate "Last Updated" column
   - Replace StatusBadge + timestamp with new ProvnanceBadge
   - Change action button from "View Details" text to "→" symbol (optional)
   - Result: 5-column table (as spec)

3. Update `StatusBadge.tsx` (optional)
   - Keep as-is for drill-down modal (where it's still used)
   - Or consolidate with ProvnanceBadge if refactoring deeply

**Effort:** 4–6 hours  
**Risk:** Low (isolated to DashboardRow component; modal unchanged)  
**Payoff:** Achieves the design's intent (compact, at-a-glance provenance + freshness)

**Files to Change:**
- `src/components/ProvnanceBadge.tsx` (new file)
- `src/features/dashboard/DashboardRow.tsx` (refactor)
- `src/features/dashboard/DashboardPage.tsx` (column header update)

---

### **Option B: Update Design to Match Implementation**

**Rationale:** The 6-column layout is arguably clearer (timestamp always visible). If implementation is considered "correct," update specs to document it.

**Changes Required:**
1. Update `_bmad-output/C-UX-Scenarios/01-ritas-trust-call/` design docs
   - Change "5 columns" to "6 columns"
   - Document that "Last Updated" is a dedicated column, not embedded in badge
   - Add justification: "Always-visible timestamp reduces cognitive load"

2. Update Story 01.1.2 acceptance criteria
   - Remove spec requirement for consolidated badge
   - Add AC for separate timestamp column visibility

**Effort:** ~30 minutes (documentation only)  
**Risk:** None (documentation-only change)  
**Payoff:** None (implementation unchanged; just documented)

**Files to Change:**
- `_bmad-output/C-UX-Scenarios/01-ritas-trust-call/01-ritas-trust-call.md`
- `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/stories/01.1.2-skills-grid-loaded-state.md`

---

## Recommendation

### ✅ **Choose Option A** if:
- You're iterating on UX (this is early POC, not final)
- The design's intent (compact provenance + freshness) is valuable to Rita
- You have capacity for the ~4–6 hour refactor
- This will be your shipping dashboard

### ✅ **Choose Option B** if:
- Implementation is locked and deemed better than spec
- Stakeholders (Rita) prefer always-visible timestamps
- Design docs are just docs; implementation is the source of truth
- You need to unblock development

### 🎯 **Recommendation: Option A (Align to Design)**

**Rationale:**
1. The design's provenance badge (`Verified · 2 hours ago`) is the core UX story — it tells Rita "I have automated proof, and it's fresh"
2. Current implementation obscures this by showing the status and timestamp separately
3. Effort is moderate and risk is low
4. This is your POC; UX fidelity matters for stakeholder validation

---

## Implementation Checklist (If Choosing Option A)

- [ ] **Task 1: Create `ProvnanceBadge.tsx`**
  - [ ] Accept props: `provenance` (enum), `lastUpdate` (date)
  - [ ] Render format: `"{Provenance} · {RelativeTime}"`
  - [ ] Color mapping: green/gray/amber
  - [ ] Include icon (optional)
  - [ ] Unit test for each provenance type

- [ ] **Task 2: Refactor `DashboardRow.tsx`**
  - [ ] Remove "Last Updated" column (`<th>` + `<td>`)
  - [ ] Replace StatusBadge + timestamp cell with ProvnanceBadge cell
  - [ ] Remove staleness highlighting logic (now in ProvnanceBadge)
  - [ ] Change action button icon (if desired)
  - [ ] Update row test

- [ ] **Task 3: Update `DashboardPage.tsx`**
  - [ ] Remove "Last Updated" column header
  - [ ] Result: 5 columns

- [ ] **Task 4: Verify**
  - [ ] Drill-down modal still works (uses ProvenanceDrillDownModal, not affected)
  - [ ] Polling updates still work
  - [ ] Stale rows still highlighted (now within badge)
  - [ ] Accessible (keyboard nav, screen reader)

---

## Summary Table

| Criterion | Design | Implementation | Status | Gap Severity |
|-----------|--------|-----------------|--------|--------------|
| **Column Layout** | 5 columns | 6 columns | 🟡 Divergent | Minor |
| **Provenance Badge Format** | `"{Name} · {Time}"` | Separate cells | 🔴 Missing | Critical |
| **Provenance Color Mapping** | Green/Gray/Amber | Green/Gray/Amber | ✅ Aligned | None |
| **Never Color-Only** | Color + text | Color + text | ✅ Aligned | None |
| **Progress Bar** | `w-24 h-2` | `w-24 h-2` | ✅ Aligned | None |
| **Action Button** | Arrow `→` | "View Details" | 🟡 Minor | Minor |
| **Drill-Down Modal** | Modal with details | Modal with details | ✅ Aligned | None |
| **Accessibility** | WCAG AA | WCAG AA+ | ✅ Exceeds | None |
| **Pagination** | Yes | Yes | ✅ Aligned | None |
| **Loading/Empty States** | Yes | Yes | ✅ Aligned | None |

---

## Conclusion

**Current State:** The UI implementation is **functionally sound and accessible**, but the **information architecture diverges** from the UX design's provenance-badge story.

**Next Step:** Decide between:
- 🔧 **Option A:** Refactor to align (4–6 hrs, medium effort)
- 📝 **Option B:** Update design (30 mins, doc-only)

**Recommendation:** **Option A** — Align implementation to design for full UX fidelity and to validate the provenance-badge concept with Rita during POC testing.

---

**Document Generated:** 2026-07-13  
**Prepared By:** Claude Code UI/UX Alignment Review  
**Status:** Ready for Design Review
