import abc
import asyncio
from wcps_core.packets import InPacket

import networking.packets
import networking.servers
import networking.users


class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    def handle(self, packet_to_handle):
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, networking.users.User) or isinstance(
            receptor, networking.servers.GameServer
        ):
            self.process(receptor)
        else:
            print("No receptor for this packet!")

    @abc.abstractmethod
    def process(self, user_or_server):
        pass


class LauncherHandler(PacketHandler):
    def process(self, receptor):
        launch_packet = networking.packets.Launcher().build()
        asyncio.create_task(receptor.send(launch_packet))


class ServerListHandler(PacketHandler):
    def process(self, user):
        print("hre")


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        print(f"Unknown packet ID {packet_id}")
        return None


handlers = {}
handlers[networking.packets.PacketList.Launcher] = LauncherHandler
