import asyncio

from wcps_core.constants import Ports
from wcps_core.packets import InPacket, OutPacket, Connection

from .packets import Launcher

class User:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

        # Send a connection packet
        self._connection = Connection(xor_key=0x96).build()
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
                decoded = InPacket(data, xor_key=0xC3)
                print(decoded.packet_id)
           

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()


class UserListener:
    def __init__(self, address:str = "127.0.0.1"):
        self.server = asyncio.start_server(User, address, Ports.AUTH_CLIENT)

    async def begin_listening(self):
        async with await self.server as server:
            await server.serve_forever()


def start_user_listener():
    listener = UserListener()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listener.begin_listening())