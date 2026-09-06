import sys
import os
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

import routers.dns as _dns_router
from main import app


@pytest_asyncio.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def no_dns_agent_dispatch(monkeypatch):
    """Keep unit tests off the real agent/session: DNS mutations schedule a
    background push that would otherwise dial DATABASE_URL. Tests that assert
    dispatch behavior re-patch routers.dns.apply_dns_config_task themselves."""

    async def _noop(instance_id):
        return None

    monkeypatch.setattr(_dns_router, "apply_dns_config_task", _noop)
