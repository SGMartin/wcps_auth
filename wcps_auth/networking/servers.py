import asyncio

from wcps_core.constants import ServerTypes, InternalKeys
from wcps_core.packets import InPacket, OutPacket, Connection

import aiomysql

import networking.handlers

class GameServer:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.address, self.port = reader._transport.get_extra_info("peername")
        self.reader = reader
        self.writer = writer
        self.id = 0
        self._name = ""
        self._server_type = ServerTypes.NONE
        self._is_online = False
        self._current_players = 0
        self._max_players = 0

        ## Send a connection packet to incoming gameservers
        self.xor_key_send = InternalKeys.XOR_AUTH_SEND
        self.xor_key_recieve = InternalKeys.XOR_GAME_SEND

        self._connection = Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))

        # Start the listen loop
        asyncio.create_task(self.listen())

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def server_type(self):
        return self._server_type

    @server_type.setter
    def server_type(self, new_type: ServerTypes):
        self._server_type = ServerTypes

    @property
    def is_online(self):
        return self._is_online

    @is_online.setter
    def is_online(self, status: bool):
        self._is_online = status

    @property
    def max_players(self):
        return self._max_players

    @max_players.setter
    def max_players(self, max_players: int):
        try:
            max_players = int(max_players)
            if max_players not in range(0, 3601):
                self.disconnect()
                print("max players must be in the 0-3600 range")
            else:
                self._max_players = max_players
        except ValueError:
            print("Cannot cast max players to int")
            self.disconnect()

    @property
    def current_players(self):
        return self._current_players

    @current_players.setter
    def current_players(self, players: int):
        try:
            players = int(players)
            if players not in range(0, self._max_players):
                print("Invalid current players.")
                self.disconnect()
            else:
                self._current_players = players
        except ValueError:
            print("Cannot cast current players to int")
            self.disconnect()

    def authorize(self, server_name:str, server_type:int, current_players:int, max_players:int) -> None:
        self.is_online = True

    async def listen(self):
        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                self.disconnect()
                break
            else:
                #try:
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
                        else:
                            print(f"Unknown handler for packet {incoming_packet.packet_id}")
                    else:
                        print(f"Cannot decrypt packet {incoming_packet}")
                        self.disconnect()

                #except Exception as e:
                 #   print(f"Bad packet {incoming_packet}")
                 #   self.disconnect()
                 #   break


    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()
