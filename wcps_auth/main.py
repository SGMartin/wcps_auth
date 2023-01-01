import asyncio
import datetime
import socket
import time 
import threading

from networking import start_listeners
from networking import get_server_list

async def connect_to_game_server(server):
    server_address, server_port = server
    try:
        reader, writer = await asyncio.open_connection(server_address, server_port)
        writer.close()
    except:
        print(f"Cannot connect to {server_address}:{server_port}.")

async def main():
    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True 

    print("Retrieving game server master list...")
    all_game_servers = get_server_list("root", "root", "auth_test")
    print(f"Found {len(all_game_servers)} server/s to watch.")

    # Start the asyncio listeners
    asyncio.create_task(start_listeners())

    while(keep_running):
        print("Begin game server scan...")
        tasks = []
        for server in all_game_servers:
            task = asyncio.create_task(connect_to_game_server(server))
            tasks.append(task)
        await asyncio.gather(*tasks)
        
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
