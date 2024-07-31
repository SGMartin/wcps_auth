import hashlib

from .base import PacketHandler
from database import get_user_details
from packets.packet_factory import PacketFactory
from packets.packet_list import PacketList
from sessions import SessionManager

from wcps_core.constants import ErrorCodes

class ServerListHandler(PacketHandler):
    async def process(self, user) -> None:
        input_id = self.get_block(2)
        input_pw = self.get_block(3)

        # Validate input ID
        if len(input_id) < 3 or not input_id.isalnum():
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.ENTER_ID_ERROR)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Validate input password
        if len(input_pw) < 3:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.ENTER_PASSWORD_ERROR)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Retrieve user details
        this_user = await get_user_details(input_id)
        if not this_user:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.WRONG_USER)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Hash password and verify
        password_to_hash = f"{input_pw}{this_user['salt']}".encode("utf-8")
        hashed_password = hashlib.sha256(password_to_hash).hexdigest()
        if this_user["password"] != hashed_password:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.WRONG_PW)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Check user rights
        if this_user["rights"] == 0:
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.BANNED)
            await user.send(packet.build())
            await user.disconnect()
            return

        # Check session status
        session_manager = SessionManager()
        is_authorized = await session_manager.is_user_authorized(this_user["username"])
        session_id = await session_manager.get_user_session_id(this_user["username"])
        is_activated_session = await session_manager.is_user_session_activated(session_id)

        if not is_authorized or (is_authorized and session_id is not None and not is_activated_session):
            if is_authorized:
                await session_manager.unauthorize_user(this_user["username"])
            
            await user.authorize(
                username=this_user["username"],
                displayname=this_user["displayname"],
                rights=this_user["rights"]
            )
            packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ErrorCodes.SUCCESS, u=user)
            await user.send(packet.build())
            await user.disconnect()
        else:
            if is_activated_session:
                packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.ALREADY_LOGGED_IN)
            else:
                packet = PacketFactory.create_packet(PacketList.SERVER_LIST, ServerList.ErrorCodes.ILLEGAL_EXCEPTION)
            
            await user.send(packet.build())
            await user.disconnect()
