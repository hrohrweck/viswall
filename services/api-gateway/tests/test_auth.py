import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_missing_fields(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code in (400, 401, 422)


async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "wrongpass"
    })
    assert response.status_code in (401, 500)
