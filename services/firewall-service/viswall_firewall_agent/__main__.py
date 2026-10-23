"""Module entrypoint: python -m viswall_firewall_agent"""

import asyncio

from viswall_firewall_agent.main import main


if __name__ == "__main__":
    asyncio.run(main())
