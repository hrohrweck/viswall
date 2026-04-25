"""Viswall SDK exceptions."""

from typing import Optional, Dict, Any


class ViswallError(Exception):
    """Base exception for all Viswall SDK errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ViswallAPIError(ViswallError):
    """Raised when the Viswall API returns an error response."""
    
    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body or {}

    def __str__(self) -> str:
        return f"API Error {self.status_code}: {self.message}"


class AuthenticationError(ViswallAPIError):
    """Raised when authentication fails (401/403)."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class NotFoundError(ViswallAPIError):
    """Raised when a resource is not found (404)."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(ViswallAPIError):
    """Raised when request validation fails (422)."""
    
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422)
        self.errors = errors or {}


class ServerError(ViswallAPIError):
    """Raised when the server returns a 5xx error."""
    
    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class RateLimitError(ViswallAPIError):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
