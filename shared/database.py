from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# Environment variable is read lazily so that importing this module (e.g. for
# OpenAPI export or SDK generation) does not crash when DATABASE_URL is unset.
# The check fires on first real DB access instead.
engine = None
AsyncSessionLocal = None


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return url


def _ensure_engine():
    """Create the async engine and session factory on first use."""
    global engine, AsyncSessionLocal
    if engine is None:
        url = _get_database_url()
        engine = create_async_engine(
            url,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            future=True,
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


async def get_db():
    _ensure_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database by running Alembic migrations."""
    _ensure_engine()
    from alembic.config import Config
    from alembic import command

    here = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.dirname(here)
    _candidates = [
        os.path.join(app_root, "services", "api-gateway"),
        app_root,
    ]
    api_gateway_dir = next(
        (d for d in _candidates if os.path.exists(os.path.join(d, "alembic.ini"))),
        app_root,
    )
    alembic_cfg = Config(os.path.join(api_gateway_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(api_gateway_dir, "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", _get_database_url())

    # Use sync API since Alembic doesn't have async API
    def run_upgrade():
        command.upgrade(alembic_cfg, "head")

    # Run in a thread pool since alembic is synchronous
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_upgrade)
