import abc
import asyncio

import wcps_core

from database import get_user_details, get_server_list
from sessions import SessionManager
from packets import PacketList
from entities import BaseNetworkEntity

class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: wcps_core.packets.InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, BaseNetworkEntity):
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
            await user.disconnect()
            return

        if len(input_pw) < 3:
            await user.send(ServerList(ServerList.ErrorCodes.ENTER_PASSWORD_ERROR).build())
            await user.disconnect()
            return

        this_user = await get_user_details(input_id)

        if not this_user:
            await user.send(ServerList(ServerList.ErrorCodes.WRONG_USER).build())
            await user.disconnect()
            return

        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()

        if this_user["password"] != hashed_password:
            await user.send(ServerList(ServerList.ErrorCodes.WRONG_PW).build())
            await user.disconnect()
            return

        if this_user["rights"] == 0:
            await user.send(ServerList(ServerList.ErrorCodes.BANNED).build())
            await user.disconnect()
            return

        ## check if a session already exists for this player
        session_manager = SessionManager()
        is_authorized = await session_manager.is_user_authorized(this_user["username"])
        session_id = await session_manager.get_user_session_id(this_user["username"])
        ## Will be false if session does not exists
        is_activated_session = await session_manager.is_user_session_activated(session_id)

        ## First log OR relog after game server reject
        if not is_authorized or (is_authorized and session_id is not None and not is_activated_session):
            if is_authorized: ## destroy the previous session first
                await session_manager.unauthorize_user(this_user["username"])
            
            ## first time authorize or reauthorize
            await user.authorize(
                username=this_user["username"],
                displayname=this_user["displayname"],
                rights=this_user["rights"]
            )
            await user.send(ServerList(wcps_core.constants.ErrorCodes.SUCCESS, u=user).build())
            ## Can be safely disconnect after this packet
            await user.disconnect()
        else:
            if is_activated_session:
                await user.send(ServerList(ServerList.ErrorCodes.ALREADY_LOGGED_IN).build())
            else:
                await user.send(ServerList(ServerList.ErrorCodes.ILLEGAL_EXCEPTION).build())

            await user.disconnect()


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
            await server.disconnect()
            return
        
        if not server_id or not server_id.isalnum():
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_ERROR_OTHER).build())
            logging.error(f"Invalid server ID {server_id}")
            await server.disconnect()
            return

        if not current_players.isdigit() or not max_players.isdigit():
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SERVER_ERROR_OTHER).build())
            logging.error(f"Invalid value/s reported ¨{current_players}/{max_players}")
            await server.disconnect()
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
            await server.disconnect()
            return
        
        ## get list of servers registered in the DB
        ## server list format is [(id,ip,addr)]
        ##TODO: Potential DDoS here... generate a list that only updates each X?
        ##TODO: check against max. number of authorized servers
        all_active_servers = await get_server_list()
        if not (server_id, server_addr, server_port) in all_active_servers:
            logging.error(f"Unregistered server: {server_addr}:{server_port}")
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.INVALID_SESSION_MATCH).build())
            await server.disconnect()
            return

        is_server_authorized = await session_manager.is_server_authorized(server_id)

        if is_server_authorized:
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.ALREADY_AUTHORIZED).build())
            logging.info(f"Server {server_addr} already registered")
            await server.disconnect()

        else:
            ##TODO: Move this to authorize and improve the data structure
            server.address = server_addr
            server.port = server_port
            await server.authorize(
                server_name=server_name,
                server_id=server_id,
                server_type=int(server_type),
                current_players=int(current_players),
                max_players=int(max_players)
            )
            await server.send(InternalGameAuthentication(wcps_core.constants.ErrorCodes.SUCCESS, server).build())
            logging.info(f"Server {server.address}:{server.port} authenticated as {server.session_id}")


class GameServerStatusHandler(PacketHandler):
    async def process(self, server) -> None:
        ## Check if the server is authorized
        if server.authorized:
            server_time = self.get_block(1)
            server_id   = self.get_block(2)
            current_players = self.get_block(3)
            current_rooms = self.get_block(4)
            
            ##TODO: Update more data
            server.current_players = int(current_players)
        else:
            logging.info(f"Ping from unauthorized server ignored")
            await server.disconnect()

class InternalClientAuthRequestHandler(PacketHandler):
    async def process(self, server) -> None:
        if server.authorized:
            error_code = int(self.get_block(0))
            reported_session_id = int(self.get_block(1))
            reported_username = self.get_block(2)
            reported_rights = int(self.get_block(3))

            session_manager = SessionManager()
            has_login_session = await session_manager.is_user_authorized(reported_username)
            error_to_report = wcps_core.constants.ErrorCodes.INVALID_KEY_SESSION

            if not has_login_session:
                error_to_report = wcps_core.constants.ErrorCodes.INVALID_KEY_SESSION

            stored_session_id = await session_manager.get_user_session_id(reported_username)
            is_activated_session = await session_manager.is_user_session_activated(stored_session_id)

            if reported_session_id == stored_session_id:
                if is_activated_session:
                    ## check if the server wants us to unauthorize the user
                    if error_code == wcps_core.constants.ErrorCodes.END_CONNECTION:
                        await session_manager.unauthorize_user(reported_username)
                        return
                        
                    error_to_report = wcps_core.constants.ErrorCodes.ALREADY_AUTHORIZED
                else:
                    error_to_report = wcps_core.constants.ErrorCodes.SUCCESS
                    ## Activate the sesssion
                    await session_manager.activate_user_session(stored_session_id)
            else:
                error_to_report = wcps_core.constants.ErrorCodes.INVALID_SESSION_MATCH
            
            ##TODO sanitize rights against 
            # this_user = await session_manager.get_user_by_session_id(stored_session_id)
            
            await server.send(InternalClientAuthentication(
                error_to_report,
                reported_session=reported_session_id,
                reported_user=reported_username,
                reported_rights=reported_rights
                ).build()
                )
        else:
            logging.info(f"Unauthorized client authorization request from {server.address}")
            server.disconnect()


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
    PacketList.INTERNALGAMEAUTHENTICATION: GameServerAuthHandler,
    PacketList.INTERNALGAMESTATUS: GameServerStatusHandler,
    PacketList.INTERNALPLAYERAUTHENTICATION: InternalClientAuthRequestHandler
}