# Logical View Map — Scenario 02: Casey's Resume & Watch

**Created:** 2026-07-08
**Confirmed by user:** 2026-07-08

---

## Views Identified

### View 1: Content Discovery

**File:** `02.1-Content-Discovery.html`

**Scenario steps mapped to this view:** 02.1 only

**Why separate from Continue Watching:** Own URL route (`/assignments/:id/content`), no overlay/inherit relationship — a distinct full page per spec.

**States to implement:**
| State | Trigger |
|---|---|
| Loaded | Assignment card + content recommendation fetched successfully |
| Loading | Page opens, data not yet returned |
| Empty | Skill assigned but no matching content found |
| Error | Video fails to load/play |

**Design ref:** `../../C-UX-Scenarios/02-caseys-resume-and-watch/02.1-content-discovery/02.1-content-discovery.md`

---

### View 2: Continue Watching

**File:** `02.2-Continue-Watching.html`

**Scenario steps mapped to this view:** 02.2 only

**Why separate from Content Discovery:** Own URL route (`/continue-watching`), no overlay/inherit relationship — a distinct full page per spec.

**States to implement:**
| State | Trigger |
|---|---|
| Continue Watching (loaded) | Progress card with resume button displayed |
| Loading | Saved watch-position not yet returned |
| Empty | No in-progress skills exist |
| Error | Saved watch-position fails to load or resume playback fails |

**Design ref:** `../../C-UX-Scenarios/02-caseys-resume-and-watch/02.2-resume-continue-watching/02.2-resume-continue-watching.md`

---

## Build Order

1. **Content Discovery** — first step in the user journey (Casey encounters this before ever resuming anything)
2. **Continue Watching** — second step

---

## Notes

- Unlike Scenario 01, these two views do NOT share a single HTML file — each has its own route and is a standalone page.
- Demo data (`data/demo-data.js`) provides independent state for each view (`contentDiscovery` fresh/0%, `continueWatching` mid-progress/51%) rather than one shared timeline — see `PROTOTYPE-ROADMAP.md`.
