"""Main Viswall SDK client."""

from typing import Optional, Dict, Any, TypeVar
import httpx

from viswall.exceptions import (
    ViswallAPIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
    RateLimitError,
)
from viswall.resources import (
    AuthResource,
    InstancesResource,
    UsersResource,
    FirewallResource,
    RoutingResource,
    MailResource,
    MetricsResource,
    AuditResource,
    VPNResource,
    AssistantResource,
    GroupwareResource,
)

T = TypeVar("T")


class ViswallClient:
    """Resource-oriented client for the Viswall API.
    
    Args:
        base_url: Base URL of the Viswall instance (e.g., "https://viswall.example.com")
        token: JWT authentication token
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        client = ViswallClient(
            base_url="https://viswall.example.com",
            token="eyJhbGciOiJIUzI1NiIs..."
        )
        
        # Auth
        me = client.auth.me()
        
        # Instances
        instance = client.instances.create(name="edge-01", hostname="10.0.0.10")
        
        # Firewall
        rules = client.firewall.list_rules(instance_id=instance.id)
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        
        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=f"{self.base_url}/api/v1",
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        
        # Set auth header if token provided
        if token:
            self._client.headers["Authorization"] = f"Bearer {token}"
        
        # Initialize resources
        self.auth = AuthResource(self)
        self.instances = InstancesResource(self)
        self.users = UsersResource(self)
        self.firewall = FirewallResource(self)
        self.routing = RoutingResource(self)
        self.mail = MailResource(self)
        self.metrics = MetricsResource(self)
        self.audit = AuditResource(self)
        self.vpn = VPNResource(self)
        self.assistant = AssistantResource(self)
        self.groupware = GroupwareResource(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an HTTP request and handle errors.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (relative to /api/v1)
            params: Query parameters
            json: JSON request body
            
        Returns:
            Parsed JSON response
            
        Raises:
            ViswallAPIError: On API errors
            AuthenticationError: On 401/403
            NotFoundError: On 404
            ValidationError: On 422
            ServerError: On 5xx
        """
        response = self._client.request(
            method=method,
            url=path,
            params=params,
            json=json,
        )
        
        # Handle errors
        if response.status_code >= 400:
            self._handle_error(response)
        
        # Parse response
        if response.status_code == 204:
            return {}
        
        return response.json()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        try:
            body = response.json()
            message = body.get("detail", body.get("message", "Unknown error"))
        except Exception:
            message = response.text or "Unknown error"
            body = {}
        
        if response.status_code in (401, 403):
            raise AuthenticationError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code == 422:
            raise ValidationError(message, errors=body)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 0))
            raise RateLimitError(message, retry_after=retry_after)
        elif response.status_code >= 500:
            raise ServerError(message, status_code=response.status_code)
        else:
            raise ViswallAPIError(message, status_code=response.status_code, response_body=body)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "ViswallClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
