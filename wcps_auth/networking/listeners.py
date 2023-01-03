import asyncio
from wcps_core.constants import Ports

import networking.users
import networking.servers


async def start_listeners():
    try:
        client_server = await asyncio.start_server(
            networking.users.User, "127.0.0.1", Ports.AUTH_CLIENT
        )
        print("Client listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.AUTH_CLIENT}")
        return

    try:
        server_listener = await asyncio.start_server(
            networking.servers.GameServer, "127.0.0.1", 5013
        )
        print("Server listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.OTHER_SERVER}")
        return

    # Create tasks to run the servers in the background
    client_server_task = asyncio.create_task(client_server.serve_forever())
    server_listener_task = asyncio.create_task(server_listener.serve_forever())

    # Wait for the tasks to complete
    await asyncio.gather(client_server_task, server_listener_task)
