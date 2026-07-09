# Reviewer: Adversarial divergence hunter

**Method:** construct two units one level down that each obey every AD to the letter yet still build incompatibly. Every such pair is a hole.

**Verdict:** 3 real seams found, all closed by tightening existing ADs (no new hole remains open).

## Findings (all FIXED in the spine)

1. **Status/Provenance conflation (prototype trap).** The prototype's demo-data stored `status: "Needs Attention"` (a Provenance value) as a Status. A builder copying the prototype would put Needs Attention on the Status axis; a builder reading the PRD would keep it on Provenance. AD-3 did not name the value sets. → **Fixed:** AD-3 now declares Status ∈ {Not Started, In Progress, Completed} and Provenance ∈ {Verified, Self-reported, Needs Attention, HR Override} as orthogonal axes, Needs Attention never a Status.

2. **Who creates the progress row.** AD-1 makes `progress/` the sole writer of `skill_progress`; a brand-new Assignment has no watch signal. Builder A (assignments) could assume a progress row is seeded on assignment; builder B (progress) could create it lazily on first watch — leaving a new row with no progress row and undefined derivation. → **Fixed:** AD-3 now states an Assignment with no watch signal derives as Not Started with no row required to pre-exist, so `assignments/` never writes into `progress/`'s domain.

3. **Identity-scoping breaks the HR dashboard.** AD-6(c) hard-scoped *every* query to the caller's identity — correct for Employees, but the HR Admin dashboard legitimately reads across all Employees. A literal implementation would return an empty dashboard for HR. → **Fixed:** AD-6(c) is now role-aware — Employee sessions hard-scoped to own identity; HR Admin sessions may read org-wide but only through AD-2's coaching-shaped read methods, never a raw/export path (so the coaching-only boundary still holds for the org-wide read).

## Probed and found sound

- content/ ingestion→matching→assignment(FR-2 read) all cross module boundaries via Service APIs only (AD-1/AD-8) — no divergence.
- HR Override coexistence (AD-4) holds against fresh watch writes (AD-5) — separate records, single derivation reconciles.
- `skill_progress` keyed by `assignment_id` correctly handles FR-1's duplicate-assignment case (per-assignment, not per employee×skill).
