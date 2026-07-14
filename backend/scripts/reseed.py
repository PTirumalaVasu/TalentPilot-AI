"""Truncate seed-owned tables and re-run seeds from a clean state.

Usage: python -m scripts.reseed
"""
import asyncio

from sqlalchemy import text

from app.core.db import async_session_factory
from app.core.seeds import run_seeds

TABLES = (
    "assignment_overrides",
    "skill_progress",
    "assignments",
    "content_catalog",
    "accounts",
    "skills",
    "employees",
)


async def main() -> None:
    async with async_session_factory() as session:
        await session.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
        await session.commit()
        await run_seeds(session)
    print("Reseed complete")


if __name__ == "__main__":
    asyncio.run(main())
