---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: ['_bmad-output/project-context.md', '_bmad-output/planning-artifacts/research/technical-third-party-video-embeds-youtubevimeo-with-custom-watch-progress-tracking-research-2026-07-07.md', '_bmad-output/planning-artifacts/research/technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md']
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'Overall technical stack and architecture for TalentPilot-AI (internal HR skill-tracking/talent-pool MVP)'
research_goals: 'Recommend a complete, current-best-practice technical implementation for TalentPilot-AI, given no fixed frontend/backend framework yet but with Postgres+pgvector, YouTube IFrame API, Adapter pattern, and conditional-write persistence already decided. Cover: overall application architecture, frontend framework/folder/component structure, backend layered architecture, full database schema (incl. video-progress and pgvector tables), REST API design, authentication approach, UI component library, form validation, error handling, responsive UI, UX best practices, deployment, and clean/maintainable code structure.'
user_name: 'TalentPilot'
date: '2026-07-08'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-07-08
**Author:** TalentPilot
**Research Type:** technical

---

## Research Overview

This research recommends a complete, current-best-practice technical implementation for TalentPilot-AI's overall stack — an internal HR skill-tracking/talent-pool MVP under a 5-week build timeline. It builds directly on top of two decisions already locked in prior research (YouTube IFrame API for video-progress capture; PostgreSQL+pgvector for skill-to-tutorial matching) and TalentPilot's directed choice of **Python/FastAPI (backend)**, **React (frontend)**, **PostgreSQL (database)**. It covers overall application architecture, backend layered/feature-domain structure, frontend folder/component structure, database access patterns, REST API design, authentication, UI component library, form validation, testing, and deployment. See the Technical Research Synthesis section near the end for the full executive summary and recommendations.

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technical Research Scope Confirmation

**Research Topic:** Overall technical stack and architecture for TalentPilot-AI (internal HR skill-tracking/talent-pool MVP)
**Research Goals:** Recommend a complete, current-best-practice technical implementation for TalentPilot-AI, given no fixed frontend/backend framework yet but with Postgres+pgvector, YouTube IFrame API, Adapter pattern, and conditional-write persistence already decided. Cover: overall application architecture, frontend framework/folder/component structure, backend layered architecture, full database schema (incl. video-progress and pgvector tables), REST API design, authentication approach, UI component library, form validation, error handling, responsive UI, UX best practices, deployment, and clean/maintainable code structure.

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture (built around Postgres+pgvector as fixed)
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - frontend/backend framework candidates, languages, tools, platforms
- Integration Patterns - REST API design, auth, YouTube/pgvector integration points
- Performance Considerations - scalability, optimization, patterns appropriate for an internal pilot

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-07-08

---

## Technology Stack Analysis

### Programming Languages

**[User-directed decision, 2026-07-08]: Python (backend) + JavaScript/TypeScript (React frontend), superseding the full-stack-TypeScript option initially explored.** TalentPilot chose Python/FastAPI for the backend, React for the frontend, and PostgreSQL for the database. This is a deliberate two-language split rather than the unified-TypeScript path — the trade-off (no shared types across the API boundary) is accepted in exchange for FastAPI's fit with the project's AI/ML-adjacent surface (embeddings for the RAG/pgvector matching feature) and Python's ecosystem strength there (`sentence-transformers`, `openai`, `pgvector` client libraries are Python-first).
_Recommendation: Python 3.12+ (backend), TypeScript (React frontend) — not full-stack TypeScript._

### Development Frameworks and Libraries

