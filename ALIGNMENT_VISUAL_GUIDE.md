# UI/UX Alignment — Visual Guide

## Quick Reference: What's Different?

### The Core Issue: One Cell vs Two Cells

#### **Design Intent: Provenance + Freshness = One Badge**

```
┌─────────────┬──────────────────────────────────────────────────┬──────────┐
│  Employee   │ Verified · 92% watched, 2 hours ago              │ Progress │
│             │ ✓ Green badge = I trust this signal              │ ████░░░░ │
│             │                                                  │          │
│  Casey Reid │ This tells Rita: "Recent automated proof exists" │          │
└─────────────┴──────────────────────────────────────────────────┴──────────┘

Rita's question: "Is Casey ready, and do I have current proof?"
Answer in one glance: ✓ Verified + "2 hours ago" = YES, current.
```

**Design Quote (Story 01.1.2):**
> "Provenance labels (Verified · 92% / Self-reported · 14 days / Assigned · Awaiting) on the Assignment Dashboard, spots inconsistencies, drills down"

---

#### **Current Implementation: Split Across Two Columns**

```
┌─────────────┬─────────────────────┬──────────────────────────┬──────────┐
│  Employee   │ Status              │ Last Updated             │ Progress │
│             │ In Progress (92%)    │ 2 hours ago              │ ████░░░░ │
│             │ ✓ Green badge       │ Text showing recency     │          │
│             │                     │                          │          │
│  Casey Reid │ WHAT: workflow state│ WHEN: timestamp          │          │
└─────────────┴─────────────────────┴──────────────────────────┴──────────┘

Rita's question: "Is Casey ready?"
Answer: Check column 2 → "In Progress (92%)" ✓ (looks good)
        But is this fresh? Check column 3 → "2 hours ago" ✓
Two separate glances; splits provenance intent.
```

---

## Component Comparison

### StatusBadge (Current)

```tsx
// Current: Renders workflow status, NOT provenance
<StatusBadge status="In Progress" percentage={92} />
// Output: 
//   ▶ In Progress (92%)
//   (Green badge, icon + text)

// Problem: "In Progress" is WHAT, but we need PROOF-TYPE (Verified vs Self-reported)
```

**From code:** `StatusBadge.tsx:19-38` — Config for "Not Started" | "In Progress" | "Completed"

---

### ProvnanceBadge (Spec Intent)

```tsx
// Recommended: Render provenance + timestamp in one badge
<ProvnanceBadge provenance="Verified" lastUpdate={new Date(...)} />
// Output:
//   ✓ Verified · 2 hours ago
//   (Green badge, icon + text + timestamp)

// Result: One cell answers both "Is it trustworthy?" + "Is it current?"
```

---

## Data Flow Diagram

### Current Implementation

```
API Response
├── status: "In Progress"        → StatusBadge renders this
├── status_percentage: 92        → StatusBadge renders this
├── provenance: "Verified"       → DashboardRow uses for staleness check only
└── last_updated: "2024-07-11"   → Separate column renders this

Result: Provenance field is read but never displayed! ❌
```

### Spec-Aligned Flow

```
API Response
├── status: "In Progress"        → (unused by ProvnanceBadge)
├── status_percentage: 92        → Progress bar renders this
├── provenance: "Verified"       → ProvnanceBadge renders this
└── last_updated: "2024-07-11"   → ProvnanceBadge formats & renders this

Result: Provenance field is read AND displayed in one badge ✅
```

---

## Color Legend (What Provenance Badges Communicate)

### Design Defines:

```
🟢 GREEN (bg-green-100):    "Verified" → Automated capture, trustworthy
   "I have machine proof; you can trust this without verifying"
   Example: "✓ Verified · 92% watched, 2 hours ago"

⚫ GRAY (bg-gray-100):       "Self-reported" → Manual entry, honest but not automated
   "I'm taking the person at their word; they updated this"
   Example: "○ Self-reported · Last reported 14 days ago"

🟠 AMBER (bg-amber-100):     "Needs Attention" → Stale, action needed
   "This data is old; I haven't seen proof in a while"
   Example: "⚠ Needs Attention · Not updated in 21 days"
```

**Current Implementation:**
- ✅ Color classes are correct
- ❌ Badge text never says "Verified" / "Self-reported" / "Needs Attention"
- ❌ Status column shows "In Progress", "Not Started", etc. instead

