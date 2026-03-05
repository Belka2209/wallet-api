from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()