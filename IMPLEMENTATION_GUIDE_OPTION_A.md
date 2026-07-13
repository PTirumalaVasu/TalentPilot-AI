# Implementation Guide: Align UI to Design (Option A)

**Objective:** Refactor dashboard to consolidate provenance badge + timestamp into single cell, matching UX spec  
**Estimated Effort:** 4–6 hours  
**Risk Level:** Low (isolated changes, well-tested)  
**Breaking Changes:** None (internal refactor only)

---

## Overview

This guide provides step-by-step code changes to align the current implementation with the UX design specification. The key change is replacing the split "Status" + "Last Updated" columns with a single consolidated "Provenance Badge" cell.

---

## File Changes Summary

| File | Change | Lines | Effort |
|------|--------|-------|--------|
| `src/components/ProvnanceBadge.tsx` | **NEW** | ~60 | 30 min |
| `src/components/ProvnanceBadge.test.tsx` | **NEW** | ~80 | 45 min |
| `src/features/dashboard/DashboardRow.tsx` | **REFACTOR** | ~30 | 45 min |
| `src/features/dashboard/DashboardRow.test.tsx` | **UPDATE** | ~20 | 30 min |
| `src/features/dashboard/DashboardPage.tsx` | **MINOR** | ~5 | 15 min |
| `src/lib/utils/staleness.ts` | **NO CHANGE** | — | — |

**Total:** ~3–4 hours implementation + 1–2 hours testing = 4–6 hours

---

## Step 1: Create New ProvnanceBadge Component

### File: `src/components/ProvnanceBadge.tsx`

**Purpose:** Display provenance (Verified/Self-reported/Needs Attention) + relative time in a single badge

