# handlers/handler_factory.py

import logging

from wcps_auth.packets.packet_list import PacketList

from .base import PacketHandler
from .launcher import LauncherHandler
from .server_list import ServerListHandler
from .internal_server_auth import GameServerAuthHandler
from .internal_server_status import GameServerStatusHandler
from .internal_client_auth import InternalClientAuthRequestHandler

# Dictionary to map packet IDs to handler classes
HANDLER_MAP = {
    PacketList.LAUNCHER: LauncherHandler,  # Replace with actual packet ID values
    PacketList.SERVER_LIST: ServerListHandler,
    PacketList.INTERNALGAMEAUTHENTICATION: GameServerAuthHandler,
    PacketList.INTERNALGAMESTATUS: GameServerStatusHandler,
    PacketList.INTERNALPLAYERAUTHENTICATION: InternalClientAuthRequestHandler
}

def get_handler_for_packet(packet_id: int) -> PacketHandler:
    handler_class = HANDLER_MAP.get(packet_id)
    if handler_class:
        return handler_class()
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None
