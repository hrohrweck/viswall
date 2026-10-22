"""Module entrypoint: python -m viswall_vpn_agent"""

import asyncio

from viswall_vpn_agent.main import main


if __name__ == "__main__":
    asyncio.run(main())
