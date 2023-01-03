import asyncio

from wcps_core.constants import Ports
from wcps_core.packets import InPacket, OutPacket, Connection

import sessions
import networking.packets
import networking.handlers


class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # Authorization data
        self.authorized = False
        self.username = "none"
        self.displayname = ""
        self.rights = 0
        self.session_id = -1

        # connection data
        self.reader = reader
        self.writer = writer
        # Send a connection packet
        self.xor_key_send = networking.packets.ClientXorKeys.Send
        self.xor_key_recieve = networking.packets.ClientXorKeys.Recieve

        self._connection = Connection(xor_key=self.xor_key_send).build()
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
                    buffer=data, receptor=self, xor_key=self.xor_key_recieve
                )
                if incoming_packet.decoded_buffer:
                    print(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = networking.handlers.get_handler_for_packet(
                        incoming_packet.packet_id
                    )
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()
        if self.authorized:
            sessions.Remove(self)


    def authorize(self, username:str, displayname:str, rights:int):
        self.username = username
        self.displayname = displayname
        self.rights = rights
        self.authorized = True
