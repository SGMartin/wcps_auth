import asyncio

from wcps_core.constants import ServerTypes, InternalKeys
from wcps_core.packets import InPacket, OutPacket

import mysql.connector

class GameServer:
    def __init__(
        self,
        reader:asyncio.StreamReader,
        writer:asyncio.StreamWriter,
        name: str = "",
        server_type: ServerTypes = ServerTypes.NONE,
        online: bool = False,
        current_players: int = 3600,
        max_players: int = 3600
    ):
        self.address, self.port = reader._transport.get_extra_info("peername")
        self.reader = reader
        self.writer = writer
        self.id = 0
        self._name = name
        self._server_type = server_type
        self._is_online = online
        self._current_players = current_players
        self._max_players = max_players

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
    def max_players(self, max_players:int):
        try:
            max_players = int(max_players)
            if max_players not in range(0, 3601):
                # TODO: HANDLE THIS
                print("max players must be in the 0-3600 range")
            else:
                self._max_players = max_players
        except ValueError: 
            print("Cannot cast max players to int")

    @property
    def current_players(self):
        return self._current_players
    
    @current_players.setter
    def current_players(self, players:int):
        try:
            players = int(players)
            if players not in range(0, self._max_players):
                # TODO: handle this
                print("Invalid current players.")
            else:
                self._current_players = players
        except ValueError:
            print("Cannot cast current players to int")
    

    async def listen(self):
        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                print(f"No data recieved... disconnecting.")
                self.disconnect()
                break
            else:
                decoded = InPacket(data, xor_key=InternalKeys.XOR_GAME_SEND)
                print(decoded.packet_id)
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


def generate_servers_addresses(query_results: list) -> list:

    server_list = []
    for candidate_server in query_results:
        ## Each result is a tuple of 4 fields
        server_id, addr, port, active = candidate_server
        server_list.append((addr, port))

    return server_list


def get_server_list(user: str, password: str, database: str) -> list[GameServer]:
    # Connect to the database
    conn = mysql.connector.connect(
        host="localhost", port=3306, user=user, password=password, database=database
    )

    try:
        # Create a cursor
        cursor = conn.cursor()

        # Execute the query
        query = "SELECT * FROM servers WHERE active = 1"
        cursor.execute(query)

        # Fetch the results
        result = cursor.fetchall()

        # Close the cursor
        cursor.close()

        all_servers = generate_servers_addresses(result)
        return all_servers
    except mysql.connector.Error as err:
        # Print the error message and exit
        print(f"An error occurred when executing the query: {err}")
        return None
    finally:
        # Close the connection
        conn.close()