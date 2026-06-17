from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://viswall:viswall@localhost/viswall"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database by running Alembic migrations."""
    from alembic.config import Config
    from alembic import command
    import os

    api_gateway_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "services", "api-gateway"
    )
    alembic_cfg = Config(os.path.join(api_gateway_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(api_gateway_dir, "migrations"))

    # Use sync API since Alembic doesn't have async API
    def run_upgrade():
        command.upgrade(alembic_cfg, "head")

    # Run in a thread pool since alembic is synchronous
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_upgrade)
