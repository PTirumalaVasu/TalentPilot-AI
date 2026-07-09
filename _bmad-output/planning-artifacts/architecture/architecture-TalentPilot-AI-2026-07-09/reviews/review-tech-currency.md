# Reviewer: Technology currency & reality-check

**Verdict:** PASS with one flagged tension.

Every technology in the Stack table was web-researched with source verification in `technical-overall-stack-architecture-...-2026-07-08.md` (frontmatter `web_research_enabled: true`, `source_verification: true`) and the two prior narrow technical research docs. All are current, mainstream 2026 choices: FastAPI, async SQLAlchemy 2.0 + asyncpg, Postgres 16 + pgvector, React+TS+Vite, shadcn/ui+Tailwind, RHF+Zod, Pydantic, uvicorn, Docker Compose, pytest/httpx, Vitest/RTL. pgvector's exclusion of Neon/PlanetScale is correctly captured; now moot since deployment is out of scope.

## Findings

1. **[HIGH — needs user decision] Embedding model is a paid external API under a zero-budget + local-only constraint.** `text-embedding-3-small` is OpenAI's hosted API — it requires a billed OpenAI account and an outbound network call per ingest/query. This sits in tension with §9 "Zero budget: no new paid infrastructure" and the just-made "local working copy only" decision. Cost at pilot scale is genuinely pennies, but it is nonzero and non-local. A local open-weights model (`sentence-transformers`, e.g. `all-MiniLM-L6-v2`) runs free and fully offline, fits local-only cleanly, and the RAG research already named `sentence-transformers` as a Python-first option — at some cost to match quality vs OpenAI. This was "locked" in the addendum, so it is surfaced to the user rather than silently overridden.

No other currency issues. YouTube IFrame API free tier + ~100/day search.list quota correctly drives batch ingestion (AD-7).
