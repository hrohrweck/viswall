"""Pytest configuration for CLI tests."""

import pytest


@pytest.fixture
def httpx_mock(httpx_mock):
    """Override httpx_mock to clear existing responses."""
    httpx_mock.reset()
    return httpx_mock
