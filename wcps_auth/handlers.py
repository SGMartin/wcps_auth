import abc
import asyncio
import hashlib

from wcps_core.packets import InPacket
from wcps_core.constants import ErrorCodes
from wcps_core.constants import ServerTypes

import sessions
import networking.database
import networking.packets
import networking.servers
import networking.users


class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, networking.users.User) or isinstance(
            receptor, networking.servers.GameServer
        ):
            await self.process(receptor)
        else:
            print("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]


class LauncherHandler(PacketHandler):
    async def process(self, receptor) -> None:
        launch_packet = networking.packets.Launcher().build()
        asyncio.create_task(receptor.send(launch_packet))


class ServerListHandler(PacketHandler):
    async def process(self, user) -> None:
        input_id = self.get_block(2)
        input_pw = self.get_block(3)
        is_new_display_name = False

        # Invalid username.
        if len(input_id) < 3 or not input_id.isalnum():
            asyncio.create_task(
                user.send(
                    networking.packets.ServerList(
                        networking.packets.ServerList.ErrorCodes.EnterIDError
                    ).build()
                )
            )
            return
        # Invalid password: too short.
        if len(input_pw) < 3:
            asyncio.create_task(
                user.send(
                    networking.packets.ServerList(
                        networking.packets.ServerList.ErrorCodes.EnterPasswordError
                    ).build()
                )
            )
            return

        # Query the database for the login details
        this_user = await networking.database.get_user_details(input_id)
        # User id does not exists
        if not this_user:
            asyncio.create_task(
                user.send(
                    networking.packets.ServerList(
                        networking.packets.ServerList.ErrorCodes.WrongUser
                    ).build()
                )
            )
            return

        ## hash the password
        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()

        # Wrong password.
        if this_user["password"] != hashed_password:
            asyncio.create_task(
                user.send(
                networking.packets.ServerList(networking.packets.ServerList.ErrorCodes.WrongPW).build()
                )
            )
            return
        
        # Banned user
        if this_user["rights"] == 0:
            asyncio.create_task(
                user.send(networking.packets.ServerList(networking.packets.ServerList.ErrorCodes.Banned).build())
            )
            return

        # This user is already logged in
        if input_id in sessions.GetAllAuthorized():
            asyncio.create_task(
                user.send(networking.packets.ServerList(networking.packets.ServerList.ErrorCodes.AlreadyLoggedIn).build())
            )
        else:
            # Log the user and authorize it
            user.authorize(username=input_id, displayname=this_user["displayname"], rights=this_user["rights"])
            sessions.Authorize(user)
            asyncio.create_task(
                user.send(networking.packets.ServerList(ErrorCodes.SUCCESS, u = user).build())
            )

class GameServerDetails(PacketHandler):
    async def process(self, server) -> None:
        # Display name of the server
        displayname = self.get_block(0)
        # To be cast to ServerTypes, indicates which kind of server it is
        server_type = self.get_block(1)
        # Current player load
        current_players = self.get_block(2)
        # Max server load. Client is limited to 3600 by default
        max_players = self.get_block(3)

        # TODO: build internal packet for this
        if len(displayname < 3) or not displayname.isalnum():
            print("Invalid server name")
            return

        if not current_players.isdigit() or not max_players.isdigit():
            print(f"Invalid value/s reported ¨{current_players}/{max_players}")
            return 
        
        # TODO: This could/should be moved to config.
        valid_servers = [
            ServerTypes.ENTIRE,
            ServerTypes.ADULT,
            ServerTypes.CLAN,
            ServerTypes.TEST,
            ServerTypes.DEVELOPMENT,
            ServerTypes.TRAINEE
        ]

        if server_type.isdigit() and int(server_type) in valid_servers:
            server.authorize(
                server_name=displayname,
                server_type=server_type,
                current_players=int(current_players),
                max_players=int(max_players)
                )


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        print(f"Unknown packet ID {packet_id}")
        return None


handlers = {}
handlers[networking.packets.PacketList.Launcher] = LauncherHandler
handlers[networking.packets.PacketList.ServerList] = ServerListHandler
