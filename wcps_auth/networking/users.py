import asyncio

from wcps_core.constants import Ports
from wcps_core.packets import InPacket, OutPacket, Connection

from .packets import ClientXorKeys
from .handlers import get_handler_for_packet

class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        # Send a connection packet
        self._connection = Connection(xor_key=ClientXorKeys.Send).build()
        asyncio.create_task(self.send(self._connection))

        # Start the listen loop
        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                self.disconnect()
                break
            else:
                incoming_packet = InPacket(
                    buffer=data, receptor=self, xor_key=ClientXorKeys.Recieve
                )
                if incoming_packet.decoded_buffer:
                    handler = get_handler_for_packet(incoming_packet.packet_id)
                    if handler:
                        handler.handle(incoming_packet)

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()
