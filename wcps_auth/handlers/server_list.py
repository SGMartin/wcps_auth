import hashlib

from wcps_auth.handlers.base import PacketHandler
from wcps_auth.database import get_user_details
from wcps_auth.packets.packet_factory import PacketFactory
from wcps_auth.packets.packet_list import PacketList
from wcps_auth.sessions import SessionManager

from wcps_core.constants import ErrorCodes as corerr
from wcps_auth.error_codes import ServerListError

class ServerListHandler(PacketHandler):
    async def process(self, user) -> None:
        input_id = self.get_block(2)
        input_pw = self.get_block(3)

        # Validate input ID
        if len(input_id) < 3 or not input_id.isalnum():
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.ENTER_ID_ERROR)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Validate input password
        if len(input_pw) < 3:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.ENTER_PASSWORD_ERROR)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Retrieve user details
        this_user = await get_user_details(input_id)
        if not this_user:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.WRONG_USER)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Hash password and verify
        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()
        if this_user["password"] != hashed_password:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.WRONG_PW)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Check user rights
        if this_user["rights"] == 0:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.BANNED)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Check session status
        session_manager = SessionManager()
        is_authorized = await session_manager.is_user_authorized(this_user["username"])
        session_id = await session_manager.get_user_session_id(this_user["username"])
        is_activated_session = await session_manager.is_user_session_activated(session_id)

        # When players leave the server selection menu or are rejected by a server
        # their session will exists already after reaching this code block, 
        # but it won't be active

        if not is_authorized or (is_authorized and session_id is not None and not is_activated_session):
            if is_authorized:
                await session_manager.unauthorize_user(this_user["username"])
            
            await user.authorize(
                username=this_user["username"],
                displayname=this_user["displayname"],
                rights=this_user["rights"]
            )
            ## Nickname is not set. Send new nickname packet
            if not this_user["displayname"]:
                packet = PacketFactory.create_packet(
                    packet_id=PacketList.SERVER_LIST, 
                    error_code=ServerListError.NEW_NICKNAME
                    )
                await user.send(packet.build())
            else:
                packet = PacketFactory.create_packet(PacketList.SERVER_LIST, corerr.SUCCESS, u=user)
                await user.send(packet.build())
                await user.disconnect()
        else:
            if is_activated_session:
                packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.ALREADY_LOGGED_IN)
            else:
                packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerListError.ILLEGAL_EXCEPTION)
            
            await user.send(packet.build())
            await user.disconnect()
