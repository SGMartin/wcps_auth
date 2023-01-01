import asyncio
from networking.users import User
from networking.servers import GameServer
from wcps_core.constants import Ports


async def start_listeners():
    try:
        client_server = await asyncio.start_server(User, "127.0.0.1", Ports.AUTH_CLIENT)
        print("Client listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.CLIENT_SERVER}")
        return

    try:
        server_listener = await asyncio.start_server(GameServer, "127.0.0.1", 5013)
        print("Server listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.OTHER_SERVER}")
        return

    # Create tasks to run the servers in the background
    client_server_task = asyncio.create_task(client_server.serve_forever())
    server_listener_task = asyncio.create_task(server_listener.serve_forever())

    # Wait for the tasks to complete
    await asyncio.gather(client_server_task, server_listener_task)
