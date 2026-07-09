# Deferred Work Ledger

## Deferred from: code review of 1-1-project-structure-and-core-dependencies (2026-07-09)

- **JWT `role` claim accepts any string (no enum check); `JWT_EXPIRATION_HOURS` has no bounds check** [backend/app/core/security.py] — not required by Story 1.1's AC3; Story 1.3 ("Role & Identity Scoping on Every Request") already specs role-enum validation (403 on unrecognized role) at the FastAPI-dependency layer — make sure that story's implementation covers this, don't let it slip through as "already handled."
- **No `import-linter`/lint enforcement of the AD-1 single-owner module boundary** — module `repository.py`/`service.py` stubs are docstring comments only; nothing structurally prevents a future cross-module import. Worth a dedicated architecture-hardening story/task once more modules have real code to enforce against.
- **No lockfile/hash-pinning beyond top-level `==` pins in `backend/requirements.txt`** — transitive dependencies are unconstrained. Reasonable for a 5-week internal pilot; revisit (e.g. `pip-compile` with hashes) only if reproducibility becomes an actual problem.
- **No engine-disposal/lifespan hook to close the async DB engine on shutdown** [backend/app/main.py] — no live-connection bug exists yet since Story 1.7 is the first story to exercise a real DB connection; add a `lifespan` context manager calling `engine.dispose()` once real DB traffic exists.