```tsx
import { formatDistanceToNow } from "date-fns";

type ProvnanceType = "Verified" | "Self-reported" | "Needs Attention";

interface ProvnanceBadgeProps {
  provenance: ProvnanceType;
  lastUpdate: string; // ISO date string
}

export function ProvnanceBadge({ provenance, lastUpdate }: ProvnanceBadgeProps) {
  // Config: color classes + icon for each provenance type
  const provenanceConfig: Record<
    ProvnanceType,
    { bg: string; text: string; icon: string }
  > = {
    Verified: {
      bg: "bg-green-100",
      text: "text-green-800",
      icon: "✓",
    },
    "Self-reported": {
      bg: "bg-gray-100",
      text: "text-gray-700",
      icon: "○",
    },
    "Needs Attention": {
      bg: "bg-amber-100",
      text: "text-amber-800",
      icon: "⚠",
    },
  };

  const config = provenanceConfig[provenance];
  const relativeTime = formatDistanceToNow(new Date(lastUpdate), {
    addSuffix: true,
  });

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-medium text-xs ${config.bg} ${config.text}`}
      role="status"
      aria-live="off"
      aria-label={`${provenance}, last updated ${relativeTime}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>
        {provenance} · {relativeTime}
      </span>
    </span>
  );
}
```

**Key Points:**
- Accepts `provenance` (enum) and `lastUpdate` (ISO string)
- Formats: `"{icon} {provenance} · {relativeTime}"`
- Color mapping: green (Verified), gray (Self-reported), amber (Needs Attention)
- Accessible: aria-label includes both provenance and time
- aria-live="off" prevents double-announcement (dashboard's aria-live handles it)

---

### File: `src/components/ProvnanceBadge.test.tsx`

**Purpose:** Unit test the new component

```tsx
import { render, screen } from "@testing-library/react";
import { ProvnanceBadge } from "./ProvnanceBadge";

describe("ProvnanceBadge", () => {
  // Use a fixed date for consistent snapshots
  const referenceDate = "2026-07-11T14:32:00Z";

  it("renders Verified badge with green background", () => {
    render(
      <ProvnanceBadge provenance="Verified" lastUpdate={referenceDate} />
    );
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-green-100", "text-green-800");
    expect(screen.getByText(/Verified/)).toBeInTheDocument();
  });

  it("renders Self-reported badge with gray background", () => {
    render(
      <ProvnanceBadge
        provenance="Self-reported"
        lastUpdate={referenceDate}
      />
    );
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100", "text-gray-700");
    expect(screen.getByText(/Self-reported/)).toBeInTheDocument();
  });

  it("renders Needs Attention badge with amber background", () => {
    render(
      <ProvnanceBadge
        provenance="Needs Attention"
        lastUpdate={referenceDate}
      />
    );
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-amber-100", "text-amber-800");
    expect(screen.getByText(/Needs Attention/)).toBeInTheDocument();
  });

  it("includes relative time in badge text", () => {
    render(
      <ProvnanceBadge provenance="Verified" lastUpdate={referenceDate} />
    );
    // Should contain both provenance and time
    expect(screen.getByText(/Verified · .* ago/)).toBeInTheDocument();
  });

  it("includes icon with aria-hidden for each provenance type", () => {
    const { rerender } = render(
      <ProvnanceBadge provenance="Verified" lastUpdate={referenceDate} />
    );
    expect(screen.getByText("✓", { selector: "[aria-hidden]" })).toBeInTheDocument();

    rerender(
      <ProvnanceBadge
        provenance="Self-reported"
        lastUpdate={referenceDate}
      />
    );
    expect(screen.getByText("○", { selector: "[aria-hidden]" })).toBeInTheDocument();

    rerender(
      <ProvnanceBadge
        provenance="Needs Attention"
        lastUpdate={referenceDate}
      />
    );
    expect(screen.getByText("⚠", { selector: "[aria-hidden]" })).toBeInTheDocument();
  });

  it("has accessible aria-label combining provenance and time", () => {
    render(
      <ProvnanceBadge provenance="Verified" lastUpdate={referenceDate} />
    );
    const badge = screen.getByRole("status");
    expect(badge).toHaveAttribute("aria-label", expect.stringContaining("Verified"));
    expect(badge).toHaveAttribute("aria-label", expect.stringContaining("last updated"));
  });
});
```

---

## Step 2: Refactor DashboardRow Component

### File: `src/features/dashboard/DashboardRow.tsx`

**Current Implementation:**
```tsx
// Column 3: StatusBadge (workflow status)
<td className="px-4 py-3">
  <StatusBadge
    status={row.status}
    percentage={row.status_percentage}
    employeeName={row.employee_name}
    skillName={row.skill_name}
  />
</td>

// Column 4: Progress bar
<td className="px-4 py-3">
  <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
    <div className="h-full bg-blue-600" style={{ width: `${progressPercent}%` }}></div>
  </div>
</td>

// Column 5: Last Updated (staleness check)
<td className={`px-4 py-3 text-sm ${isStale ? "text-red-700 font-medium" : "text-gray-500"}`}>
  {formatDistanceToNow(new Date(row.last_updated), { addSuffix: true })}
  {isStale && ` (${formatStaleDaysText(staleDays!)})`}
</td>

// Column 6: Actions
<td className="px-4 py-3">
  <button
    onClick={() => onViewDetails(row.assignment_id)}
    aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
    className="text-blue-600 hover:underline text-sm font-medium"
  >
    View Details
  </button>
</td>
```

**New Implementation:**
```tsx
import { formatDistanceToNow } from "date-fns";
import { AssignmentRow } from "../../types/dashboard";
import { ProvnanceBadge } from "../../components/ProvnanceBadge";

interface DashboardRowProps {
  row: AssignmentRow;
  onViewDetails: (assignmentId: string) => void;
}

export function DashboardRow({ row, onViewDetails }: DashboardRowProps) {
  const progressPercent = row.status_percentage || 0;

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      {/* Column 1: Employee */}
      <td className="px-4 py-3 text-gray-900">{row.employee_name}</td>

      {/* Column 2: Skill */}
      <td className="px-4 py-3 text-gray-700">{row.skill_name}</td>

      {/* Column 3: Provenance Badge (CONSOLIDATED — was split into 2 columns) */}
      <td className="px-4 py-3">
        <ProvnanceBadge provenance={row.provenance} lastUpdate={row.last_updated} />
      </td>

      {/* Column 4: Progress Bar */}
      <td className="px-4 py-3">
        <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600"
            style={{ width: `${progressPercent}%` }}
            role="progressbar"
            aria-valuenow={progressPercent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${row.skill_name} progress: ${progressPercent}%`}
          ></div>
        </div>
      </td>

      {/* Column 5: Actions (was column 6, now 5) */}
      <td className="px-4 py-3 text-center">
        <button
          onClick={() => onViewDetails(row.assignment_id)}
          aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
          className="text-gray-400 hover:text-blue-600 transition-colors text-lg"
          title="View details"
        >
          →
        </button>
      </td>
    </tr>
  );
}
```

**Key Changes:**
1. **Removed:** StatusBadge component (workflow status was not part of design)
2. **Removed:** Separate "Last Updated" column
3. **Added:** ProvnanceBadge component in column 3
4. **Simplified:** Action button now just shows "→" arrow
5. **Result:** 5 columns (down from 6)

---

### File: `src/features/dashboard/DashboardRow.test.tsx`

**Update Tests:**

```tsx
import { render, screen } from "@testing-library/react";
import { DashboardRow } from "./DashboardRow";
import { AssignmentRow } from "../../types/dashboard";

