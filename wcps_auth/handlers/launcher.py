from .base import PacketHandler
from packets.packet_factory import PacketFactory
from packets.packet_list import PacketList

class LauncherHandler(PacketHandler):
    async def process(self, receptor) -> None:
        packet = PacketFactory.create_packet(PacketList.LAUNCHER)
        await receptor.send(packet.build())
