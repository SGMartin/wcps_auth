import asyncio
import abc
import hashlib
import logging
from enum import Enum

import sessions
import wcps_core

from database import get_user_details

logging.basicConfig(level=logging.INFO)

class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3

class PacketList:
    LAUNCHER = 0x1010
    SERVER_LIST = 0x1100
    NICKNAME = 0x1101
    TEST = 0x1102

async def start_listeners():
    try:
        client_server = await asyncio.start_server(User, "127.0.0.1", wcps_core.constants.Ports.AUTH_CLIENT)
        logging.info("Client listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.AUTH_CLIENT}")
        return

    try:
        server_listener = await asyncio.start_server(GameServer, "127.0.0.1", wcps_core.constants.Ports.INTERNAL)
        logging.info("Server listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.INTERNAL}")
        return

    await asyncio.gather(client_server.serve_forever(), server_listener.serve_forever())

class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.authorized = False
        self.username = "none"
        self.displayname = ""
        self.rights = 0
        self.session_id = -1
        self.reader = reader
        self.writer = writer
        self.xor_key_send = ClientXorKeys.SEND
        self.xor_key_receive = ClientXorKeys.RECEIVE
        self._connection = wcps_core.packets.Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))
        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                self.disconnect()
                break

            try:
                incoming_packet = wcps_core.packets.InPacket(buffer=data, receptor=self, xor_key=self.xor_key_receive)
                if incoming_packet.decoded_buffer:
                    logging.info(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = get_handler_for_packet(incoming_packet.packet_id)
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        logging.error(f"Unknown handler for packet {incoming_packet.packet_id}")
                else:
                    logging.error(f"Cannot decrypt packet {incoming_packet}")
                    self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
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
        self.xor_key_send = wcps_core.constants.InternalKeys.XOR_AUTH_SEND
        self.xor_key_receive = wcps_core.constants.InternalKeys.XOR_GAME_SEND
        self._connection = wcps_core.packets.Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))
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
            if not (0 <= max_players <= 3600):
                logging.error("max players must be in the 0-3600 range")
                self.disconnect()
            else:
                self._max_players = max_players
        except ValueError:
            logging.error("Cannot cast max players to int")
            self.disconnect()

    @property
    def current_players(self):
        return self._current_players

    @current_players.setter
    def current_players(self, players: int):
        try:
            players = int(players)
            if not (0 <= players <= self._max_players):
                logging.error("Invalid current players.")
                self.disconnect()
            else:
                self._current_players = players
        except ValueError:
            logging.error("Cannot cast current players to int")
            self.disconnect()

    def authorize(self, server_name: str, server_type: int, current_players: int, max_players: int) -> None:
        self.is_online = True

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                self.disconnect()
                break

            try:
                incoming_packet = wcps_core.packets.InPacket(buffer=data, receptor=self, xor_key=self.xor_key_receive)
                if incoming_packet.decoded_buffer:
                    logging.info(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = get_handler_for_packet(incoming_packet.packet_id)
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        logging.error(f"Unknown handler for packet {incoming_packet.packet_id}")
                else:
                    logging.error(f"Cannot decrypt packet {incoming_packet}")
                    self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()

class Launcher(wcps_core.packets.OutPacket):
    def __init__(self):
        super().__init__(packet_id=PacketList.LAUNCHER, xor_key=ClientXorKeys.SEND)
        self.fill(0, 7)

class ServerList(wcps_core.packets.OutPacket):
    class ErrorCodes(Enum):
        ILLEGAL_EXCEPTION = 70101
        NEW_NICKNAME = 72000
        WRONG_USER = 72010
        WRONG_PW = 72020
        ALREADY_LOGGED_IN = 72030
        CLIENT_VER_NOT_MATCH = 70301
        BANNED = 73050
        BANNED_TIME = 73020
        NOT_ACTIVE = 73040
        ENTER_ID_ERROR = 74010
        ENTER_PASSWORD_ERROR = 74020
        ERROR_NICKNAME = 74030
        NICKNAME_TAKEN = 74070
        NICKNAME_TOO_LONG = 74100
        ILLEGAL_NICKNAME = 74110

    def __init__(self, error_code: ErrorCodes, u=None):
        super().__init__(packet_id=PacketList.SERVER_LIST, xor_key=ClientXorKeys.SEND)
        if error_code != wcps_core.constants.ErrorCodes.SUCCESS or not u:
            self.append(error_code.value)
        else:
            self.append(1)
            self.append(1)  # ID
            self.append(0)  # unknown
            self.append(u.username)  # userid
            self.append("NULL")  # user PW. whatever is put here will be sent back if logged again
            self.append(u.displayname)
            self.append(u.session_id)  # current session ID
            self.append(0)  # unknown??? whatever is put here will be sent back if logged again
            self.append(0)  # unknown
            self.append(u.rights)  # rights
            self.append(1)  # Old servers say to append 1.11025 for PF20, but seems to be working atm.
            self.append(4)  # Maximum value of servers for 2008 client is 31

            for i in range(4):
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
            logging.error("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]

class LauncherHandler(PacketHandler):
    async def process(self, receptor) -> None:
        launch_packet = Launcher().build()
        await receptor.send(launch_packet)

class ServerListHandler(PacketHandler):
    async def process(self, user) -> None:
        input_id = self.get_block(2)
        input_pw = self.get_block(3)

        if len(input_id) < 3 or not input_id.isalnum():
            await user.send(ServerList(ServerList.ErrorCodes.ENTER_ID_ERROR).build())
            return

        if len(input_pw) < 3:
            await user.send(ServerList(ServerList.ErrorCodes.ENTER_PASSWORD_ERROR).build())
            return

        this_user = await get_user_details(input_id)

        if not this_user:
            await user.send(ServerList(ServerList.ErrorCodes.WRONG_USER).build())
            return

        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()

        if this_user["password"] != hashed_password:
            await user.send(ServerList(ServerList.ErrorCodes.WRONG_PW).build())
            return

        if this_user["rights"] == 0:
            await user.send(ServerList(ServerList.ErrorCodes.BANNED).build())
            return

        if input_id in sessions.GetAllAuthorized():
            await user.send(ServerList(ServerList.ErrorCodes.ALREADY_LOGGED_IN).build())
        else:
            user.authorize(username=input_id, displayname=this_user["displayname"], rights=this_user["rights"])
            sessions.Authorize(user)
            await user.send(ServerList(wcps_core.constants.ErrorCodes.SUCCESS, u=user).build())

class GameServerDetails(PacketHandler):
    async def process(self, server) -> None:
        displayname = self.get_block(0)
        server_type = self.get_block(1)
        current_players = self.get_block(2)
        max_players = self.get_block(3)

        if len(displayname) < 3 or not displayname.isalnum():
            logging.error("Invalid server name")
            return

        if not current_players.isdigit() or not max_players.isdigit():
            logging.error(f"Invalid value/s reported ¨{current_players}/{max_players}")
            return

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
                server_type=int(server_type),
                current_players=int(current_players),
                max_players=int(max_players),
            )

def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None


handlers = {
    PacketList.LAUNCHER: LauncherHandler,
    PacketList.SERVER_LIST: ServerListHandler,
}
