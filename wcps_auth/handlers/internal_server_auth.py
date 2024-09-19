import logging

from wcps_core.constants import ErrorCodes, ServerTypes

from wcps_auth.packets.packet_factory import PacketFactory
from wcps_auth.packets.packet_list import PacketList

from wcps_auth.handlers.base import PacketHandler
from wcps_auth.database import get_server_list
from wcps_auth.sessions import SessionManager


class GameServerAuthHandler(PacketHandler):
    async def process(self, server) -> None:

        error_code = int(self.get_block(0))

        if error_code != ErrorCodes.SUCCESS:
            return

        # Check if the auth server is already full before anything else
        session_manager = SessionManager()

        servers_registered = len(session_manager.get_all_authorized_servers())

        if servers_registered >= 31:
            logging.error("Maximum limit of servers reached. Rejecting...")
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.SERVER_LIMIT_REACHED
            )
            await server.send(packet.build())
            return

        server_id = self.get_block(1)
        server_name = self.get_block(2)
        server_addr = self.get_block(3)
        server_port = int(self.get_block(4))
        server_type = self.get_block(5)
        current_players = self.get_block(6)
        max_players = self.get_block(7)

        if len(server_name) < 3 or not server_name.isalnum():
            logging.error(f"Invalid server name for ID {server_id} at {server_addr}")
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.SERVER_ERROR_OTHER
            )
            await server.send(packet.build())
            await server.disconnect()
            return

        if not server_id or not server_id.isalnum():
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.SERVER_ERROR_OTHER
            )
            await server.send(packet.build())
            logging.error(f"Invalid server ID {server_id}")
            await server.disconnect()
            return

        if not current_players.isdigit() or not max_players.isdigit():
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.SERVER_ERROR_OTHER
            )
            await server.send(packet.build())
            logging.error(f"Invalid value/s reported ¨{current_players}/{max_players}")
            await server.disconnect()
            return

        valid_servers = [
            ServerTypes.ENTIRE,
            ServerTypes.ADULT,
            ServerTypes.CLAN,
            ServerTypes.TEST,
            ServerTypes.DEVELOPMENT,
            ServerTypes.TRAINEE,
        ]

        if not (server_type.isdigit() and int(server_type) in valid_servers):
            logging.error(f"Invalid server type: {server_type}")
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.INVALID_SERVER_TYPE
            )
            await server.send(packet.build())
            await server.disconnect()
            return

        # get list of servers registered in the DB
        # server list format is [(id,ip,addr)]
        # TODO: Potential DDoS here... generate a list that only updates each X?
        # TODO: check against max. number of authorized servers
        all_active_servers = await get_server_list()
        if not (server_id, server_addr, server_port) in all_active_servers:
            logging.error(f"Unregistered server: {server_addr}:{server_port}")
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.INVALID_SESSION_MATCH
            )
            await server.send(packet.build())
            await server.disconnect()
            return

        is_server_authorized = await session_manager.is_server_authorized(server_id)

        if is_server_authorized:
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.ALREADY_AUTHORIZED
            )
            await server.send(packet.build())
            logging.info(f"Server {server_addr} already registered")
            await server.disconnect()

        else:
            # TODO: Move this to authorize and improve the data structure
            server.address = server_addr
            server.port = server_port
            await server.authorize(
                server_name=server_name,
                server_id=server_id,
                server_type=int(server_type),
                current_players=int(current_players),
                max_players=int(max_players),
            )
            packet = PacketFactory.create_packet(
                PacketList.INTERNALGAMEAUTHENTICATION, ErrorCodes.SUCCESS, server
            )
            await server.send(packet.build())
            logging.info(
                f"Server {server.address}:{server.port} authenticated as {server.session_id}"
            )