---

## Row Layout Comparison

### Scenario: Casey Reid's skill assignment

#### **Design (Story 01.1.2 Spec)**

```
Employee          Assigned Skill        Status                               Progress    Action
─────────────────────────────────────────────────────────────────────────────────────────────────
Casey Reid        Python Basics         ✓ Verified · 92%, 2 hrs ago         ████░░░░   →

Legend:
- Column 3 shows PROVENANCE BADGE (not workflow status)
- Format: "{Provenance} · {Percentage}, {TimeAgo}"
- One cell communicates BOTH trust (Verified) AND freshness (2 hrs)
```

#### **Current Implementation**

```
Employee          Assigned Skill        Status                Progress         Last Updated          Actions
─────────────────────────────────────────────────────────────────────────────────────────────────────────────
Casey Reid        Python Basics         ▶ In Progress (92%)   ████░░░░         2 hours ago           View Details

Legend:
- Column 3: Workflow status (In Progress/Not Started/Completed)
- Column 5: Separate timestamp column
- Missing: Provenance information (Verified/Self-reported/Needs Attention)
- Result: Rita can't scan provenance + freshness in one glance
```

---

## The Missing Element: Provenance Visibility

### Provenance Data in API Response

```json
{
  "assignment_id": "assign-001",
  "employee_name": "Casey Reid",
  "skill_name": "Python Basics",
  "status": "In Progress",
  "status_percentage": 92,
  "provenance": "Verified",        ← EXISTS in data
  "last_updated": "2026-07-11T14:32:00Z"
}
```

### Provenance Display in Current UI

```tsx
// DashboardRow.tsx reads provenance:
const isStale = row.provenance === "Needs Attention";  // Line 23
const staleDays = isStale ? staleDaysSince(row.last_updated) : null;

// But never DISPLAYS provenance value:
<StatusBadge
  status={row.status}        // "In Progress" ← Used
  percentage={row.status_percentage}  // 92 ← Used
  // row.provenance           ← Read but NOT passed to badge
/>

// Result: User never sees "Verified" / "Self-reported" / "Needs Attention"
```

### Provenance Display in Spec

```tsx
// Design calls for provenanceBadge:
const label = `${a.provenance} · ${a.lastUpdate}`;  // "Verified · 2 hours ago"
return `<span class="bg-green-100 text-green-800">${label}</span>`;

// Result: User sees both provenance AND freshness in one badge
```

---

## Table Structure Comparison

### Design (5 Columns)

```
┌──────────────────────────────────────────────────────────────────┐
│ Employee | Skill | Status (w/ Provenance) | Progress | Action    │
│ ---------|-------|------------------------|----------|-----------|
│ 1        | 2     | 3 (badge + timestamp) | 4        | 5 (arrow) │
└──────────────────────────────────────────────────────────────────┘

Column 3 is the hero: it says everything Rita needs to know.
```

### Current (6 Columns)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Employee | Skill | Status | Progress | Last Updated | Actions           │
│ ---------|-------|--------|----------|--------------|------|
│ 1        | 2     | 3      | 4        | 5            | 6 (text btn)      │
└──────────────────────────────────────────────────────────────────────────┘

