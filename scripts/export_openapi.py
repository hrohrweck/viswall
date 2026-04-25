#!/usr/bin/env python3
"""
Export FastAPI OpenAPI spec to JSON.

Usage:
    python scripts/export_openapi.py

This script imports the FastAPI app and writes its OpenAPI schema
to services/api-gateway/openapi.json for SDK generation.
"""

import json
import sys
from pathlib import Path

# Add the repo root and api-gateway directory to the path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "services" / "api-gateway"))

from main import app


def export_openapi():
    openapi_schema = app.openapi()
    output_path = Path(__file__).parent.parent / "services" / "api-gateway" / "openapi.json"
    
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2, default=str)
    
    print(f"Exported OpenAPI spec to {output_path}")
    print(f"  Title: {openapi_schema.get('info', {}).get('title', 'N/A')}")
    print(f"  Version: {openapi_schema.get('info', {}).get('version', 'N/A')}")
    print(f"  Paths: {len(openapi_schema.get('paths', {}))}")
    print(f"  Components: {len(openapi_schema.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    export_openapi()
