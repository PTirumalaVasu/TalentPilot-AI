# Scenario 01: Rita's Trust Call - Prototype Roadmap

**Scenario**: Rita's Trust Call
**Pages**: 01.1 through 01.2
**Device Compatibility**: Desktop-Only (1280px+)
**Design Fidelity**: Generic Gray Model (wireframe, Tailwind defaults)
**Last Updated**: 2026-07-08

---

## Scenario Overview

**User Journey**: Rita opens the Skills Dashboard to answer a staffing-readiness question. She scans provenance-labeled rows (Verified / Self-reported / Needs Attention), drills into a stale row to see the raw signal data and a plain-language explanation, then closes the drill-down with enough confidence to make her staffing call — without cross-referencing a spreadsheet.

**Pages in this Scenario**:
1. **01.1 Skills Dashboard** - Grid of employee assignments with provenance labels
2. **01.2 Provenance Drill-Down** - Modal showing raw signal data behind a row's status (implemented as an overlay *within* the Skills Dashboard file — see `work/Logical-View-Map.md`; it has no separate route)

**Source specs:** `../../C-UX-Scenarios/01-ritas-trust-call/`
**Design Delivery:** `../../deliveries/DD-001-poc-hypothesis-flows.yaml`

---

## Device Compatibility

**Type**: Desktop-Only (1280px+)

**Reasoning:** All 6 page specs across all 3 scenarios state "Desktop-primary, no mobile version needed" — Rita and Casey both work from a desktop/laptop, confirmed in the Product Brief and every page spec's Design Constraints section.

**Test Viewports**:
- Desktop 1280px - Minimum supported width
- Desktop 1440px - Common laptop width
- Desktop 1920px - Common external monitor width

**Optimization Strategy**:
- Fixed large layout, no responsive breakpoints
- Hover interactions always available
- No touch-target sizing constraints
- Not included: mobile layout, tablet layout, touch gestures

---

## Design Fidelity

**Generic Gray Model** — no design system exists for this project (`design_system_mode: none`). Uses Tailwind CDN defaults (grays, a single accent blue) rather than branded tokens. Focus is on validating functionality and information hierarchy (provenance labeling, drill-down clarity) before any visual polish investment.

---

## Folder Structure

**HTML Files** (root level - double-click to open):
```
01.1-Skills-Dashboard.html   (includes the 01.2 Provenance Drill-Down modal overlay — see Logical View Map)
```

**Supporting Folders**:
- `shared/` - Shared code (ONE COPY for all pages in this scenario)
- `components/` - Reusable UI components (ONE COPY)
- `pages/` - Page-specific scripts (only if a page's inline JS exceeds ~150 lines)
- `data/` - Demo data (auto-loads on first use) — Rita, Casey, Morgan, Jordan, Sam + assignments
- `stories/` - Section development documentation (created just-in-time)
- `work/` - Planning files (one `work.yaml` per page)

---

## Quick Start

### For Testing
1. **Open** `01.1-Skills-Dashboard.html` (double-click)
2. **Demo data prompt** → Click YES
3. **Navigate** through the flow (drill down on a row, close, repeat)
4. **Data persists** across pages (sessionStorage)

### For Stakeholders
1. **Unzip** the Prototype folder
2. **Open** `01.1-Skills-Dashboard.html`
3. **Test**: try to answer "who's ready for the Q3 initiative?" using only the dashboard + drill-down
4. **Share feedback**

---

## Production Migration Note

This prototype is a **throwaway static mockup** (Tailwind CDN + vanilla JS + sessionStorage) for UX validation only. It is explicitly separate from the real implementation described in `DD-001-poc-hypothesis-flows.yaml` (React+Vite frontend, FastAPI+Postgres+pgvector backend). Nothing here is migrated directly to production — it validates the UX before that real build starts.

---

## Prototype Status

| Page | Status | Sections | Last Updated | Notes |
|------|--------|----------|--------------|-------|
| 01.1 Skills Dashboard (incl. 01.2 modal) | ⏸️ Not Started | 0/? | - | Planned — single logical view, see Logical View Map |

**Status Legend:** ✅ Complete · 🚧 In Progress · ⏸️ Not Started · 🔴 Blocked

---

## Scenario Statistics

**Total Pages**: 2
**Completed**: 0
**In Progress**: 0
**Estimated Test Time**: ~3 minutes (complete flow)

---

## Change Log

### 2026-07-08
- Prototype environment created (folder structure + demo data)
- Scenario 01 selected as starting point (foundational — Scenarios 02/03 both extend this same dashboard)

---

**Last Updated**: 2026-07-08
**Version**: 1.0
**Status**: In Development
