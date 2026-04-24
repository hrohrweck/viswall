import sys
import os
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Set test environment variables BEFORE any other imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://viswall:viswall@localhost/viswall_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

_api_gw_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = os.path.dirname(os.path.dirname(_api_gw_dir))

for p in [_project_root, _api_gw_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app


@pytest_asyncio.fixture(scope="session")
async def client():
    # Give database service time to initialize
    await asyncio.sleep(3)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
