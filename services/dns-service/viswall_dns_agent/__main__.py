"""Uvicorn entrypoint: python -m viswall_dns_agent"""

from __future__ import annotations

import uvicorn

from viswall_dns_agent.config import load_config


def main() -> None:
    config = load_config()
    uvicorn.run(
        "viswall_dns_agent.api:app",
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
