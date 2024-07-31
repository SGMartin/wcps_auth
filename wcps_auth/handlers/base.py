import abc
import asyncio

from wcps_core.packets import InPacket

from wcps_auth.entities import BaseNetworkEntity

class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, BaseNetworkEntity):
            await self.process(receptor)
        else:
            logging.error("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]