describe("DashboardRow", () => {
  const mockAssignment: AssignmentRow = {
    assignment_id: "assign-001",
    employee_name: "Casey Reid",
    skill_name: "Python Basics",
    status: "In Progress",
    status_percentage: 92,
    provenance: "Verified",
    last_updated: "2026-07-11T14:32:00Z",
  };

  it("renders employee name", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    expect(screen.getByText("Casey Reid")).toBeInTheDocument();
  });

  it("renders skill name", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    expect(screen.getByText("Python Basics")).toBeInTheDocument();
  });

  it("renders provenance badge (not workflow status)", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    // Should show Verified, not "In Progress"
    expect(screen.getByText(/Verified/)).toBeInTheDocument();
    expect(screen.queryByText("In Progress")).not.toBeInTheDocument();
  });

  it("renders progress bar with correct percentage", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "92");
    expect(progressBar).toHaveStyle("width: 92%");
  });

  it("renders action button with arrow icon", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    expect(screen.getByText("→")).toBeInTheDocument();
  });

  it("calls onViewDetails when action button is clicked", () => {
    const mockCallback = jest.fn();
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={mockCallback} />
        </tbody>
      </table>
    );
    screen.getByText("→").click();
    expect(mockCallback).toHaveBeenCalledWith("assign-001");
  });

  it("has accessible labels on action button", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={mockAssignment} onViewDetails={() => {}} />
        </tbody>
      </table>
    );
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute(
      "aria-label",
      "View details for Casey Reid Python Basics"
    );
  });
});
```

---

## Step 3: Update DashboardPage Column Headers

### File: `src/features/dashboard/DashboardPage.tsx`

**Current Implementation:**
```tsx
<thead>
  <tr className="border-b border-gray-200 text-left text-gray-500">
    <th className="px-4 py-3 font-medium">Employee</th>
    <th className="px-4 py-3 font-medium">Assigned Skill</th>
    <th className="px-4 py-3 font-medium">Status</th>
    <th className="px-4 py-3 font-medium">Progress</th>
    <th className="px-4 py-3 font-medium">Last Updated</th>
    <th className="px-4 py-3 font-medium">Actions</th>
  </tr>
</thead>
```

**Updated:**
```tsx
<thead>
  <tr className="border-b border-gray-200 text-left text-gray-500">
    <th className="px-4 py-3 font-medium">Employee</th>
    <th className="px-4 py-3 font-medium">Assigned Skill</th>
    <th className="px-4 py-3 font-medium">Status</th>
    <th className="px-4 py-3 font-medium">Progress</th>
    <th className="px-4 py-3 font-medium"></th> {/* Action column, no header */}
  </tr>
