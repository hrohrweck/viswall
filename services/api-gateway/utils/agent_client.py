import httpx
import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.models import Instance

logger = logging.getLogger(__name__)

DEFAULT_AGENT_TIMEOUT = 30.0


class AgentClientError(Exception):
    pass


class AgentConnectionError(AgentClientError):
    pass


class AgentResponseError(AgentClientError):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


async def get_instance_endpoint(db: AsyncSession, instance_id: int) -> str:
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise AgentClientError(f"Instance {instance_id} not found")
    if not instance.api_endpoint:
        raise AgentClientError(f"Instance {instance_id} has no api_endpoint configured")
    return instance.api_endpoint.rstrip("/")


async def agent_request(
    db: AsyncSession,
    instance_id: int,
    method: str,
    path: str,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = DEFAULT_AGENT_TIMEOUT,
) -> Dict[str, Any]:
    endpoint = await get_instance_endpoint(db, instance_id)
    url = f"{endpoint}{path}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                json=json_data,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to agent at {url}: {e}")
            raise AgentConnectionError(f"Cannot connect to agent at {url}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent returned error {e.response.status_code} for {url}: {e.response.text}")
            raise AgentResponseError(
                f"Agent returned error {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to agent at {url}: {e}")
            raise AgentConnectionError(f"Timeout connecting to agent at {url}")
        except Exception as e:
            logger.error(f"Unexpected error calling agent at {url}: {e}")
            raise AgentClientError(f"Unexpected error calling agent: {e}")
