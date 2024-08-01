from wcps_core.constants import ErrorCodes

from wcps_auth.handlers.base import PacketHandler
from wcps_auth.sessions import SessionManager
from wcps_auth.packets.packet_factory import PacketFactory
from wcps_auth.packets.packet_list import PacketList


class InternalClientAuthRequestHandler(PacketHandler):
    async def process(self, server) -> None:
        if server.authorized:
            error_code = int(self.get_block(0))
            reported_session_id = int(self.get_block(1))
            reported_username = self.get_block(2)
            reported_rights = int(self.get_block(3))

            session_manager = SessionManager()
            has_login_session = await session_manager.is_user_authorized(
                reported_username
            )
            error_to_report = ErrorCodes.INVALID_KEY_SESSION

            if not has_login_session:
                error_to_report = ErrorCodes.INVALID_KEY_SESSION

            stored_session_id = await session_manager.get_user_session_id(
                reported_username
            )
            is_activated_session = await session_manager.is_user_session_activated(
                stored_session_id
            )

            if reported_session_id == stored_session_id:
                if is_activated_session:
                    ## check if the server wants us to unauthorize the user
                    if error_code == ErrorCodes.END_CONNECTION:
                        await session_manager.unauthorize_user(reported_username)
                        return

                    error_to_report = ErrorCodes.ALREADY_AUTHORIZED
                else:
                    error_to_report = ErrorCodes.SUCCESS
                    ## Activate the sesssion
                    await session_manager.activate_user_session(stored_session_id)
            else:
                error_to_report = ErrorCodes.INVALID_SESSION_MATCH

            ##TODO sanitize rights against
            # this_user = await session_manager.get_user_by_session_id(stored_session_id)
            packet = PacketFactory.create_packet(
                PacketList.INTERNALPLAYERAUTHENTICATION,
                error_to_report,
                reported_session=reported_session_id,
                reported_user=reported_username,
                reported_rights=reported_rights,
            )
            await server.send(packet.build())
        else:
            logging.info(
                f"Unauthorized client authorization request from {server.address}"
            )
            server.disconnect()
