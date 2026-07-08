# Scenario 03: Rita's Assignment & Track - Prototype Roadmap

**Scenario**: Rita's Assignment & Track
**Pages**: 03.1 through 03.2
**Device Compatibility**: Desktop-Only (1280px+)
**Design Fidelity**: Generic Gray Model (wireframe, Tailwind defaults)
**Last Updated**: 2026-07-08

---

## Scenario Overview

**User Journey**: Rita clicks [+ New Assignment] on the Skills Dashboard, completes a 3-step form (employee → skill → auto-linked content review), and sees the new assignment appear immediately on the dashboard with a confirmation toast — closing the assignment-to-tracking loop.

**Pages in this Scenario**:
1. **03.1 Skill Assignment Flow** - 3-step modal form, auto-linked content
2. **03.2 Assignment Confirmation & Auto-Update** - the Skills Dashboard, updated with the new row + toast

**Source specs:** `../../C-UX-Scenarios/03-ritas-assignment-and-track/`
**Design Delivery:** `../../deliveries/DD-001-poc-hypothesis-flows.yaml`

---

## Important: This Reuses Scenario 01's Dashboard, Not New Pages

Both 03.1 and 03.2 are explicitly extensions of the **same Skills Dashboard** built in `../01-Ritas-Trust-Call-Prototype/01.1-Skills-Dashboard.html`:
- **03.2's own spec** says "Layout Sections: Same as 01.1 - Skills Dashboard, plus: Toast/Confirmation, New Row Highlight"
- **03.1's entry point** is the `[+ New Assignment]` button, which Scenario 01 built as a stub logging *"full flow is Scenario 03, not built in this pass"*

Per the project's chosen approach (new per-scenario folder, rather than editing Scenario 01's file directly), this folder contains a **duplicated copy** of the finished Scenario 01 dashboard as its starting point, extended here with the real Skill Assignment Flow modal and the toast/new-row-highlight behavior. This does mean the dashboard logic now exists in two places (Scenario 01's original + this copy) — noted as a known trade-off, not an oversight.

---

## Device Compatibility

**Type**: Desktop-Only (1280px+) — same reasoning as Scenarios 01/02.

---

## Demo Data Note

Starting assignments match Scenario 01 exactly (Casey/Morgan/Jordan/Sam). Completing the assignment flow adds a 5th row — Casey + Python Basics, "Assigned · Awaiting first watch" — matching the 03.2 spec's own worked example.

---

## Production Migration Note

Same as Scenarios 01/02: throwaway static mockup for UX validation only, separate from the real DD-001 implementation.

---

## Prototype Status

| Page | Status | Sections | Last Updated | Notes |
|------|--------|----------|--------------|-------|
| Dashboard (duplicated from 01.1) | ⏸️ Not Started | 0/? | - | Starting point copy |
| 03.1 Skill Assignment Flow (modal) | ⏸️ Not Started | 0/? | - | Planned |
| 03.2 Toast/New-Row-Highlight | ⏸️ Not Started | 0/? | - | Planned |

**Status Legend:** ✅ Complete · 🚧 In Progress · ⏸️ Not Started · 🔴 Blocked

---

## Change Log

### 2026-07-08
- Prototype environment created (folder structure + demo data + shared infra)
