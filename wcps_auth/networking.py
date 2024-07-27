import asyncio
import abc
import hashlib
from enum import Enum

import sessions
import wcps_core

from database import get_user_details


class ClientXorKeys:
    Send = 0x96
    Recieve = 0xC3


class PacketList:
    Launcher = 0x1010
    ServerList = 0x1100
    NickName = 0x1101
    Test = 0x1102


async def start_listeners():
    try:
        client_server = await asyncio.start_server(
            User, "127.0.0.1", wcps_core.constants.Ports.AUTH_CLIENT
        )
        print("Client listener started.")
    except OSError:
        print(f"Failed to bind to port {wcps_core.constants.Ports.AUTH_CLIENT}")
        return

    try:
        server_listener = await asyncio.start_server(
            GameServer, "127.0.0.1", wcps_core.constants.Ports.INTERNAL
        )
        print("Server listener started.")
    except OSError:
        print(f"Failed to bind to port {wcps_core.constants.Ports.INTERNAL}")
        return

    # Create tasks to run the servers in the background
    client_server_task = asyncio.create_task(client_server.serve_forever())
    server_listener_task = asyncio.create_task(server_listener.serve_forever())

    # Wait for the tasks to complete
    await asyncio.gather(client_server_task, server_listener_task)


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
        self.xor_key_send = ClientXorKeys.Send
        self.xor_key_recieve = ClientXorKeys.Recieve

        self._connection = wcps_core.packets.Connection(
            xor_key=self.xor_key_send
        ).build()
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
                try:
                    incoming_packet = wcps_core.packets.InPacket(
                        buffer=data, receptor=self, xor_key=self.xor_key_recieve
                    )
                    if incoming_packet.decoded_buffer:
                        print(f"IN:: {incoming_packet.decoded_buffer}")
                        handler = get_handler_for_packet(incoming_packet.packet_id)
                        if handler:
                            asyncio.create_task(handler.handle(incoming_packet))
                        else:
                            print(f"Unknown handler for packet {handler.packet_id}")
                    else:
                        print(f"Cannot decrypt packet {incoming_packet}")
                        self.disconnect()

                except Exception as e:
                    print(f"Bad packet listenning {incoming_packet}")
                    self.disconnect()
                    break

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

    def authorize(self, username: str, displayname: str, rights: int):
        self.username = username
        self.displayname = displayname
        self.rights = rights
        self.authorized = True


