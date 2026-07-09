# Skills Dashboard Comparison: 01.1 vs 03

## Overview

Both pages display skill assignments in a table format, but they serve different purposes and include different features:

- **01.1-Skills-Dashboard.html** (Scenario 01 - Ritas's Trust Call)
  - Focus: Provenance verification and staffing decisions
  - Rita's perspective on trust/reliability of assignments
  - Modal: Provenance drill-down

- **03-Skills-Dashboard.html** (Scenario 03 - Rita's Assignment & Track)
  - Focus: Assignment workflow and progress tracking
  - Rita's perspective on managing skill assignments
  - Modals: Provenance drill-down + Assignment flow + Toast notifications

---

## Side-by-Side Comparison

### File Size
| Aspect | 01.1 | 03 |
|--------|------|-----|
| Total Lines | 413 | 674 |
| Difference | - | +261 lines (65% more) |

### Purpose & Focus

| Aspect | 01.1 | 03 |
|--------|------|-----|
| **Primary Goal** | View & analyze assignments with provenance data | Create new assignments & track progress |
| **User Action** | Review, verify, drill-down | Assign, track, monitor |
| **Key Feature** | Provenance verification modal | Assignment creation wizard + Toast |

---

## Feature Comparison

### 1. **Modal/Dialog Features**

#### 01.1-Skills-Dashboard.html
```
✅ Provenance Drill-Down Modal (01.2)
   - Shows detailed provenance information
   - Displays raw signal data
   - Provides explanation of verification status
   - Modal ID: assignment-details-modal
```

#### 03-Skills-Dashboard.html
```
✅ Provenance Drill-Down Modal (01.2) - SAME AS 01.1
   - Identical drill-down functionality
   - Same modal structure and logic

✅ Skill Assignment Flow Modal (03.1) - NEW
   - Step 1: Select employee (dropdown)
   - Step 2: Select skill (dropdown)
   - Step 3: Review content recommendation
   - Multi-step wizard for new assignments
   - Modal ID: skill-assignment-flow-modal

✅ Assignment Confirmation Toast (03.2) - NEW
   - Success notification after assignment
   - Fixed bottom-center positioning
   - Auto-dismiss behavior
   - Toast ID: assignment-confirmation-toast
```

### 2. **Data Display**

#### 01.1-Skills-Dashboard.html
```
Table Display:
  Columns:
    1. Employee
    2. Assigned Skill
    3. Status (Provenance badge)
    4. Progress (Progress bar)
    5. Action button (→)
  
  Functionality:
    - Click → button to open drill-down modal
    - View provenance details
    - See raw signal data
```

#### 03-Skills-Dashboard.html
```
Table Display:
  SAME AS 01.1 - Identical table structure
  
  Additional Features:
    - "+ New Assignment" button at top
    - Toast notification system
    - New modal for assignment creation
    - Same drill-down as 01.1
```

### 3. **Toolbar/Controls**

#### 01.1-Skills-Dashboard.html
```
Simple toolbar:
  [+ New Assignment] (button only, no action)
```

#### 03-Skills-Dashboard.html
```
Same toolbar as 01.1:
  [+ New Assignment] (button, opens assignment modal)
  
  Addition:
    - Button now functional
    - Triggers skill-assignment-flow-modal
    - 3-step assignment workflow
```

---

## HTML Structure Breakdown

### 01.1 HTML Elements
```
Header:
  - Navigation
  - User menu

Main Content:
  - Title & Summary
  - Table (assignments)
  - Loading skeleton
  - Empty state
  - Error state
  - Pagination controls
  - Version info

Modals:
  - assignment-details-modal (Provenance drill-down)

Scripts:
  - 4 shared scripts
  - Page-specific script (main functionality)
```

### 03 HTML Elements
```
Header:
  - Navigation (Same as 01.1)
  - User menu (Same as 01.1)

Main Content:
  - Title & Summary (Same as 01.1)
  - Table (Same as 01.1)
  - Loading skeleton (Same as 01.1)
  - Empty state (Same as 01.1)
  - Error state (Same as 01.1)
  - Pagination controls (Same as 01.1)
  - Version info (Same as 01.1)

Modals:
  - assignment-details-modal (SAME - Provenance drill-down)
  - skill-assignment-flow-modal (NEW - 3-step assignment wizard)
  - assignment-confirmation-toast (NEW - Success notification)

Scripts:
  - 4 shared scripts (Same as 01.1)
  - Page-specific script (Extended functionality)
```

---

## JavaScript Functionality Comparison

### 01.1 Functions

```javascript
Core Functions:
  - loadDashboard()           // Load and render assignments
  - rowHtml(a)               // Generate table row HTML
  - provenanceBadge(a)       // Create status badge
  - progressBar(percent)      // Create progress bar
  - openDrillDown()          // Open provenance modal
  - closeDrillDown()         // Close modal
  - setGridState()           // Toggle grid states
  - setModalState()          // Toggle modal states
  - renderRawSignal(a)       // Format raw data
  - renderExplanation(a)     // Format explanation text

Features:
  - View assignments
  - Drill into provenance details
  - See raw signal data
  - Verification status display
```

### 03 Functions

```javascript
Core Functions (SAME AS 01.1):
  - loadDashboard()           // SAME
  - rowHtml(a)               // SAME
  - provenanceBadge(a)       // SAME
  - progressBar(percent)      // SAME
  - openDrillDown()          // SAME
  - closeDrillDown()         // SAME
  - setGridState()           // SAME
  - setModalState()          // SAME
  - renderRawSignal(a)       // SAME
  - renderExplanation(a)     // SAME

NEW Functions:
  - openAssignmentFlow()      // Open assignment modal
  - closeAssignmentFlow()     // Close modal
  - goToStep(n)              // Navigate between steps
  - onEmployeeSelected()      // Handle employee selection
  - onSkillSelected()         // Handle skill selection
  - handleAssign()           // Create new assignment
  - handleViewContent()      // Open video link
  - handleChangeContent()    // Browse content options
  - showConfirmationToast()  // Show success message
  - setAssignmentFlowState() // Toggle flow states
  - setModalState() for flow // Additional state mgmt

Additional Features:
  - Create new assignments (3-step flow)
  - Employee selection
  - Skill selection
  - Content review
  - Assignment confirmation
  - Toast notifications
```

---

## Data Model Comparison

### Demo Data Structure

Both use similar data structure, but 03 has additional features:

#### 01.1 Demo Data
```javascript
employees: [...]
skills: [...]
content_catalog: [...]
assignments: [
  { 
    id, employeeId, skillId, contentId,
    status, provenance, watchPercent,
    lastUpdate, assignedDate
  }
]
```

#### 03 Demo Data
```javascript
// SAME STRUCTURE as 01.1, PLUS:

// Same as 01.1 for compatibility
employees: [...]
skills: [...]
content_catalog: [...]
assignments: [...]

// Extended with more assignment data for new features
// Comments and provenance tracking expanded
```

---

## Scenario Purpose

### Scenario 01.1 (01.1-Skills-Dashboard.html)
**Title:** Rita's Trust Call Prototype

**User Story:**
- Rita reviews all skill assignments
- Rita checks provenance (verified/self-reported)
- Rita drills down for details
- Rita makes staffing/readiness decisions based on trust

**Key Actions:**
1. View assignments table
2. Check provenance badges
3. Click → to drill down
4. Review raw signal data
5. Make trust-based decisions

### Scenario 03 (03-Skills-Dashboard.html)
**Title:** Rita's Assignment & Track Prototype

**User Story:**
- Rita views current assignments (same as 01.1)
- Rita can create new assignments (3-step flow)
- Rita gets confirmation feedback
- Rita tracks assignment progress

**Key Actions:**
1. View assignments table (same as 01.1)
2. Click "+ New Assignment" button
3. Step 1: Select employee
4. Step 2: Select skill
5. Step 3: Review content
6. Confirm assignment
7. See success toast
8. (Optional) Drill into provenance (same as 01.1)

---

## Modals Comparison

### 01.1 Modals
| Modal | Purpose | Steps | Features |
|-------|---------|-------|----------|
| Provenance Drill-Down | View assignment details | Single | Badge, raw data, explanation |

### 03 Modals
| Modal | Purpose | Steps | Features |
|-------|---------|-------|----------|
| Provenance Drill-Down | View assignment details | Single | Badge, raw data, explanation (SAME) |
| Skill Assignment Flow | Create new assignment | 3 | Employee select, skill select, content review |
| Confirmation Toast | Show success | 1 | Auto-dismiss notification |

---

## UI/UX Differences

### 01.1 UX
```
User sees:
  - Assignment table
  - Provenance status for each
  - Can click for details
  - Can filter by provenance
  - Focus: TRUST & VERIFICATION
```

### 03 UX
```
User sees:
  - Assignment table (same as 01.1)
  - "+ New Assignment" button (NEW)
  - Can click for details (same as 01.1)
  - Can create new assignment (NEW)
  - Gets success feedback (NEW)
  - Focus: MANAGEMENT & TRACKING
```

---

## Summary Table

| Feature | 01.1 | 03 | Notes |
|---------|------|-----|-------|
| **View Assignments** | ✅ | ✅ | Identical table |
| **Provenance Badge** | ✅ | ✅ | Same badge display |
| **Progress Bar** | ✅ | ✅ | Same progress display |
| **Drill-Down Modal** | ✅ | ✅ | Identical functionality |
| **New Assignment** | ❌ | ✅ | Only in 03 |
| **Assignment Wizard** | ❌ | ✅ | 3-step flow in 03 |
| **Employee Select** | ❌ | ✅ | In wizard (03 only) |
| **Skill Select** | ❌ | ✅ | In wizard (03 only) |
| **Content Review** | ❌ | ✅ | In wizard (03 only) |
| **Toast Notification** | ❌ | ✅ | Success feedback (03 only) |
| **Pagination** | ✅ | ✅ | Same controls |
| **Line Count** | 413 | 674 | +261 lines in 03 |

---

## Code Reusability

### Shared Between Both
```
✅ Table rendering logic
✅ Provenance badge styling
✅ Progress bar rendering
✅ Drill-down modal logic
✅ Grid state management
✅ Data loading from API
✅ HTML/CSS structure (base)
```

### Unique to 01.1
```
- None (everything in 01.1 also exists in 03)
```

### Unique to 03
```
✅ Assignment wizard (3-step flow)
✅ Employee selection logic
✅ Skill selection logic
✅ Content review logic
✅ Assignment creation logic
✅ Toast notification system
✅ Additional state management
```

---

## Why Two Separate Files?

### Documentation Notes (from file headers):

**01.1:**
```
Title: 01.1 Skills Dashboard
Purpose: Rita scans provenance-labeled assignments and drills into
         raw signal data to make a staffing-readiness call.
```

**03:**
```
Title: 01.1 Skills Dashboard (+ 01.2 Provenance Drill-Down modal)
Note: This file is a duplicated starting point from Scenario 01,
      extended here with the real Skill Assignment Flow modal (03.1)
      and toast/new-row-highlight behavior (03.2).
```

### Reason for Duplication:

From the PROTOTYPE-ROADMAP.md comment:
> "Important: This Reuses Scenario 01's Dashboard"
> Duplication was chosen over editing the Scenario 01 file directly
> to keep each scenario independent and avoid breaking changes

---

## When to Use Each

### Use 01.1-Skills-Dashboard.html when:
- Focusing on trust and verification
- Analyzing provenance data
- Making staffing decisions
- Reviewing assignment reliability

### Use 03-Skills-Dashboard.html when:
- Managing active assignments
- Creating new assignments
- Tracking progress
- Providing feedback (toasts)
- Full assignment lifecycle management

---

## Key Takeaways

| Aspect | 01.1 | 03 |
|--------|------|-----|
| **Focus** | View & Verify | Create & Track |
| **Primary Action** | Drill-down | Assign |
| **User Intent** | Analyze | Manage |
| **Modals** | 1 | 3 |
| **Complexity** | Lower | Higher |
| **Code Reuse** | 100% | 100% of 01.1 + 50% new |

---

## Relationship

```
01.1 Skills Dashboard (Scenario 01)
  └─ Duplicated in Scenario 03
       └─ Extended with:
            ├─ Assignment Wizard (03.1)
            ├─ Toast Notifications (03.2)
            └─ New Assignment Flow
```

---

## Recommendation

### For Rita's Workflow:

**Step 1:** Open 01.1-Skills-Dashboard.html
- Review existing assignments
- Check provenance
- Drill for details

**Step 2:** Use 03-Skills-Dashboard.html
- Create new assignments
- Track progress
- Get feedback

Both dashboards complement each other:
- **01.1** = Analysis & Verification
- **03** = Management & Operations

---

## Document Info

- **Created:** July 9, 2026
- **Comparison Type:** Feature & Functional
- **Scope:** HTML, CSS, JavaScript
- **Audience:** Development & Product Teams
- **Status:** Complete
