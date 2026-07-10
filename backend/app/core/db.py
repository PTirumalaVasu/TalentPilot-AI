from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped session: commits on successful completion of the route
    handler, rolls back if the handler raises. Establishes the app-wide
    commit convention — individual repository/service functions should flush,
    not commit, and rely on this to persist the transaction."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
