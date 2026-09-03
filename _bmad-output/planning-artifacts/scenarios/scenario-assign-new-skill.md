# Scenario: Assign a New Skill (HR Admin)

**Entry point:** HR Dashboard → "+ New Assignment" button
**Component:** `AssignmentModal` (`frontend/src/features/assignments/AssignmentModal.tsx`)

## Steps

1. **Step 1 — Employee**
   - Combobox: "Who should learn this?" — search or select from list (`listEmployees`)
   - [Cancel] closes modal · [Continue to Skill Selection] enabled once an employee is picked
2. **Step 2 — Skill**
   - Combobox: "What skill?" — search or select (`listSkills`)
   - On [Review Content]: duplicate check (`checkDuplicateAssignment`) runs first
     - **If duplicate found:** interstitial — "This skill is already assigned to {Employee}." → [View] (closes modal) or [Assign Again] (proceeds to Step 3 anyway)
     - **If none:** proceeds straight to Step 3, kicks off content match fetch
   - [Back] returns to Step 1 · [Cancel] closes modal
3. **Step 3 — Review + Confirm**
   - Fetches best-match content for the skill (`matchContentForSkill`)
     - Loading: skeleton
     - Error: message + [Retry]
     - Found: thumbnail (if YouTube), title, source, duration, description, "✓ Approved" badge, "View on YouTube" link
     - Not found: "No approved content found yet for this skill." — user can still assign without content
   - Assignment Summary block: Employee / Skill / Content / "Assignment Date: Today" / "Status: Will be 'Assigned · Awaiting first watch'"
   - [Back] → Step 2 (resets duplicate/content state) · [Cancel] closes modal · [Assign] / [Assign without content] submits (`createAssignment`)

## Success Path
Assign succeeds → modal closes → HR Dashboard grid refetches → toast: "✓ Skill assigned to {FirstName} — {SkillName}"

## Error States
- Duplicate check fails: "Couldn't check for an existing assignment. Please try again." (stays on Step 2)
- Content fetch fails: "Couldn't load content recommendation." + Retry (stays on Step 3)
- Submit fails: "Couldn't create the assignment. Please try again." (stays on Step 3)

## Notes
- Closing mid-flight (Escape/backdrop-click) is silently blocked while a duplicate-check or submit is in-flight, to prevent a stale async response writing into a closed-and-reset modal.
- Every async call is token-guarded against out-of-order responses (a common pattern across this codebase's async components).
