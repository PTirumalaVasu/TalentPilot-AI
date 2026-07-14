"""Run idempotent seed scripts against the database (safe on first run or repeat runs).

Usage: python -m scripts.seed
"""
import asyncio

from app.core.db import async_session_factory
from app.core.seeds import run_seeds


async def main() -> None:
    async with async_session_factory() as session:
        await run_seeds(session)
    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(main())