Column 3 + 5 together contain what the design puts in column 3 alone.
Requires two columns; adds visual width.
```

---

## Alignment Gap Severity

### 🔴 CRITICAL GAPS

#### Gap 1: Provenance Badge Format

| Spec | Implementation | Impact |
|------|---|---|
| `"{Provenance} · {Time}"` in single badge | Split across two columns | **Rita can't scan provenance in one glance** |
| Example: `"Verified · 2 hrs ago"` | Example: Status="In Progress", Time="2 hrs ago" | **Core UX intent lost** |

#### Gap 2: Provenance Field Unused

| Spec | Implementation | Impact |
|------|---|---|
| Provenance determines badge appearance | Provenance only used for staleness highlight | **Provenance value never displayed** |
| "Verified" → green badge | Status "In Progress" → yellow badge | **Rita sees workflow state, not proof type** |

---

### 🟡 MINOR GAPS

#### Gap 3: Column Count

| Design | Implementation | Impact |
|--------|---|---|
| 5 columns | 6 columns | **Table 15% wider** |
| Compact | More spacing | **Less critical; depends on design intent** |

#### Gap 4: Action Button

| Design | Implementation | Impact |
|--------|---|---|
| `→` (minimal) | "View Details" (explicit) | **Both functional; minor UX difference** |

---

## Decision Matrix: What Should You Do?

| Situation | Recommendation | Effort | Risk |
|-----------|---|---|---|
| **"This is a POC; fidelity matters"** | Align to design (Option A) | 4–6 hrs | Low |
| **"Let's ship this and iterate"** | Update design (Option B) | 30 min | None |
| **"I like the 6-column layout better"** | Document Option B + ship | 30 min | None |
| **"Rita prefers the spec; let's build it"** | Align to design (Option A) | 4–6 hrs | Low |

---

## Implementation Path (If Choosing Option A)

### Step 1: Create ProvnanceBadge.tsx

```tsx
interface ProvnanceBadgeProps {
  provenance: 'Verified' | 'Self-reported' | 'Needs Attention';
  lastUpdate: Date;
}

export function ProvnanceBadge({ provenance, lastUpdate }: ProvnanceBadgeProps) {
  const config = {
    'Verified': { bg: 'bg-green-100', text: 'text-green-800', icon: '✓' },
    'Self-reported': { bg: 'bg-gray-100', text: 'text-gray-700', icon: '○' },
    'Needs Attention': { bg: 'bg-amber-100', text: 'text-amber-800', icon: '⚠' },
  };
  const { bg, text, icon } = config[provenance];
  const relativeTime = formatDistanceToNow(lastUpdate, { addSuffix: true });
  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded font-medium ${bg} ${text}`}>
      <span>{icon}</span>
      <span>{provenance} · {relativeTime}</span>
    </span>
  );
}
```

### Step 2: Update DashboardRow.tsx

```tsx
// Before:
<td>
  <StatusBadge status={row.status} percentage={row.status_percentage} />
</td>
<td>
  {formatDistanceToNow(...)}
  {isStale && ` (${formatStaleDaysText(...)})`}
</td>

// After:
<td>
  <ProvnanceBadge provenance={row.provenance} lastUpdate={row.last_updated} />
</td>

// Result: One column (3) instead of two (3 + 5)
```

### Step 3: Remove "Last Updated" Column Header

```tsx
// Before:
<th className="px-4 py-3 font-medium">Status</th>
<th className="px-4 py-3 font-medium">Progress</th>
<th className="px-4 py-3 font-medium">Last Updated</th>  // ← Remove
<th className="px-4 py-3 font-medium">Actions</th>

// After:
<th className="px-4 py-3 font-medium">Status</th>
<th className="px-4 py-3 font-medium">Progress</th>
<th className="px-4 py-3 font-medium">Actions</th>  // ← Result: 5 columns
```

---

## Testing Checklist (Option A)

- [ ] ProvnanceBadge renders "Verified · 2 hours ago" format
- [ ] All three provenance types display (Verified, Self-reported, Needs Attention)
- [ ] Colors are correct (green, gray, amber)
- [ ] Icons display (✓, ○, ⚠)
- [ ] "Last Updated" column is removed
- [ ] Table is now 5 columns (not 6)
- [ ] Action button/link still works
- [ ] Drill-down modal still opens on click
- [ ] Polling updates still trigger (if enabled)
- [ ] Keyboard navigation works
- [ ] Screen reader announces provenance badge correctly

---

## Summary

| Aspect | Current | Design | Recommendation |
|--------|---------|--------|---|
| **Provenance Visible** | ❌ No | ✅ Yes | **Fix: Create ProvnanceBadge** |
| **Format** | Status + Time (2 cells) | Provenance + Time (1 cell) | **Fix: Consolidate** |
| **Column Count** | 6 | 5 | **Minor; consolidate with above** |
| **Color Mapping** | ✅ Correct | ✅ Correct | **OK** |
| **Never Color-Only** | ✅ Met | ✅ Met | **OK** |
| **Accessibility** | ✅ Excellent | ✅ Excellent | **OK** |

**Next Step:** Review this guide with stakeholders (Rita, design team), decide on Option A or B, and proceed.

---

_Document Generated: 2026-07-13 | Prepared for UX/Dev Alignment Review_
