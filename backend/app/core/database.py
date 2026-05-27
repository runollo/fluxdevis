"""Configuration de la base de donnees."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Engine asynchrone (pour FastAPI)
async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Engine synchrone (pour Alembic et scripts d'import)
sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=settings.DEBUG)
SyncSessionLocal = sessionmaker(sync_engine)


async def get_db() -> AsyncSession:
    """Dependency FastAPI pour obtenir une session BDD."""
    async with AsyncSessionLocal() as session:
        yield session
