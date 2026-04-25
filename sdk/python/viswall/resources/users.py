"""Users resource."""

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from viswall.client import ViswallClient


class UsersResource:
    """User management operations."""

    def __init__(self, client: "ViswallClient"):
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        return self._client._request("GET", "/users")

    def create(self, username: str, email: str, password: str, **kwargs: Any) -> Dict[str, Any]:
        """Create a new user (admin only).
        
        Args:
            username: Username
            email: Email address
            password: Initial password
            **kwargs: Additional fields (role, instances, etc.)
            
        Returns:
            Created user
        """
        data = {"username": username, "email": email, "password": password, **kwargs}
        return self._client._request("POST", "/users", json=data)

    def get(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID."""
        return self._client._request("GET", f"/users/{user_id}")

    def update(self, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update user."""
        return self._client._request("PATCH", f"/users/{user_id}", json=kwargs)

    def delete(self, user_id: int) -> None:
        """Delete user."""
        self._client._request("DELETE", f"/users/{user_id}")

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        return self._client._request(
            "POST",
            f"/users/{user_id}/change-password",
            json={"current_password": current_password, "new_password": new_password},
        )