class GameServer:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.address, self.port = reader._transport.get_extra_info("peername")
        self.reader = reader
        self.writer = writer
        self.id = 0
        self._name = ""
        self._server_type = wcps_core.constants.ServerTypes.NONE
        self._is_online = False
        self._current_players = 0
        self._max_players = 0

        ## Send a connection packet to incoming gameservers
        self.xor_key_send = wcps_core.constants.InternalKeys.XOR_AUTH_SEND
        self.xor_key_recieve = wcps_core.constants.InternalKeys.XOR_GAME_SEND

        self._connection = wcps_core.packets.Connection(
            xor_key=self.xor_key_send
        ).build()
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
    def server_type(self, new_type: wcps_core.constants.ServerTypes):
        self._server_type = new_type

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

    def authorize(
        self, server_name: str, server_type: int, current_players: int, max_players: int
    ) -> None:
        self.is_online = True

    async def listen(self):
        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                self.disconnect()
                break
            else:
                # try:
                incoming_packet = wcps_core.packets.InPacket(
                    buffer=data, receptor=self, xor_key=self.xor_key_recieve
                )
                if incoming_packet.decoded_buffer:
                    print(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = get_handler_for_packet(incoming_packet.packet_id)
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        print(f"Unknown handler for packet {incoming_packet.packet_id}")
                else:
                    print(f"Cannot decrypt packet {incoming_packet}")
                    self.disconnect()

            # except Exception as e:
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


class Launcher(wcps_core.packets.OutPacket):
    def __init__(self):
        super().__init__(packet_id=PacketList.Launcher, xor_key=ClientXorKeys.Send)
        self.fill(0, 7)


class ServerList(wcps_core.packets.OutPacket):
    class ErrorCodes(Enum):
        IllegalException = 70101
        NewNickname = 72000
        WrongUser = 72010
        WrongPW = 72020
        AlreadyLoggedIn = 72030
        ClientVerNotMatch = 70301
        Banned = 73050
        BannedTime = 73020
        NotActive = 73040
        EnterIDError = 74010
        EnterPasswordError = 74020
        ErrorNickname = 74030
        NicknameTaken = 74070
        NicknameToLong = 74100
        IlligalNickname = 74110

    def __init__(self, error_code: ErrorCodes, u=None):
        super().__init__(packet_id=PacketList.ServerList, xor_key=ClientXorKeys.Send)
        if error_code != wcps_core.constants.ErrorCodes.SUCCESS or not u:
            self.append(error_code.value)
        else:
            self.append(1)
            self.append(1)  # ID
            self.append(0)  # unknown
            self.append(u.username)  # userid
            self.append(
                "NULL"
            )  # user PW. whatever is put here will be sent back if logged again
            self.append(u.displayname)
            self.append(u.session_id)  ## current session ID
            self.append(
                0
            )  # unknown??? whatever is put here will be sent back if logged again
            self.append(0)  # unknown
            self.append(u.rights)  # rights
            self.append(
                1
            )  # Olds servers say to append 1.11025 for PF20, but seems to be working atm.
            self.append(4)  ## Maximum value of servers for 2008 client is 31

            for i in range(0, 4):
                self.append(i)  # Server ID
                self.append(f"Test {i}")
                self.append("0.0.0.0.0")
                self.append("5340")
                self.append(100)
                self.append(1)

            self.fill(-1, 4)  # unknown
            self.append(0)  # unknown
            self.append(0)  # unknown


class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: wcps_core.packets.InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, User) or isinstance(receptor, GameServer):
            await self.process(receptor)
        else:
            print("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]


class LauncherHandler(PacketHandler):
    async def process(self, receptor) -> None:
        launch_packet = Launcher().build()
        asyncio.create_task(receptor.send(launch_packet))


class ServerListHandler(PacketHandler):
    async def process(self, user) -> None:
        input_id = self.get_block(2)
        input_pw = self.get_block(3)
        is_new_display_name = False

        # Invalid username.
        if len(input_id) < 3 or not input_id.isalnum():
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.EnterIDError).build())
            )
            return
        # Invalid password: too short.
        if len(input_pw) < 3:
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.EnterPasswordError).build())
            )
            return

        # Query the database for the login details
        this_user = await get_user_details(input_id)
        # User id does not exists
        if not this_user:
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.WrongUser).build())
            )
            return

        ## hash the password
        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()

        # Wrong password.
        if this_user["password"] != hashed_password:
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.WrongPW).build())
            )
            return

        # Banned user
        if this_user["rights"] == 0:
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.Banned).build())
            )
            return

        # This user is already logged in
        if input_id in sessions.GetAllAuthorized():
            asyncio.create_task(
                user.send(ServerList(ServerList.ErrorCodes.AlreadyLoggedIn).build())
            )
        else:
            # Log the user and authorize it
            user.authorize(
                username=input_id,
                displayname=this_user["displayname"],
                rights=this_user["rights"],
            )
            sessions.Authorize(user)
            asyncio.create_task(
                user.send(
                    ServerList(wcps_core.constants.ErrorCodes.SUCCESS, u=user).build()
                )
            )


class GameServerDetails(PacketHandler):
    async def process(self, server) -> None:
        # Display name of the server
        displayname = self.get_block(0)
        # To be cast to ServerTypes, indicates which kind of server it is
        server_type = self.get_block(1)
        # Current player load
        current_players = self.get_block(2)
        # Max server load. Client is limited to 3600 by default
        max_players = self.get_block(3)

        # TODO: build internal packet for this
        if len(displayname < 3) or not displayname.isalnum():
            print("Invalid server name")
            return

        if not current_players.isdigit() or not max_players.isdigit():
            print(f"Invalid value/s reported ¨{current_players}/{max_players}")
            return

        # TODO: This could/should be moved to config.
        valid_servers = [
            wcps_core.constants.ServerTypes.ENTIRE,
            wcps_core.constants.ServerTypes.ADULT,
            wcps_core.constants.ServerTypes.CLAN,
            wcps_core.constants.ServerTypes.TEST,
            wcps_core.constants.ServerTypes.DEVELOPMENT,
            wcps_core.constants.ServerTypes.TRAINEE,
        ]

        if server_type.isdigit() and int(server_type) in valid_servers:
            server.authorize(
                server_name=displayname,
                server_type=server_type,
                current_players=int(current_players),
                max_players=int(max_players),
            )


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        print(f"Unknown packet ID {packet_id}")
        return None


handlers = {}
handlers[PacketList.Launcher] = LauncherHandler
handlers[PacketList.ServerList] = ServerListHandler
