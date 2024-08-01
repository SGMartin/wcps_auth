from .base import PacketHandler
from wcps_auth.packets.packet_factory import PacketFactory
from wcps_auth.packets.packet_list import PacketList


class LauncherHandler(PacketHandler):
    async def process(self, receptor) -> None:
        packet = PacketFactory.create_packet(PacketList.LAUNCHER)
        await receptor.send(packet.build())
