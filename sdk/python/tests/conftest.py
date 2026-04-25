"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def base_url():
    """Base URL for tests."""
    return "https://test.example.com"


@pytest.fixture
def api_token():
    """Test API token."""
    return "test-jwt-token"
