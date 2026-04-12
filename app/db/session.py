import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db import models  # noqa: F401
from app.utils.config import Settings


class DatabaseManager:
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_async_engine(
            settings.postgres_dsn,
            echo=settings.is_debug,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_schema(self, attempts: int = 10, delay_seconds: int = 2) -> None:
        for attempt in range(1, attempts + 1):
            try:
                async with self.engine.begin() as connection:
                    await connection.run_sync(Base.metadata.create_all)
                return
            except Exception:
                if attempt == attempts:
                    raise
                await asyncio.sleep(delay_seconds)

    async def dispose(self) -> None:
        await self.engine.dispose()
