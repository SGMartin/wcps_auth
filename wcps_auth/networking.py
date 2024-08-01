import asyncio
import logging

import wcps_core.constants
import wcps_core.packets

from wcps_auth.config import settings
from wcps_auth.entities import BaseNetworkEntity
from wcps_auth.sessions import SessionManager

from wcps_auth.handlers import get_handler_for_packet

logging.basicConfig(level=logging.INFO)


class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3


async def start_listeners():
    try:
        client_server = await asyncio.start_server(
            User, settings().server_ip, wcps_core.constants.Ports.AUTH_CLIENT
        )
        logging.info("Client listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.AUTH_CLIENT}")
        return

    try:
        server_listener = await asyncio.start_server(
            GameServer, settings().server_ip, wcps_core.constants.Ports.INTERNAL
        )
        logging.info("Server listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.INTERNAL}")
        return

    await asyncio.gather(client_server.serve_forever(), server_listener.serve_forever())


class User(BaseNetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(reader, writer, ClientXorKeys.SEND, ClientXorKeys.RECEIVE)
        self.username = "none"
        self.displayname = ""
        self.rights = 0

    async def authorize(self, username: str, displayname: str, rights: int):
        self.username = username
        self.displayname = displayname
        self.rights = rights
        self.authorized = True
        session_manager = SessionManager()
        self.session_id = await session_manager.authorize_user(self)

    async def update_displayname(self, new_nickname: str):
        self.displayname = new_nickname

        session_manager = SessionManager()
        if await session_manager.is_user_authorized(self.username):
            this_user = await session_manager.get_user_by_session_id(self.session_id)
            # Just in case some random disconnection happened lol
            this_user.displayname = new_nickname

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)


class GameServer(BaseNetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(
            reader,
            writer,
            wcps_core.constants.InternalKeys.XOR_AUTH_SEND,
            wcps_core.constants.InternalKeys.XOR_GAME_SEND,
        )
        self.address = None
        self.port = None
        self.name = ""
        self.id = -1
        self.server_type = wcps_core.constants.ServerTypes.NONE
        self.current_players = 0
        self.max_players = 0

    async def authorize(
        self,
        server_name: str,
        server_id: str,
        server_type: int,
        current_players: int,
        max_players: int,
    ):
        self.name = server_name
        self.id = server_id
        self.authorized = True
        self.max_players = max_players
        self.current_players = current_players
        self.server_type = server_type

        session_manager = SessionManager()
        self.session_id = await session_manager.authorize_server(self)

    async def disconnect(self):
        await super().disconnect()
        if self.authorized:
            self.authorized = False
            session_manager = SessionManager()
            if await session_manager.is_server_authorized(self.id):
                await session_manager.unauthorize_server(self.id)

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)
