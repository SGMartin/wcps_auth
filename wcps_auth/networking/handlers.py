import abc
import asyncio
import hashlib

from wcps_core.packets import InPacket
from wcps_core.constants import ErrorCodes

import networking.database
import networking.packets
import networking.servers
import networking.users


class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle):
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

    def get_block(self, block_id: int):
        return self.in_packet.blocks[block_id]


class LauncherHandler(PacketHandler):
    async def process(self, receptor):
        launch_packet = networking.packets.Launcher().build()
        asyncio.create_task(receptor.send(launch_packet))


class ServerListHandler(PacketHandler):
    async def process(self, user):
        input_id = self.get_block(2)
        input_pw = self.get_block(3)
        is_new_display_name = False

        if len(input_id) < 3 or not input_id.isalnum():
            asyncio.create_task(
                user.send(
                    networking.packets.ServerList(
                        networking.packets.ServerList.ErrorCodes.EnterIDError
                    ).build()
                )
            )
            return

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

        if this_user["password"] == hashed_password:
            print("Correct password")
            if this_user["rights"] == 0:
                asyncio.create_task(
                    user.send(
                        networking.packets.ServerList(
                            networking.packets.ServerList.ErrorCodes.Banned
                        ).build()
                    )
                )
            else:
                # TODO: check if online and proceed
                asyncio.create_task(
                    user.send(
                        networking.packets.ServerList(ErrorCodes.SUCCESS, user).build()
                    )
                )
        else:
            asyncio.create_task(
                user.send(
                    networking.packets.ServerList(
                        networking.packets.ServerList.ErrorCodes.WrongPW
                    ).build()
                )
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
