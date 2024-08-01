import asyncio
import datetime
import logging
import time

from wcps_auth.database import get_server_list, run_pool
from wcps_auth.networking import start_listeners

# ASCII LOGO
WCPS_IMAGE = r"""

____    __    ____  ______ .______     _______.   
\   \  /  \  /   / /      ||   _  \   /       |   
 \   \/    \/   / |  ,----'|  |_)  | |   (----`   
  \            /  |  |     |   ___/   \   \       
   \    /\    /   |  `----.|  |   .----)   |      
    \__/  \__/     \______|| _|   |_______/       
                            by SGMartin      
"""
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main():
    print(WCPS_IMAGE)

    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True
    logging.info("Initializing database pool...")
    await run_pool()

    logging.info("Retrieving game server master list...")
    all_game_servers = await get_server_list()
    logging.info(f"Found {len(all_game_servers)} server/s to watch.")

    # Start the asyncio listeners
    asyncio.create_task(start_listeners())

    while keep_running:
        logging.info("Server is running. Awaiting connections...")
        # tasks = []
        # for server in all_game_servers:
        #     task = asyncio.create_task(connect_to_game_server(server))
        #     tasks.append(task)
        # await asyncio.gather(*tasks)

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