**Backend: FastAPI.** [Confidence: High] "FastAPI has become the default way to ship Python APIs in 2026," pairing type-hint-driven validation (via Pydantic) with native `async`/`await` and auto-generated OpenAPI 3.1 docs. This fits TalentPilot-AI well: async support matters because the backend talks to two I/O-bound external dependencies (YouTube IFrame API client-side, plus any embedding-generation calls), and Pydantic schemas double as request/response validation without a separate library.
_Recommended structure: domain-module organization (per FastAPI community convention, e.g. the "Netflix Dispatch"-inspired layout) — each module (e.g. `video_progress/`, `skill_matching/`, `auth/`) holds its own `router.py`, `schemas.py`, `models.py`, `dependencies.py`, rather than a single flat `routes.py`/`models.py` pair — keeps the video-tracking and RAG-matching features cleanly separated._
_Source: [FastAPI Tutorial: Build REST API in 13 Steps (2026)](https://tech-insider.org/fastapi-tutorial-python-rest-api-13-steps-2026/), [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices), [Production-Ready FastAPI Project Structure (2026 Guide)](https://dev.to/datanestdigital/production-ready-fastapi-project-structure-2026-guide-b1g)_

**Frontend: plain React (Vite), not Next.js.** [Confidence: High] Current guidance is consistent and specific to this exact scenario — an authenticated, internal, non-public dashboard: "Internal dashboards, admin panels, and tools that live behind a login do not need SEO. Server-side rendering adds complexity without value... choose plain React if you're building an internal tool or admin dashboard that doesn't require SEO and is always behind authentication." TalentPilot-AI is precisely this case (internal HR pilot tool, no public/SEO surface, single-tenant use). Next.js's SSR/routing/server-actions machinery would add build complexity with no corresponding benefit for a 5-week internal pilot, and would need to coexist with a separate FastAPI backend anyway (losing Next.js's main "unified backend" selling point).
_Recommendation: React + TypeScript + Vite (SPA), not Next.js._
_Source: [Next.js vs React: When to Use Which (2026)](https://designrevision.com/blog/nextjs-vs-react), [Next.js vs React 2026: What's the Difference?](https://www.groovyweb.co/blog/nextjs-vs-react-comparison-2026)_

**Database access layer: SQLAlchemy 2.0 (async) + asyncpg, with SQLModel considered for simple entities.** [Confidence: High] "SQLAlchemy 2.0 ships first-class async support via AsyncEngine and AsyncSession, but you must use an async driver (asyncpg) and the `postgresql+asyncpg://` dialect" — this pairs directly with FastAPI's async request handlers so DB calls don't block the event loop. For schema simplicity, "SQLModel combines Pydantic and SQLAlchemy into a single class... cutting the schema layer in half for simple projects," but "for projects where the API contract diverges from the storage shape, keep the two layers separate" — relevant here since the video-progress table (internal write-heavy, conditional-write logic) and the tutorial/skill-matching table (pgvector similarity queries) likely warrant explicit separation between DB models and API schemas rather than SQLModel's merged shape.
_Recommendation: async SQLAlchemy 2.0 + asyncpg as the default; use SQLModel only for straightforward CRUD entities (e.g. `users`) if it measurably reduces boilerplate, not uniformly across the whole schema._
_Source: [Setting up a FastAPI App with Async SQLAlchemy 2.0 & Pydantic V2](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308), [Building High-Performance Async APIs with FastAPI, SQLAlchemy 2.0, and Asyncpg](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)_

**pgvector integration confirmed compatible and well-trodden with this exact stack.** [Confidence: High] "FastAPI can be utilized for the HTTP API, with pgvector and SQLAlchemy for the vector database side" is a standard, multiply-documented pattern — not novel risk. Async SQLAlchemy + asyncpg + pgvector work together cleanly, including ordering query results by vector distance (`.order_by(embedding.cosine_distance(query_vector))`) inside an async session. Index choice for the tutorial-catalog scale (likely low hundreds/thousands of rows for a pilot) doesn't need HNSW's complexity — IVFFlat, or even no index at all below a few thousand rows, is sufficient; revisit only if catalog size grows materially.
_Source: [Building a FastAPI-Powered RAG Backend with PostgreSQL & pgvector](https://medium.com/@fredyriveraacevedo13/building-a-fastapi-powered-rag-backend-with-postgresql-pgvector-c239f032508a), [PostgreSQL with pgvector as a Vector Database for RAG](https://codeawake.com/blog/postgresql-vector-database)

### Database and Storage Technologies

**Postgres + pgvector is already decided** (carried forward from the RAG/vector-database research, 2026-07-08) for the skill-to-tutorial matching feature. Current sources confirm this remains the right call rather than something to revisit: "pgvector is now mature and used in production by OpenAI, Supabase, Neon, and thousands of teams... if you're starting a new production RAG project today and don't have a strong reason to choose something else, start with pgvector on Postgres, and move to a dedicated vector DB only when you can name the specific bottleneck." This project has no such bottleneck (small tutorial catalog, retrieval-only, not full RAG) — a dedicated vector DB (Pinecone/Weaviate) would be pure added infrastructure with no payoff.
_One hosting constraint worth flagging: serverless Postgres platforms optimized for scale-to-zero (Neon, PlanetScale) do **not** support pgvector — "serverless Postgres platforms like Neon and PlanetScale don't support pgvector, as they optimize for scale-to-zero and connection pooling rather than custom extensions." This rules out Neon despite it otherwise fitting a low-traffic internal pilot._
_Recommendation: use any standard Postgres instance with pgvector enabled for local/dev work (e.g. a Docker Compose Postgres+pgvector container); avoid Neon/PlanetScale specifically since they don't support pgvector. Managed-hosting provider choice (Supabase, Railway, Render, etc.) is deferred — not a current focus, see Cloud Infrastructure and Deployment below._
_Source: [Hosting Postgres with pgvector: provider tradeoffs](https://blog.railway.com/p/hosting-postgres-with-pgvector), [Best PostgreSQL hosting providers for developers in 2026](https://northflank.com/blog/best-postgresql-hosting-providers)_

### Development Tools and Platforms

_Build tool: Vite for the React frontend — fast dev server and build times, the current default over Create React App for new 2026 React projects._
_Backend runtime: Python 3.12+ with `uvicorn` as the ASGI server (FastAPI's standard pairing), managed via `uv` or `poetry` for dependency/venv management over raw `pip`+`requirements.txt`._
_Testing: Vitest + React Testing Library (frontend); `pytest` + `httpx.AsyncClient` (backend API tests against FastAPI's `TestClient`/async test fixtures) — the standard FastAPI-native testing approach, not a JS test runner against the Python backend._
_Version control/CI: Git with GitHub Actions running frontend lint/typecheck/test (ESLint, `tsc`, Vitest) and backend lint/typecheck/test (`ruff`, `mypy`, `pytest`) as separate jobs, matching the existing project convention (branch naming, PR-based merges) already recorded in project-context.md._

### Cloud Infrastructure and Deployment

**Explicitly out of scope for now, per TalentPilot's direction — deployment/hosting is not a current focus.** Local/dev-environment setup (e.g. Docker Compose for Postgres+pgvector during development) is the only near-term concern; production hosting choice (Railway/Render vs. other options) is deferred to a later pass, not decided here. Treat any deployment-shaped recommendation elsewhere in this document as illustrative only, not a locked decision.

### Technology Adoption Trends

_A React + FastAPI split (rather than full-stack TypeScript) is itself a well-established, mainstream 2026 pattern for AI/ML-adjacent products specifically — not a niche or legacy choice — because it puts the backend in the same language as the embedding/matching logic (`sentence-transformers`, `openai`, pgvector client libraries) instead of requiring a Python "sidecar" service alongside a Node API. The trade-off accepted here is no shared types across the API boundary (mitigated by keeping Pydantic schemas and TypeScript API types manually in sync, or generating one from FastAPI's OpenAPI schema)._
_Legacy pattern being phased out, still relevant: hand-rolled SSR/Next.js for internal, authenticated-only tools — current guidance explicitly calls this out as unnecessary complexity for this project's shape, independent of the backend-language choice._
_Source: [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices), [Next.js vs React: When to Use Which (2026)](https://designrevision.com/blog/nextjs-vs-react)_

---

## Integration Patterns Analysis

### API Design Patterns

[Confidence: High] RESTful, resource-oriented JSON API is the correct and only relevant choice for a React SPA talking to a single FastAPI backend. FastAPI generates OpenAPI 3.1 docs automatically from route/Pydantic definitions, which also gives a natural path to auto-generating a typed TypeScript client for the frontend if the manual-type-sync cost (noted in Technology Adoption Trends above) becomes a real friction point.
_RESTful APIs: plural-noun resources (`/api/videos/{id}/progress`, `/api/tutorials`, `/api/skills/{id}/tutorials`), standard HTTP verbs, shallow nesting (≤2 levels)._
_GraphQL/gRPC: not applicable — a fixed, small domain model (users, videos, progress, skills, tutorials) has no query-flexibility or service-to-service performance problem that would justify either._
_Source: [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices)_

### Communication Protocols

_HTTP/HTTPS REST over JSON is the only protocol needed. No WebSocket requirement — watch-progress capture is client-side polling/event-driven against the YouTube IFrame API (per the earlier video-embed research) and persisted via periodic REST POST, not a live server-push channel._
_Message queues/gRPC: not applicable at this scale — no async job processing beyond a possible scheduled batch ingestion job for tutorial content (per the RAG research's YouTube search-quota constraint), which is a cron/scheduled-task concern, not a message-broker one._

### Data Formats and Standards

_JSON is the standard format for all request/response bodies, matching both React's `fetch`/axios handling and FastAPI/Pydantic's native JSON serialization._
_Pydantic schemas (request/response models) should stay separate from SQLAlchemy ORM models — consistent with the Technology Stack Analysis recommendation against SQLModel for the video-progress and tutorial-matching tables — so the API contract doesn't leak internal storage shape._

### System Interoperability Approaches

_Point-to-point: the only relevant pattern — one React SPA calling one FastAPI REST API directly. No API Gateway or service mesh needed at this scale; introducing either would be pure overhead for an internal single-environment pilot._
_Illustrative endpoint shape (to be finalized in architecture phase):_
- `POST /api/auth/login` — credential check, returns auth cookie (see Integration Security Patterns below)
- `GET /api/videos/{videoId}` , `POST /api/videos/{videoId}/progress` — watch-progress capture (conditional-write, per prior video research)
- `GET /api/employees/{employeeId}/assigned-skills` — HR-assigned skills for an employee
- `GET /api/skills/{skillId}/tutorials` — pgvector-ranked tutorial recommendations for a skill

### Microservices Integration Patterns

Not applicable — this is intentionally a single FastAPI monolith. No API gateway, service discovery, circuit breakers, or saga pattern; all would be over-engineering relative to a 5-week internal pilot with one deployable backend.

### Event-Driven Integration

Not applicable for the primary request/response paths. The one background-processing need — periodically ingesting/embedding new tutorial content within YouTube's ~100-call/day search quota (per the RAG research) — is a scheduled batch job (e.g., a daily cron task), not a pub/sub or message-broker architecture.

### Integration Security Patterns

[Confidence: High] **Recommendation: JWT stored in an HTTP-only, Secure, SameSite cookie** — not JWT in `localStorage`, and not a heavier session-store framework. Current sources are explicit and consistent: "JWTs should not be kept in the browser's local storage, as this is a known bad practice despite being commonly done in tutorials," while "using JWT in cookies is highly recommended if your frontend interacts with the backend" — HTTP-only prevents JavaScript/XSS access to the token, `Secure` enforces HTTPS-only transmission, and `SameSite` mitigates CSRF. This fits TalentPilot-AI's real auth shape (per the earlier decisions carried in project-context.md-equivalent research): a small, fixed set of HR/employee users, not a public multi-tenant system — so a lightweight JWT-in-cookie pattern is right-sized, avoiding both the XSS risk of `localStorage` JWTs and the added infrastructure of a server-side session store.
_CORS: configure `CORSMiddleware` with explicit allowed origins (the React dev server origin, and the production frontend origin) — never `allow_origins=["*"]`, since cookie-based auth requires credentialed CORS requests, which are incompatible with a wildcard origin._
_Error handling: override FastAPI's default `HTTPException`/`RequestValidationError` handlers with a single consistent JSON error shape (status, error code, message, timestamp) via `@app.exception_handler(...)`, so the React frontend has one error contract to parse across all endpoints._
_Source: [JWT and Cookie Auth in FastAPI](https://retz.dev/blog/jwt-and-cookie-auth-in-fastapi/), [Bulletproof JWT Authentication in FastAPI](https://medium.com/@ancilartech/bulletproof-jwt-authentication-in-fastapi-a-complete-guide-2c5602a38b4f), [Blocked by CORS in FastAPI? Here's How to Fix It](https://davidmuraya.com/blog/fastapi-cors-configuration/), [FastAPI Error Handling: Types, Methods, and Best Practices](https://www.honeybadger.io/blog/fastapi-error-handling/)_

---

## Architectural Patterns and Design

### System Architecture Patterns

[Confidence: High] A simple two-tier architecture is correct for this scope: React SPA (client) ↔ FastAPI REST API (server) ↔ PostgreSQL+pgvector (persistence), with the browser also talking directly to the embedded YouTube IFrame player. No microservices, no serverless split, no event-driven layer — all would add operational complexity (multiple deployables, network hops, eventual consistency) with no corresponding benefit for a single-environment internal pilot.
_Overall flow: Browser (React SPA) → HTTPS/REST/JSON → FastAPI (Router → Service → Repository) → PostgreSQL+pgvector; Browser ↔ YouTube IFrame Player directly (client-side only, per the video-embed research)._
_Source: synthesized from Integration Patterns Analysis and Technology Stack Analysis sections above_

### Design Principles and Best Practices

**Backend: layered architecture (Router → Service → Repository), not a flat/monolithic file.** [Confidence: High] Current guidance converges on this structure for production FastAPI apps: "routers for HTTP endpoints, services for business workflows, repositories for database queries, schemas for request and response validation, and core modules for configuration and infrastructure concerns" — with the service layer holding business rules "separate from both HTTP handling and database access," and the repository layer owning data access so "you can swap databases without touching logic."
_Recommended layout, adapted to a feature/domain hybrid (since "if you split directories strictly by layers, you often end up jumping across folders to understand a single feature; 'by feature' tends to fit web APIs well" — and this project has exactly two distinct feature domains: video-progress tracking and skill-to-tutorial matching):_
```
app/
├── main.py
├── core/            (config, security/JWT, CORS setup)
├── video_progress/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py     (SQLAlchemy)
│   └── schemas.py    (Pydantic)
├── skill_matching/
│   ├── router.py
│   ├── service.py
│   ├── repository.py (incl. pgvector similarity queries)
│   ├── models.py
│   └── schemas.py
├── auth/
│   ├── router.py, service.py, schemas.py
└── tests/
```
_Source: [Production-Ready FastAPI Project Structure (2026 Guide)](https://dev.to/thesius_code_7a136ae718b7/production-ready-fastapi-project-structure-2026-guide-b1g), [Layered Architecture & Dependency Injection: A Recipe for Clean and Testable FastAPI Code](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)_

**Frontend: feature-based folder structure.** [Confidence: High] "The most popular modern approach is to group files by feature... If you're unsure, start with a Feature-Based approach. It offers the best balance of scalability and simplicity," while shared/dumb components, hooks, and API-call helpers stay in top-level folders. TalentPilot-AI's two feature domains (video progress, skill/tutorial matching) plus auth map directly onto this.
_Recommended layout:_
```
src/
├── api/             (axios/fetch clients per resource: videoApi.ts, tutorialApi.ts, authApi.ts)
├── components/       (shared presentational: Button, Modal, Badge)
├── features/
│   ├── video-progress/   (player wrapper, progress hooks/components)
│   ├── skill-tutorials/  (recommendation list, matching UI)
│   └── auth/             (login form)
├── hooks/            (shared custom hooks)
├── types/            (TypeScript interfaces mirroring FastAPI Pydantic schemas)
└── App.tsx
```
_Source: [React Folder Structure Best Practices (2026)](https://www.robinwieruch.de/react-folder-structure/), [How to structure a React app in 2026](https://dangz.dev/blog/how-to-structure-a-react-app-in-2026)_

### Scalability and Performance Patterns

Not a primary concern for an internal pilot with a small, known user base (HR + assigned employees), but worth building in as low-cost defaults: paginate list endpoints (tutorials, employees) rather than returning unbounded result sets, and cache pgvector similarity results per skill briefly if the tutorial catalog is re-queried frequently — neither adds meaningful complexity and both are standard practice regardless of scale.

### Integration and Communication Patterns

Already covered in the Integration Patterns Analysis section above — point-to-point REST/JSON between a single React SPA and a single FastAPI monolith, JWT-in-cookie auth, centralized exception handling. No changes needed here.

### Security Architecture Patterns

_JWT-in-HTTP-only-cookie auth (per Integration Patterns Analysis), CORS restricted to explicit origins, Pydantic-level input validation on all inbound request schemas (FastAPI validates automatically against type hints, returning 422 on mismatch)._
_Data-access boundary: per the PRFAQ's locked privacy decision (auto-captured watch-progress data is coaching-only, never used in performance evaluations), this constraint should be enforced at the repository/service layer — e.g., a distinct query path or explicit field-level access control — not left as a UI-only convention, since the architecture must make the "coaching-only" guarantee structurally true, not just documented._

### Data Architecture Patterns

_Standard normalized relational schema via SQLAlchemy models, with pgvector as a column type (not a separate database) on the tutorial-embeddings table — consistent with the RAG research's filter-then-rank approach (metadata pre-filter on skill tag, then vector similarity ranks within that set). No CQRS or event sourcing — unnecessary complexity at this scale._

### Deployment and Operations Architecture

**Deferred — not a current focus.** Whatever hosting/deployment is chosen later, the only architectural constraint worth locking in now is: no Kubernetes, no multi-region, no serverless FaaS split — those would all be premature complexity for a single-environment internal pilot regardless of which specific host is picked.

---

## Implementation Approaches and Technology Adoption

_Adapted to project scope: the standard template's technology-migration, team-organization, and cost-optimization sections assume an enterprise rollout onto existing systems, which doesn't apply to a from-scratch 5-week internal pilot with a small/solo team. This section instead covers the concrete remaining implementation areas: UI component library, form validation, testing/CI, and deployment practices — mirroring what was covered for the Kanban project's technical research._

### UI Component Library Recommendation

[Confidence: High] **shadcn/ui + Tailwind CSS**, not MUI. Current sources: "shadcn/ui is the top pick for most new React projects in 2026: Tailwind-native, copy-paste components, zero runtime overhead... you copy components into your project and own them completely, with no dependency lock-in, no version conflicts, no black boxes." MUI is noted as stronger specifically for "data-heavy and enterprise React applications" with complex data-table/form systems — TalentPilot-AI's dashboard (video progress list, skill/tutorial recommendations) is real but not that data-dense, so shadcn/ui's lighter bundle and full code ownership fit better than adopting MUI's heavier Material Design system and CSS-in-JS runtime cost for a 5-week build.
_Source: [14 Best React UI Component Libraries in 2026](https://www.untitledui.com/blog/react-component-libraries), [Best UI Component Libraries in 2026: shadcn/ui, MUI, Radix, Base UI Compared](https://dualite.dev/blogs/best-ui-component-libraries)_

### Form Validation

[Confidence: High] **React Hook Form + Zod** (frontend), paired with **Pydantic** (backend, native to FastAPI). Frontend: one Zod schema per form (e.g., login, HR skill-assignment if editable in-app), wired via `@hookform/resolvers/zod`, with `z.infer<>` giving the matching TypeScript type. Backend: FastAPI's Pydantic request models validate automatically against type hints (422 on mismatch) — no separate validation library needed server-side, consistent with the Technology Stack Analysis finding that Pydantic schemas double as validation.
_Security note: client-side validation is UX-only; the FastAPI/Pydantic layer is the real guard against malformed input, matching the JWT/CORS boundary already established._

### Testing and Quality Assurance

[Confidence: High] **Backend:** `pytest` + `pytest-asyncio` (or `asyncio_mode = "auto"` in `pytest.ini` to avoid decorating every test), with `httpx.AsyncClient` against FastAPI's app for endpoint tests, and `dependency_overrides` to mock the DB/auth dependencies rather than hitting a real Postgres instance in unit tests — "clean database testing uses rollbacks or in-memory databases for isolated runs" for the subset of tests that do need real DB behavior (e.g., pgvector query correctness).
_**Frontend:** Vitest + React Testing Library, consistent with the Vite build tool already chosen._
_Source: [Continuous Integration on Github with FastAPI and pytest](https://retz.dev/blog/continuous-integration-github-fastapi-and-pytest/), [What Is FastAPI Testing? Tools, Frameworks, and Best Practices](https://www.frugaltesting.com/blog/what-is-fastapi-testing-tools-frameworks-and-best-practices)_

### CI Practices (deployment itself deferred)

[Confidence: High] GitHub Actions CI should run backend (`ruff`, `mypy`, `pytest --ignore=tests/integration` for fast feedback, full suite on merge) and frontend (`eslint`, `tsc`, `vitest`) as separate parallel jobs, matching the branch/PR conventions already recorded in project-context.md. **Containerization and hosting (Docker, Railway/Render, etc.) are explicitly out of scope for now per TalentPilot's direction** — not researched or recommended in this pass.
_Source: [Continuous Integration on Github with FastAPI and pytest](https://retz.dev/blog/continuous-integration-github-fastapi-and-pytest/)_

### Risk Assessment and Mitigation

- **Two-language stack (Python + TypeScript) risk:** no shared types across the API boundary — mitigated by keeping Pydantic schemas and TypeScript interfaces manually aligned, or generating a TS client from FastAPI's OpenAPI schema if drift becomes a real problem.
- **pgvector at small scale:** no meaningful risk — confirmed mature, production-used technology; index tuning (IVFFlat/HNSW) is a non-issue until the tutorial catalog grows into the thousands of rows.
- **Privacy/architecture risk (carried forward from PRFAQ):** the "coaching-only" data-use guarantee must be enforced at the service/repository layer, not just documented — a real launch-blocking risk if skipped, per the Architectural Patterns section above.
- **YouTube search-quota risk (carried forward from RAG research):** ~100 calls/day constrains content ingestion to a scheduled batch job — already accounted for in the Event-Driven Integration section, not a new risk but worth restating as a build-order dependency (ingestion pipeline must exist before the skill-matching feature has real data to rank).

## Technical Research Recommendations

### Implementation Roadmap

1. Backend: scaffold FastAPI project with the layered/feature-domain structure above (`core/`, `auth/`, `video_progress/`, `skill_matching/`), async SQLAlchemy + asyncpg engine, Postgres+pgvector connection.
2. Backend: implement JWT-in-cookie auth, CORS config, centralized exception handlers.
3. Backend: implement video-progress endpoints (conditional-write persistence, per prior research) and skill/tutorial-matching endpoints (pgvector filter-then-rank query).
4. Frontend: scaffold React + TypeScript + Vite, install shadcn/ui + Tailwind, React Hook Form + Zod.
5. Frontend: build the video-progress capture adapter (YouTube IFrame polling, per prior research) wired to the backend endpoint, and the skill/tutorial recommendation UI.
6. Wire up auth flow (login form → JWT cookie → protected routes).
7. Add CI (GitHub Actions: backend + frontend jobs). Deployment/hosting is a separate, later decision — not part of this build order.

### Technology Stack Recommendations (summary)

Python 3.12+ / FastAPI (layered, feature-domain structure) + async SQLAlchemy 2.0 + asyncpg + PostgreSQL/pgvector + JWT-in-cookie auth | React + TypeScript + Vite + shadcn/ui + Tailwind + React Hook Form/Zod. Deployment/hosting: deferred, not decided in this research.

### Skill Development Requirements

Not applicable in a team-training sense (small/solo pilot build), but worth noting for the PRD/architecture handoff: this stack assumes working familiarity with FastAPI's dependency-injection model, async SQLAlchemy sessions, and pgvector's similarity-query syntax — all mainstream, well-documented technologies with strong 2026 tutorial coverage.

### Success Metrics and KPIs

Per the PRFAQ, success = the pilot's own stated goals (automatic progress tracking replacing manual chasing, coaching-only data use holding structurally, dashboard live by 13 July 2026) — not this research's concern directly, but the architecture above is built to not block any of them: the layered backend keeps the coaching-only guarantee enforceable in code.

---

## Technical Research Synthesis

### Executive Summary

This research delivers a complete technical blueprint for TalentPilot-AI's overall stack, building on top of (not replacing) the two decisions already locked in prior research: **YouTube IFrame API** for video-progress capture and **PostgreSQL + pgvector** for skill-to-tutorial matching. TalentPilot directed the remaining stack choice — **Python/FastAPI backend, React frontend, PostgreSQL database** — and this research confirms that choice is well-supported for 2026 and fits the project's shape: FastAPI's async, type-hint-native design pairs cleanly with pgvector/SQLAlchemy for the RAG-adjacent matching feature, while plain React (not Next.js) is the correct call for an internal, authenticated-only dashboard with no SEO requirement. The recommended architecture (layered FastAPI backend organized by feature domain, feature-based React frontend, JWT-in-cookie auth) is deliberately right-sized for a 5-week internal pilot — no microservices, no message queues — while still reflecting current, non-legacy practice. **Deployment/hosting is explicitly out of scope for this pass**, per TalentPilot's direction — deferred to a later decision rather than researched here.

### Key Findings Summary

1. **Backend:** FastAPI, layered by Router→Service→Repository within feature-domain folders (`video_progress/`, `skill_matching/`, `auth/`) — not a flat structure, and not split further into microservices.
2. **Frontend:** React + Vite (not Next.js), feature-based folders mirroring the backend's domains.
3. **Database access:** async SQLAlchemy 2.0 + asyncpg, kept separate from Pydantic API schemas (not merged via SQLModel) since the video-progress and pgvector tables have storage shapes that diverge from their API contracts.
4. **Auth:** JWT in an HTTP-only/Secure/SameSite cookie — not `localStorage`, not a heavier session-store framework.
5. **UI library:** shadcn/ui + Tailwind over MUI — better fit for code ownership and bundle size at this project's data density.
6. **Validation:** React Hook Form + Zod (client) and Pydantic (server) — both ends, server is the real guard.
7. **Critical structural requirement, not just a stack choice:** the PRFAQ's "coaching-only data" privacy guarantee must be enforced at the service/repository layer in code — the architecture research flags this as the one place a technology choice alone doesn't satisfy a product requirement; it needs deliberate implementation.

### Recommendations for Next Phase

- **Feed this research directly into `bmad-architecture`** — the folder structures, schema approach, and API/auth patterns above are concrete enough to seed architecture documents or PRD acceptance criteria directly, alongside the two prior narrow research docs (video embeds, RAG/pgvector).
- **Treat the Implementation Roadmap** above as the literal build order for the 5-week timeline.
- **Do not revisit the YouTube or pgvector decisions** without new evidence — both were already resolved in prior research and confirmed still correct here.
- **Carry the "coaching-only" enforcement requirement into architecture/PRD acceptance criteria explicitly** — it's a compliance-shaped requirement hiding inside a technical decision, easy to lose track of if only recorded as prose.

### Research Limitations

- Recommendations are synthesized from current (2026) industry blog/documentation sources, not hands-on benchmarking of this specific FastAPI+React+pgvector combination — appropriate for architectural direction, not a substitute for validating choices once code exists.
- No load/performance testing was conducted or is warranted for an internal pilot with a small known user base.
- Security research covered baseline web-app practices (JWT/CORS/validation) but not a full audit — consistent with the PRFAQ's explicit, conscious decision to defer formal legal/compliance review for this pilot's current scope.

### Source Documentation

All findings are cited inline within each section (Technology Stack Analysis, Integration Patterns Analysis, Architectural Patterns and Design, Implementation Approaches and Technology Adoption). Primary source types: FastAPI/React official-adjacent documentation and current (2026) technical blogs/guides on production FastAPI structure, React folder conventions, JWT/cookie auth, and pgvector integration.
