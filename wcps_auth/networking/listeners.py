import asyncio
from networking.users import User
from wcps_core.constants import Ports
#from networking.servers import GameServer

async def start_listeners():
    try:
        client_server = await asyncio.start_server(User, "127.0.0.1", Ports.CLIENT_SERVER)
        print("Client listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.CLIENT_SERVER}")
        return

    try:
        server_listener = await asyncio.start_server(User, "127.0.0.1", Ports.INTERNAL)
        print("Server listener started.")
    except OSError:
        print(f"Failed to bind to port {Ports.OTHER_SERVER}")
        return

    async with client_server, server_listener:
        # Await the serve_forever method to handle incoming connections
        await asyncio.gather(client_server.serve_forever(), server_listener.serve_forever())
