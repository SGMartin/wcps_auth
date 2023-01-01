import asyncio

from wcps_core.constants import Ports
from wcps_core.packets import InPacket, OutPacket, Connection

from .packets import Launcher, ClientXorKeys

class User:
    def __init__(self, reader, writer):
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
                print(f"No data recieved... disconnecting.")
                self.disconnect()
                break
            else:
                decoded = InPacket(data, xor_key=ClientXorKeys.Recieve)
                print(decoded.packet_id)
                asyncio.create_task(self.send(Launcher().build()))
                print("HANDLERS HERE!")

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()