</thead>
```

**Change:** Remove "Last Updated" column header (now consolidated into Status column)

---

## Step 4: Update DashboardPage Import

### File: `src/features/dashboard/DashboardPage.tsx`

**Add Import:**
```tsx
import { ProvnanceBadge } from "../../components/ProvnanceBadge";
```

(Actually, this import is not used directly by DashboardPage; it's imported by DashboardRow, so this step may be optional.)

---

## Step 5: Remove Now-Unused Functions

### File: `src/features/dashboard/DashboardRow.tsx`

**Remove:** The following are no longer needed since ProvnanceBadge handles this:
```tsx
// Delete these (now in ProvnanceBadge):
// - staleDaysSince()
// - formatStaleDaysText()
// - isStale check
```

Actually, keep these in place for now—they may be used by ProvenanceDrillDownModal. Only delete if they're truly orphaned.

---

## Testing Checklist

### Unit Tests
- [ ] ProvnanceBadge renders all 3 provenance types (Verified, Self-reported, Needs Attention)
- [ ] ProvnanceBadge colors are correct (green, gray, amber)
- [ ] ProvnanceBadge format includes both icon and timestamp
- [ ] DashboardRow renders ProvnanceBadge (not StatusBadge)
- [ ] DashboardRow has 5 columns (not 6)
- [ ] Action button shows "→" (not "View Details")
- [ ] Progress bar renders correctly

### Integration Tests
- [ ] Dashboard page loads without errors
- [ ] All 4 demo assignments render
- [ ] Each row shows correct provenance (Verified, Self-reported, Needs Attention)
- [ ] Drill-down modal still opens on action button click
- [ ] Polling updates still work
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader announces provenance badge

### Visual Regression
- [ ] Table layout matches design (5 columns, compact)
- [ ] Provenance badges align with color spec
- [ ] Progress bars render at correct width
- [ ] No layout shifts or jank

### Accessibility
- [ ] aria-labels on all interactive elements
- [ ] aria-live region still announces changes
- [ ] Tab order is logical
- [ ] Keyboard shortcuts (Escape to close modal)

---

## Rollback Plan

If issues arise:
1. Revert `src/features/dashboard/DashboardRow.tsx` to use StatusBadge (original)
2. Re-add the "Last Updated" column in DashboardPage
3. Delete `src/components/ProvnanceBadge.tsx` and test file

---

## Success Criteria

✅ **Functional:**
- All rows render correctly
- Drill-down modal opens/closes
- Polling updates work
- No console errors

✅ **Visual:**
- 5 columns (not 6)
- Provenance badge shows "{icon} {Provenance} · {Time}"
- Colors match spec (green/gray/amber)
- Action arrow is visible

✅ **Accessible:**
- Keyboard navigation works
- Screen reader announces provenance badge
- aria-live region captures changes
- All buttons have aria-labels

✅ **Tested:**
- Unit tests pass
- Integration tests pass
- Manual testing confirms visual alignment with design

---

## Estimated Timeline

| Task | Duration |
|------|----------|
| Create ProvnanceBadge.tsx | 30 min |
| Create ProvnanceBadge.test.tsx | 45 min |
| Refactor DashboardRow.tsx | 45 min |
| Update DashboardRow.test.tsx | 30 min |
| Update DashboardPage.tsx headers | 15 min |
| **Implementation Total** | **2.5 hours** |
| Testing (unit + integration + manual) | 1.5–2 hours |
| **Grand Total** | **4–4.5 hours** |

---

## Next Steps

1. **Review** this implementation guide with the team
2. **Create a feature branch:** `feat/provenance-badge-consolidation`
3. **Implement** in this order: ProvnanceBadge → DashboardRow → DashboardPage
4. **Test** using the checklist above
5. **Review** PR against original design spec (Story 01.1.2)
6. **Merge** and validate in staging

---

## Questions?

Refer back to:
- [UI/UX Alignment Analysis](./UI_UX_ALIGNMENT_ANALYSIS.md) — for context and rationale
- [Visual Guide](./ALIGNMENT_VISUAL_GUIDE.md) — for side-by-side comparisons
- Design spec: `_bmad-output/C-UX-Scenarios/01-ritas-trust-call/` — for reference

---

_Implementation Guide Generated: 2026-07-13 | Ready for Dev Team Review_
