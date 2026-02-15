# Viswall API Gateway Tests

This directory contains tests for the API Gateway service.

## Running Tests

```bash
# From services/api-gateway directory
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html

# Specific test file
pytest tests/test_auth.py -v
```

## Test Structure

- `test_main.py` - Main application tests (health, API info)
- `test_auth.py` - Authentication tests
- `test_instances.py` - Instance management tests
- `test_users.py` - User management tests
- `conftest.py` - Shared fixtures and configuration

## Fixtures Needed

- `client` - Async HTTP client
- `db_session` - Database session for tests
- `test_user` - Pre-created test user
- `test_admin` - Pre-created admin user
