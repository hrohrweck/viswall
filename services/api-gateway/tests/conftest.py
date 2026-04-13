import sys
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

_api_gw_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = os.path.dirname(os.path.dirname(_api_gw_dir))

for p in [_project_root, _api_gw_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
