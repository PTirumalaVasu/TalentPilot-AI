# Scenario 02: Casey's Resume & Watch - Prototype Roadmap

**Scenario**: Casey's Resume & Watch
**Pages**: 02.1 through 02.2
**Device Compatibility**: Desktop-Only (1280px+)
**Design Fidelity**: Generic Gray Model (wireframe, Tailwind defaults)
**Last Updated**: 2026-07-08

---

## Scenario Overview

**User Journey**: Casey receives an assigned skill, sees exactly one human-approved content recommendation on Content Discovery, plays it, and later returns to Continue Watching to resume at the exact last-watched position — no manual logging, no searching, no seeking.

**Pages in this Scenario**:
1. **02.1 Content Discovery** - Assignment card with single AI-recommended content, play button
2. **02.2 Continue Watching** - Resume card with progress bar and exact-timestamp resume

**Source specs:** `../../C-UX-Scenarios/02-caseys-resume-and-watch/`
**Design Delivery:** `../../deliveries/DD-001-poc-hypothesis-flows.yaml`

---

## Device Compatibility

**Type**: Desktop-Only (1280px+) — same reasoning as Scenario 01: every page spec states desktop-primary, no mobile version needed.

---

## Design Fidelity

**Generic Gray Model** — same as Scenario 01, no design system exists for this project (`design_system_mode: none`).

---

## Demo Data Note

Content Discovery and Continue Watching are **independent full pages** (each has its own URL route per spec, unlike Scenario 01's dashboard+modal pairing), so each page loads its own demo state rather than sharing one continuous timeline:
- **Content Discovery**: Casey's assignment fresh, "Assigned · Awaiting first watch," 0% progress
- **Continue Watching**: Casey's assignment mid-progress, 51% watched / 14:32 of 28:00 — matching the 02.2 spec's own worked example exactly

---

## Quick Start

### For Testing
1. Open `02.1-Content-Discovery.html` or `02.2-Continue-Watching.html` directly (each is independent)
2. Demo data auto-loads via `data/demo-data.js`

---

## Production Migration Note

Same as Scenario 01: this is a throwaway static mockup (Tailwind CDN + vanilla JS + sessionStorage) for UX validation only, separate from the real DD-001 implementation (React+Vite + FastAPI+Postgres+pgvector).

---

## Prototype Status

| Page | Status | Sections | Last Updated | Notes |
|------|--------|----------|--------------|-------|
| 02.1 Content Discovery | ⏸️ Not Started | 0/? | - | Planned |
| 02.2 Continue Watching | ⏸️ Not Started | 0/? | - | Planned |

**Status Legend:** ✅ Complete · 🚧 In Progress · ⏸️ Not Started · 🔴 Blocked

---

## Change Log

### 2026-07-08
- Prototype environment created (folder structure + demo data)
