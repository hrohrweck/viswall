from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import os

_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://viswall:viswall@localhost/viswall"
)

engine = create_async_engine(
    _DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    # Recreate engine if DATABASE_URL has changed (for testing)
    global engine, AsyncSessionLocal
    current_url = os.getenv("DATABASE_URL", _DATABASE_URL)
    if current_url != _DATABASE_URL:
        engine = create_async_engine(
            current_url,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            future=True
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    from shared.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
