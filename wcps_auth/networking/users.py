import asyncio

from wcps_core.constants import Ports
from wcps_core.packets import OutPacket, Connection

class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

        # send a connection packet
        self._connection = Connection(xor_key = 0x96).build(encrypted=True)
        print(f"Sending {self._connection}")
        self.send(self._connection)
        

    def send(self, buffer):
        self.writer.write(buffer)

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
