import asyncio
import abc
import hashlib
import logging
from enum import Enum

import sessions
import wcps_core.constants
import wcps_core.packets

from database import get_user_details, get_server_list
from sessions import SessionManager

logging.basicConfig(level=logging.INFO)

class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3

class PacketList:
    INTERNALGAMEAUTHENTICATION = wcps_core.packets.PacketList.GameServerAuthentication
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
                await self.disconnect()
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
                    await self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                await self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
            await self.disconnect()

    async def disconnect(self):
        self.writer.close()
        if self.authorized:
            self.authorized = False
            ## Clear the session just in case
            session_manager = SessionManager()

            if await session_manager.is_user_authorized(self.username):
                await session_manager.unauthorize_user(self.username)

    
    async def authorize(self, username: str, displayname: str, rights: int):
        self.username = username
        self.displayname = displayname
        self.rights = rights
        self.authorized = True
        session_manager = SessionManager()
        session_id = await session_manager.authorize_user(self)
        self.session_id = session_id


class GameServer:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.address, self.port = reader._transport.get_extra_info("peername")
        self.reader = reader
        self.writer = writer
        
        ## Actual game server data
        self.id = -1
        self.name = ""
        self.server_type = wcps_core.constants.ServerTypes.NONE
        self.current_players = 0
        self.max_players = 0
        self.authorized = False
        self.session_id = -1
        
        if self.max_players > 3600:
            self.max_players = 3600
        
        if self.current_players < 0:
            self.current_players = 0

        ## Send a connection packet
        self.xor_key_send = wcps_core.constants.InternalKeys.XOR_AUTH_SEND
        self.xor_key_receive = wcps_core.constants.InternalKeys.XOR_GAME_SEND
        self._connection = wcps_core.packets.Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))
        asyncio.create_task(self.listen())

    async def authorize(self, server_name: str, server_id:str, server_type: int, current_players: int, max_players: int) -> None:
        self.name = server_name
        self.id = server_id
        self.authorized = True
        self.max_players = max_players
        self.current_players = current_players
        self.server_type =  server_type
        
        ## Add the user to session manager
        session_manager = SessionManager()
        session_id = await session_manager.authorize_server(self)
        self.session_id = session_id

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                await self.disconnect()
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
                    await self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                await self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
            await self.disconnect()

    async def disconnect(self):
        self.writer.close()
        if self.authorized:
            self.authorized = False
            ## Clear the session just in case
            session_manager = SessionManager()
            if await session_manager.is_server_authorized(self.id):
                await session_manager.unauthorize_server(self.id)


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

            ## get all authorized servers
            session_manager = SessionManager()
            all_servers_sessions = session_manager.get_all_authorized_servers()

            # The 2008 client can handle up to 31 servers
            self.append(len(all_servers_sessions)) 

            for session in all_servers_sessions:
                s = session["server"] # Get the actual server
                
                self.append(s.id)  # Server ID
                self.append(s.name)
                self.append(s.address)
                self.append(s.port)
                ## Current pop. Assumed to be x/3600. In the future, maybe
                ## do fractions for servers with smaller capacity
                self.append(s.current_players) 
                self.append(s.server_type)

            self.fill(-1, 4)  # ID?/NAME?/MASTER?/Unknown
            self.append(0)    # unknown
            self.append(0)  # unknown

class InternalGameAuthentication(wcps_core.packets.OutPacket):
    def __init__(self, error_code, s=None):
        super().__init__(
            packet_id=PacketList.INTERNALGAMEAUTHENTICATION, 
            xor_key=wcps_core.constants.InternalKeys.XOR_AUTH_SEND)

        if error_code != wcps_core.constants.ErrorCodes.SUCCESS or not s:
            self.append(error_code)
        else:
            self.append(wcps_core.constants.ErrorCodes.SUCCESS)
            self.append(s.session_id) ## tell the server their session ID 
        
        

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

        ## check if a session already exists for this player
        session_manager = SessionManager()
        is_authorized = await session_manager.is_user_authorized(this_user["username"])

        ## The user is already logged in
        if is_authorized:
            await user.send(ServerList(ServerList.ErrorCodes.ALREADY_LOGGED_IN).build())
        else:
            ## Authenticate it and let him log!
            await user.authorize(
                username=input_id,
                displayname=this_user["displayname"],
                rights=this_user["rights"]
            )
            await user.send(ServerList(wcps_core.constants.ErrorCodes.SUCCESS, u=user).build())


class GameServerAuthHandler(PacketHandler):
    async def process(self, server) -> None:

        error_code = int(self.get_block(0))

        if error_code != wcps_core.constants.ErrorCodes.SUCCESS:
            return

        ## Check if the auth server is already full before anything else
        session_manager = SessionManager()

        servers_registered = len(session_manager.get_all_authorized_servers())

        if servers_registered >= 31:
            logging.error(f"Maximum limit of servers reached. Rejecting...")
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_LIMIT_REACHED).build())
            return
        
        server_id = self.get_block(1)
        server_name = self.get_block(2)
        server_addr = self.get_block(3)
        server_port = self.get_block(4)
        server_type = self.get_block(5)
        current_players = self.get_block(6)
        max_players = self.get_block(7)

        if len(server_name) < 3 or not server_name.isalnum():
            logging.error(f"Invalid server name for ID {server_id} at {server_addr}")
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_ERROR_OTHER).build())
            return
        
        if not server_id or not server_id.isalnum():
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_ERROR_OTHER).build())
            logging.error(f"Invalid server ID {server_id}")
            return

        if not current_players.isdigit() or not max_players.isdigit():
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_ERROR_OTHER).build())
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

        if not (server_type.isdigit() and int(server_type) in valid_servers):
            logging.error(f"Invalid server type: {server_type}")
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.INVALID_SERVER_TYPE).build())
            return
        
        ## get list of servers registered in the DB
        ## server list format is [(id,ip,addr)]
        ##TODO: Potential DDoS here... generate a list that only updates each X?
        ##TODO: check against max. number of authorized servers
        all_active_servers = await get_server_list()
        if not (server_id, server_addr, server_port) in all_active_servers:
            logging.error(f"Unregistered server: {server_addr}:{server_port}")
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.INVALID_SESSION_MATCH).build())
            return

        is_server_authorized = await session_manager.is_server_authorized(server_id)

        if is_server_authorized:
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.ALREADY_AUTHORIZED).build())
            logging.info(f"Server {server_addr} already registered")

        else:
            await server.authorize(
                server_name=server_name,
                server_id=server_id,
                server_type=int(server_type),
                current_players=int(current_players),
                max_players=int(max_players)
            )
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SUCCESS, server).build())
            logging.info(f"Server {server_addr} authenticated as {server.session_id}")


class GameServerAuthHandler(PacketHandler):
    async def process(self, server) -> None:
        print("Received ping from server")

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
    PacketList.INTERNALGAMEAUTHENTICATION: GameServerAuthHandler
}
